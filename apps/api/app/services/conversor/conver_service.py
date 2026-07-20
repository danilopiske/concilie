"""Orquestrador: parser → fallback Gemini → xlsx."""

from __future__ import annotations

import logging
from typing import Optional

from app.services.conversor.gemini_fallback import processar_linhas_nao_reconhecidas
from app.services.conversor.rede_parser import RedeParser, ResultadoParsing
from app.services.conversor.xlsx_builder import gerar_zip, nome_arquivo_saida

logger = logging.getLogger(__name__)


def _agrupar_por_secao(
    linhas_nao_rec: list[tuple[int, str]]
) -> dict[str, list[tuple[int, str]]]:
    """Heurística simples para tentar associar linhas soltas à seção mais provável."""
    # Sem contexto de seção aqui, agrupamos tudo como "credito" para o Gemini decidir
    return {"credito": linhas_nao_rec}


def processar_arquivo(conteudo: bytes, nome_arquivo: str) -> ResultadoParsing:
    try:
        texto = conteudo.decode("latin-1")
    except Exception:
        texto = conteudo.decode("utf-8", errors="replace")

    parser = RedeParser(nome_arquivo=nome_arquivo)
    resultado = parser.parse(texto)

    linhas_nao_rec = resultado.linhas_nao_reconhecidas
    if linhas_nao_rec:
        logger.info(
            "%s: %d linha(s) não reconhecida(s) pelo parser — enviando ao Gemini",
            nome_arquivo, len(linhas_nao_rec)
        )
        # Por simplicidade, tentamos interpretar como crédito (Gemini decide)
        _processar_fallback(linhas_nao_rec, resultado)

    logger.info(
        "%s: crédito=%d débito=%d pagamentos=%d tarifas=%d",
        nome_arquivo,
        len(resultado.vendas_credito),
        len(resultado.vendas_debito),
        len(resultado.pagamentos),
        len(resultado.tarifas_debitos),
    )
    return resultado


def _processar_fallback(
    linhas: list[tuple[int, str]], resultado: ResultadoParsing
) -> None:
    from app.services.conversor.rede_parser import (
        Pagamento, TarifaDebito, VendaCredito, VendaDebito, _parse_data, _parse_valor
    )

    registros = processar_linhas_nao_reconhecidas(
        linhas, "credito", resultado.estabelecimento, ""
    )

    for reg in registros:
        # Tenta encaixar no tipo correto pelo conteúdo
        if "data_venda" in reg and "bandeira" in reg:
            resultado.vendas_credito.append(VendaCredito(
                estabelecimento=reg.get("estabelecimento", resultado.estabelecimento),
                origem_arquivo=reg.get("origem_arquivo", ""),
                data_venda=_parse_data(reg.get("data_venda", "")),
                data_recebimento=_parse_data(reg.get("data_recebimento", "")),
                resumo_vendas=reg.get("resumo_vendas", ""),
                bandeira=reg.get("bandeira", ""),
                quantidade=reg.get("quantidade", 0),
                modalidade=reg.get("modalidade", ""),
                valor_bruto=reg.get("valor_bruto", 0.0),
                valor_correcao=reg.get("valor_correcao", 0.0),
                valor_liquido=reg.get("valor_liquido", 0.0),
                tipo_lancamento=reg.get("tipo_lancamento", "EFETUADO"),
            ))
        elif "banco_agencia_conta" in reg and "ordem_credito" in reg:
            resultado.pagamentos.append(Pagamento(
                estabelecimento=reg.get("estabelecimento", resultado.estabelecimento),
                origem_arquivo=reg.get("origem_arquivo", ""),
                data_recebimento=_parse_data(reg.get("data_recebimento", "")),
                ordem_credito=reg.get("ordem_credito", ""),
                valor_liquido=reg.get("valor_liquido", 0.0),
                banco_agencia_conta=reg.get("banco_agencia_conta", ""),
            ))


def converter_arquivos(arquivos: list[tuple[str, bytes]]) -> tuple[bytes, str]:
    """Processa N arquivos TXT e retorna (zip_bytes, nome_arquivo) com os 4 xlsx separados."""
    resultados = []
    for nome, conteudo in arquivos:
        resultado = processar_arquivo(conteudo, nome)
        resultados.append(resultado)

    zip_bytes = gerar_zip(resultados)
    nome = nome_arquivo_saida(resultados)
    return zip_bytes, nome
