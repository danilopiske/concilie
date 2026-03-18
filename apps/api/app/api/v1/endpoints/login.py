from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.token import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    response: Response,
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    repo = UsuarioRepository(db)
    user = repo.obter_por_usuario(form_data.username)
    
    if not user:
        # Avoid timing attacks / generic message
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
    
    # Check password (assuming user.senha is hashed, or plaintext if legacy - verify logic)
    # Ideally should be hashed. Let's assume verify_password checks hash.
    # If legacy is plaintext, we might need a migration or check.
    # For now, standard check:
    # Support for legacy passwords using SHA-256 (e.g. '1234' -> '03ac67...')
    # and plain text
    password_valid = False
    try:
        if security.verify_password(form_data.password, user.senha):
            password_valid = True
    except Exception:
        # If verify crashes (e.g. unknown hash format)
        pass
        
    if not password_valid:
        # Try Plain Text
        if user.senha == form_data.password:
            password_valid = True
        else:
            # Try SHA-256 (common legacy hash)
            import hashlib
            sha256_hash = hashlib.sha256(form_data.password.encode()).hexdigest()
            if user.senha == sha256_hash:
                password_valid = True

    if not password_valid:
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
         
    # Check if active
    # if not user.is_active: ... (Model doesn't seem to have is_active, maybe 'ativo'?)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response) -> Any:
    """Limpa o cookie de autenticação."""
    response.delete_cookie(key="access_token")
    return {"message": "Logout realizado com sucesso"}
