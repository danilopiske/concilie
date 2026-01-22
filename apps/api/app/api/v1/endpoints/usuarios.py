from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter()

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Listar usuários.
    """
    repo = UsuarioRepository(db)
    return repo.listar(skip=skip, limit=limit)

@router.post("/", response_model=UsuarioResponse)
def criar_usuario(
    usuario_in: UsuarioCreate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Criar novo usuário.
    """
    repo = UsuarioRepository(db)
    if repo.obter_por_usuario(usuario_in.usuario):
        raise HTTPException(
            status_code=400,
            detail="Usuário já existe no sistema."
        )
    return repo.criar(usuario_in)

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Atualizar usuário.
    """
    repo = UsuarioRepository(db)
    usuario = repo.atualizar(usuario_id, usuario_in)
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    return usuario

@router.delete("/{usuario_id}", response_model=Any)
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Deletar usuário.
    """
    repo = UsuarioRepository(db)
    if not repo.deletar(usuario_id):
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    return {"message": "Usuário deletado com sucesso"}
