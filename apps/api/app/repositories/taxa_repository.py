"""
Taxa Repository
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.taxa import Taxa


class TaxaRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_por_ec(self, ec: str, contexto: str = "padrao") -> List[Dict[str, Any]]:
        """List taxas for EC"""
        taxas = (
            self.db.query(Taxa)
            .filter(Taxa.ec == ec, Taxa.contexto == contexto)
            .order_by(Taxa.bandeira, Taxa.forma_pagamento, Taxa.parcelas_ini)
            .all()
        )

        return [
            {
                "id": t.id,
                "ec": t.ec,
                "bandeira": t.bandeira,
                "forma_pagamento": t.forma_pagamento,
                "parcelado": t.parcelado,
                "parcelas_ini": t.parcelas_ini,
                "parcelas_fim": t.parcelas_fim,
                "data_ini": t.data_ini,
                "data_fim": t.data_fim,
                "taxa": float(t.taxa),
                "contexto": t.contexto,
            }
            for t in taxas
        ]

    def adicionar(self, taxa_data: Dict[str, Any]) -> Taxa:
        """Add taxa"""
        nova_taxa = Taxa(**taxa_data)
        self.db.add(nova_taxa)
        self.db.commit()
        self.db.refresh(nova_taxa)
        return nova_taxa

    def excluir(self, taxa_id: int) -> bool:
        """Delete taxa"""
        taxa = self.db.query(Taxa).filter(Taxa.id == taxa_id).first()

        if taxa:
            self.db.delete(taxa)
            self.db.commit()
            return True
        return False

    def copiar_taxas(
        self,
        ec_origem: str,
        ecs_destino: List[str],
        contexto: str = "padrao",
        sobrescrever: bool = False,
    ) -> Dict[str, Any]:
        """Copy taxas from one EC to others"""
        # Get source taxas
        taxas_origem = self.list_por_ec(ec_origem, contexto)

        if not taxas_origem:
            return {
                "sucesso": False,
                "mensagem": "EC origem não possui taxas",
                "copiadas": 0,
                "removidas": 0,
            }

        copiadas = 0
        removidas = 0

        for ec_dest in ecs_destino:
            if sobrescrever:
                # Remove existing taxas
                taxas_removidas = (
                    self.db.query(Taxa)
                    .filter(Taxa.ec == ec_dest, Taxa.contexto == contexto)
                    .delete()
                )
                removidas += taxas_removidas

            # Copy each taxa
            for taxa_orig in taxas_origem:
                nova_taxa = Taxa(
                    ec=ec_dest,
                    bandeira=taxa_orig["bandeira"],
                    forma_pagamento=taxa_orig["forma_pagamento"],
                    parcelado=taxa_orig["parcelado"],
                    parcelas_ini=taxa_orig["parcelas_ini"],
                    parcelas_fim=taxa_orig["parcelas_fim"],
                    data_ini=taxa_orig["data_ini"],
                    data_fim=taxa_orig["data_fim"],
                    taxa=taxa_orig["taxa"],
                    contexto=contexto,
                )
                self.db.add(nova_taxa)
                copiadas += 1

        self.db.commit()

        return {
            "sucesso": True,
            "mensagem": f"Taxas copiadas de {ec_origem} para {len(ecs_destino)} ECs",
            "copiadas": copiadas,
            "removidas": removidas,
        }
