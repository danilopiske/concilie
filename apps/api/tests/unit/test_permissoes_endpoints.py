"""
Testes unitários para controle de acesso (Story 3.39).
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.deps import get_user_perfil, require_role


class TestGetUserPerfil:
    def test_retorna_perfil_da_permissao(self):
        user = MagicMock()
        user.permissao.perfil = "operador"
        assert get_user_perfil(user) == "operador"

    def test_sem_permissao_retorna_admin(self):
        user = MagicMock()
        user.permissao = None
        assert get_user_perfil(user) == "admin"


class TestRequireRole:
    def _make_user(self, perfil: str):
        user = MagicMock()
        user.permissao.perfil = perfil
        return user

    def test_perfil_permitido_passa(self):
        user = self._make_user("admin")
        checker = require_role(["admin", "operador"])
        with patch("app.api.deps.get_current_user", return_value=user):
            result = checker(current_user=user)
        assert result == user

    def test_perfil_bloqueado_levanta_403(self):
        user = self._make_user("visualizador")
        checker = require_role(["admin", "operador"])
        with pytest.raises(HTTPException) as exc:
            checker(current_user=user)
        assert exc.value.status_code == 403
        assert "visualizador" in exc.value.detail

    def test_operador_nao_acessa_admin_only(self):
        user = self._make_user("operador")
        checker = require_role(["admin"])
        with pytest.raises(HTTPException) as exc:
            checker(current_user=user)
        assert exc.value.status_code == 403

    def test_visualizador_nao_acessa_calculos(self):
        user = self._make_user("visualizador")
        checker = require_role(["admin", "operador"])
        with pytest.raises(HTTPException) as exc:
            checker(current_user=user)
        assert exc.value.status_code == 403
