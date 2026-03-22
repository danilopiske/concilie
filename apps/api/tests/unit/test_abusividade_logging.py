"""
Testes unitários para logging do AbusividadeRelatorioService (Story 3.40).
"""
import logging
from unittest.mock import MagicMock, patch


class TestAbusividadeLogging:
    def _make_service(self):
        db = MagicMock()
        with patch("os.makedirs"):
            from app.services.abusividade_relatorio_service import AbusividadeRelatorioService
            return AbusividadeRelatorioService(db=db)

    def test_gerar_html_loga_inicio(self, caplog):
        service = self._make_service()
        with caplog.at_level(logging.INFO, logger="app.services.abusividade_relatorio_service"):
            with patch.object(service, "gerar_html", wraps=service.gerar_html):
                with patch("app.services.abusividade_relatorio_service.AbusividadeService") as mock_svc:
                    mock_svc.return_value.analisar_processamento.return_value = []
                    service.gerar_html("proc-123")

        assert any("proc-123" in r.message and "Iniciando" in r.message for r in caplog.records)

    def test_gerar_html_loga_conclusao(self, caplog):
        from unittest.mock import MagicMock
        service = self._make_service()

        fake_dado = {
            "data_venda": MagicMock(strftime=lambda f: "01/01/2026"),
            "valor_venda": 100.0,
            "taxa_aplicada": 2.5,
            "cod_autorizacao": "12345",
            "horario": "10:00",
            "numero_maquina": "001",
            "bandeira": "Visa",
        }

        with caplog.at_level(logging.INFO, logger="app.services.abusividade_relatorio_service"):
            with patch("app.services.abusividade_relatorio_service.AbusividadeService") as mock_svc:
                mock_svc.return_value.analisar_processamento.return_value = [fake_dado]
                with patch("builtins.open", MagicMock()):
                    service.gerar_html("proc-456")

        assert any("Concluído" in r.message and "proc-456" in r.message for r in caplog.records)

    def test_gerar_html_loga_excecao(self, caplog):
        service = self._make_service()

        with caplog.at_level(logging.ERROR, logger="app.services.abusividade_relatorio_service"):
            with patch("app.services.abusividade_relatorio_service.AbusividadeService") as mock_svc:
                mock_svc.return_value.analisar_processamento.side_effect = RuntimeError("DB error")
                result = service.gerar_html("proc-err")

        assert result is None
        assert any("proc-err" in r.message for r in caplog.records)

    def test_gerar_relatorio_async_loga_task_nao_encontrada(self, caplog):
        service = self._make_service()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with caplog.at_level(logging.ERROR, logger="app.services.abusividade_relatorio_service"):
            with patch("app.services.abusividade_relatorio_service.AbusividadeTask", create=True):
                service.gerar_relatorio_async("task-999", "proc-999", db)

        assert any("task-999" in r.message for r in caplog.records)
