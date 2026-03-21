import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from app.models.base import Base


class AbusividadeTask(Base):
    __tablename__ = "abusividade_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    processamento_id = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")  # pending | ready | error
    result_path = Column(String(500), nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
