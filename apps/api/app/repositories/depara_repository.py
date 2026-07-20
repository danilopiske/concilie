from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.legacy_depara import DeParaColunasLegacy
from app.schemas.depara import DeParaCreate, DeParaResponse, DeParaUpdate


class DeParaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(
        self,
        cliente_id: Optional[int] = None,
        contexto: Optional[str] = None,
        tipo_origem: Optional[str] = None,
        ativo: Optional[int] = 1,
        search: Optional[str] = None
    ) -> List[DeParaResponse]:
        query = self.db.query(DeParaColunasLegacy)

        if ativo is not None:
            query = query.filter(DeParaColunasLegacy.ativo == ativo)

        if contexto:
            query = query.filter(DeParaColunasLegacy.contexto == contexto)

        if tipo_origem:
            query = query.filter(DeParaColunasLegacy.tipo_origem == tipo_origem)

        if search:
            search_filt = f"%{search}%"
            query = query.filter(
                (DeParaColunasLegacy.origem_nome.ilike(search_filt)) |
                (DeParaColunasLegacy.destino_nome.ilike(search_filt))
            )

        return query.order_by(DeParaColunasLegacy.contexto, DeParaColunasLegacy.destino_nome).all()

    def criar(self, depara: DeParaCreate) -> DeParaResponse:
        db_obj = DeParaColunasLegacy(
            origem_nome=depara.origem_nome,
            destino_nome=depara.destino_nome,
            contexto=depara.contexto,
            tipo_origem=depara.tipo_origem,
            tipo_preenchimento=depara.tipo_preenchimento,
            valor_padrao=depara.valor_padrao,
            ativo=depara.ativo,
            criado_por=depara.criado_por or 'system'
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def atualizar(self, id: int, depara_update: DeParaUpdate) -> Optional[DeParaResponse]:
        db_obj = self.db.query(DeParaColunasLegacy).filter(DeParaColunasLegacy.id == id).first()
        if not db_obj:
            return None

        update_data = depara_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def deletar(self, id: int) -> bool:
        db_obj = self.db.query(DeParaColunasLegacy).filter(DeParaColunasLegacy.id == id).first()
        if not db_obj:
            return False

        # Soft delete
        db_obj.ativo = 0
        self.db.add(db_obj)
        self.db.commit()
        return True
