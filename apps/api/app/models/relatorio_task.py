from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .base import Base
import uuid

class RelatorioTask(Base):
    __tablename__ = "relatorio_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    processamento_id = Column(String(100), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, PROCESSING, SUCCESS, FAILED
    progress = Column(Integer, default=0)
    message = Column(String(1000))
    tipo_relatorio = Column(String(50)) # mensal, retroativo, abusividade
    usuario = Column(String(50))
    result_path = Column(String(500))
    abusividade_path = Column(String(500))
    sintetico_path = Column(String(500))
    excel_path = Column(String(500))
    metadata_json = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
