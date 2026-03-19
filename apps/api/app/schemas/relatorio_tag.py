"""
Pydantic schemas para RelatorioTag
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


TIPOS_VALIDOS = ("secao", "clausula", "assinatura", "cabecalho", "rodape")


class RelatorioTagBase(BaseModel):
    nome: str = Field(..., max_length=50, description="Nome único da tag")
    tipo: str = Field(..., description="Tipo: secao, clausula, assinatura, cabecalho, rodape")
    descricao: Optional[str] = Field(None, max_length=200)
    conteudo_padrao: str = Field(..., description="Conteúdo HTML inserido ao selecionar a tag")
    ativo: bool = Field(True)


class RelatorioTagCreate(RelatorioTagBase):
    pass


class RelatorioTagUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = None
    descricao: Optional[str] = Field(None, max_length=200)
    conteudo_padrao: Optional[str] = None
    ativo: Optional[bool] = None


class RelatorioTagResponse(RelatorioTagBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
