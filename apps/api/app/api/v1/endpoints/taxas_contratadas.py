from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.taxa_contratada import (
    ComparacaoResponse,
    HistoricoDesviosResponse,
    TaxaContratadaCreate,
    TaxaContratadaResponse,
    TaxaContratadaUpdate,
)
from app.services import taxa_contratada_service as svc

router = APIRouter()


@router.get("/{cliente_id}/taxas-contratadas", response_model=List[TaxaContratadaResponse])
def listar_taxas(
    cliente_id: int,
    vigente: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.listar(cliente_id, vigente, db)


@router.post("/{cliente_id}/taxas-contratadas", response_model=TaxaContratadaResponse, status_code=201)
def criar_taxa(
    cliente_id: int,
    body: TaxaContratadaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.criar(cliente_id, body, db)


@router.put("/{cliente_id}/taxas-contratadas/{id}", response_model=TaxaContratadaResponse)
def atualizar_taxa(
    cliente_id: int,
    id: int,
    body: TaxaContratadaUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = svc.atualizar(id, cliente_id, body, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Taxa contratada não encontrada")
    return obj


@router.delete("/{cliente_id}/taxas-contratadas/{id}", status_code=204)
def remover_taxa(
    cliente_id: int,
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not svc.remover(id, cliente_id, db):
        raise HTTPException(status_code=404, detail="Taxa contratada não encontrada")


@router.get("/{cliente_id}/taxas-contratadas/comparacao", response_model=ComparacaoResponse)
def comparacao(
    cliente_id: int,
    processamento_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.comparar_contratado_vs_cobrado(cliente_id, processamento_id, db)


@router.get("/{cliente_id}/taxas-contratadas/historico-desvios", response_model=HistoricoDesviosResponse)
def historico_desvios(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.historico_desvios(cliente_id, db)
