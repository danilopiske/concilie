"""
Clientes Endpoints
"""

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate
from app.services.cliente_service import ClienteService

router = APIRouter()


@router.get("/exportar-csv")
async def exportar_clientes_csv(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Exporta lista de clientes como CSV, com filtro opcional por nome/CNPJ."""
    query = db.query(Cliente)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Cliente.nome_fantasia.ilike(like))
            | (Cliente.razao_social.ilike(like))
            | (Cliente.cnpj.ilike(like))
        )
    clientes = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome Fantasia", "Razão Social", "CNPJ"])
    for c in clientes:
        writer.writerow([c.cliente_id, c.nome_fantasia or "", c.razao_social or "", c.cnpj or ""])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clientes.csv"},
    )


@router.get("/", response_model=List[dict])
async def listar_clientes(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all clientes, with optional search by nome/CNPJ."""
    if q:
        like = f"%{q}%"
        clientes = (
            db.query(Cliente)
            .filter(
                (Cliente.nome_fantasia.ilike(like))
                | (Cliente.razao_social.ilike(like))
                | (Cliente.cnpj.ilike(like))
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "cliente_id": c.cliente_id,
                "nome_fantasia": c.nome_fantasia,
                "razao_social": c.razao_social,
                "cnpj": c.cnpj,
            }
            for c in clientes
        ]
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
