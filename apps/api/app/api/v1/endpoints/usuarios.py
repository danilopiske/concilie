from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.api.deps import require_role
from app.models.usuario_cliente import UsuarioCliente
from app.models.usuario_contexto import UsuarioContexto
from app.models.usuario_permissao import UsuarioPermissao
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.schemas.usuario_permissao import PermissaoResponse, PermissaoUpdate

router = APIRouter()

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    _: Any = Depends(require_role(["admin"])),
) -> Any:
    """
    Listar usuários.
    """
    repo = UsuarioRepository(db)
    return repo.listar(skip=skip, limit=limit)

@router.post("/", response_model=UsuarioResponse)
def criar_usuario(
    usuario_in: UsuarioCreate,
    db: Session = Depends(deps.get_db),
    _: Any = Depends(require_role(["admin"])),
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
    db: Session = Depends(deps.get_db),
    _: Any = Depends(require_role(["admin"])),
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
    db: Session = Depends(deps.get_db),
    _: Any = Depends(require_role(["admin"])),
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


@router.get("/{usuario_id}/permissoes", response_model=PermissaoResponse)
def get_permissoes(
    usuario_id: int,
    db: Session = Depends(deps.get_db),
    _: Any = Depends(deps.require_role(["admin"])),
) -> Any:
    """Retorna perfil e escopos do usuário."""
    repo = UsuarioRepository(db)
    usuario = repo.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    perfil = usuario.permissao.perfil if usuario.permissao else "admin"
    contextos_ids = [uc.contexto_id for uc in usuario.contextos_permitidos]
    clientes_ids = [uc.cliente_id for uc in usuario.clientes_permitidos]

    return PermissaoResponse(perfil=perfil, contextos_ids=contextos_ids, clientes_ids=clientes_ids)


@router.put("/{usuario_id}/permissoes", response_model=PermissaoResponse)
def set_permissoes(
    usuario_id: int,
    data: PermissaoUpdate,
    db: Session = Depends(deps.get_db),
    _: Any = Depends(deps.require_role(["admin"])),
) -> Any:
    """Atualiza perfil e escopos do usuário. Aplica imediatamente."""
    repo = UsuarioRepository(db)
    usuario = repo.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Upsert permissao
    if usuario.permissao:
        usuario.permissao.perfil = data.perfil
        usuario.permissao.atualizado_em = datetime.utcnow()
    else:
        db.add(UsuarioPermissao(usuario_id=usuario_id, perfil=data.perfil))

    # Substituir contextos
    db.query(UsuarioContexto).filter(UsuarioContexto.usuario_id == usuario_id).delete()
    for cid in data.contextos_ids or []:
        db.add(UsuarioContexto(usuario_id=usuario_id, contexto_id=cid))

    # Substituir clientes
    db.query(UsuarioCliente).filter(UsuarioCliente.usuario_id == usuario_id).delete()
    for cid in data.clientes_ids or []:
        db.add(UsuarioCliente(usuario_id=usuario_id, cliente_id=cid))

    db.commit()
    db.refresh(usuario)

    contextos_ids = [uc.contexto_id for uc in usuario.contextos_permitidos]
    clientes_ids = [uc.cliente_id for uc in usuario.clientes_permitidos]
    return PermissaoResponse(
        perfil=usuario.permissao.perfil,
        contextos_ids=contextos_ids,
        clientes_ids=clientes_ids,
    )
