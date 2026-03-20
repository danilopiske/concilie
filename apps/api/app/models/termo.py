"""
Termo Filtravel Model
"""

from sqlalchemy import CHAR, Column, Integer, String

from app.models.base import Base


class TermoFiltravel(Base):
    __tablename__ = "termos_filtraveis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ec = Column(String(20), nullable=False, index=True)
    termo = Column(String(100), nullable=False)
    contexto = Column(String(100), nullable=False, default="padrao")
    tipo = Column(CHAR(1), nullable=False)  # 'I'=incluir, 'E'=excluir

    def __repr__(self):
        return f"<TermoFiltravel(ec={self.ec}, termo={self.termo}, tipo={self.tipo})>"
