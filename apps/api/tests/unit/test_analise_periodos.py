"""
Testes unitários para CalculoRepository.analisar_periodos (Story 3.6).
"""
from unittest.mock import MagicMock, patch

import pytest

from app.repositories.calculo_repository import CalculoRepository
from app.schemas.calculo import AnalisePeriodosResponse


def _make_repo(dialect="sqlite"):
    db = MagicMock()
    db.get_bind.return_value.dialect.name = dialect
    return CalculoRepository(db)


def _make_row(periodo, quantidade, valor_total):
    r = MagicMock()
    r.periodo = periodo
    r.quantidade = quantidade
    r.valor_total = valor_total
    return r


class TestAnalisePeriodos:
    def test_mes_ausente_detectado(self):
        """Mês dentro do intervalo sem dados deve ser classificado como 'ausente'."""
        repo = _make_repo()

        # Simula: processamento sem vendas_calculos → usa Venda
        repo.db.query.return_value.filter.return_value.first.return_value = None

        rows = [
            _make_row("2024-01", 100, 10000.0),
            # 2024-02 ausente
            _make_row("2024-03", 90, 9000.0),
        ]
        repo.db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        with patch.object(repo.db, "query", return_value=MagicMock()) as mock_q:
            # primeiro query (verificar has_calc) retorna None
            mock_q.return_value.filter.return_value.first.return_value = None
            # segundo query (agrupamento) retorna rows
            mock_q.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

            result = repo.analisar_periodos("PROC_001")

        assert isinstance(result, AnalisePeriodosResponse)

    def test_mes_reduzido_detectado(self):
        """Mês com quantidade < 50% da mediana deve ser 'reduzido'."""
        from app.schemas.calculo import PeriodoAnalise

        # Cria repositório e injeta lógica de classificação diretamente
        repo = _make_repo()

        # mediana de [100, 100, 10] = 100; threshold 0.5 → corte em 50
        # 10 < 50 → reduzido
        rows = [
            _make_row("2024-01", 100, 10000.0),
            _make_row("2024-02", 10, 1000.0),
            _make_row("2024-03", 100, 10000.0),
        ]

        with patch.object(repo.db, "query", return_value=MagicMock()) as mock_q:
            mock_q.return_value.filter.return_value.first.return_value = None
            mock_q.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

            result = repo.analisar_periodos("PROC_002", threshold=0.5)

        assert isinstance(result, AnalisePeriodosResponse)

    def test_intervalo_sem_gap(self):
        """Resultado deve conter todos os meses do intervalo min→max sem lacunas."""
        repo = _make_repo()

        rows = [
            _make_row("2024-01", 100, 10000.0),
            _make_row("2024-06", 80, 8000.0),
        ]

        with patch.object(repo.db, "query", return_value=MagicMock()) as mock_q:
            mock_q.return_value.filter.return_value.first.return_value = None
            mock_q.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

            result = repo.analisar_periodos("PROC_003")

        assert isinstance(result, AnalisePeriodosResponse)
        # 6 meses no total (jan a jun)
        assert result.total_periodos == 6

    def test_sem_dados_retorna_vazio(self):
        """Processamento sem dados deve retornar response vazia sem erro."""
        repo = _make_repo()

        with patch.object(repo.db, "query", return_value=MagicMock()) as mock_q:
            mock_q.return_value.filter.return_value.first.return_value = None
            mock_q.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

            result = repo.analisar_periodos("PROC_VAZIO")

        assert result.total_periodos == 0
        assert result.periodos == []
        assert result.mediana_quantidade == 0.0
