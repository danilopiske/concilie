import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente especialista em conciliação financeira de cartões de crédito e débito no Brasil.
Você analisa dados de transações de adquirentes (Cielo, Rede, Stone, GetNet, etc.) e identifica cobranças abusivas de MDR (taxa de desconto).
Responda sempre em português brasileiro, de forma clara e objetiva.
Use os dados fornecidos no contexto para responder. Não invente dados.
Ao final de cada resposta, sugira 2-3 perguntas de follow-up relevantes no seguinte formato JSON (após o texto da resposta):
{"sugestoes": ["pergunta 1", "pergunta 2", "pergunta 3"]}"""

# Rate limiting em memória
_rate_limit: dict = defaultdict(list)


def check_rate_limit(user_id: str, max_per_minute: int = 10) -> bool:
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=1)
    _rate_limit[user_id] = [t for t in _rate_limit[user_id] if t > window_start]
    if len(_rate_limit[user_id]) >= max_per_minute:
        return False
    _rate_limit[user_id].append(now)
    return True


class AIService:

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
             logger.warning("OPENAI_API_KEY not found in settings. AI features will be disabled.")
             self.llm = None
        else:
            try:
                # Initialize LLM with support for custom base URL (e.g. Abacus.AI)
                self.llm = ChatOpenAI(
                    model=settings.AI_MODEL,
                    temperature=0,
                    api_key=self.api_key,
                    base_url=settings.OPENAI_API_BASE,
                    model_kwargs={"stop": ["\nObservation:", "Observation:", "Observation:\n"]}
                )
            except Exception as e:
                logger.error("Error initializing ChatOpenAI: %s", e)
                self.llm = None


    def _handle_error(self, error) -> str:
        # Custom error handler to recover from "Both Final Answer and Action" errors
        str_error = str(error)

        # Check if the model actually gave us the Final Answer inside the error message
        if "Final Answer:" in str_error:
            # Extract everything after "Final Answer:"
            return str_error.split("Final Answer:")[-1].strip()

        # If the model gave an observation/thought that looks like an answer
        if "Observation:" in str_error and "Thought:" not in str_error:
             return str_error.split("Observation:")[-1].strip()

        return f"Desculpe, tive um problema técnico ao processar sua resposta. Tente reformular a pergunta. (Erro: {str_error[:100]}...)"

    async def analyze(self, question: str) -> dict:
        """
        Analyze data using SQL Agent (Real-time Database)
        """
        if not self.llm:
            return {
                "answer": "A chave da OpenAI não está configurada. Por favor, adicione OPENAI_API_KEY ao arquivo .env no backend."
            }

        try:
            # Connect directly to Database (Real-time)
            # include_tables limits scope for safety and focus
            db = SQLDatabase(engine, include_tables=['vendas_processadas', 'clientes'])

            # Instructions for the agent
            prefix = """
            Você é um analista de dados especialista em finanças e conciliação de cartões.
            Sua missão é ajudar o usuário a entender os dados do banco de dados MySQL em TEMPO REAL.

            Tabelas Disponíveis:
            - `vendas_processadas`: Contém as vendas importadas (NSU, valor, bandeira, adquirente, etc).
            - `clientes`: Contém os dados cadastrais (nome, cnpj, id).

            Regras Importantes:
            1. SEMPRE responda em Português do Brasil (pt-BR).
            2. Se a pergunta for sobre "vendas" ou "faturamento", consulte a tabela `vendas_processadas`.
            3. Se a pergunta for sobre "clientes" ou "cadastro", consulte a tabela `clientes`.
            4. Se precisar cruzar dados (ex: vendas de um cliente), faça um JOIN entre `vendas_processadas.cliente_id` e `clientes.cliente_id`.
            5. Use formatação Markdown para tabelas.
            6. Seja direto e objetivo.
            7. Ao responder, comece dizendo "Consultando a base de dados em tempo real..." para o usuário saber que é live.
            """

            # Create SQL Agent
            agent = create_sql_agent(
                llm=self.llm,
                db=db,
                agent_type="zero-shot-react-description",
                verbose=True,
                handle_parsing_errors=self._handle_error,
                limit_executions=10,
                prefix=prefix
            )

            # Run Agent
            result = agent.invoke(question)

            return {
                "answer": result.get("output", "Desculpe, não consegui analisar os dados."),
                "generated_code": ""
            }

        except Exception as e:
            error_str = str(e)
            if "Final Answer:" in error_str:
                return {
                    "answer": error_str.split("Final Answer:")[-1].strip().split("For troubleshooting")[0].strip()
                }

            logger.error("Error in AI analysis: %s", e)
            return {
                "answer": f"Desculpe, não consegui processar sua pergunta corretamente. Tente ser mais específico. (Erro técnico: {str(e)[:100]}...)"
            }

    def montar_contexto(self, processamento_id: str, db: Session) -> tuple[str, dict]:
        """Monta sumário estruturado do processamento para o contexto do LLM."""
        from app.models.vendas_calculos import VendasCalculos

        try:
            rows = (
                db.query(VendasCalculos)
                .filter(VendasCalculos.calc_id == processamento_id)
                .all()
            )
        except Exception as e:
            logger.warning("Erro ao buscar VendasCalculos para contexto: %s", e)
            rows = []

        if not rows:
            contexto = f"Processamento ID: {processamento_id}\nNenhum dado encontrado para este processamento."
            return contexto, {}

        total_tx = len(rows)
        total_valor = sum(float(r.vl_venda or 0) for r in rows)
        total_perda = sum(float(r.perda or 0) for r in rows)

        # Agrupamento por bandeira
        grupos: dict = defaultdict(lambda: {"tx": 0, "valor": 0.0, "soma_taxa": 0.0, "perda": 0.0, "n_taxa": 0})
        for r in rows:
            chave = f"{r.bandeira or 'Desconhecida'} {r.forma_pagamento or ''}".strip()
            g = grupos[chave]
            g["tx"] += 1
            g["valor"] += float(r.vl_venda or 0)
            g["perda"] += float(r.perda or 0)
            if r.tx_venda:
                g["soma_taxa"] += float(r.tx_venda)
                g["n_taxa"] += 1

        linhas_grupos = []
        for nome, g in sorted(grupos.items(), key=lambda x: -x[1]["tx"])[:10]:
            taxa_media = g["soma_taxa"] / g["n_taxa"] if g["n_taxa"] else 0
            perda_str = f", perda R$ {g['perda']:,.2f}" if g["perda"] > 0.01 else ""
            linhas_grupos.append(
                f"  - {nome}: {g['tx']} transações, R$ {g['valor']:,.2f}, taxa média {taxa_media:.2f}%{perda_str}"
            )

        dados_contexto = {
            "total_transacoes": total_tx,
            "valor_total": round(total_valor, 2),
            "perda_total": round(total_perda, 2),
        }

        contexto = (
            f"Processamento ID: {processamento_id}\n"
            f"Total transações: {total_tx:,}\n"
            f"Valor total: R$ {total_valor:,.2f}\n"
            f"Perda/excesso total: R$ {total_perda:,.2f}\n"
            f"Por bandeira/modalidade (top 10):\n"
            + "\n".join(linhas_grupos)
        )
        return contexto, dados_contexto

    def chat(
        self,
        mensagem: str,
        contexto: str,
        historico: Optional[List[dict]] = None,
        max_tentativas: int = 3,
        timeout_segundos: int = 30,
    ) -> tuple[str, List[str]]:
        """Envia mensagem ao Gemini com contexto do processamento.

        Implementa retry com backoff exponencial (max 3 tentativas) e
        timeout de 30s por chamada. Histórico limitado a 20 mensagens.
        """
        if not settings.GEMINI_API_KEY:
            return (
                "A chave GEMINI_API_KEY não está configurada. Adicione ao arquivo .env.",
                [],
            )

        # Limitar histórico para evitar overflow de tokens
        MAX_HISTORY = 20
        historico_limitado = (historico or [])[-MAX_HISTORY:]

        try:
            import google.generativeai as genai  # lazy import — opcional

            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )

            gemini_history = []
            for msg in historico_limitado:
                role = msg.get("role", "user")
                gemini_history.append({
                    "role": role if role == "user" else "model",
                    "parts": [msg.get("content", "")],
                })

            chat_session = model.start_chat(history=gemini_history)
            prompt = f"Contexto dos dados:\n{contexto}\n\nPergunta: {mensagem}" if contexto else mensagem

            # Retry com backoff exponencial
            ultimo_erro: Exception | None = None
            for tentativa in range(max_tentativas):
                try:
                    response = chat_session.send_message(
                        prompt,
                        request_options={"timeout": timeout_segundos},
                    )
                    texto = response.text
                    break
                except Exception as e:
                    ultimo_erro = e
                    if tentativa < max_tentativas - 1:
                        logger.warning(
                            "Gemini tentativa %d/%d falhou: %s — aguardando %ds",
                            tentativa + 1, max_tentativas, e, 2 ** tentativa,
                        )
                        time.sleep(2 ** tentativa)
            else:
                logger.error("Gemini falhou após %d tentativas: %s", max_tentativas, ultimo_erro)
                return "Serviço temporariamente indisponível. Tente novamente em instantes.", []

            # Extrair sugestões do JSON no final da resposta
            sugestoes: List[str] = []
            match = re.search(r'\{[^{}]*"sugestoes"[^{}]*\}', texto, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group())
                    sugestoes = parsed.get("sugestoes", [])
                    texto = texto[: match.start()].strip()
                except json.JSONDecodeError:
                    pass

            return texto, sugestoes

        except Exception as e:
            logger.error("Erro no chat Gemini: %s", e)
            return f"Erro ao processar resposta: {str(e)[:200]}", []
