from datetime import datetime

from sqlalchemy import DECIMAL, BigInteger, Column, DateTime, ForeignKey, Integer, String, Text

from app.models.base import Base


class Venda(Base):
    __tablename__ = "vendas_processadas"

    id = Column(Integer, primary_key=True, index=True)

    # Identificadores
    processamentoid = Column(String(50), index=True)
    cliente_id = Column(Integer, index=True)
    ec_id = Column(BigInteger, index=True)

    # Dados da Venda
    data_venda = Column("data_da_venda", DateTime, index=True)
    valor_venda = Column("Valor_da_venda", DECIMAL(18, 2))
    valor_liquido = Column("Valor_líquido_da_venda", DECIMAL(18, 2))

    # Dados do Cartão
    nsu = Column("NSU", String(100))
    autorizacao = Column("Código_de_autorização", String(100))
    bandeira = Column("Bandeira", String(100), index=True)
    forma_pagamento = Column("Forma_de_pagamento", String(100), index=True)

    # Meta
    status = Column("status_da_venda", String(50), default="Pendente", index=True)
    adquirente = Column("Adquirente", String(100))

    data_processamento = Column(DateTime, default=datetime.now)
    arquivo_origem = Column(Text)

class VendaFiltrada(Base):
    __tablename__ = "vendas_filtradas"

    id = Column(Integer, primary_key=True, index=True)

    # Identificadores
    processamentoid = Column(String(50), index=True)
    cliente_id = Column(Integer, index=True)
    ec_id = Column(BigInteger, index=True)

    # Dados da Venda
    data_venda = Column("data_da_venda", DateTime, index=True)
    valor_venda = Column("Valor_da_venda", DECIMAL(18, 2))
    valor_liquido = Column("Valor_líquido_da_venda", DECIMAL(18, 2))

    # Dados do Cartão
    nsu = Column("NSU", Text)
    autorizacao = Column("Código_de_autorização", Text)
    bandeira = Column("Bandeira", String(100))
    forma_pagamento = Column("Forma_de_pagamento", String(100))

    # Meta
    status = Column("status_da_venda", String(50), default="Pendente")
    adquirente = Column("Adquirente", String(100))

    data_processamento = Column(DateTime, default=datetime.now)
    arquivo_origem = Column(Text)
