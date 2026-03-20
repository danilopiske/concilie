from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.correcao_repository import CorrecaoRepository
from app.schemas.correcao import (
    AplicarTaxaBCRequest,
    AtualizarRequest,
    FiltrosBCResponse,
    HistoricoItem,
    RemoverRequest,
    ResumoResponse,
)

router = APIRouter()

@router.get("/resumo", response_model=ResumoResponse)
def obter_resumo(
    processamento_id: str,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    return repo.listar_resumo(processamento_id)

@router.get("/historico", response_model=List[HistoricoItem])
def obter_historico(
    processamento_id: str,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    return repo.listar_historico(processamento_id)

@router.patch("/atualizar")
def atualizar_em_massa(
    request: AtualizarRequest,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    try:
        count = repo.atualizar_em_massa(
            request.processamento_id,
            request.campo,
            request.valores_antigos,
            request.valor_novo
        )
        return {"message": "Atualizado com sucesso", "linhas_afetadas": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/remover")
def remover_em_massa(
    request: RemoverRequest,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    try:
        count = repo.mover_para_filtradas(
            request.processamento_id,
            request.campo,
            request.valores
        )
        return {"message": "Removido com sucesso (movido para filtrados)", "linhas_afetadas": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/excluir-filtradas")
def excluir_filtradas(
    request: RemoverRequest,
    db: Session = Depends(get_db)
):
    """
    Remove permanentemente itens da tabela de filtrados.
    """
    repo = CorrecaoRepository(db)
    try:
        count = repo.deletar_filtradas(
            request.processamento_id,
            request.campo,
            request.valores
        )
        return {"message": "Excluído permanentemente do sistema (tabela de filtrados)", "linhas_afetadas": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/filtros-taxa-bc", response_model=FiltrosBCResponse)
def obter_filtros_taxa_bc(
    processamento_id: str,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    return repo.listar_filtros_taxa_bc(processamento_id)

@router.post("/aplicar-taxa-bc")
def aplicar_taxa_bc(
    request: AplicarTaxaBCRequest,
    db: Session = Depends(get_db)
):
    repo = CorrecaoRepository(db)
    try:
        count = repo.aplicar_taxa_bc(
            request.processamento_id,
            request.forma_pagamento,
            request.bandeira,
            request.data_ini,
            request.data_fim,
            request.nova_taxa,
            request.usuario
        )
        return {"message": "Taxa BC aplicada com sucesso", "linhas_afetadas": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
