"""Testes unitários para RelatorioService — Story 3.4 (B-05 parcial)."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.relatorio_service import RelatorioService


def _make_service():
    mock_db = MagicMock()
    return RelatorioService(db=mock_db), mock_db


def test_create_task_returns_relatorio_task():
    service, mock_db = _make_service()
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: None

    task = service.create_task("proc_123", "retroativo", "user1")

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert task.processamento_id == "proc_123"
    assert task.tipo_relatorio == "retroativo"
    assert task.status == "PENDING"
    assert task.progress == 0


def test_get_task_returns_none_when_not_found():
    service, mock_db = _make_service()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = service.get_task("nonexistent-id")

    assert result is None
    mock_db.query.assert_called_once()


def test_list_tasks_applies_processamento_filter():
    service, mock_db = _make_service()
    mock_tasks = [MagicMock(), MagicMock()]
    (
        mock_db.query.return_value
        .filter.return_value
        .order_by.return_value
        .offset.return_value
        .limit.return_value
        .all.return_value
    ) = mock_tasks

    result = service.list_tasks(processamento_id="proc_456")

    assert result == mock_tasks
    mock_db.query.return_value.filter.assert_called_once()


def test_save_edit_writes_file_and_updates_result_path(tmp_path):
    service, mock_db = _make_service()

    mock_task = MagicMock()
    mock_task.status = "SUCCESS"
    mock_task.result_path = str(tmp_path / "report.html")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_task

    html_content = "<html><body>Edited</body></html>"
    edited_path = service.save_edit("task-001", html_content)

    assert edited_path.endswith("_edited.html")
    from pathlib import Path
    assert Path(edited_path).read_text(encoding="utf-8") == html_content
    mock_db.commit.assert_called_once()
