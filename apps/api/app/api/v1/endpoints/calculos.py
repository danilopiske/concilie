from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.calculo_repository import CalculoRepository
from app.schemas.calculo import (
    CalculoPreviewRequest, 
    CalculoStats, 
    CalculoRequest, 
    CalculoResultado
)

router = APIRouter()

@router.post("/preview", response_model=CalculoStats)
def preview_calculo(req: CalculoPreviewRequest, db: Session = Depends(get_db)):
    repo = CalculoRepository(db)
    return repo.preview_calculo(req)

@router.post("/processar")
def processar_calculo(req: CalculoRequest, db: Session = Depends(get_db)):
    # Note: Long running process. Ideally should be background task.
    # For MVP/Legacy parity, running synchronously (ensure timeout cfg is high)
    repo = CalculoRepository(db)
    try:
        repo.processar_calculo(req)
        return {"status": "success", "message": "Cálculo processado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resultados/{calc_id}", response_model=List[CalculoResultado])
def listar_resultados(
    calc_id: str, 
    skip: int = Query(0), 
    limit: int = Query(100), 
    db: Session = Depends(get_db)
):
    repo = CalculoRepository(db)
    return repo.listar_resultados(calc_id, skip, limit)
