"""
Termo Filtravel Schemas
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class TermoFiltravelBase(BaseModel):
    ec: str
    termo: str
    tipo: str = Field(
        ...,
        description="Tipo do termo: v (venda), r (recebível), l (lançamento), status",
    )
    contexto: str = Field(default="padrao", description="Contexto do termo")


class TermoFiltravelCreate(TermoFiltravelBase):
    """Schema para criação de termo filtrável"""

    pass


class TermoFiltravelUpdate(BaseModel):
    """Schema para atualização de termo filtrável"""

    termo: Optional[str] = None
    tipo: Optional[str] = None


class TermoFiltravelResponse(TermoFiltravelBase):
    """Schema de resposta de termo filtrável"""

    id: int

    model_config = ConfigDict(from_attributes=True)
