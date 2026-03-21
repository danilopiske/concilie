from sqlalchemy import Column, Integer, String

from app.models.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(50), unique=True, index=True, nullable=False)
    senha = Column(String(64), nullable=False)  # Char(64) suggests SHA256 hex digest
    nome = Column(String(100), nullable=True)
    empresa = Column(String(100), nullable=True)

    # Optional fields based on common patterns, can be added if schema inspection reveals them
    # criado_em = Column(DateTime, server_default=func.now())
    # atualizado_em = Column(DateTime, onupdate=func.now())
