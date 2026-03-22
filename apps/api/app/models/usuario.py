from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(50), unique=True, index=True, nullable=False)
    senha = Column(String(64), nullable=False)  # Char(64) suggests SHA256 hex digest
    nome = Column(String(100), nullable=True)
    empresa = Column(String(100), nullable=True)

    permissao = relationship("UsuarioPermissao", uselist=False, back_populates="usuario", cascade="all, delete-orphan")
    contextos_permitidos = relationship("UsuarioContexto", back_populates="usuario", cascade="all, delete-orphan")
    clientes_permitidos = relationship("UsuarioCliente", back_populates="usuario", cascade="all, delete-orphan")
