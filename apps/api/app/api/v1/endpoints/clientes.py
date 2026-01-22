"""
Clientes Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse
from app.services.cliente_service import ClienteService

router = APIRouter()


@router.get("/", response_model=List[dict])
async def listar_clientes(db: Session = Depends(get_db)):
    """List all clientes"""
    service = ClienteService(db)
    return service.listar_clientes()


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Get cliente by ID"""
    service = ClienteService(db)
    try:
        return service.obter_cliente(cliente_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=ClienteResponse, status_code=201)
async def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    """Create new cliente"""
    service = ClienteService(db)
    try:
        return service.criar_cliente(cliente.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: int, cliente: ClienteUpdate, db: Session = Depends(get_db)
):
    """Update cliente"""
    service = ClienteService(db)
    try:
        return service.atualizar_cliente(
            cliente_id, cliente.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{cliente_id}", status_code=204)
async def deletar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Delete cliente"""
    service = ClienteService(db)
    try:
        service.deletar_cliente(cliente_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{cliente_id}/ecs", response_model=List[str])
async def listar_ecs_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """List ECs for cliente"""
    service = ClienteService(db)
    return service.listar_ecs(cliente_id)
