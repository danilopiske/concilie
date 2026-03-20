from sqlalchemy import DECIMAL, Column, Date, DateTime, Integer, String

from app.models.base import Base


class Recebivel(Base):
    __tablename__ = "recebiveis_processados"

    id = Column(Integer, primary_key=True, index=True)
    processamentoid = Column(String(50), index=True)
    lancamento = Column(String(100), index=True)  # Key for grouping

    # Financials
    valor_recebivel = Column(DECIMAL(18, 2))
    valor_liquido = Column(DECIMAL(18, 2))

    # Dates
    data_pagamento = Column(DateTime)
    data_recebivel = Column(DateTime)

    # Identifiers
    recebivel_id = Column(String(100))
    adquirente = Column(String(100))
    descricao = Column(String(255))

    # Bank info
    banco = Column(String(20))
    agencia = Column(String(20))
    conta = Column(String(20))

    # Metadata
    cliente_id = Column(String(50))
    ec_id = Column(String(50))
    data_processamento = Column(DateTime)
    usuario_processamento = Column(String(100))
    arquivo_origem = Column(String(255))

class RecebivelFiltrado(Base):
    __tablename__ = "recebiveis_filtrados"

    id = Column(Integer, primary_key=True, index=True)
    processamentoid = Column(String(50), index=True)
    lancamento = Column(String(100))

    # Financials
    valor_recebivel = Column(DECIMAL(18, 2))
    valor_liquido = Column(DECIMAL(18, 2))

    # Dates
    data_pagamento = Column(DateTime)
    data_recebivel = Column(DateTime)

    # Identifiers
    recebivel_id = Column(String(100))
    adquirente = Column(String(100))
    descricao = Column(String(255))

    # Bank info
    banco = Column(String(20))
    agencia = Column(String(20))
    conta = Column(String(20))

    # Metadata
    cliente_id = Column(String(50))
    ec_id = Column(String(50))
    data_processamento = Column(DateTime)
    usuario_processamento = Column(String(100))
    arquivo_origem = Column(String(255))
