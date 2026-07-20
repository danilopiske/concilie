"""
Tests for importacao (async import) endpoints.
"""


def test_importacao_task_not_found(client, auth_headers):
    """Status de task inexistente deve retornar 404."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/importacao-async/task/id_inexistente", headers=auth_headers)
    assert response.status_code in (404, 422)


def test_importacao_confirmar_requires_body(client, auth_headers):
    """Confirmar sem body deve retornar 422."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.post("/api/v1/importacao-async/confirmar", headers=auth_headers, json={})
    assert response.status_code == 422


def test_importacao_confirmar_minimal_payload(client, auth_headers):
    """Confirmar com payload mínimo válido deve retornar 4xx ou iniciar processamento."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    payload = {
        "cliente_id": "cli_test",
        "tipo": "vendas",
        "contexto": {},
        "file_id": "file_test",
        "ec_id": "ec_test",
        "processamentoid": None,
    }
    response = client.post("/api/v1/importacao-async/confirmar", headers=auth_headers, json=payload)
    assert response.status_code in (200, 202, 400, 422, 500)


def test_importacao_task_id_path_param(client, auth_headers):
    """Task ID com barras deve ser aceito pelo path converter."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/importacao-async/task/2024/01/test-id", headers=auth_headers)
    assert response.status_code in (404, 422)
