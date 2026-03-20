"""
Application Configuration
"""

import json
import logging
import os
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)

# Calculate absolute path for SQLite here (outside class)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, "../../../.."))
SQLITE_DB_PATH_CALCULATED = os.path.join(_root_dir, "data", "concilie.db")



class Settings(BaseSettings):
    PROJECT_NAME: str = "Financial  API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    # Set this env var to override the full CORS list in staging/prod
    # Example: ALLOWED_ORIGINS_STR='["https://app.concilie.com.br"]'
    ALLOWED_ORIGINS_STR: Optional[str] = None

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Dynamic CORS origins based on environment.
        If ALLOWED_ORIGINS_STR is set, it takes full precedence (staging/prod).
        Otherwise falls back to ALLOWED_ORIGINS + optional FRONTEND_URL.
        """
        if self.ALLOWED_ORIGINS_STR:
            try:
                return json.loads(self.ALLOWED_ORIGINS_STR)
            except json.JSONDecodeError as e:
                _logger.warning(
                    "ALLOWED_ORIGINS_STR inválido (%s), usando defaults. Valor: %r",
                    e, self.ALLOWED_ORIGINS_STR
                )

        origins = self.ALLOWED_ORIGINS.copy()

        # Add Railway/Production URL from env
        if os.getenv("FRONTEND_URL"):
            origins.append(os.getenv("FRONTEND_URL"))

        # Add Render/Heroku URLs if needed
        if os.getenv("RAILWAY_PUBLIC_DOMAIN"):
            origins.append(f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}")

        return origins

    # Database
    DATABASE_TYPE: str = "mysql"  # mysql ou sqlite
    MYSQL_SERVER: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "bd_conciliacao"

    # SQLite Path calculated outside class to avoid Pydantic annotation errors
    SQLITE_DB_PATH: str = SQLITE_DB_PATH_CALCULATED

    # Debug
    DEBUG_SQL: bool = False  # True para ver queries SQL no console
    DEBUG: bool = True  # Debug mode geral
    ENV: str = "development"  # development, production

    # Auth
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-only-for-local")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o"


    # CORS (alias para ALLOWED_ORIGINS)
    # CORS (alias for property in Pydantic v2 might need computed_field,
    # but for v1 or simple usage we use the property above directly in main.py)
    # Removing static CORS_ORIGINS to rely on the dynamic property logic or
    # we can use a validator if strictly needed by Pydantic.
    # For now, we will access settings.CORS_ORIGINS as a property where needed.

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
