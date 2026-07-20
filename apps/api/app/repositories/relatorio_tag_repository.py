"""
Repository para RelatorioTag
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.relatorio_tag import RelatorioTag
from app.schemas.relatorio_tag import RelatorioTagCreate, RelatorioTagUpdate


class RelatorioTagRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, ativo: Optional[bool] = True) -> List[RelatorioTag]:
        query = self.db.query(RelatorioTag)
        if ativo is not None:
            query = query.filter(RelatorioTag.ativo == ativo)
        return query.order_by(RelatorioTag.nome).all()

    def get(self, tag_id: int) -> Optional[RelatorioTag]:
        return self.db.query(RelatorioTag).filter(RelatorioTag.id == tag_id).first()

    def get_by_nome(self, nome: str) -> Optional[RelatorioTag]:
        return self.db.query(RelatorioTag).filter(RelatorioTag.nome == nome).first()

    def create(self, data: RelatorioTagCreate) -> RelatorioTag:
        tag = RelatorioTag(**data.model_dump())
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag_id: int, data: RelatorioTagUpdate) -> Optional[RelatorioTag]:
        tag = self.get(tag_id)
        if not tag:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tag, field, value)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag_id: int) -> bool:
        tag = self.get(tag_id)
        if not tag:
            return False
        # Soft delete
        tag.ativo = False
        self.db.commit()
        return True
