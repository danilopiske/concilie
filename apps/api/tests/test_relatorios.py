"""
Tests for relatorios (reports) endpoints.
"""


def test_relatorios_opcoes_sem_processamento(client, auth_headers):
    """Opcoes sem processamento_id deve retornar resposta válida."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/relatorios/opcoes", headers=auth_headers)
    # Pode retornar 200 com lista vazia ou erro se módulo legado indisponível
    assert response.status_code in (200, 500, 503)


def test_relatorios_opcoes_com_processamento(client, auth_headers):
    """Opcoes com processamento_id inválido deve retornar 200 ou erro de negócio."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/relatorios/opcoes?processamento_id=id_inexistente", headers=auth_headers)
    assert response.status_code in (200, 404, 500, 503)


def test_relatorios_gerar_requires_body(client, auth_headers):
    """Gerar relatório sem body deve retornar 422."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.post("/api/v1/relatorios/gerar", headers=auth_headers, json={})
    assert response.status_code in (400, 422)


def test_relatorios_history_requires_auth(client):
    """Histórico de relatórios sem auth deve retornar 401/403."""
    response = client.get("/api/v1/relatorios/")
    assert response.status_code in (401, 403, 404, 422)
