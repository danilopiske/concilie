from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.database import engine


class AIService:

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
             print("Warning: OPENAI_API_KEY not found in settings. AI features will be disabled.")
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
                print(f"Error initializing ChatOpenAI: {e}")
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

            print(f"Error in AI analysis: {e}")
            return {
                "answer": f"Desculpe, não consegui processar sua pergunta corretamente. Tente ser mais específico. (Erro técnico: {str(e)[:100]}...)"
            }
