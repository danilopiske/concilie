from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.models.base import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions_ia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
