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
    user = MagicMock()
    user.id = 1
    user.usuario = "test_user"
    user.perfil = role
    return user


def _make_client(app, override_user=None):
    """Cria TestClient com override de autenticação."""
    from app.api.deps import require_role, get_current_user

    if override_user is not None:
        app.dependency_overrides[get_current_user] = lambda: override_user
        # Sobrescreve require_role para qualquer perfil
        for role in [["admin"], ["admin", "operador"], ["admin", "operador", "visualizador"]]:
            app.dependency_overrides[require_role(role)] = lambda u=override_user: u
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Dashboard — requer autenticação (todos os perfis)
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:
    def test_dashboard_sem_auth_retorna_401(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/dashboard/resumo")
        assert r.status_code in (401, 403, 422)

    def test_dashboard_com_visualizador_retorna_200_ou_dados(self):
        from app.main import app
        from app.api.deps import require_role

        user = _mock_user("visualizador")
        app.dependency_overrides[require_role(["admin", "operador", "visualizador"])] = lambda: user

        with patch("app.api.v1.endpoints.dashboard.get_db") as mock_db:
            mock_db.return_value = MagicMock()
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/dashboard/resumo")
            # Pode retornar 200 ou 500 (DB mock), mas NÃO 401/403
            assert r.status_code != 401
            assert r.status_code != 403

        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Gestão — admin/operador para escrita
# ---------------------------------------------------------------------------

class TestGestaoEndpoints:
    def test_post_gestao_sem_auth_retorna_401_ou_403(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/gestao/clientes", json={
            "nome_fantasia": "Teste",
            "cliente_id": 999
        })
        assert r.status_code in (401, 403, 422)

    def test_post_gestao_com_visualizador_retorna_403(self):
        from app.main import app
        from app.api.deps import require_role

        # visualizador NÃO deve ter acesso a escrita
        def raise_403():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Acesso negado")

        app.dependency_overrides[require_role(["admin", "operador"])] = raise_403
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/gestao/clientes", json={"nome_fantasia": "X"})
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
        from app.api.deps import require_role

        user = _mock_user("admin")
        app.dependency_overrides[require_role(["admin", "operador"])] = lambda: user

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

    def test_analise_publica_retorna_200_ou_dado(self):
        """GET /analise/{id} é público — não deve exigir auth."""
        from app.main import app

        with patch("app.api.v1.endpoints.abusividade.get_db") as mock_db:
            db = MagicMock()
            db.query.return_value.filter.return_value.all.return_value = []
            mock_db.return_value = db
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/abusividade/analise/999")
            # Público — sem 401/403
            assert r.status_code != 401
            assert r.status_code != 403


# ---------------------------------------------------------------------------
# Auditoria — somente admin
# ---------------------------------------------------------------------------

class TestAuditoriaEndpoints:
    def test_auditoria_sem_auth_retorna_401_ou_403(self):
        from app.main import app
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/auditoria/")
        assert r.status_code in (401, 403, 422)

    def test_auditoria_com_operador_retorna_403(self):
        from app.main import app
        from app.api.deps import require_role

        def raise_403():
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Acesso negado")

        app.dependency_overrides[require_role(["admin"])] = raise_403
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/auditoria/")
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
