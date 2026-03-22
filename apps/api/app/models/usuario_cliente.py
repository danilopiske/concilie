from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.models.base import Base


class UsuarioCliente(Base):
    __tablename__ = "usuario_clientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.cliente_id", ondelete="CASCADE"), nullable=False, index=True)

    usuario = relationship("Usuario", back_populates="clientes_permitidos")
