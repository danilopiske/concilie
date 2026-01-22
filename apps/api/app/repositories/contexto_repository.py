"""
Contexto Repository
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.contexto import Contexto


class ContextoRepository(BaseRepository[Contexto]):
    def __init__(self, db: Session):
        super().__init__(Contexto, db)
    
    def list_all(self, incluir_inativos: bool = False) -> List[Dict[str, Any]]:
        """List all contextos"""
        query = self.db.query(Contexto)
        if not incluir_inativos:
            query = query.filter(Contexto.ativo == True)
        
        contextos = query.order_by(Contexto.nome).all()
        return [
            {
                "id": c.id,
                "nome": c.nome,
                "descricao": c.descricao,
                "ativo": c.ativo
            }
            for c in contextos
        ]
    
    def get_by_nome(self, nome: str) -> Optional[Contexto]:
        """Get contexto by name"""
        return self.db.query(Contexto).filter(Contexto.nome == nome).first()
