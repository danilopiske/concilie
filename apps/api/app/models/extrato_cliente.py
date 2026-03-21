import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.models.base import Base


class ExtratoCliente(Base):
    __tablename__ = "extratos_cliente"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = Column(Integer, ForeignKey("clientes.cliente_id"), nullable=False, index=True)
    nome_arquivo = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(500))
    tipo = Column(String(50), default="Outro")  # Venda | Recebivel | Outro
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(30), default="aguardando")  # aguardando | importado | divergente
    processamento_id = Column(Integer, nullable=True)
