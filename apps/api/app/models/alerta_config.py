import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from .base import Base


class AlertaConfig(Base):
    __tablename__ = "alerta_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = Column(Integer, nullable=True)  # None = global
    tipo_alerta = Column(String(100), nullable=False)
    # Tipos: "variacao_taxa_pct", "importacao_erros_count", "calculo_divergencia_pct"
    threshold_valor = Column(Float, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    descricao = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
