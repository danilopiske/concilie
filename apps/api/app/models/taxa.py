"""
Taxa Model
"""

from sqlalchemy import CHAR, DECIMAL, TIMESTAMP, Column, Date, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class Taxa(Base):
    __tablename__ = "taxas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ec = Column(String(20), nullable=False, index=True)
    bandeira = Column(String(50))
    forma_pagamento = Column(String(50))
    parcelado = Column(CHAR(1), default="N")  # 'S'=sim, 'N'=não
    parcelas_ini = Column(Integer, nullable=False)
    parcelas_fim = Column(Integer, nullable=False)
    data_ini = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    taxa = Column(DECIMAL(10, 2), nullable=False)
    criado_em = Column(TIMESTAMP, server_default=func.current_timestamp())
    atualizado_em = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    contexto = Column(String(50))

    def __repr__(self):
        return f"<Taxa(ec={self.ec}, bandeira={self.bandeira}, taxa={self.taxa})>"
