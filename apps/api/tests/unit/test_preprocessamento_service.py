"""Testes unitários para preprocessamento_service."""

import json
import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ─────────────────────────────────────────────
# Testes: invalidar_parquet
# ─────────────────────────────────────────────

class TestInvalidarParquet:
    def test_deleta_pasta_existente(self, tmp_path):
        """invalidar_parquet deve deletar toda a pasta base quando adquirente=None."""
        from app.services.preprocessamento_service import invalidar_parquet

        pasta = tmp_path / "proc123" / "todos"
        pasta.mkdir(parents=True)
        (pasta / "vendas_calculos.parquet").write_bytes(b"fake")

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            invalidar_parquet("proc123")

        assert not (tmp_path / "proc123").exists()

    def test_nao_falha_pasta_inexistente(self, tmp_path):
        """invalidar_parquet não deve lançar exceção se pasta não existe."""
        from app.services.preprocessamento_service import invalidar_parquet

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            invalidar_parquet("proc_inexistente")  # não deve lançar

    def test_deleta_apenas_adquirente_especifico(self, tmp_path):
        """invalidar_parquet com adquirente deve deletar só aquela subpasta."""
        from app.services.preprocessamento_service import invalidar_parquet

        pasta_cielo = tmp_path / "proc123" / "cielo"
        pasta_rede = tmp_path / "proc123" / "rede"
        pasta_cielo.mkdir(parents=True)
        pasta_rede.mkdir(parents=True)

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            invalidar_parquet("proc123", adquirente="cielo")

        assert not pasta_cielo.exists()
        assert pasta_rede.exists()


# ─────────────────────────────────────────────
# Testes: status_parquet
# ─────────────────────────────────────────────

class TestStatusParquet:
    def test_retorna_false_sem_cache(self, tmp_path):
        """status_parquet retorna exists=False quando não há _meta.json."""
        from app.services.preprocessamento_service import status_parquet

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            result = status_parquet("proc_vazio")

        assert result["exists"] is False

    def test_retorna_true_com_meta_json(self, tmp_path):
        """status_parquet retorna exists=True quando _meta.json existe."""
        from app.services.preprocessamento_service import status_parquet

        pasta = tmp_path / "proc123" / "todos"
        pasta.mkdir(parents=True)
        meta = {
            "gerado_em": "2026-04-10T10:00:00",
            "calc_tipo": "anual",
            "secoes": ["vendas_calculos"],
        }
        (pasta / "_meta.json").write_text(json.dumps(meta))

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            result = status_parquet("proc123")

        assert result["exists"] is True
        assert "gerado_em" in result

    def test_meta_json_retorna_calc_tipo(self, tmp_path):
        """status_parquet deve expor calc_tipo presente no _meta.json."""
        from app.services.preprocessamento_service import status_parquet

        pasta = tmp_path / "proc456" / "todos"
        pasta.mkdir(parents=True)
        meta = {
            "gerado_em": "2026-04-10T12:00:00",
            "calc_tipo": "mensal",
            "secoes": ["vendas_calculos", "perdas_semestre"],
        }
        (pasta / "_meta.json").write_text(json.dumps(meta))

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            result = status_parquet("proc456")

        assert result.get("calc_tipo") == "mensal"

    def test_adquirente_especifico(self, tmp_path):
        """status_parquet verifica o slot do adquirente correto."""
        from app.services.preprocessamento_service import status_parquet

        pasta = tmp_path / "proc789" / "cielo"
        pasta.mkdir(parents=True)
        meta = {"gerado_em": "2026-04-10T09:00:00", "calc_tipo": "anual", "secoes": []}
        (pasta / "_meta.json").write_text(json.dumps(meta))

        with patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)):
            result_cielo = status_parquet("proc789", adquirente="cielo")
            result_rede = status_parquet("proc789", adquirente="rede")

        assert result_cielo["exists"] is True
        assert result_rede["exists"] is False


