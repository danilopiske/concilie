import hashlib
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.base import BaseRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(Usuario, db)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 hex digest (64 chars)"""
        return hashlib.sha256(password.encode()).hexdigest()

    def listar(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        return self.db.query(Usuario).offset(skip).limit(limit).all()

    def obter_por_usuario(self, usuario: str) -> Optional[Usuario]:
        return self.db.query(Usuario).filter(Usuario.usuario == usuario).first()

    def criar(self, dados: UsuarioCreate) -> Usuario:
        db_obj = Usuario(
            usuario=dados.usuario,
            senha=self._hash_password(dados.senha),
            nome=dados.nome,
            empresa=dados.empresa
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def atualizar(self, usuario_id: int, dados: UsuarioUpdate) -> Optional[Usuario]:
        db_obj = self.get(usuario_id)
        if not db_obj:
            return None

        update_data = dados.model_dump(exclude_unset=True)
        if "senha" in update_data:
            update_data["senha"] = self._hash_password(update_data["senha"])

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def deletar(self, usuario_id: int) -> bool:
        db_obj = self.get(usuario_id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True
