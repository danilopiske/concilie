from sqlalchemy import Column, Integer, String, Boolean
from app.models.base import Base

class DeParaColunasLegacy(Base):
    __tablename__ = "depara_colunas"

    id = Column(Integer, primary_key=True, index=True)
    origem_nome = Column(String(255))
    destino_nome = Column(String(255))
    contexto = Column(String(100))
    tipo_origem = Column(String(50)) # V, R, L
    ativo = Column(Integer, default=1)
    tipo_preenchimento = Column(String(50))
    valor_padrao = Column(String(255))
    criado_por = Column(String(100))
