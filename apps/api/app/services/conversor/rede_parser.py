"""Parser posicional para extratos TXT da credenciadora Rede."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Tipos de dados ─────────────────────────────────────────────────────────────

@dataclass
class VendaCredito:
    estabelecimento: str
    origem_arquivo: str
    data_venda: Optional[datetime]
    data_recebimento: Optional[datetime]
    resumo_vendas: str
    bandeira: str
    quantidade: int
    modalidade: str
    valor_bruto: float
    valor_correcao: float
    valor_liquido: float
    tipo_lancamento: str


@dataclass
class VendaDebito:
    estabelecimento: str
    origem_arquivo: str
    data_venda: Optional[datetime]
    data_recebimento: Optional[datetime]
    resumo_vendas: str
    bandeira: str
    quantidade: int
    modalidade: str
    valor_bruto: float
    valor_saque: float
    valor_liquido: float
    banco_agencia_conta: str


@dataclass
class Pagamento:
    estabelecimento: str
    origem_arquivo: str
    data_recebimento: Optional[datetime]
    ordem_credito: str
    valor_liquido: float
    banco_agencia_conta: str


@dataclass
class TarifaDebito:
    estabelecimento: str
    origem_arquivo: str
    data_inclusao: Optional[datetime]
    data_pagamento: Optional[datetime]
    motivo_debito: str
    resumo: str
    valor_devido: float
    valor_debitado: float
    meio_pagamento: str


@dataclass
class ResultadoParsing:
    estabelecimento: str = ""
    periodo: str = ""
    data_emissao: Optional[datetime] = None
    vendas_credito: list[VendaCredito] = field(default_factory=list)
    vendas_debito: list[VendaDebito] = field(default_factory=list)
    pagamentos: list[Pagamento] = field(default_factory=list)
    tarifas_debitos: list[TarifaDebito] = field(default_factory=list)
    linhas_nao_reconhecidas: list[tuple[int, str]] = field(default_factory=list)


# ── Helpers ────────────────────────────────────────────────────────────────────

_RE_DATA = re.compile(r'(\d{2}/\d{2}/\d{2,4})')
_RE_VALOR = re.compile(r'([\d\.]+,\d{2})')
_RE_ESTABELECIMENTO = re.compile(r'N[ÂÃU]?[º°O]\s+DO\s+ESTABELECIMENTO[:\s]+(\d[\d\.]+)', re.IGNORECASE)
_RE_PERIODO = re.compile(r'PER[ÃI][OD]+O[:\s]+([\d/]+\s+A\s+[\d/]+)', re.IGNORECASE)
_RE_EMISSAO = re.compile(r'DATA\s+DA\s+EMISS[ÃA]O[:\s]+([\d/]+)', re.IGNORECASE)
_RE_EC_CABECALHO = re.compile(r'^\s*(\d{8,9})\s+\d+')

# Padrão de linha de detalhe de venda — modalidade usa [^\d] para capturar chars acentuados (À VISTA, PARC.ESTAB.)
_RE_LINHA_VENDA = re.compile(
    r'(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})\*?\s+'
    r'(\d+)\s+(\d+)\s+([A-Z]{2})\s+'
    r'(\d+|-)\s+'
    r'([A-Za-z\x80-\xFF\s\.\/]+?)\s{2,}'
    r'([\d\.]+,\d{2})\s+'
    r'(-|[\d\.]+,\d{2})\s+'
    r'([\d\.]+,\d{2})'
)

# Padrão linha de pagamento (movimento financeiro)
_RE_LINHA_PAGAMENTO = re.compile(
    r'(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})\s+(\d+)\s+([\d]+)\s+([\d\.]+,\d{2})\s+'
    r'(\d{4}/\d+/\d+)'
)

# Padrão simplificado para pagamento: data + ordem + valor + banco/ag/conta
_RE_PAGAMENTO_SIMPLES = re.compile(
    r'(\d{2}/\d{2}/\d{2})\s+(\d+)\s+([\d\.]+,\d{2})\s+(\d{4}/\d+/\d+)'
)

# Padrão linha de tarifa/débito
_RE_LINHA_TARIFA = re.compile(
    r'(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2})\s+\d+\s+(.+?)\s+([\d\*]+)\s+'
    r'([\d\.]+,\d{2})\s+([\d\.]+,\d{2})\s+(\w[\w\s]+)$'
)

# VALOR CREDITADO EM banco/ag/conta + valor
_RE_CREDITADO = re.compile(
    r'(\d{2}/\d{2}/\d{2})\s+VALOR\s+CREDITADO\s+EM\s+(\d{4}/\d+/\d+)\s+([\d\.]+,\d{2})',
    re.IGNORECASE
)
_RE_CREDITADO_SEM_DATA = re.compile(
    r'VALOR\s+CREDITADO\s+EM\s+(\d{4}/\d+/\d+)\s+([\d\.]+,\d{2})',
    re.IGNORECASE
)

# Ordem de crédito
_RE_ORDEM = re.compile(r'(\d{2}/\d{2}/\d{2})\s+(\d{9})\s+([\d\.]+,\d{2})\s+(\d{4}/\d+/\d+)')


def _parse_data(s: str) -> Optional[datetime]:
    s = s.strip()
    for fmt in ('%d/%m/%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_valor(s: str) -> float:
    s = s.strip().replace('.', '').replace(',', '.')
    if s == '-' or not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _extrair_banco_ag_conta(linha: str) -> str:
    m = re.search(r'(\d{4}/\d{3,6}/\d{6,10})', linha)
    return m.group(1) if m else ""


# ── Seções ─────────────────────────────────────────────────────────────────────

_SECAO_CREDITO = "credito"
_SECAO_DEBITO = "debito"
_SECAO_FINANCEIRO = "financeiro"
_SECAO_TARIFA = "tarifa"
_SECAO_NENHUMA = None


def _detectar_secao(linha: str) -> Optional[str]:
    upper = linha.upper()
    # MOVIMENTO FINANCEIRO tem prioridade — detectar antes de checar 'VENDAS COM CART'
    if 'MOVIMENTO FINANCEIRO' in upper:
        return _SECAO_FINANCEIRO
    # 'VALORES PAGOS' é sub-cabeçalho do financeiro — ignorar (retorna None para não alterar seção)
    if 'VALORES PAGOS' in upper:
        return None
    # Seção de crédito: linha de título principal (sem DÉBITO)
    if 'VENDAS COM CART' in upper and 'BITO' not in upper and 'CR' in upper:
        return _SECAO_CREDITO
    # Seção de débito: linha de título contém DÉBITO / DEBITO
    if 'VENDAS COM CART' in upper and 'BITO' in upper:
        return _SECAO_DEBITO
    # Seção de tarifas/débitos: detectada pelo cabeçalho de colunas
    if re.search(r'INCLUS', upper) and 'PGTO' in upper and 'ESTABELEC' in upper:
        return _SECAO_TARIFA
    return None


def _eh_linha_cabecalho(linha: str) -> bool:
    upper = linha.upper()
    skip_patterns = [
        'DATA DA', 'QTDE', 'VALOR BRUTO', 'TOTAL DO PER',
        'MASTERCARD', 'VISA', 'ELO', 'HIPERCARD', 'AMEX', 'CABAL',
        'ATEN', 'DEMONSTR', '____', 'BANDEIRA', 'MODALIDADE',
        'VALORES PAGOS', 'VALOR L', 'TOTAL DO', 'USEREDE',
        'NUMERO', 'MOTIVO', 'MEIO DE',
        'CB-CABAL', 'MT-MAEST', 'VE-VISA', 'AX-AMEX',
        'ACESSE', 'PARA DETAL',
    ]
    linha_strip = linha.strip()
    if len(linha_strip) < 10:
        return True
    for p in skip_patterns:
        if p in upper:
            return True
    return False


# ── Parser principal ───────────────────────────────────────────────────────────

class RedeParser:
    def __init__(self, nome_arquivo: str = ""):
        self._nome = nome_arquivo

    def parse(self, conteudo: str) -> ResultadoParsing:
        resultado = ResultadoParsing()
        linhas = conteudo.splitlines()

        # Extrair cabeçalho do arquivo
        self._extrair_cabecalho(linhas[:30], resultado)

        secao_atual = _SECAO_NENHUMA
        data_pagamento_atual: Optional[str] = None  # para seção financeiro

        for i, linha in enumerate(linhas):
            nova_secao = _detectar_secao(linha)
            if nova_secao:
                secao_atual = nova_secao
                continue

            if secao_atual is None:
                continue

            if _eh_linha_cabecalho(linha):
                continue

            linha_strip = linha.strip()
            if not linha_strip:
                continue

            reconhecida = False

            if secao_atual == _SECAO_CREDITO:
                reconhecida = self._parse_linha_credito(linha, resultado)

            elif secao_atual == _SECAO_DEBITO:
                reconhecida = self._parse_linha_debito(linha, resultado)

            elif secao_atual == _SECAO_FINANCEIRO:
                reconhecida, data_pagamento_atual = self._parse_linha_financeiro(
                    linha, resultado, data_pagamento_atual
                )

            elif secao_atual == _SECAO_TARIFA:
                reconhecida = self._parse_linha_tarifa(linha, resultado)

            if not reconhecida:
                resultado.linhas_nao_reconhecidas.append((i + 1, linha))

        return resultado

    def _extrair_cabecalho(self, linhas: list[str], resultado: ResultadoParsing) -> None:
        texto = '\n'.join(linhas)

        m = _RE_ESTABELECIMENTO.search(texto)
        if m:
            resultado.estabelecimento = m.group(1).replace('.', '')

        if not resultado.estabelecimento:
            m2 = _RE_EC_CABECALHO.match(linhas[0]) if linhas else None
            if m2:
                resultado.estabelecimento = m2.group(1)

        m = _RE_PERIODO.search(texto)
        if m:
            resultado.periodo = m.group(1).strip()

        m = _RE_EMISSAO.search(texto)
        if m:
            resultado.data_emissao = _parse_data(m.group(1))

    def _parse_linha_credito(self, linha: str, resultado: ResultadoParsing) -> bool:
        m = _RE_LINHA_VENDA.search(linha)
        if not m:
            return False

        modalidade = m.group(7).strip()
        tipo = "FUTURO" if re.search(r'PARC', modalidade, re.IGNORECASE) else "EFETUADO"

        resultado.vendas_credito.append(VendaCredito(
            estabelecimento=resultado.estabelecimento,
            origem_arquivo=self._nome,
            data_venda=_parse_data(m.group(1)),
            data_recebimento=_parse_data(m.group(2)),
            resumo_vendas=m.group(4),
            bandeira=m.group(5),
            quantidade=int(m.group(6)) if m.group(6) != '-' else 0,
            modalidade=modalidade,
            valor_bruto=_parse_valor(m.group(8)),
            valor_correcao=_parse_valor(m.group(9)),
            valor_liquido=_parse_valor(m.group(10)),
            tipo_lancamento=tipo,
        ))
        return True

    def _parse_linha_debito(self, linha: str, resultado: ResultadoParsing) -> bool:
        m = _RE_LINHA_VENDA.search(linha)
        if not m:
            return False

        banco_ag_conta = _extrair_banco_ag_conta(linha)

        resultado.vendas_debito.append(VendaDebito(
            estabelecimento=resultado.estabelecimento,
            origem_arquivo=self._nome,
            data_venda=_parse_data(m.group(1)),
            data_recebimento=_parse_data(m.group(2)),
            resumo_vendas=m.group(4),
            bandeira=m.group(5),
            quantidade=int(m.group(6)) if m.group(6) != '-' else 0,
            modalidade=m.group(7).strip(),
            valor_bruto=_parse_valor(m.group(8)),
            valor_saque=_parse_valor(m.group(9)),
            valor_liquido=_parse_valor(m.group(10)),
            banco_agencia_conta=banco_ag_conta,
        ))
        return True

    def _parse_linha_financeiro(
        self, linha: str, resultado: ResultadoParsing, data_atual: Optional[str]
    ) -> tuple[bool, Optional[str]]:
        # Detectar data de pagamento no contexto
        m_data = re.match(r'^\s*(\d{2}/\d{2}/\d{2})', linha)
        if m_data:
            data_atual = m_data.group(1)

        # Padrão: data recebimento + ordem + valor + banco
        m = _RE_ORDEM.search(linha)
        if m:
            resultado.pagamentos.append(Pagamento(
                estabelecimento=resultado.estabelecimento,
                origem_arquivo=self._nome,
                data_recebimento=_parse_data(m.group(1)),
                ordem_credito=m.group(2),
                valor_liquido=_parse_valor(m.group(3)),
                banco_agencia_conta=m.group(4),
            ))
            return True, data_atual

        # Padrão: VALOR CREDITADO EM banco/ag/conta + valor (com ou sem data)
        m2 = _RE_CREDITADO.search(linha)
        if m2:
            resultado.pagamentos.append(Pagamento(
                estabelecimento=resultado.estabelecimento,
                origem_arquivo=self._nome,
                data_recebimento=_parse_data(m2.group(1)),
                ordem_credito="",
                valor_liquido=_parse_valor(m2.group(3)),
                banco_agencia_conta=m2.group(2),
            ))
            return True, data_atual

        m3 = _RE_CREDITADO_SEM_DATA.search(linha)
        if m3:
            resultado.pagamentos.append(Pagamento(
                estabelecimento=resultado.estabelecimento,
                origem_arquivo=self._nome,
                data_recebimento=_parse_data(data_atual) if data_atual else None,
                ordem_credito="",
                valor_liquido=_parse_valor(m3.group(2)),
                banco_agencia_conta=m3.group(1),
            ))
            return True, data_atual

        return False, data_atual

    def _parse_linha_tarifa(self, linha: str, resultado: ResultadoParsing) -> bool:
        m = _RE_LINHA_TARIFA.search(linha)
        if not m:
            return False

        resultado.tarifas_debitos.append(TarifaDebito(
            estabelecimento=resultado.estabelecimento,
            origem_arquivo=self._nome,
            data_inclusao=_parse_data(m.group(1)),
            data_pagamento=_parse_data(m.group(2)),
            motivo_debito=m.group(3).strip(),
            resumo=m.group(4).strip(),
            valor_devido=_parse_valor(m.group(5)),
            valor_debitado=_parse_valor(m.group(6)),
            meio_pagamento=m.group(7).strip(),
        ))
        return True
