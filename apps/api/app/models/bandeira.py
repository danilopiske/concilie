"""
Bandeira Models
"""

from sqlalchemy import Boolean, Column, Integer, String

from app.models.base import Base


class BandeiraDisponivel(Base):
    __tablename__ = "bandeiras_disponiveis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    padrao = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<BandeiraDisponivel(id={self.id}, nome={self.nome})>"


class BandeiraCliente(Base):
    __tablename__ = "bandeiras_cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ec = Column(String(20), nullable=False, index=True)
    bandeira = Column(String(50), nullable=False)
    ativo = Column(Boolean, nullable=False, default=False)
    contexto = Column(String(100), nullable=False, default="padrao")

    def __repr__(self):
        return f"<BandeiraCliente(ec={self.ec}, bandeira={self.bandeira})>"
