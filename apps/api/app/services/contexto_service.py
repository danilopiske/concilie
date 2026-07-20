"""
Service de Contextos - Lógica de negócio
"""

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.contexto import Contexto
from app.repositories.contexto_repository import ContextoRepository
from app.schemas.contexto import ContextoCreate, ContextoUpdate


class ContextoService:
    def __init__(self, db: Session):
        self.repository = ContextoRepository(db)
        self.db = db

    def listar_contextos(
        self, skip: int = 0, limit: int = 100, incluir_inativos: bool = False
    ) -> List[Contexto]:
        """Listar todos os contextos"""
        query = self.db.query(Contexto)
        if not incluir_inativos:
            query = query.filter(Contexto.ativo == True)

        return query.order_by(Contexto.nome).offset(skip).limit(limit).all()

    def obter_contexto(self, contexto_id: int) -> Optional[Contexto]:
        """Obter contexto por ID"""
        contexto = self.db.query(Contexto).filter(Contexto.id == contexto_id).first()
        if not contexto:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")
        return contexto

    def criar_contexto(self, dados: ContextoCreate) -> Contexto:
        """Criar novo contexto"""
        # Verificar nome duplicado
        existe = self.db.query(Contexto).filter(Contexto.nome == dados.nome).first()
        if existe:
            raise HTTPException(
                status_code=400,
                detail=f"Já existe um contexto com o nome '{dados.nome}'",
            )

        # Criar contexto
        contexto = Contexto(**dados.model_dump())
        self.db.add(contexto)
        self.db.commit()
        self.db.refresh(contexto)
        return contexto

    def atualizar_contexto(self, contexto_id: int, dados: ContextoUpdate) -> Contexto:
        """Atualizar contexto existente"""
        # Verificar se existe
        contexto = self.db.query(Contexto).filter(Contexto.id == contexto_id).first()
        if not contexto:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")

        # Verificar nome duplicado (se nome foi alterado)
        if dados.nome and dados.nome != contexto.nome:
            existe = (
                self.db.query(Contexto)
                .filter(Contexto.nome == dados.nome, Contexto.id != contexto_id)
                .first()
            )
            if existe:
                raise HTTPException(
                    status_code=400,
                    detail=f"Já existe um contexto com o nome '{dados.nome}'",
                )

        # Atualizar apenas campos fornecidos
        update_dict = dados.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(contexto, field, value)

        self.db.commit()
        self.db.refresh(contexto)
        return contexto

    def deletar_contexto(self, contexto_id: int) -> bool:
        """Deletar contexto"""
        # Verificar se existe
        contexto = self.db.query(Contexto).filter(Contexto.id == contexto_id).first()
        if not contexto:
            raise HTTPException(status_code=404, detail="Contexto não encontrado")

        # TODO: Verificar se pode deletar (não está em uso)
        # Isso seria feito verificando se há termos_filtraveis usando este contexto

        self.db.delete(contexto)
        self.db.commit()
        return True
