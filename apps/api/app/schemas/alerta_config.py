from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertaConfigCreate(BaseModel):
    tipo_alerta: str
    threshold_valor: float
    descricao: Optional[str] = None
    ativo: bool = True


class AlertaConfigResponse(BaseModel):
    id: str
    usuario_id: Optional[int] = None
    tipo_alerta: str
    threshold_valor: float
    ativo: bool
    descricao: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
