import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, Enum, Float, Integer, String, Text

from app.models.base import Base


class StatusContestacao(str, PyEnum):
    rascunho = "rascunho"
    enviada = "enviada"
    em_analise = "em_analise"
    deferida = "deferida"
    indeferida = "indeferida"


class Contestacao(Base):
    __tablename__ = "contestacoes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = Column(Integer, nullable=False, index=True)
    processamento_id = Column(Integer, nullable=True)
    adquirente = Column(String(100), nullable=False)
    periodo_inicio = Column(Date, nullable=False)
    periodo_fim = Column(Date, nullable=False)
    valor_excesso_total = Column(Float, nullable=False, default=0.0)
    status = Column(
        Enum(StatusContestacao, native_enum=False),
        nullable=False,
        default=StatusContestacao.rascunho,
    )
    html_carta = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False, default="sistema")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Contestacao(id={self.id}, cliente={self.cliente_id}, status={self.status})>"
