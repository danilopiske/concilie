"""
Endpoints de Taxas
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.taxas_repository import TaxasRepository
from app.schemas.taxa import (
    TaxaCopiarRequest,
    TaxaCopiarResponse,
    TaxaCreate,
    TaxaResponse,
    TaxaUpdate,
)

router = APIRouter()


@router.get("/{ec}", response_model=List[TaxaResponse])
async def listar_taxas_ec(
    ec: str,
    contexto: str = Query("padrao", description="Contexto das taxas"),
    db: Session = Depends(get_db),
):
    """
    Listar todas as taxas de um EC específico
    """
    repository = TaxasRepository(db)
    taxas = repository.listar_por_ec(ec, contexto)
    return taxas


@router.post("/", response_model=dict, status_code=201)
async def criar_taxa(taxa: TaxaCreate, db: Session = Depends(get_db)):
    """
    Criar nova taxa

    **Campos obrigatórios:**
    - ec: Código do estabelecimento
    - forma_pagamento: Forma de pagamento
    - taxa: Taxa percentual (> 0)
    - data_ini: Data de início de vigência

    **Campos opcionais:**
    - bandeira: Bandeira do cartão (NULL = taxa genérica para todas as bandeiras)
    - parcelado: "S" ou "N" (padrão: "N")
    - parcelas_ini: Parcela inicial (padrão: 1)
    - parcelas_fim: Parcela final (padrão: 1)
    - data_fim: Data de fim de vigência
    - contexto: Contexto da taxa (padrão: "padrao")
    """
    repository = TaxasRepository(db)
    sucesso = repository.criar(taxa)

    if not sucesso:
        raise HTTPException(status_code=400, detail="Erro ao criar taxa")

    tipo_taxa = "genérica (todas bandeiras)" if not taxa.bandeira else "específica"
    return {
        "message": f"Taxa {tipo_taxa} criada com sucesso",
        "taxa": taxa.model_dump(),
    }


@router.put("/{taxa_id}", response_model=dict)
async def atualizar_taxa(taxa_id: int, taxa: TaxaUpdate, db: Session = Depends(get_db)):
    """
    Atualizar taxa existente
    """
    repository = TaxasRepository(db)
    sucesso = repository.atualizar(taxa_id, taxa)

    if not sucesso:
        raise HTTPException(
            status_code=404, detail="Taxa não encontrada ou erro ao atualizar"
        )

    return {"message": "Taxa atualizada com sucesso"}


@router.delete("/{taxa_id}", response_model=dict)
async def deletar_taxa(taxa_id: int, db: Session = Depends(get_db)):
    """
    Deletar taxa por ID
    """
    repository = TaxasRepository(db)
    sucesso = repository.deletar(taxa_id)

    if not sucesso:
        raise HTTPException(
            status_code=404, detail="Taxa não encontrada ou erro ao deletar"
        )

    return {"message": "Taxa deletada com sucesso"}


@router.post("/copiar", response_model=TaxaCopiarResponse)
async def copiar_taxas(request: TaxaCopiarRequest, db: Session = Depends(get_db)):
    """
    Copiar taxas de um EC de origem para um ou mais ECs de destino

    **Parâmetros:**
    - ec_origem: EC de origem das taxas
    - ecs_destino: Lista de ECs de destino
    - sobrescrever: Se True, remove taxas existentes nos ECs de destino antes de copiar (padrão: False)
    - contexto: Contexto das taxas (padrão: "padrao")

    **Retorna:**
    - copiadas: Número de taxas copiadas
    - removidas: Número de taxas removidas (se sobrescrever=True)
    - erros: Lista de erros ocorridos
    """
    repository = TaxasRepository(db)
    resultado = repository.copiar(request)

    return TaxaCopiarResponse(**resultado)
