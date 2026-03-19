"""
Endpoints CRUD para RelatorioTag (seções inseríveis no editor via slash commands)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.relatorio_tag import RelatorioTagCreate, RelatorioTagUpdate, RelatorioTagResponse
from app.repositories.relatorio_tag_repository import RelatorioTagRepository

router = APIRouter()


def _parse_ativo(ativo: Optional[str] = "true") -> Optional[bool]:
    """Converte query param 'true'|'false'|'all' para bool ou None."""
    if ativo == "all":
        return None
    return ativo != "false"


@router.get("/", response_model=List[RelatorioTagResponse])
def listar_tags(
    ativo: Optional[str] = "true",
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista tags. ativo=true (default) | false | all"""
    repo = RelatorioTagRepository(db)
    return repo.list(ativo=_parse_ativo(ativo))


@router.post("/", response_model=RelatorioTagResponse, status_code=201)
def criar_tag(
    data: RelatorioTagCreate,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria nova tag. Retorna 422 se nome já existir."""
    repo = RelatorioTagRepository(db)
    if repo.get_by_nome(data.nome):
        raise HTTPException(
            status_code=422,
            detail=f"Já existe uma tag com o nome '{data.nome}'",
        )
    return repo.create(data)


@router.get("/{tag_id}", response_model=RelatorioTagResponse)
def obter_tag(
    tag_id: int,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna tag por ID."""
    repo = RelatorioTagRepository(db)
    tag = repo.get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    return tag


@router.put("/{tag_id}", response_model=RelatorioTagResponse)
def atualizar_tag(
    tag_id: int,
    data: RelatorioTagUpdate,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atualiza tag. Retorna 422 se novo nome já existir em outra tag."""
    repo = RelatorioTagRepository(db)
    if data.nome:
        existing = repo.get_by_nome(data.nome)
        if existing and existing.id != tag_id:
            raise HTTPException(
                status_code=422,
                detail=f"Já existe uma tag com o nome '{data.nome}'",
            )
    tag = repo.update(tag_id, data)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    return tag


@router.delete("/{tag_id}", status_code=204)
def excluir_tag(
    tag_id: int,
    _: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete: marca tag como inativa."""
    repo = RelatorioTagRepository(db)
    if not repo.delete(tag_id):
        raise HTTPException(status_code=404, detail="Tag não encontrada")
