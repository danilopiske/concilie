"""
Endpoints de Contextos
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.contexto import ContextoCreate, ContextoUpdate, ContextoResponse
from app.services.contexto_service import ContextoService

router = APIRouter()


@router.get("/", response_model=List[ContextoResponse])
def listar_contextos(
    skip: int = 0,
    limit: int = 100,
    incluir_inativos: bool = Query(False, description="Incluir contextos inativos"),
    db: Session = Depends(get_db),
):
    """
    Listar todos os contextos
    """
    service = ContextoService(db)
    return service.listar_contextos(skip, limit, incluir_inativos)


@router.get("/{contexto_id}", response_model=ContextoResponse)
def obter_contexto(contexto_id: int, db: Session = Depends(get_db)):
    """
    Obter contexto por ID
    """
    service = ContextoService(db)
    return service.obter_contexto(contexto_id)


@router.post("/", response_model=ContextoResponse, status_code=201)
def criar_contexto(contexto: ContextoCreate, db: Session = Depends(get_db)):
    """
    Criar novo contexto
    """
    service = ContextoService(db)
    return service.criar_contexto(contexto)


@router.put("/{contexto_id}", response_model=ContextoResponse)
def atualizar_contexto(
    contexto_id: int, contexto: ContextoUpdate, db: Session = Depends(get_db)
):
    """
    Atualizar contexto existente
    """
    service = ContextoService(db)
    return service.atualizar_contexto(contexto_id, contexto)


@router.delete("/{contexto_id}", status_code=204)
def deletar_contexto(contexto_id: int, db: Session = Depends(get_db)):
    """
    Deletar contexto
    """
    service = ContextoService(db)
    service.deletar_contexto(contexto_id)
    return None
