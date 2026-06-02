"""Fallback Gemini Flash para linhas não reconhecidas pelo parser posicional."""
from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_MAX_LINHAS_POR_CHAMADA = 20
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _call_gemini(prompt: str) -> Optional[str]:
    from app.core.config import settings
    if not settings.GEMINI_API_KEY:
        return None
    model = settings.GEMINI_MODEL or "gemini-2.5-flash"
    url = _GEMINI_URL.format(model=model)
    try:
        resp = httpx.post(
            url,
            params={"key": settings.GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.warning("Gemini fallback indisponível: %s", e)
        return None


_PROMPT_TEMPLATE = """Você é um parser de extratos bancários da credenciadora Rede (Brasil).
Analise as linhas abaixo que não foram reconhecidas pelo parser posicional.
A seção atual do extrato é: {secao}

Linhas não reconhecidas:
{linhas}

Retorne um JSON com a lista de registros extraídos no formato abaixo.
Para seção "credito" ou "debito":
{{"registros": [{{"data_venda": "DD/MM/AAAA", "data_recebimento": "DD/MM/AAAA",
  "resumo_vendas": "string", "bandeira": "XX", "quantidade": 0,
  "modalidade": "string", "valor_bruto": 0.0, "valor_correcao": 0.0,
  "valor_liquido": 0.0, "banco_agencia_conta": ""}}]}}

Para seção "financeiro":
{{"registros": [{{"data_recebimento": "DD/MM/AAAA", "ordem_credito": "string",
  "valor_liquido": 0.0, "banco_agencia_conta": "string"}}]}}

Para seção "tarifa":
{{"registros": [{{"data_inclusao": "DD/MM/AAAA", "data_pagamento": "DD/MM/AAAA",
  "motivo_debito": "string", "resumo": "string",
  "valor_devido": 0.0, "valor_debitado": 0.0, "meio_pagamento": "string"}}]}}

Se não houver dados válidos nas linhas, retorne {{"registros": []}}.
Retorne APENAS o JSON, sem texto adicional."""


def processar_linhas_nao_reconhecidas(
    linhas: list[tuple[int, str]],
    secao: str,
    estabelecimento: str,
    origem_arquivo: str,
) -> list[dict]:
    if not linhas:
        return []

    # Fallback desabilitado: evita timeouts no processamento síncrono
    logger.debug("Gemini fallback desabilitado — %d linha(s) ignorada(s) na seção '%s'", len(linhas), secao)
    return []

    resultados = []
    for i in range(0, len(linhas), _MAX_LINHAS_POR_CHAMADA):
        lote = linhas[i:i + _MAX_LINHAS_POR_CHAMADA]
        lote_texto = '\n'.join(f"[{num}] {txt}" for num, txt in lote)
        prompt = _PROMPT_TEMPLATE.format(secao=secao, linhas=lote_texto)

        texto = _call_gemini(prompt)
        if not texto:
            logger.warning("Gemini fallback sem resposta — %d linha(s) ignorada(s)", len(lote))
            continue

        try:
            texto = texto.strip()
            if texto.startswith("```"):
                texto = '\n'.join(texto.split('\n')[1:])
            if texto.endswith("```"):
                texto = '\n'.join(texto.split('\n')[:-1])
            dados = json.loads(texto)
            for reg in dados.get("registros", []):
                reg["estabelecimento"] = estabelecimento
                reg["origem_arquivo"] = origem_arquivo
                resultados.append(reg)
        except Exception as e:
            logger.error("Erro ao parsear resposta Gemini (lote %d): %s", i, e)

    return resultados