# ─────────────────────────────────────────────
# Testes: preprocessar_relatorio
# ─────────────────────────────────────────────

class TestPreprocessarRelatorio:
    _DF = pd.DataFrame({"col": [1, 2, 3]})

    def _patches(self, tmp_path):
        """Retorna lista de patches comuns para isolar o service."""
        return [
            patch("app.services.preprocessamento_service._PREPROC_CACHE_DIR", str(tmp_path)),
            patch("app.services.preprocessamento_service.load_vendas_calculos_cached", return_value=self._DF),
            patch("app.services.preprocessamento_service.calcular_perdas_por_semestre", return_value=self._DF),
            patch("app.services.preprocessamento_service.calcular_min_max_taxas_agrupado", return_value=self._DF),
            patch("app.services.preprocessamento_service.calcular_contagem_taxas_agrupado", return_value=self._DF),
            patch("app.services.preprocessamento_service.calcular_sumario_recebiveis", return_value=self._DF),
            patch("app.services.preprocessamento_service.calcular_tabela_consolidada_mensal", return_value=self._DF),
            patch("app.services.preprocessamento_service.obter_evidencias_transacoes", return_value={}),
            patch("app.services.preprocessamento_service.obter_dados_bancarios_distintos", return_value=self._DF),
        ]

    def test_cria_meta_json(self, tmp_path):
        """preprocessar_relatorio deve criar _meta.json na pasta de cache."""
        from app.services.preprocessamento_service import preprocessar_relatorio

        engine_mock = MagicMock()

        with patch.multiple("app.services.preprocessamento_service",
                            _PREPROC_CACHE_DIR=str(tmp_path),
                            load_vendas_calculos_cached=MagicMock(return_value=self._DF),
                            calcular_perdas_por_semestre=MagicMock(return_value=self._DF),
                            calcular_min_max_taxas_agrupado=MagicMock(return_value=self._DF),
                            calcular_contagem_taxas_agrupado=MagicMock(return_value=self._DF),
                            calcular_sumario_recebiveis=MagicMock(return_value=self._DF),
                            calcular_tabela_consolidada_mensal=MagicMock(return_value=self._DF),
                            obter_evidencias_transacoes=MagicMock(return_value={}),
                            obter_dados_bancarios_distintos=MagicMock(return_value=self._DF)):
            preprocessar_relatorio(engine_mock, "proc_test", "anual")

        # _meta.json deve existir
        meta_candidates = list(tmp_path.rglob("_meta.json"))
        assert len(meta_candidates) >= 1, "_meta.json não foi criado"

        with open(meta_candidates[0]) as f:
            meta = json.load(f)
        assert "gerado_em" in meta
        assert meta["calc_tipo"] == "anual"

    def test_nao_lanca_excecao_em_erro_de_calculo(self, tmp_path):
        """preprocessar_relatorio não deve propagar exceções das seções com erro."""
        from app.services.preprocessamento_service import preprocessar_relatorio

        engine_mock = MagicMock()

        with patch.multiple("app.services.preprocessamento_service",
                            _PREPROC_CACHE_DIR=str(tmp_path),
                            load_vendas_calculos_cached=MagicMock(side_effect=Exception("DB error")),
                            calcular_perdas_por_semestre=MagicMock(return_value=self._DF),
                            calcular_min_max_taxas_agrupado=MagicMock(return_value=self._DF),
                            calcular_contagem_taxas_agrupado=MagicMock(return_value=self._DF),
                            calcular_sumario_recebiveis=MagicMock(return_value=self._DF),
                            calcular_tabela_consolidada_mensal=MagicMock(return_value=self._DF),
                            obter_evidencias_transacoes=MagicMock(return_value={}),
                            obter_dados_bancarios_distintos=MagicMock(return_value=self._DF)):
            result = preprocessar_relatorio(engine_mock, "proc_err", "anual")

        # Deve retornar dict com erros, não lançar exceção
        assert isinstance(result, dict)
