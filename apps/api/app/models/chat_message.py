from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from app.models.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages_ia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions_ia.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    sql_gerado = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
