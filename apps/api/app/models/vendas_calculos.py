from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, BigInteger
from app.models.base import Base
from datetime import datetime

class VendasCalculos(Base):
    __tablename__ = "vendas_calculos"

    id = Column(Integer, primary_key=True, index=True)
    
    # FK e Identificadores do Processamento
    id_venda = Column(Integer, index=True) # Referência lógica à vendas_processadas.id
    calc_id = Column(String(50), index=True) # ID do processamento
    calc_tipo = Column(String(50), index=True) # log_mensal, log_anual, etc.
    calc_usuario = Column(String(100))
    calc_data = Column(DateTime, default=datetime.now)

    # Identificadores da Venda (Redundantes para facilitar query sem JOIN)
    bandeira = Column(String(100))
    forma_pagamento = Column(String(100))
    data_venda = Column(DateTime)
    ec_id = Column(BigInteger)
    adquirente = Column(String(100))
    arquivo_origem = Column(String(255))
    nsu = Column(String(100))
    cod_autorizacao = Column(String(100))

    # Valores Originais (da Venda)
    vl_venda = Column(DECIMAL(18, 2))
    tx_venda = Column(DECIMAL(18, 4))
    desc_venda = Column(DECIMAL(18, 2))
    vl_liq_venda = Column(DECIMAL(18, 2))
    
    tx_rr_venda = Column(DECIMAL(18, 4))
    vl_rr_venda = Column(DECIMAL(18, 2))

    # Valores Calculados (pelo Sistema)
    tx_calc = Column(DECIMAL(18, 4), nullable=True)
    desc_calc = Column(DECIMAL(18, 2), nullable=True)
    vl_liq_calc = Column(DECIMAL(18, 2), nullable=True)
    
    tx_rr_calc = Column(DECIMAL(18, 4), nullable=True)
    vl_rr_calc = Column(DECIMAL(18, 2), nullable=True)
    
    # Diferença / Perda
    perda = Column(DECIMAL(18, 2), nullable=True)
    perda_rr = Column(DECIMAL(18, 2), nullable=True)

