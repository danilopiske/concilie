"""
Testes de segurança para extratos_cliente (Story 3.7 — edge cases críticos).
"""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.extratos_cliente import (
    _sanitizar_filename,
    _validar_path_dentro_base,
    BASE_EXTRATOS_DIR,
    deletar_extrato,
)


class TestSanitizarFilename:
    def test_filename_none_levanta_400(self):
        with pytest.raises(HTTPException) as exc:
            _sanitizar_filename(None)
        assert exc.value.status_code == 400

    def test_filename_vazio_levanta_400(self):
        with pytest.raises(HTTPException):
            _sanitizar_filename("")

    def test_path_traversal_simples(self):
        """../../../etc/passwd deve retornar apenas 'passwd'."""
        result = _sanitizar_filename("../../../etc/passwd")
        assert result == "passwd"
        assert ".." not in result
        assert "/" not in result

    def test_path_traversal_windows(self):
        """..\\..\\windows\\system32 deve retornar apenas 'system32'."""
        result = _sanitizar_filename("..\\..\\windows\\system32")
        assert ".." not in result

    def test_filename_normal_preservado(self):
        result = _sanitizar_filename("vendas_jan_2026.xlsx")
        assert result == "vendas_jan_2026.xlsx"

    def test_filename_ponto_levanta_400(self):
        with pytest.raises(HTTPException):
            _sanitizar_filename(".")

    def test_filename_dois_pontos_levanta_400(self):
        with pytest.raises(HTTPException):
            _sanitizar_filename("..")


class TestValidarPathDentroBase:
    def test_path_valido_nao_levanta(self):
        path = BASE_EXTRATOS_DIR / "1" / "arquivo.xlsx"
        # não deve levantar para path dentro da base
        try:
            _validar_path_dentro_base(path, BASE_EXTRATOS_DIR)
        except HTTPException:
            pytest.fail("Não deveria levantar para path válido")

    def test_path_fora_da_base_levanta_400(self):
        base = Path("/app/extratos_clientes").resolve()
        path_malicioso = Path("/etc/passwd")
        with pytest.raises(HTTPException) as exc:
            _validar_path_dentro_base(path_malicioso, base)
        assert exc.value.status_code == 400

    def test_path_com_dotdot_levanta_400(self):
        base = Path("/app/extratos_clientes").resolve()
        path_escape = Path("/app/extratos_clientes/../../../etc/shadow")
        with pytest.raises(HTTPException) as exc:
            _validar_path_dentro_base(path_escape, base)
        assert exc.value.status_code == 400


class TestDeletarExtratoSeguranca:
    def _make_db(self, extrato):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = extrato
        return db

    def test_delete_caminho_fora_da_base_bloqueado(self):
        """caminho_arquivo manipulado no banco não deve ser servido."""
        extrato = MagicMock()
        extrato.status = "aguardando"
        extrato.caminho_arquivo = "/etc/passwd"
        db = self._make_db(extrato)

        with pytest.raises(HTTPException) as exc:
            deletar_extrato(cliente_id=1, extrato_id="abc", db=db)
        assert exc.value.status_code == 400

    def test_delete_race_condition_nao_crasha(self):
        """Arquivo já removido por outro processo não deve causar crash."""
        extrato = MagicMock()
        extrato.status = "aguardando"
        extrato.caminho_arquivo = str(BASE_EXTRATOS_DIR / "1" / "arquivo.xlsx")
        db = self._make_db(extrato)

        with patch("app.api.v1.endpoints.extratos_cliente._validar_path_dentro_base"):
            with patch.object(Path, "unlink", side_effect=FileNotFoundError):
                # não deve propagar FileNotFoundError
                result = deletar_extrato(cliente_id=1, extrato_id="abc", db=db)
                assert result["message"] == "Extrato removido com sucesso"
