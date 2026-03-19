"""
Tests para a API de RelatorioTags (CRUD e validações).
"""

import pytest

def test_listar_tags_vazio(client, auth_headers):
    """Lista de tags deve retornar lista vazia inicialmente."""
    response = client.get("/api/v1/relatorio-tags/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_criar_tag_com_sucesso(client, auth_headers):
    """Cria uma nova tag válida."""
    payload = {
        "nome": "Tag de Teste",
        "tipo": "secao",
        "descricao": "Uma descrição de teste",
        "conteudo_padrao": "<h1>Conteudo</h1>",
        "ativo": True
    }
    response = client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == payload["nome"]
    assert "id" in data

def test_criar_tag_nome_duplicado(client, auth_headers):
    """Tentar criar tag com nome já existente deve retornar 422."""
    payload = {
        "nome": "Tag Unica",
        "tipo": "secao",
        "conteudo_padrao": "...",
    }
    # Primeira criação
    client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload)
    
    # Segunda criação
    response = client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload)
    assert response.status_code == 422
    assert "Já existe uma tag com o nome" in response.json()["detail"]

def test_obter_tag_por_id(client, auth_headers):
    """Busca uma tag específica pelo seu ID."""
    payload = {"nome": "Tag ID", "tipo": "secao", "conteudo_padrao": "..."}
    created = client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload).json()
    
    response = client.get(f"/api/v1/relatorio-tags/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["nome"] == "Tag ID"

def test_atualizar_tag(client, auth_headers):
    """Atualiza os dados de uma tag existente."""
    payload = {"nome": "Tag Original", "tipo": "secao", "conteudo_padrao": "Original"}
    created = client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload).json()
    
    update_payload = {"nome": "Tag Atualizada", "ativo": False}
    response = client.put(f"/api/v1/relatorio-tags/{created['id']}", headers=auth_headers, json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Tag Atualizada"
    assert data["ativo"] is False

def test_excluir_tag_soft_delete(client, auth_headers):
    """Exclusão de tag deve desativar a tag (soft delete)."""
    payload = {"nome": "Tag para Deletar", "tipo": "secao", "conteudo_padrao": "..."}
    created = client.post("/api/v1/relatorio-tags/", headers=auth_headers, json=payload).json()
    
    response = client.delete(f"/api/v1/relatorio-tags/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    
    # Verificar se ficou inativa
    get_response = client.get(f"/api/v1/relatorio-tags/{created['id']}", headers=auth_headers)
    assert get_response.json()["ativo"] is False

def test_listar_com_filtro_ativo(client, auth_headers):
    """Verifica filtros de ativo (true, false, all) na listagem."""
    # Criar uma ativa e uma inativa
    client.post("/api/v1/relatorio-tags/", headers=auth_headers, json={"nome": "Ativa", "tipo": "secao", "conteudo_padrao": "...", "ativo": True})
    client.post("/api/v1/relatorio-tags/", headers=auth_headers, json={"nome": "Inativa", "tipo": "secao", "conteudo_padrao": "...", "ativo": False})

    # Listar apenas ativas (default)
    res_default = client.get("/api/v1/relatorio-tags/", headers=auth_headers)
    assert all(t["ativo"] for t in res_default.json())

    # Listar apenas inativas
    res_inativas = client.get("/api/v1/relatorio-tags/?ativo=false", headers=auth_headers)
    assert all(not t["ativo"] for t in res_inativas.json())

    # Listar todas
    res_all = client.get("/api/v1/relatorio-tags/?ativo=all", headers=auth_headers)
    nomes = [t["nome"] for t in res_all.json()]
    assert "Ativa" in nomes
    assert "Inativa" in nomes
