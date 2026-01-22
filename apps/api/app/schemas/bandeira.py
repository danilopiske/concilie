"""
Bandeira Schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
