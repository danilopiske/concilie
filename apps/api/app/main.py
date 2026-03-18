"""
Financial  API
FastAPI Application Entry Point
"""

import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# sys.path needed for remaining legacy imports:
#   - apps/api/app/api/v1/endpoints/depara.py        → proc.proc_importacao (lazy import)
#   - apps/api/app/api/v1/endpoints/calculos.py      → modules.reconciliation_core
#   - apps/api/app/api/v1/endpoints/relatorios.py    → modules.reports
#   - apps/api/app/services/calculo_service.py       → modules.reconciliation_core
#   - apps/api/app/services/relatorio_service.py     → modules.reports
#   - apps/api/app/services/import_service.py        → proc.proc_importacao
# TODO: remove after completing Sprint 2 / Sprint 3 migration
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db
from fastapi.responses import JSONResponse, ORJSONResponse
from app.api.deps import get_current_user

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Conciliacao Financeira",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    default_response_class=ORJSONResponse,
)


# Inicializar banco de dados ao startar
@app.on_event("startup")
async def startup_event():
    """Criar tabelas se não existirem"""
    init_db()
    logger.info("Banco de dados inicializado")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("GLOBAL EXCEPTION: %s", exc, exc_info=True)
    detail = str(exc) if settings.DEBUG else "Internal Server Error"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug("[IN]  [%s] %s", request.method, request.url.path)
    response = await call_next(request)
    logger.debug("[OUT] [%s] %s", response.status_code, request.url.path)
    return response


@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "api": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """Health check com informações do banco de dados"""
    from app.core.database import get_db_info

    db_info = get_db_info()

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": {
            "type": db_info["type"],
            "dialect": db_info["dialect"],
            "driver": db_info["driver"],
            "connection": db_info["url"],
        },
    }


@app.get("/debug/db-info")
async def debug_database_info(_: str = Depends(get_current_user)):
    """Endpoint de debug - informações detalhadas do banco"""
    from app.core.database import get_db_info, engine

    db_info = get_db_info()

    return {
        "database_type": db_info["type"],
        "is_mysql": db_info["is_mysql"],
        "is_sqlite": db_info["is_sqlite"],
        "dialect": db_info["dialect"],
        "driver": db_info["driver"],
        "connection_url": db_info["url"],
        "pool_size": engine.pool.size(),
        "debug_sql_enabled": (
            settings.DEBUG_SQL if hasattr(settings, "DEBUG_SQL") else False
        ),
    }
