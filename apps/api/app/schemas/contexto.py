"""
Contexto Schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ContextoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True


class ContextoCreate(ContextoBase):
    criado_por: Optional[str] = None


class ContextoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None


class ContextoResponse(ContextoBase):
    id: int
    criado_por: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
