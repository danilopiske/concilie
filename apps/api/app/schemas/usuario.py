from typing import Optional, List
from pydantic import BaseModel

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
    
    class Config:
        from_attributes = True
