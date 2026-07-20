import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = Column(Integer, nullable=True)  # None = global/todos
    tipo = Column(String(50), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensagem = Column(Text, nullable=False)
    link = Column(String(500), nullable=True)
    lida = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
