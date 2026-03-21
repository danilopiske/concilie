from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.alerta_config import AlertaConfigCreate, AlertaConfigResponse
from app.services.alerta_config_service import AlertaConfigService

router = APIRouter()


@router.get("", response_model=List[AlertaConfigResponse])
def listar_alertas(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usuario_id = getattr(current_user, "id", None)
    return AlertaConfigService.listar_todos(db, usuario_id=usuario_id)


@router.post("", response_model=AlertaConfigResponse)
def criar_alerta(
    body: AlertaConfigCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usuario_id = getattr(current_user, "id", None)
    return AlertaConfigService.criar(
        db,
        tipo_alerta=body.tipo_alerta,
        threshold_valor=body.threshold_valor,
        usuario_id=usuario_id,
        descricao=body.descricao,
    )


class AlertaConfigUpdate(BaseModel):
    threshold_valor: Optional[float] = None
    ativo: Optional[bool] = None
    descricao: Optional[str] = None


@router.put("/{config_id}", response_model=AlertaConfigResponse)
def atualizar_alerta(
    config_id: str,
    body: AlertaConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    config = AlertaConfigService.atualizar(
        db,
        config_id,
        threshold_valor=body.threshold_valor,
        ativo=body.ativo,
        descricao=body.descricao,
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return config


@router.delete("/{config_id}")
def remover_alerta(
    config_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not AlertaConfigService.remover(db, config_id):
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    return {"ok": True}
