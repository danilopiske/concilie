from typing import List, Literal, Optional

from pydantic import BaseModel


class PermissaoResponse(BaseModel):
    perfil: Literal["admin", "operador", "visualizador"]
    contextos_ids: List[int]
    clientes_ids: List[int]

    class Config:
        from_attributes = True


class PermissaoUpdate(BaseModel):
    perfil: Literal["admin", "operador", "visualizador"]
    contextos_ids: Optional[List[int]] = []
    clientes_ids: Optional[List[int]] = []
