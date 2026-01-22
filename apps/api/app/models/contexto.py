"""
Contexto Model
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.models.base import Base


class Contexto(Base):
    __tablename__ = "contextos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_por = Column(String(100))
    criado_em = Column(TIMESTAMP, server_default=func.current_timestamp())
    atualizado_em = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    def __repr__(self):
        return f"<Contexto(id={self.id}, nome={self.nome})>"
