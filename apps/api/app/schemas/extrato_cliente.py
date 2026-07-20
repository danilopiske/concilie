from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExtratoClienteCreate(BaseModel):
    tipo: str = Field("Outro", max_length=50)


class ExtratoClienteResponse(BaseModel):
    id: str
    cliente_id: int
    nome_arquivo: str
    tipo: str
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    status: str
    processamento_id: Optional[int] = None

    model_config = {"from_attributes": True}


class ExtratoStatusResumo(BaseModel):
    total: int
    aguardando: int
    importado: int
    divergente: int
