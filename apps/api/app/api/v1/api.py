"""
API v1 Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    clientes,
    gestao,
    termos,
    taxas,
    depara,
    processamentos,
    correcao,
    importacao,
    analista,
    calculos,
    relatorios,
    usuarios,
    contextos,
    contextos,
    login,
    abusividade,
    ai
)

api_router = APIRouter()

api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

api_router.include_router(clientes.router, prefix="/clientes", tags=["clientes"])

api_router.include_router(gestao.router, prefix="/gestao", tags=["gestao"])

api_router.include_router(termos.router, prefix="/termos", tags=["termos"])

api_router.include_router(taxas.router, prefix="/taxas", tags=["taxas"])

api_router.include_router(depara.router, prefix="/depara", tags=["depara"])

api_router.include_router(processamentos.router, prefix="/processamentos", tags=["processamentos"])

api_router.include_router(correcao.router, prefix="/correcao", tags=["correcao"])

api_router.include_router(importacao.router, prefix="/importar", tags=["importacao"])

api_router.include_router(analista.router, prefix="/analista", tags=["analista"])

api_router.include_router(calculos.router, prefix="/calculos", tags=["calculos"])

api_router.include_router(relatorios.router, prefix="/relatorios", tags=["relatorios"])

api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])

api_router.include_router(contextos.router, prefix="/contextos", tags=["contextos"])

api_router.include_router(abusividade.router, prefix="/abusividade", tags=["abusividade"])

api_router.include_router(login.router, tags=["login"])

