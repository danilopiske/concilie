from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class DeParaBase(BaseModel):
    origem_nome: Optional[str] = None
    destino_nome: Optional[str] = ""
    contexto: Optional[str] = ""
    tipo_origem: Optional[str] = "V"  # V, R, L
    tipo_preenchimento: Optional[str] = "importado"  # importado, padrao, sistema
    valor_padrao: Optional[str] = None
    ativo: Optional[int] = 1  # 1 or 0 in DB
    criado_por: Optional[str] = None

    @field_validator('destino_nome', 'contexto', mode='before')
    @classmethod
    def empty_string_if_none(cls, v):
        return v or ""

    @field_validator('tipo_origem', mode='before')
    @classmethod
    def default_tipo_origem(cls, v):
        return v or "V"

    @field_validator('tipo_preenchimento', mode='before')
    @classmethod
    def default_tipo_preenchimento(cls, v):
        return v or "importado"

    @field_validator('ativo', mode='before')
    @classmethod
    def default_ativo(cls, v):
        if v is None:
            return 1
        return v


class DeParaCreate(DeParaBase):
    pass

class DeParaUpdate(BaseModel):
    origem_nome: Optional[str] = None
    destino_nome: Optional[str] = None
    contexto: Optional[str] = None
    tipo_origem: Optional[str] = None
    tipo_preenchimento: Optional[str] = None
    valor_padrao: Optional[str] = None
    ativo: Optional[int] = None

class DeParaResponse(DeParaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
