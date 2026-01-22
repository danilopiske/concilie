"""
Pydantic schemas para Formas de Pagamento
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class FormaPagamentoBase(BaseModel):
    """Schema base de forma de pagamento"""

    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, max_length=50)
    ativo: bool = True


class FormaPagamentoCreate(FormaPagamentoBase):
    """Schema para criação de forma de pagamento"""

    created_by: Optional[str] = None

    @validator("nome")
    def normalizar_nome(cls, v):
        """Normalizar nome (título, trim)"""
        return v.strip().title()

    @validator("categoria")
    def validar_categoria(cls, v):
        """Validar categoria permitida"""
        if v is not None:
            categorias_validas = ["credito", "debito", "pix", "boleto", "outros"]
            v_lower = v.lower()
            if v_lower not in categorias_validas:
                raise ValueError(
                    f'Categoria deve ser uma de: {", ".join(categorias_validas)}'
                )
            return v_lower
        return v


class FormaPagamentoUpdate(BaseModel):
    """Schema para atualização de forma de pagamento"""

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, max_length=50)
    ativo: Optional[bool] = None
    updated_by: Optional[str] = None

    @validator("nome")
    def normalizar_nome(cls, v):
        if v is not None:
            return v.strip().title()
        return v

    @validator("categoria")
    def validar_categoria(cls, v):
        if v is not None:
            categorias_validas = ["credito", "debito", "pix", "boleto", "outros"]
            v_lower = v.lower()
            if v_lower not in categorias_validas:
                raise ValueError(
                    f'Categoria deve ser uma de: {", ".join(categorias_validas)}'
                )
            return v_lower
        return v


class FormaPagamentoResponse(FormaPagamentoBase):
    """Schema de resposta de forma de pagamento"""

    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


class FormaPagamentoList(BaseModel):
    """Schema para lista de formas de pagamento"""

    total: int
    formas_pagamento: List[FormaPagamentoResponse]


class FormaPagamentoBandeiraBase(BaseModel):
    """Schema base de relação forma-bandeira"""

    forma_pagamento_id: int
    bandeira_id: int
    ativo: bool = True


class FormaPagamentoBandeiraCreate(FormaPagamentoBandeiraBase):
    """Schema para criação de relação forma-bandeira"""

    pass


class FormaPagamentoBandeiraResponse(FormaPagamentoBandeiraBase):
    """Schema de resposta de relação forma-bandeira"""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True
