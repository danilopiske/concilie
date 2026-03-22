from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class UsuarioContexto(Base):
    __tablename__ = "usuario_contextos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    contexto_id = Column(Integer, ForeignKey("contextos.id", ondelete="CASCADE"), nullable=False)

    usuario = relationship("Usuario", back_populates="contextos_permitidos")
