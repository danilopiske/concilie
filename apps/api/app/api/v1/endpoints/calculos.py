import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
from app.core.database import get_db
from app.repositories.calculo_repository import CalculoRepository
from app.services.calculo_service import CalculoService
from app.services.reconciliation_core import ReconciliationCore
from fastapi import BackgroundTasks
from app.schemas.calculo import (
    CalculoPreviewRequest, 
    CalculoStats, 
    CalculoRequest, 
    CalculoResultado,
    CalculoHistoryItem
)

router = APIRouter()

@router.post("/preview", response_model=CalculoStats)
def preview_calculo(req: CalculoPreviewRequest, db: Session = Depends(get_db)):
    repo = CalculoRepository(db)
    return repo.preview_calculo(req)

@router.get("/historico-calculos", response_model=List[CalculoHistoryItem])
async def get_historico_calculos(
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de cálculos únicos salvos no banco.
    """
    repo = CalculoRepository(db)
    return repo.listar_historico(skip=skip, limit=limit)

@router.post("/processar")
def processar_calculo(req: CalculoRequest, db: Session = Depends(get_db)):
    """
    Runs calculation synchronously using the high-performance Polars engine.
    For very large datasets, use /processar-async.
    """
    try:
        repo = CalculoRepository(db)
        custom_id = repo.processar_calculo(req)
        
        engine = db.get_bind()
        result = ReconciliationCore.calculate_rates(
            engine=engine,
            proc_id=req.processamento_id,
            tipo_taxa=req.tipo_taxa,
            usar_taxa_cad=req.usar_taxa_cad,
            tem_receba_rapido=req.tem_receba_rapido,
            custom_calc_id=custom_id
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
            
        return {
            "status": "success", 
            "message": f"Cálculo processado com sucesso. {result.get('rows')} registros.",
            "calc_id": custom_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processar-async")
async def processar_calculo_async(
    req: CalculoRequest, 
    background_tasks: BackgroundTasks,
    usuario: str = "api_user",
    db: Session = Depends(get_db)
):
    """Starts calculation in background and returns a task_id."""
    service = CalculoService(db)
    task = service.create_calculo_task(
        processamento_id=req.processamento_id,
        tipo_taxa=req.tipo_taxa,
        usuario=usuario,
        usar_taxa_cad=req.usar_taxa_cad,
        tem_receba_rapido=req.tem_receba_rapido,
        substituir=req.substituir
    )
    
    background_tasks.add_task(service.run_async_calculo, task.id)
    
    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Cálculo iniciado em segundo plano."
    }

@router.get("/task/{task_id:path}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Returns current calculation task status."""
    service = CalculoService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    return {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "updated_at": task.updated_at,
        "processamento_id": task.processamento_id,
        "tipo_taxa": task.tipo_taxa
    }

@router.get("/resultados/{calc_id:path}", response_model=List[CalculoResultado])
def listar_resultados(
    calc_id: str, 
    skip: int = Query(0), 
    limit: int = Query(100), 
    db: Session = Depends(get_db)
):
    logger.debug("Buscando resultados para calc_id: %s", calc_id)
    repo = CalculoRepository(db)
    return repo.listar_resultados(calc_id, skip, limit)


@router.delete("/{calc_id:path}")
async def delete_calculo(
    calc_id: str,
    db: Session = Depends(get_db)
):
    """
    Deleta um cálculo específico do banco de dados.
    """
    repo = CalculoRepository(db)
    repo.deletar_calculo(calc_id)
    return {"status": "success", "message": f"Cálculo {calc_id} deletado."}

@router.get("/historico")
async def get_historico(
    processamento_id: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de TAREFAS de cálculo (async).
    """
    service = CalculoService(db)
    tasks = service.list_tasks(skip=skip, limit=limit, processamento_id=processamento_id)
    return tasks
