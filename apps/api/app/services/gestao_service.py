"""
Gestao Service - Consolidated service for all management operations
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.repositories.bandeira_repository import (
    BandeiraClienteRepository,
    BandeiraDisponivelRepository,
)
from app.repositories.contexto_repository import ContextoRepository
from app.repositories.taxa_repository import TaxaRepository
from app.repositories.termo_repository import TermoFiltravelRepository


class GestaoService:
    def __init__(self, db: Session):
        self.db = db
        self.contexto_repo = ContextoRepository(db)
        self.bandeira_disp_repo = BandeiraDisponivelRepository(db)
        self.bandeira_cliente_repo = BandeiraClienteRepository(db)
        self.termo_repo = TermoFiltravelRepository(db)
        self.taxa_repo = TaxaRepository(db)

    # Contextos
    def listar_contextos(self, incluir_inativos: bool = False) -> List[Dict[str, Any]]:
        return self.contexto_repo.list_all(incluir_inativos)

    def criar_contexto(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        contexto = self.contexto_repo.create(dados)
        return {
            "id": contexto.id,
            "nome": contexto.nome,
            "descricao": contexto.descricao,
            "ativo": contexto.ativo,
        }

    # Bandeiras Disponiveis
    def listar_bandeiras_disponiveis(self) -> List[Dict[str, Any]]:
        return self.bandeira_disp_repo.list_all()

    def criar_bandeira_disponivel(self, nome: str, padrao: bool = False):
        return self.bandeira_disp_repo.create(
            {"nome": nome.strip().upper(), "padrao": padrao}
        )

    def deletar_bandeira_disponivel(self, bandeira_id: int):
        return self.bandeira_disp_repo.delete(bandeira_id)

    # Bandeiras por EC
    def listar_bandeiras_ec(self, ec: str, contexto: str = "padrao") -> Dict[str, int]:
        return self.bandeira_cliente_repo.get_por_ec(ec, contexto)

    def salvar_bandeiras_ec(
        self, ec: str, bandeiras: Dict[str, int], contexto: str = "padrao"
    ):
        self.bandeira_cliente_repo.salvar_para_ec(ec, bandeiras, contexto)

    # Termos Filtraveis
    def listar_termos(
        self, ec: str, contexto: str = "padrao", tipo: str = None
    ) -> List[Dict[str, Any]]:
        return self.termo_repo.list_por_ec(ec, contexto, tipo)

    def adicionar_termo(self, ec: str, termo: str, tipo: str, contexto: str = "padrao"):
        return self.termo_repo.adicionar(ec, termo, tipo, contexto)

    def excluir_termo(self, termo_id: int):
        return self.termo_repo.excluir(termo_id)

    # Taxas
    def listar_taxas(self, ec: str, contexto: str = "padrao") -> List[Dict[str, Any]]:
        return self.taxa_repo.list_por_ec(ec, contexto)

    def adicionar_taxa(self, taxa_data: Dict[str, Any]):
        return self.taxa_repo.adicionar(taxa_data)

    def excluir_taxa(self, taxa_id: int):
        return self.taxa_repo.excluir(taxa_id)

    def copiar_taxas(
        self,
        ec_origem: str,
        ecs_destino: List[str],
        contexto: str = "padrao",
        sobrescrever: bool = False,
    ) -> Dict[str, Any]:
        return self.taxa_repo.copiar_taxas(
            ec_origem, ecs_destino, contexto, sobrescrever
        )
