import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario

# from app.core.security import ALGORITHM

logger = logging.getLogger("app.api.deps")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token",
    auto_error=False,
)


def _resolve_token(request: Request, bearer: Optional[str]) -> str:
    """Aceita token via Bearer header ou cookie HttpOnly."""
    if bearer:
        logger.info("Token encontrado no Auth Header (Bearer)")
        return bearer
    cookie = request.cookies.get("access_token")
    if cookie:
        logger.info("Token encontrado no Cookie 'access_token'")
        return cookie

    logger.warning("Token não encontrado no header nem no cookie")
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
            logger.warning("Token sem 'sub'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
    except (JWTError, ValidationError) as e:
        logger.warning(f"Erro JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    from app.repositories.usuario_repository import UsuarioRepository
    repo = UsuarioRepository(db)

    try:
        user_id = int(token_data)
        user = repo.get(user_id)
        if not user:
            logger.warning(f"Usuário ID {user_id} não encontrado no banco")
    except (ValueError, TypeError):
        logger.warning(f"ID do token inválido: {token_data}")
        user = None

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_user_perfil(user: Usuario) -> str:
    """Retorna o perfil do usuário (default 'admin' para retrocompatibilidade)."""
    if user.permissao:
        return user.permissao.perfil
    return "admin"


def require_role(roles: List[str]):
    """
    Dependency factory que bloqueia acesso se o perfil do usuário
    não estiver na lista de roles permitidos.

    Uso: Depends(require_role(["admin", "operador"]))
    """
    def _check(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        perfil = get_user_perfil(current_user)
        if perfil not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfil '{perfil}' não tem permissão para esta operação.",
            )
        return current_user

    return _check
