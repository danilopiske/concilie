"""
Testes unitários para a lógica de comparação de taxas contratadas vs cobradas.
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.services.taxa_contratada_service import _calcular_status, comparar_contratado_vs_cobrado


class TestCalcularStatus:
    def test_ok(self):
        assert _calcular_status(0.0) == "ok"
        assert _calcular_status(2.0) == "ok"

    def test_atencao(self):
        assert _calcular_status(2.1) == "atencao"
        assert _calcular_status(10.0) == "atencao"

    def test_abusivo(self):
        assert _calcular_status(10.1) == "abusivo"
        assert _calcular_status(50.0) == "abusivo"


def _make_db(taxa_contratada_val, vendas_rows):
    """Cria mock de Session com Processamento e TaxaContratada configurados."""
    db = MagicMock()

    proc_mock = MagicMock()
    proc_mock.data_inicio = datetime(2025, 1, 15)

    taxa_mock = MagicMock()
    taxa_mock.taxa_contratada = taxa_contratada_val

    call_count = {"n": 0}

    def query_side(model):
        q = MagicMock()
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Primeira chamada: Processamento
            q.filter.return_value.first.return_value = proc_mock
        else:
            # Demais chamadas: TaxaContratada
            q.filter.return_value.first.return_value = taxa_mock
        return q

    db.query.side_effect = query_side
    db.execute.return_value.fetchall.return_value = vendas_rows
    return db


class TestCompararContratadoVsCobrado:
    def test_caso_ok(self):
        """Taxa cobrada == contratada → desvio 0% → status ok."""
        db = _make_db(
            taxa_contratada_val=2.0,
            vendas_rows=[("Visa", "Crédito à Vista", 2.0, 10000.0, 100)],
        )
        result = comparar_contratado_vs_cobrado(1, "42", db)

        assert result.cliente_id == 1
        assert len(result.desvios) == 1
        assert result.desvios[0].status == "ok"
        assert result.desvios[0].desvio_percentual == 0.0
        assert result.desvios[0].valor_excesso_estimado == 0.0

    def test_caso_atencao(self):
        """Taxa cobrada 5% acima da contratada → status atencao."""
        db = _make_db(
            taxa_contratada_val=2.0,
            vendas_rows=[("Visa", "Crédito à Vista", 2.1, 10000.0, 100)],
        )
        result = comparar_contratado_vs_cobrado(1, "42", db)

        assert result.desvios[0].status == "atencao"
        assert result.desvios[0].desvio_percentual == pytest.approx(5.0, rel=1e-2)
        assert result.desvios[0].valor_excesso_estimado > 0

    def test_caso_abusivo(self):
        """Taxa cobrada 50% acima da contratada → status abusivo."""
        db = _make_db(
            taxa_contratada_val=2.0,
            vendas_rows=[("Visa", "Crédito à Vista", 3.0, 10000.0, 100)],
        )
        result = comparar_contratado_vs_cobrado(1, "42", db)

        assert result.desvios[0].status == "abusivo"
        assert result.desvios[0].desvio_percentual == pytest.approx(50.0, rel=1e-2)
        assert result.desvios[0].valor_excesso_estimado == pytest.approx(5000.0, rel=1e-2)

    def test_sem_taxa_contratada_nao_retorna_desvio(self):
        """Sem taxa contratada cadastrada → lista vazia, excesso zero."""
        db = _make_db(
            taxa_contratada_val=None,
            vendas_rows=[("Visa", "Crédito à Vista", 2.5, 5000.0, 50)],
        )
        # Sobrescreve: TaxaContratada query retorna None
        proc_mock = MagicMock()
        proc_mock.data_inicio = datetime(2025, 1, 15)
        call_count = {"n": 0}

        def query_side(model):
            q = MagicMock()
            call_count["n"] += 1
            if call_count["n"] == 1:
                q.filter.return_value.first.return_value = proc_mock
            else:
                q.filter.return_value.first.return_value = None
            return q

        db.query.side_effect = query_side

        result = comparar_contratado_vs_cobrado(1, "42", db)
        assert result.desvios == []
        assert result.valor_excesso_total == 0.0
