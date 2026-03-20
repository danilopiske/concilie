from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.processamento_repository import ProcessamentoRepository
from app.schemas.processamento import ProcessamentoFilter, ProcessamentoResponse

router = APIRouter()

@router.get("/", response_model=List[ProcessamentoResponse])
def listar_processamentos(
    cliente_id: int = None,
    status: str = None,
    simple: bool = False,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    repo = ProcessamentoRepository(db)
    filtro = ProcessamentoFilter(cliente_id=cliente_id, status=status)
    return repo.listar(skip=skip, limit=limit, filtros=filtro, simple=simple)

@router.post("/batch-delete")
def deletar_processamentos(
    ids: List[str],
    db: Session = Depends(get_db)
):
    repo = ProcessamentoRepository(db)
    return {"success": repo.deletar_lista(ids), "count": len(ids)}
