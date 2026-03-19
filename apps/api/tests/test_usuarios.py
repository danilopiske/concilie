"""
Tests for usuarios endpoints (auth required).
"""


def test_listar_usuarios_sem_auth(client):
    """Listar usuários sem auth deve retornar 401/403."""
    response = client.get("/api/v1/usuarios/")
    assert response.status_code in (401, 403)


def test_criar_usuario_sem_auth(client):
    """Criar usuário sem auth deve retornar 401/403."""
    response = client.post(
        "/api/v1/usuarios/",
        json={"usuario": "novo@test.com", "senha": "senha123"},
    )
    assert response.status_code in (401, 403)


def test_listar_usuarios_com_auth(client, auth_headers):
    """Listar usuários com auth deve retornar lista."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.get("/api/v1/usuarios/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_criar_usuario_duplicado(client, auth_headers):
    """Criar usuário com nome já existente deve retornar 400."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    # Criar usuário
    client.post(
        "/api/v1/usuarios/",
        headers=auth_headers,
        json={"usuario": "dup@test.com", "senha": "senha123"},
    )
    # Tentar criar de novo com mesmo username
    response = client.post(
        "/api/v1/usuarios/",
        headers=auth_headers,
        json={"usuario": "dup@test.com", "senha": "outrasenha"},
    )
    assert response.status_code == 400


def test_atualizar_usuario_inexistente(client, auth_headers):
    """Atualizar usuário com ID inexistente deve retornar 404."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.put(
        "/api/v1/usuarios/999999",
        headers=auth_headers,
        json={"nome": "Novo Nome"},
    )
    assert response.status_code == 404


def test_deletar_usuario_inexistente(client, auth_headers):
    """Deletar usuário com ID inexistente deve retornar 404."""
    if not auth_headers:
        import pytest
        pytest.skip("No valid auth credentials configured for test environment")
    response = client.delete("/api/v1/usuarios/999999", headers=auth_headers)
    assert response.status_code == 404
