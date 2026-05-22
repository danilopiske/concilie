"""
Termo Filtravel Repository
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.termo import TermoFiltravel


class TermoFiltravelRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_por_ec(
        self, ec: str, contexto: str = "padrao", tipo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List termos for EC"""
        query = self.db.query(TermoFiltravel).filter(
            TermoFiltravel.ec == ec, TermoFiltravel.contexto == contexto
        )

        if tipo:
            query = query.filter(TermoFiltravel.tipo == tipo)

        termos = query.order_by(TermoFiltravel.termo).all()
        return [
            {
                "id": t.id,
                "ec": t.ec,
                "termo": t.termo,
                "tipo": t.tipo,
                "contexto": t.contexto,
            }
            for t in termos
        ]

    def adicionar(
        self, ec: str, termo: str, tipo: str, contexto: str = "padrao"
    ) -> TermoFiltravel:
        """Add termo"""
        novo_termo = TermoFiltravel(ec=ec, termo=termo, tipo=tipo, contexto=contexto)
        self.db.add(novo_termo)
        self.db.commit()
        self.db.refresh(novo_termo)
        return novo_termo

    def atualizar(self, termo_id: int, dados: dict) -> Optional[TermoFiltravel]:
        """Update termo"""
        termo = self.db.query(TermoFiltravel).filter(TermoFiltravel.id == termo_id).first()
        if not termo:
            return None
        if "termo" in dados and dados["termo"] is not None:
            termo.termo = dados["termo"].strip().upper()
        if "tipo" in dados and dados["tipo"] is not None:
            termo.tipo = dados["tipo"]
        self.db.commit()
        self.db.refresh(termo)
        return termo

    def excluir(self, termo_id: int) -> bool:
        """Delete termo"""
        termo = (
            self.db.query(TermoFiltravel).filter(TermoFiltravel.id == termo_id).first()
        )

        if termo:
            self.db.delete(termo)
            self.db.commit()
            return True
        return False
