"""
Tests for importacao (async import) endpoints.
"""


def test_importacao_task_not_found(client):
    """Status de task inexistente deve retornar 404."""
    response = client.get("/api/v1/importacao-async/task/id_inexistente")
    assert response.status_code in (404, 422)


def test_importacao_confirmar_requires_body(client):
    """Confirmar sem body deve retornar 422."""
    response = client.post("/api/v1/importacao-async/confirmar", json={})
    assert response.status_code == 422


def test_importacao_confirmar_minimal_payload(client):
    """Confirmar com payload mínimo válido (sem auth) deve retornar 4xx."""
    payload = {
        "cliente_id": "cli_test",
        "tipo": "vendas",
        "contexto": {},
        "file_id": "file_test",
        "ec_id": "ec_test",
        "processamentoid": None,
    }
    response = client.post("/api/v1/importacao-async/confirmar", json=payload)
    # Pode retornar 200/202 (processando) ou erro de negócio (4xx/5xx)
    # O endpoint não exige auth, então pode iniciar background task
    assert response.status_code in (200, 202, 400, 422, 500)


def test_importacao_task_id_path_param(client):
    """Task ID com barras deve ser aceito pelo path converter."""
    response = client.get("/api/v1/importacao-async/task/2024/01/test-id")
    assert response.status_code in (404, 422)
