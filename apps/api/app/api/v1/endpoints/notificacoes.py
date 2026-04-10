from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.notificacao import NotificacaoCount, NotificacaoResponse
from app.services.notificacao_service import NotificacaoService

router = APIRouter()


@router.get("/nao-lidas/count", response_model=NotificacaoCount)
def contar_nao_lidas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usuario_id = getattr(current_user, "id", None)
    count = NotificacaoService.contar_nao_lidas(db, usuario_id=usuario_id)
    return {"count": count}


@router.put("/marcar-todas-lidas")
def marcar_todas_lidas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usuario_id = getattr(current_user, "id", None)
    NotificacaoService.marcar_todas_lidas(db, usuario_id=usuario_id)
    return {"ok": True}


@router.get("", response_model=List[NotificacaoResponse])
def listar_notificacoes(
    lida: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usuario_id = getattr(current_user, "id", None)
    return NotificacaoService.listar(db, usuario_id=usuario_id, lida=lida, skip=skip, limit=limit)


@router.put("/{notificacao_id}/lida", response_model=NotificacaoResponse)
def marcar_lida(
    notificacao_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notif = NotificacaoService.marcar_lida(db, notificacao_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return notif


@router.delete("/{notificacao_id}")
def remover_notificacao(
    notificacao_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    removed = NotificacaoService.remover(db, notificacao_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return {"ok": True}
