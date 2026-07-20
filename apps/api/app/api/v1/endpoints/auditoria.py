"""
Endpoint para listagem do log de auditoria do usuário logado.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.services.audit_service import AuditService

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: str
    usuario_id: Optional[int] = None
    usuario: Optional[str] = None
    acao: str
    detalhes: Optional[str] = None
    ip: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=List[AuditLogResponse])
def listar_auditoria(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    """Lista os logs de auditoria do usuário logado."""
    usuario_id = getattr(current_user, "id", None)
    return AuditService.listar(db, usuario_id=usuario_id, skip=skip, limit=limit)
