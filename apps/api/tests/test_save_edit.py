"""
Tests para o endpoint de salvar edição de relatório (save-edit).
"""

import pytest
import os
from app.models.relatorio_task import RelatorioTask

def test_save_edit_success(client, auth_headers, db):
    """Salva edição com sucesso para uma task SUCCESS."""
    # 1. Criar uma task com status SUCCESS no banco usando a fixture 'db'
    task = RelatorioTask(
        id="test-task-123",
        processamento_id="proc-test",
        status="SUCCESS",
        result_path="relatorios_gerados/original.html"
    )
    db.add(task)
    db.commit()

    # 2. Chamar o endpoint de save-edit
    html_content = "<html><body>Editado!</body></html>"
    response = client.post(
        f"/api/v1/relatorios/tasks/{task.id}/save-edit",
        headers=auth_headers,
        json={"html_content": html_content}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "test-task-123_edited.html" in data["path"]

    # 3. Verificar se o result_path foi atualizado no banco
    db.refresh(task)
    assert "edited.html" in task.result_path
    
    # Cleanup: remover arquivo criado se necessário (opcional para testes com mocks/temp dirs)
    if os.path.exists(task.result_path):
        os.remove(task.result_path)

def test_save_edit_not_found(client, auth_headers):
    """Tentar salvar edição para task inexistente retorna 422 (ValueError no service)."""
    response = client.post(
        "/api/v1/relatorios/tasks/invalid-id/save-edit",
        headers=auth_headers,
        json={"html_content": "..."}
    )
    assert response.status_code == 422
    assert "não encontrada" in response.json()["detail"]

def test_save_edit_wrong_status(client, auth_headers, db):
    """Tentar editar relatório que ainda não está pronto (não é SUCCESS) retorna 422."""
    task = RelatorioTask(
        id="test-task-pending",
        processamento_id="proc-test",
        status="PENDING"
    )
    db.add(task)
    db.commit()

    response = client.post(
        f"/api/v1/relatorios/tasks/{task.id}/save-edit",
        headers=auth_headers,
        json={"html_content": "..."}
    )
    assert response.status_code == 422
    assert "Apenas relatórios com status SUCCESS" in response.json()["detail"]
