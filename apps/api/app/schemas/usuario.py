from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class UsuarioBase(BaseModel):
    usuario: str
    nome: Optional[str] = None
    empresa: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    usuario: Optional[str] = None
    nome: Optional[str] = None
    empresa: Optional[str] = None
    senha: Optional[str] = None  # Optional for updates

class UsuarioResponse(UsuarioBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
