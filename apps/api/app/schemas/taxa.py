"""
Pydantic schemas para Taxas
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaxaBase(BaseModel):
    """Schema base de taxa"""

    ec: str = Field(..., description="Código do Estabelecimento Comercial")
    bandeira: Optional[str] = Field(
        None, description="Bandeira do cartão (NULL para taxa genérica)"
    )
    forma_pagamento: str = Field(..., description="Forma de pagamento")
    parcelado: str = Field("N", pattern="^[SN]$", description="S=Sim, N=Não")
    parcelas_ini: int = Field(1, ge=1, description="Parcela inicial")
    parcelas_fim: int = Field(1, ge=1, description="Parcela final")
    data_ini: date = Field(..., description="Data de início de vigência")
    data_fim: Optional[date] = Field(None, description="Data de fim de vigência")
    taxa: Decimal = Field(..., decimal_places=2, description="Taxa percentual")
    contexto: str = Field("padrao", description="Contexto da taxa")

    @field_validator("taxa")
    def validar_taxa(cls, v):
        """Garantir taxa positiva e arredondada"""
        if v <= 0:
            raise ValueError("Taxa deve ser maior que zero")
        return Decimal(str(v)).quantize(Decimal("0.01"))

    @field_validator("parcelas_fim")
    def validar_parcelas(cls, v, info):
        """Parcela final deve ser >= parcela inicial"""
        if "parcelas_ini" in info.data and v < info.data["parcelas_ini"]:
            raise ValueError("Parcela final deve ser maior ou igual à parcela inicial")
        return v

    @field_validator("data_fim")
    def validar_data_fim(cls, v, info):
        """Data fim deve ser >= data início"""
        if v and "data_ini" in info.data and v < info.data["data_ini"]:
            raise ValueError("Data fim deve ser maior ou igual à data de início")
        return v

    @field_validator("bandeira")
    def validar_bandeira(cls, v):
        """Limpar espaços da bandeira"""
        if v:
            return v.strip() if v.strip() else None
        return None

    @field_validator("forma_pagamento")
    def validar_forma_pagamento(cls, v):
        """Limpar espaços da forma de pagamento"""
        return v.strip().upper()


class TaxaCreate(TaxaBase):
    """Schema para criação de taxa"""

    pass


class TaxaUpdate(BaseModel):
    """Schema para atualização de taxa"""

    ec: Optional[str] = None
    bandeira: Optional[str] = None
    forma_pagamento: Optional[str] = None
    parcelado: Optional[str] = None
    parcelas_ini: Optional[int] = None
    parcelas_fim: Optional[int] = None
    data_ini: Optional[date] = None
    data_fim: Optional[date] = None
    taxa: Optional[Decimal] = None
    contexto: Optional[str] = None

    @field_validator("taxa")
    def validar_taxa(cls, v):
        """Arredondar taxa"""
        if v is not None and v > 0:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return v


class TaxaResponse(TaxaBase):
    """Schema de resposta de taxa"""

    id: int

    model_config = ConfigDict(from_attributes=True)


class TaxaCopiarRequest(BaseModel):
    """Schema para copiar taxas entre ECs"""

    ec_origem: str = Field(..., description="EC de origem das taxas")
    ecs_destino: list[str] = Field(
        ..., min_length=1, description="Lista de ECs de destino"
    )
    sobrescrever: bool = Field(
        False, description="Se True, remove taxas existentes antes de copiar"
    )
    contexto: str = Field("padrao", description="Contexto das taxas")


class TaxaCopiarResponse(BaseModel):
    """Schema de resposta da cópia de taxas"""

    copiadas: int = Field(..., description="Número de taxas copiadas")
    removidas: int = Field(0, description="Número de taxas removidas")
    erros: list[str] = Field(
        default_factory=list, description="Lista de erros ocorridos"
    )
