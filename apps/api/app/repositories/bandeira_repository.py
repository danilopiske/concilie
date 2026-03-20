"""
Bandeira Repository
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.bandeira import BandeiraCliente, BandeiraDisponivel
from app.repositories.base import BaseRepository


class BandeiraDisponivelRepository(BaseRepository[BandeiraDisponivel]):
    def __init__(self, db: Session):
        super().__init__(BandeiraDisponivel, db)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all available bandeiras"""
        bandeiras = (
            self.db.query(BandeiraDisponivel).order_by(BandeiraDisponivel.nome).all()
        )
        return [{"id": b.id, "nome": b.nome, "padrao": b.padrao} for b in bandeiras]

    def get_by_nome(self, nome: str) -> Optional[BandeiraDisponivel]:
        """Get bandeira by name"""
        return (
            self.db.query(BandeiraDisponivel)
            .filter(BandeiraDisponivel.nome == nome.strip().upper())
            .first()
        )


class BandeiraClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_por_ec(self, ec: str, contexto: str = "padrao") -> Dict[str, int]:
        """Get bandeiras for EC"""
        bandeiras = (
            self.db.query(BandeiraCliente)
            .filter(BandeiraCliente.ec == ec, BandeiraCliente.contexto == contexto)
            .all()
        )
        return {b.bandeira: b.ativo for b in bandeiras}

    def salvar_para_ec(
        self, ec: str, bandeiras: Dict[str, int], contexto: str = "padrao"
    ):
        """Save bandeiras for EC (upsert)"""
        for bandeira, ativo in bandeiras.items():
            existing = (
                self.db.query(BandeiraCliente)
                .filter(
                    BandeiraCliente.ec == ec,
                    BandeiraCliente.bandeira == bandeira,
                    BandeiraCliente.contexto == contexto,
                )
                .first()
            )

            if existing:
                existing.ativo = ativo
            else:
                new_bandeira = BandeiraCliente(
                    ec=ec, bandeira=bandeira, ativo=ativo, contexto=contexto
                )
                self.db.add(new_bandeira)

        self.db.commit()
