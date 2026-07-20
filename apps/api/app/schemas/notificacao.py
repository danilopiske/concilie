from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificacaoResponse(BaseModel):
    id: str
    usuario_id: Optional[int] = None
    tipo: str
    titulo: str
    mensagem: str
    link: Optional[str] = None
    lida: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificacaoCount(BaseModel):
    count: int
