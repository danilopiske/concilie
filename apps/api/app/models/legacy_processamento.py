from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base

class LegacyProcessamento(Base):
    __tablename__ = "controle_processamentos"

    id_processamento = Column(String(50), primary_key=True)
    cliente_id = Column(String(50))
    ec_id = Column(String(50))
    adquirente = Column(String(100))
    descricao = Column(String(255))
    data_processamento = Column(DateTime)
