from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.analista_repository import AnalistaRepository
from app.schemas.analista import (
    AgregacaoBandeira,
    AgregacaoFormaPagamento,
    AgregacaoFormaPagamentoAno,
    AgregacaoPeriodo,
    AgregacaoRecebivel,
)

router = APIRouter()

@router.get("/{processamento_id:path}/bandeiras", response_model=List[AgregacaoBandeira])
def get_bandeiras_filtradas(processamento_id: str, db: Session = Depends(get_db)):
    repo = AnalistaRepository(db)
    return repo.get_bandeiras_filtradas(processamento_id)

@router.get("/{processamento_id:path}/formas-pagamento", response_model=List[AgregacaoFormaPagamento])
def get_formas_pagamento_filtradas(processamento_id: str, db: Session = Depends(get_db)):
    repo = AnalistaRepository(db)
    return repo.get_formas_pagamento_filtradas(processamento_id)

@router.get("/{processamento_id:path}/periodos", response_model=List[AgregacaoPeriodo])
def get_periodos_filtradas(
    processamento_id: str,
    tipo: str = Query(..., pattern="^(mes|trimestre|semestre|ano)$"),
    db: Session = Depends(get_db)
):
    repo = AnalistaRepository(db)
    return repo.get_periodos_filtradas(processamento_id, tipo)

@router.get("/{processamento_id:path}/recebiveis", response_model=List[AgregacaoRecebivel])
def get_recebiveis_filtrados(processamento_id: str, db: Session = Depends(get_db)):
    repo = AnalistaRepository(db)
    return repo.get_recebiveis_filtrados(processamento_id)

@router.get("/{processamento_id:path}/formas-por-ano", response_model=List[AgregacaoFormaPagamentoAno])
def get_formas_por_ano_filtradas(processamento_id: str, db: Session = Depends(get_db)):
    repo = AnalistaRepository(db)
    return repo.get_formas_por_ano_filtradas(processamento_id)
