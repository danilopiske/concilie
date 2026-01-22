"""
Endpoints de Formas de Pagamento
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.formas_pagamento import (
    FormaPagamentoCreate,
    FormaPagamentoUpdate,
    FormaPagamentoResponse,
    FormaPagamentoList,
    FormaPagamentoBandeiraCreate,
    FormaPagamentoBandeiraResponse,
)
from app.services.formas_pagamento_service import FormasPagamentoService

router = APIRouter()


@router.get("/", response_model=FormaPagamentoList)
async def listar_formas_pagamento(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    apenas_ativas: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Listar todas as formas de pagamento
    """
    service = FormasPagamentoService(db)
    formas = await service.listar_formas_pagamento(skip, limit, apenas_ativas)

    return {"total": len(formas), "formas_pagamento": formas}


@router.get("/estatisticas")
async def obter_estatisticas(db: Session = Depends(get_db)):
    """
    Obter estatísticas de formas de pagamento
    """
    service = FormasPagamentoService(db)
    return await service.obter_estatisticas()


@router.get("/buscar")
async def buscar_formas_pagamento(
    termo: str = Query(..., min_length=1), db: Session = Depends(get_db)
):
    """
    Buscar formas de pagamento por termo
    """
    service = FormasPagamentoService(db)
    formas = await service.buscar_formas_pagamento(termo)

    return {"total": len(formas), "formas_pagamento": formas}


@router.get("/{forma_id}", response_model=FormaPagamentoResponse)
async def obter_forma_pagamento(forma_id: int, db: Session = Depends(get_db)):
    """
    Obter forma de pagamento por ID
    """
    service = FormasPagamentoService(db)
    forma = await service.obter_forma_pagamento(forma_id)

    if not forma:
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")

    return forma


@router.post("/", response_model=FormaPagamentoResponse, status_code=201)
async def criar_forma_pagamento(
    forma: FormaPagamentoCreate, db: Session = Depends(get_db)
):
    """
    Criar nova forma de pagamento
    """
    service = FormasPagamentoService(db)

    try:
        return await service.criar_forma_pagamento(forma)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{forma_id}", response_model=FormaPagamentoResponse)
async def atualizar_forma_pagamento(
    forma_id: int, forma: FormaPagamentoUpdate, db: Session = Depends(get_db)
):
    """
    Atualizar forma de pagamento
    """
    service = FormasPagamentoService(db)

    try:
        forma_atualizada = await service.atualizar_forma_pagamento(forma_id, forma)
        if not forma_atualizada:
            raise HTTPException(
                status_code=404, detail="Forma de pagamento não encontrada"
            )
        return forma_atualizada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{forma_id}")
async def deletar_forma_pagamento(forma_id: int, db: Session = Depends(get_db)):
    """
    Deletar forma de pagamento (soft delete)
    """
    service = FormasPagamentoService(db)

    if not await service.deletar_forma_pagamento(forma_id):
        raise HTTPException(status_code=404, detail="Forma de pagamento não encontrada")

    return {"message": "Forma de pagamento deletada com sucesso"}


@router.post("/{forma_id}/bandeiras/{bandeira_id}")
async def associar_bandeira(
    forma_id: int, bandeira_id: int, db: Session = Depends(get_db)
):
    """
    Associar bandeira a uma forma de pagamento
    """
    service = FormasPagamentoService(db)

    try:
        return await service.associar_bandeira(forma_id, bandeira_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{forma_id}/bandeiras/{bandeira_id}")
async def remover_associacao_bandeira(
    forma_id: int, bandeira_id: int, db: Session = Depends(get_db)
):
    """
    Remover associação entre forma de pagamento e bandeira
    """
    service = FormasPagamentoService(db)

    try:
        return await service.remover_associacao_bandeira(forma_id, bandeira_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
