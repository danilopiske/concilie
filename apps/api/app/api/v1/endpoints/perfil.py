"""
Endpoints para gerenciamento do perfil do usuário logado.
"""
import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario

router = APIRouter()


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str


def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


@router.get("/me")
def meu_perfil(current_user: Usuario = Depends(get_current_user)):
    """Retorna dados do usuário logado."""
    return {
        "id": current_user.id,
        "usuario": current_user.usuario,
        "nome": current_user.nome,
        "empresa": current_user.empresa,
    }


@router.post("/me/alterar-senha")
def alterar_senha(
    req: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Altera a senha do usuário logado."""
    senha_atual_hash = _hash_senha(req.senha_atual)

    # Suporte a senha em texto plano (legado) ou SHA-256
    senha_valida = (
        current_user.senha == senha_atual_hash
        or current_user.senha == req.senha_atual
    )

    if not senha_valida:
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")

    if len(req.nova_senha) < 4:
        raise HTTPException(
            status_code=400, detail="A nova senha deve ter pelo menos 4 caracteres."
        )

    current_user.senha = _hash_senha(req.nova_senha)
    db.add(current_user)
    db.commit()

    return {"message": "Senha alterada com sucesso."}
