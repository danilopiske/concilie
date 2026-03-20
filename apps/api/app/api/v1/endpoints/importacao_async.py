from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.importacao import ImportacaoConfirmar
from app.services.import_service import ImportService

router = APIRouter()

@router.post("/confirmar")
async def confirmar_importacao_async(
    dados: ImportacaoConfirmar,
    background_tasks: BackgroundTasks,
    usuario: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Inicia a gravação dos dados em segundo plano.
    """
    service = ImportService(db)
    task = service.create_import_task(
        cliente_id=dados.cliente_id,
        tipo_arquivo=dados.tipo,
        contexto=dados.contexto,
        usuario=usuario,
        file_id=dados.file_id,
        ec_id=dados.ec_id,
        processamentoid=dados.processamentoid
    )

    # Adiciona a tarefa ao background do FastAPI
    background_tasks.add_task(service.run_async_import, task.id)

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Processamento iniciado em segundo plano."
    }

@router.get("/task/{task_id:path}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna o status atual de uma tarefa de importação.
    """
    service = ImportService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "updated_at": task.updated_at,
        "tipo_arquivo": task.tipo_arquivo,
        "contexto": task.contexto
    }

@router.get("/active-tasks")
async def get_active_tasks(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de tarefas ativas ou recentes de um cliente.
    """
    service = ImportService(db)
    tasks = service.get_active_tasks(cliente_id)
    return [
        {
            "id": t.id,
            "status": t.status,
            "progress": t.progress,
            "message": t.message,
            "updated_at": t.updated_at,
            "tipo_arquivo": t.tipo_arquivo,
            "contexto": t.contexto
        } for t in tasks
    ]
