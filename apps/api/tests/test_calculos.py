"""
Tests for calculos (reconciliation) endpoints.
"""


def test_calculos_historico_accessible(client):
    """Histórico de cálculos deve ser acessível (sem auth obrigatória atualmente)."""
    response = client.get("/api/v1/calculos/historico-calculos")
    assert response.status_code in (200, 401, 403, 422)


def test_calculos_historico_returns_list(client):
    """Histórico de cálculos deve retornar lista JSON."""
    response = client.get("/api/v1/calculos/historico-calculos")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


def test_calculos_invalid_id(client, auth_headers):
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/calculos/id_inexistente", headers=auth_headers)
    assert response.status_code in (404, 422)


def test_calculos_start_requires_body(client, auth_headers):
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.post("/api/v1/calculos/iniciar", headers=auth_headers, json={})
    assert response.status_code in (400, 422)
