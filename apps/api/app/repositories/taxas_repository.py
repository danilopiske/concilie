"""
Repository de Taxas
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from conf.funcoesbd import (
    taxa_adicionar,
    taxa_excluir,
    taxas_por_ec,
    taxa_atualizar,
    taxas_copiar,
)
from app.schemas.taxa import TaxaCreate, TaxaUpdate, TaxaCopiarRequest


class TaxasRepository:
    """Repository para operações de taxas"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()

    def listar_por_ec(self, ec: str, contexto: str = "padrao") -> List[Dict[str, Any]]:
        """
        Listar todas as taxas de um EC
        """
        return taxas_por_ec(self.engine, ec, contexto)

    def criar(self, taxa: TaxaCreate) -> bool:
        """
        Criar nova taxa
        """
        taxa_dict = taxa.model_dump()
        # Converter Decimal para float para compatibilidade
        taxa_dict["taxa"] = float(taxa_dict["taxa"])
        return taxa_adicionar(self.engine, taxa_dict, taxa.contexto)

    def atualizar(self, taxa_id: int, taxa: TaxaUpdate) -> bool:
        """
        Atualizar taxa existente
        """
        taxa_dict = taxa.model_dump(exclude_unset=True)
        if "taxa" in taxa_dict and taxa_dict["taxa"] is not None:
            taxa_dict["taxa"] = float(taxa_dict["taxa"])
        return taxa_atualizar(self.engine, taxa_id, taxa_dict)

    def deletar(self, taxa_id: int) -> bool:
        """
        Deletar taxa por ID
        """
        return taxa_excluir(self.engine, taxa_id)

    def copiar(self, request: TaxaCopiarRequest) -> Dict[str, Any]:
        """
        Copiar taxas de um EC para outros ECs
        """
        return taxas_copiar(
            self.engine,
            request.ec_origem,
            request.ecs_destino,
            request.contexto,
            request.sobrescrever,
        )
