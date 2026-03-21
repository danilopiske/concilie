"""
Testes unitários para lógica de validação de extratos (Story 3.7).
"""
from unittest.mock import MagicMock, patch

import pytest

from app.api.v1.endpoints.extratos_cliente import validar_extratos


def _make_extrato(nome, tipo="Venda", status="aguardando"):
    e = MagicMock()
    e.nome_arquivo = nome
    e.tipo = tipo
    e.status = status
    return e


def _make_processamento(nome, tipo_arquivo="Venda", id=1):
    p = MagicMock()
    p.nome_arquivo = nome
    p.tipo_arquivo = tipo_arquivo
    p.id = id
    return p


class TestValidarExtratos:
    def test_match_exato_importado(self):
        """Extrato com nome igual ao processamento deve ficar 'importado'."""
        extrato = _make_extrato("vendas_jan.xlsx")
        processamento = _make_processamento("vendas_jan.xlsx", tipo_arquivo="Venda")

        db = MagicMock()
        db.query.return_value.filter.return_value.all.side_effect = [
            [extrato],
            [processamento],
        ]

        result = validar_extratos(cliente_id=1, db=db)

        assert extrato.status == "importado"
        assert extrato.processamento_id == processamento.id
        assert result["atualizados"] == 1

    def test_match_substring_importado(self):
        """Extrato cujo nome está contido no nome do processamento deve ficar 'importado'."""
        extrato = _make_extrato("jan.xlsx")
        processamento = _make_processamento("uploads/vendas_jan.xlsx", tipo_arquivo="Venda")

        db = MagicMock()
        db.query.return_value.filter.return_value.all.side_effect = [
            [extrato],
            [processamento],
        ]

        result = validar_extratos(cliente_id=1, db=db)

        assert extrato.status == "importado"
        assert result["atualizados"] == 1

    def test_sem_match_permanece_aguardando(self):
        """Extrato sem match em processamentos deve permanecer 'aguardando'."""
        extrato = _make_extrato("extrato_fev.xlsx")
        processamento = _make_processamento("vendas_jan.xlsx", tipo_arquivo="Venda")

        db = MagicMock()
        db.query.return_value.filter.return_value.all.side_effect = [
            [extrato],
            [processamento],
        ]

        result = validar_extratos(cliente_id=1, db=db)

        assert extrato.status == "aguardando"
        assert result["atualizados"] == 0

    def test_tipo_divergente(self):
        """Extrato com tipo diferente do processamento deve ficar 'divergente'."""
        extrato = _make_extrato("arquivo.xlsx", tipo="Recebivel")
        processamento = _make_processamento("arquivo.xlsx", tipo_arquivo="Venda")

        db = MagicMock()
        db.query.return_value.filter.return_value.all.side_effect = [
            [extrato],
            [processamento],
        ]

        result = validar_extratos(cliente_id=1, db=db)

        assert extrato.status == "divergente"
        assert result["atualizados"] == 1
