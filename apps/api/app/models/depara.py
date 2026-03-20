from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class DeParaConfig(Base):
    __tablename__ = "depara_config"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    contexto = Column(String(100), nullable=True)
    ativo = Column(Boolean, default=True)
    criado_por = Column(String(100), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DeParaConfig(id={self.id}, titulo='{self.titulo}')>"
