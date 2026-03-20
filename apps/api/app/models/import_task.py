import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class ImportTask(Base):
    __tablename__ = "import_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id = Column(Integer, ForeignKey("clientes.cliente_id"), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, PROCESSING, SUCCESS, FAILED
    progress = Column(Integer, default=0)
    message = Column(String(255))
    tipo_arquivo = Column(String(10)) # 'V' or 'R'
    contexto = Column(String(50))
    usuario = Column(String(50))
    metadata_json = Column(JSON) # Store any extra info (e.g. filename)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
