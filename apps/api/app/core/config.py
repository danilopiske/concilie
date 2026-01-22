"""
Application Configuration
"""

from typing import List
from pydantic_settings import BaseSettings
import os

# Calculate absolute path for SQLite here (outside class)
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, "../../../.."))
SQLITE_DB_PATH_CALCULATED = os.path.join(_root_dir, "data", "concilie.db")



class Settings(BaseSettings):
    PROJECT_NAME: str = "Financial Checker API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://192.168.3.190:3000"
    ]

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
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS (alias para ALLOWED_ORIGINS)
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignora campos extras do .env


settings = Settings()
