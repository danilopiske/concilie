"""
Modelo de Tags de Relatório (seções inseríveis via slash commands no editor)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class RelatorioTag(Base):
    __tablename__ = "relatorio_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(50), unique=True, nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # secao|clausula|assinatura|cabecalho|rodape
    descricao = Column(String(200), nullable=True)
    conteudo_padrao = Column(Text, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
