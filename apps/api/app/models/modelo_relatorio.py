"""
Modelo de Modelos de Relatório — cadastro de templates disponíveis para emissão.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class ModeloRelatorio(Base):
    __tablename__ = "modelos_relatorio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    template_arquivo = Column(String(200), nullable=True)   # None = Excel gerado programaticamente
    tipo = Column(String(10), nullable=False)               # html | xml
    secoes_necessarias = Column(Text, nullable=False)       # JSON array ex: ["perdas_semestre","taxas_minmax"]
    ativo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
