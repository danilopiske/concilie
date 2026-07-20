"""
Endpoints de Termos Filtráveis
PUBLIC — intencional: dados de configuração de termos acessíveis sem restrição de perfil.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.termo_repository import TermoFiltravelRepository
from app.schemas.termo import TermoFiltravelCreate, TermoFiltravelResponse

router = APIRouter()
# Force reload for DB lock clearance


@router.get("/{ec}", response_model=List[TermoFiltravelResponse])
async def listar_termos(
    ec: str,
    contexto: str = Query(default="padrao"),
    tipo: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Listar termos filtráveis por EC e contexto

    - **ec**: Código do estabelecimento
    - **contexto**: Contexto (padrao, CIELO, REDE, etc.)
    - **tipo**: Tipo do termo (v=venda, r=recebível, l=lançamento, status=status)
    """
    repo = TermoFiltravelRepository(db)
    termos = repo.list_por_ec(ec=ec, contexto=contexto, tipo=tipo)
    return termos


@router.post("/", response_model=TermoFiltravelResponse, status_code=201)
async def adicionar_termo(
    termo: TermoFiltravelCreate,
    db: Session = Depends(get_db),
):
    """
    Adicionar novo termo filtrável

    - **ec**: Código do estabelecimento
    - **termo**: Termo a ser filtrado (ex: CANCELADO, ESTORNO)
    - **tipo**: v (venda), r (recebível), l (lançamento), status
    - **contexto**: Contexto (padrao, CIELO, REDE, etc.)
    """
    repo = TermoFiltravelRepository(db)

    # Verificar se já existe
    termos_existentes = repo.list_por_ec(
        ec=termo.ec, contexto=termo.contexto, tipo=termo.tipo
    )

    if any(t["termo"].upper() == termo.termo.upper() for t in termos_existentes):
        raise HTTPException(
            status_code=400,
            detail=f"Termo '{termo.termo}' já existe para este EC no contexto '{termo.contexto}'",
        )

    novo_termo = repo.adicionar(
        ec=termo.ec, termo=termo.termo.upper(), tipo=termo.tipo, contexto=termo.contexto
    )

    return TermoFiltravelResponse(
        id=novo_termo.id,
        ec=novo_termo.ec,
        termo=novo_termo.termo,
        tipo=novo_termo.tipo,
        contexto=novo_termo.contexto,
    )


@router.delete("/{termo_id}", status_code=204)
async def excluir_termo(
    termo_id: int,
    db: Session = Depends(get_db),
):
    """
    Excluir termo filtrável por ID

    - **termo_id**: ID do termo a ser excluído
    """
    repo = TermoFiltravelRepository(db)

    if not repo.excluir(termo_id):
        raise HTTPException(
            status_code=404, detail=f"Termo com ID {termo_id} não encontrado"
        )

    return None
