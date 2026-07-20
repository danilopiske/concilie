from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String

from app.models.base import Base


class TaxaContratada(Base):
    __tablename__ = "taxas_contratadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    bandeira = Column(String(100), nullable=False)
    modalidade = Column(String(100), nullable=False)  # ex: "Crédito à Vista", "Débito"
    taxa_contratada = Column(Float, nullable=False)  # percentual (ex: 2.50)
    vigencia_inicio = Column(Date, nullable=False)
    vigencia_fim = Column(Date, nullable=True)  # null = vigente atualmente
    observacao = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<TaxaContratada(cliente={self.cliente_id}, "
            f"bandeira={self.bandeira}, modalidade={self.modalidade}, "
            f"taxa={self.taxa_contratada}%)>"
        )
