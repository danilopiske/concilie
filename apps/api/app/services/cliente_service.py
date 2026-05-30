"""
Cliente Service
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.repositories.cliente_repository import ClienteRepository


class ClienteService:
    def __init__(self, db: Session):
        self.repository = ClienteRepository(db)

    def listar_clientes(self) -> List[Dict[str, Any]]:
        """List all clientes"""
        return self.repository.list_all()

    def obter_cliente(self, cliente_id: int) -> Dict[str, Any]:
        """Get cliente details"""
        cliente = self.repository.get_detalhes(cliente_id)
        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")
        return cliente

    def criar_cliente(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Create new cliente"""
        cliente_id = self.repository.salvar_cliente(dados, is_update=False)
        return self.obter_cliente(cliente_id)

    def atualizar_cliente(
        self, cliente_id: int, dados: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update cliente"""
        dados["cliente_id"] = cliente_id
        self.repository.salvar_cliente(dados, is_update=True)
        return self.obter_cliente(cliente_id)

    def deletar_cliente(self, cliente_id: int):
        """Delete cliente"""
        self.repository.deletar_cliente(cliente_id)

    def listar_ecs(self, cliente_id: int) -> List[str]:
        """List ECs for cliente"""
        return self.repository.get_ecs_por_cliente(cliente_id)
