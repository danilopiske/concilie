
from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario
# from app.core.security import ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def _resolve_token(request: Request, bearer: Optional[str]) -> str:
    """Aceita token via Bearer header ou cookie HttpOnly."""
    if bearer:
        return bearer
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    bearer: Optional[str] = Depends(oauth2_scheme),
) -> Usuario:
    """
    Get current user from token
    """
    # This is a placeholder implementation if needed by other modules
    # You might need to import TokenPayload or similar
    token = _resolve_token(request, bearer)
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = payload.get("sub")
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    from app.repositories.usuario_repository import UsuarioRepository
    repo = UsuarioRepository(db)
    
    try:
        user = repo.obter_por_id(int(token_data))
    except (ValueError, TypeError):
        user = None

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
