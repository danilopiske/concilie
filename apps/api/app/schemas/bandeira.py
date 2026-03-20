"""
Bandeira Schemas
"""

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict


class BandeiraDisponivelBase(BaseModel):
    nome: str
    padrao: bool = False


class BandeiraDisponivelCreate(BandeiraDisponivelBase):
    pass


class BandeiraDisponivelUpdate(BaseModel):
    nome: Optional[str] = None
    padrao: Optional[bool] = None


class BandeiraDisponivelResponse(BandeiraDisponivelBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BandeiraClienteBase(BaseModel):
    ec: str
    bandeira: str
    ativo: bool = False
    contexto: str = "padrao"


class BandeiraClienteUpdate(BaseModel):
    bandeiras: Dict[str, int]  # {nome_bandeira: ativo (0 ou 1)}
    contexto: str = "padrao"


class BandeiraClienteResponse(BandeiraClienteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
