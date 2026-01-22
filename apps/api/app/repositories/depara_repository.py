from sqlalchemy.orm import Session
from app.models.legacy_depara import DeParaColunasLegacy
from app.schemas.depara import DeParaCreate, DeParaUpdate, DeParaResponse
from typing import List, Optional

class DeParaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, cliente_id: Optional[int] = None) -> List[DeParaResponse]:
        # Ignores cliente_id for now as the legacy model doesn't explicitly link to cliente_id per row
        # It links via context/logic usually, but let's just return all active rules
        return self.db.query(DeParaColunasLegacy).filter(DeParaColunasLegacy.ativo == 1).all()

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
