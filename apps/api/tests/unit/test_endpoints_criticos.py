"""
Story 3.43 — Testes para endpoints críticos
Verifica autenticação, autorização (require_role) e contratos de resposta.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_user(role: str = "admin"):
    """Cria mock de usuário compatível com get_user_perfil (checa user.permissao.perfil)."""
    user = MagicMock()
    user.id = 1
    user.usuario = "test_user"
    user.permissao = MagicMock()
    user.permissao.perfil = role
    return user


def _override_auth(app, role: str):
    """Sobrescreve get_current_user para retornar usuário com perfil dado."""
    from app.api.deps import get_current_user
    user = _mock_user(role)
    app.dependency_overrides[get_current_user] = lambda: user
    return user


# ---------------------------------------------------------------------------
# Dashboard — requer autenticação (todos os perfis)
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:
    def test_dashboard_sem_auth_retorna_401(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/dashboard/resumo")
        assert r.status_code in (401, 403, 422)

    def test_dashboard_com_visualizador_nao_retorna_401_403(self):
        from app.main import app
        _override_auth(app, "visualizador")
        with patch("app.api.v1.endpoints.dashboard.get_db") as mock_db:
            mock_db.return_value = MagicMock()
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/dashboard/resumo")
            assert r.status_code != 401
            assert r.status_code != 403
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Gestão — admin/operador para escrita
# ---------------------------------------------------------------------------

class TestGestaoEndpoints:
    def test_post_gestao_sem_auth_retorna_401(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        # POST /gestao/contextos é uma rota protegida existente
        r = client.post("/api/v1/gestao/contextos", json={"nome": "Teste"})
        assert r.status_code in (401, 403, 422)

    def test_post_gestao_com_visualizador_retorna_403(self):
        from app.main import app
        # visualizador não tem acesso a escrita — require_role(["admin","operador"])
        _override_auth(app, "visualizador")
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/gestao/contextos", json={"nome": "Teste"})
        assert r.status_code == 403
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Contestações — admin/operador para gerar
# ---------------------------------------------------------------------------

class TestContestacaoEndpoints:
    def test_gerar_contestacao_sem_auth_retorna_401_ou_403(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/contestacoes/gerar", json={
            "cliente_id": 1,
            "processamento_id": 1
        })
        assert r.status_code in (401, 403, 422)

    def test_gerar_contestacao_com_admin_nao_retorna_401(self):
        from app.main import app
        _override_auth(app, "admin")
        with patch("app.api.v1.endpoints.contestacoes.get_db") as mock_db:
            mock_db.return_value = MagicMock()
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post("/api/v1/contestacoes/gerar", json={
                "cliente_id": 1,
                "processamento_id": 1
            })
            assert r.status_code != 401
            assert r.status_code != 403
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Abusividade — gerar relatório requer autenticação
# ---------------------------------------------------------------------------

class TestAbusividadeEndpoints:
    def test_gerar_relatorio_sem_auth_retorna_401_ou_403(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/abusividade/gerar-relatorio", json={
            "processamento_id": "123"
        })
        assert r.status_code in (401, 403, 422)

    def test_analise_com_auth_nao_retorna_401_403(self):
        """GET /analise/{id} com auth válida — não deve retornar 401/403."""
        from app.main import app
        from app.core.database import get_db

        _override_auth(app, "visualizador")
        db_mock = MagicMock()
        db_mock.query.return_value.filter.return_value.all.return_value = []
        app.dependency_overrides[get_db] = lambda: db_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/abusividade/analise/999")
        assert r.status_code != 401
        assert r.status_code != 403
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auditoria — somente admin
# ---------------------------------------------------------------------------

class TestAuditoriaEndpoints:
    def test_auditoria_sem_auth_retorna_401(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/auditoria")
        assert r.status_code in (401, 403, 422)

    def test_auditoria_com_operador_retorna_403(self):
        from app.main import app
        # operador não tem acesso — require_role(["admin"]) deve retornar 403
        _override_auth(app, "operador")
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/auditoria")
        assert r.status_code == 403
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Endpoints PÚBLICOS — devem funcionar sem token
# ---------------------------------------------------------------------------

class TestEndpointsPublicos:
    def test_login_nao_requer_token(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        # POST sem token — deve retornar 400 (bad credentials) não 401
        r = client.post(
            "/api/v1/login/access-token",
            data={"username": "x", "password": "y"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code != 401  # Não deve exigir token prévio
        assert r.status_code in (200, 400)

    def test_logout_nao_requer_token(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/login/logout")
        assert r.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Schema validation — Field constraints
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_cliente_nome_fantasia_max_length(self):
        from app.schemas.cliente import ClienteCreate
        import pytest as _pytest
        from pydantic import ValidationError

        with _pytest.raises(ValidationError):
            ClienteCreate(nome_fantasia="A" * 201)

    def test_cliente_cnpj_max_length(self):
        from app.schemas.cliente import ClienteCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClienteCreate(nome_fantasia="OK", cnpj="1" * 19)

    def test_calculo_processamento_id_max_length(self):
        from app.schemas.calculo import CalculoPreviewRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CalculoPreviewRequest(processamento_id="x" * 101)

    def test_calculo_tipo_taxa_max_length(self):
        from app.schemas.calculo import CalculoPreviewRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CalculoPreviewRequest(processamento_id="123", tipo_taxa="x" * 51)

    def test_contestacao_html_content_max_length(self):
        from app.schemas.contestacao import ContestacaoSaveEdit
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ContestacaoSaveEdit(html_content="x" * 500_001)

    def test_contestacao_html_content_valido(self):
        from app.schemas.contestacao import ContestacaoSaveEdit

        obj = ContestacaoSaveEdit(html_content="<html></html>")
        assert obj.html_content == "<html></html>"

    def test_cliente_update_max_length(self):
        from app.schemas.cliente import ClienteUpdate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClienteUpdate(nome_fantasia="X" * 201)

    def test_extrato_tipo_max_length(self):
        from app.schemas.extrato_cliente import ExtratoClienteCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ExtratoClienteCreate(tipo="X" * 51)

    def test_extrato_tipo_default(self):
        from app.schemas.extrato_cliente import ExtratoClienteCreate

        obj = ExtratoClienteCreate()
        assert obj.tipo == "Outro"
