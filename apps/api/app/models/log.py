from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base


class LogCorrecao(Base):
    __tablename__ = "log_correcoes_importacao"

    id = Column(Integer, primary_key=True, index=True)
    processamentoid = Column(String(50), index=True)
    tipo_correcao = Column(String(100))
    valor_antigo = Column(String(255))
    valor_novo = Column(String(255))
    linhas_afetadas = Column(Integer)
    usuario = Column(String(100))
    data_correcao = Column(DateTime)
