import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class CalculoTask(Base):
    __tablename__ = "calculo_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    processamento_id = Column(String(100), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, PROCESSING, SUCCESS, FAILED
    progress = Column(Integer, default=0)
    message = Column(String(1000))
    tipo_taxa = Column(String(20))
    usuario = Column(String(50))
    metadata_json = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
