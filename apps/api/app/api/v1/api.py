"""
API v1 Router
"""

from fastapi import APIRouter, Depends

from app.api import deps
from app.api.v1.endpoints import (
    abusividade,
    ai,
    analista,
    calculos,
    clientes,
    clientes_resumo,
    contestacoes,
    contextos,
    correcao,
    dashboard,
    depara,
    extratos_cliente,
    gestao,
    importacao,
    importacao_async,
    login,
    notificacoes,
    processamentos,
    relatorio_tags,
    relatorios,
    tarefas,
    taxas,
    taxas_contratadas,
    termos,
    usuarios,
)

api_router = APIRouter()

# ── Routers públicos (sem autenticação) ───────────────────────────────────────
api_router.include_router(login.router, tags=["login"])

# ── Routers protegidos (requerem JWT válido) ──────────────────────────────────
_auth = [Depends(deps.get_current_user)]

api_router.include_router(ai.router, prefix="/ai", tags=["ai"], dependencies=_auth)
api_router.include_router(clientes.router, prefix="/clientes", tags=["clientes"], dependencies=_auth)
api_router.include_router(extratos_cliente.router, prefix="/clientes", tags=["extratos-cliente"], dependencies=_auth)
api_router.include_router(taxas_contratadas.router, prefix="/clientes", tags=["taxas-contratadas"], dependencies=_auth)
api_router.include_router(clientes_resumo.router, prefix="/clientes", tags=["clientes-resumo"], dependencies=_auth)
api_router.include_router(gestao.router, prefix="/gestao", tags=["gestao"], dependencies=_auth)
api_router.include_router(termos.router, prefix="/termos", tags=["termos"], dependencies=_auth)
api_router.include_router(taxas.router, prefix="/taxas", tags=["taxas"], dependencies=_auth)
api_router.include_router(depara.router, prefix="/depara", tags=["depara"], dependencies=_auth)
api_router.include_router(processamentos.router, prefix="/processamentos", tags=["processamentos"], dependencies=_auth)
api_router.include_router(correcao.router, prefix="/correcao", tags=["correcao"], dependencies=_auth)
api_router.include_router(importacao.router, prefix="/importar", tags=["importacao"], dependencies=_auth)
api_router.include_router(importacao_async.router, prefix="/importacao-async", tags=["importacao-async"], dependencies=_auth)
api_router.include_router(analista.router, prefix="/analista", tags=["analista"], dependencies=_auth)
api_router.include_router(calculos.router, prefix="/calculos", tags=["calculos"], dependencies=_auth)
api_router.include_router(relatorios.router, prefix="/relatorios", tags=["relatorios"], dependencies=_auth)
api_router.include_router(relatorio_tags.router, prefix="/relatorio-tags", tags=["relatorio-tags"], dependencies=_auth)
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"], dependencies=_auth)
api_router.include_router(contextos.router, prefix="/contextos", tags=["contextos"], dependencies=_auth)
api_router.include_router(abusividade.router, prefix="/abusividade", tags=["abusividade"], dependencies=_auth)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"], dependencies=_auth)
api_router.include_router(contestacoes.router, prefix="/contestacoes", tags=["contestacoes"], dependencies=_auth)
api_router.include_router(notificacoes.router, prefix="/notificacoes", tags=["notificacoes"], dependencies=_auth)
api_router.include_router(tarefas.router, prefix="/tarefas", tags=["tarefas"], dependencies=_auth)
