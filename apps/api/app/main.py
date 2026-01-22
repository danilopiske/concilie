"""
Financial Checker API
FastAPI Application Entry Point
"""

import sys
from pathlib import Path

# Adicionar diretório root ao path para importar módulos legados (conf, proc, etc)
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Conciliacao Financeira",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


# Inicializar banco de dados ao startar
@app.on_event("startup")
async def startup_event():
    """Criar tabelas se não existirem"""
    init_db()
    print("✅ Banco de dados inicializado")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 [{request.method}] {request.url.path}")
    response = await call_next(request)
    print(f"📤 [{response.status_code}] {request.url.path}")
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
async def debug_database_info():
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
