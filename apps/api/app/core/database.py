"""
Database Session Management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
from urllib.parse import quote_plus
from app.core.config import settings

# Logger para SQL queries
logger = logging.getLogger("sqlalchemy.engine")
if hasattr(settings, "DEBUG_SQL") and settings.DEBUG_SQL:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)

def get_database_url() -> str:
    """Get database URL based on DATABASE_TYPE"""
    if settings.DATABASE_TYPE == "mysql":
        # URL-encode password to handle special characters
        encoded_password = quote_plus(settings.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}"
            f"@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
        )
    else:  # sqlite
        return f"sqlite:///{settings.SQLITE_DB_PATH}"


# Create engine with tuned pool performance
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_size=20 if settings.DATABASE_TYPE == "mysql" else 5,
    max_overflow=10 if settings.DATABASE_TYPE == "mysql" else 10,
    pool_recycle=3600,
    echo=settings.DEBUG_SQL if hasattr(settings, "DEBUG_SQL") else False,
)

# SQLite optimization: WAL mode (Write-Ahead Logging)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_TYPE == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables
    """
    from app.models import Base

    Base.metadata.create_all(bind=engine)


def get_db_info() -> dict:
    """
    Get database connection information
    """
    db_url = get_database_url()
    is_mysql = settings.DATABASE_TYPE == "mysql"

    return {
        "type": settings.DATABASE_TYPE,
        "is_mysql": is_mysql,
        "is_sqlite": not is_mysql,
        "url": db_url.split("@")[-1] if is_mysql else db_url,
        "dialect": engine.dialect.name,
        "driver": engine.driver,
    }


# Event listener para debug de queries SQL
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, params, context, executemany
):
    """
    Log SQL queries antes da execução
    """
    if hasattr(settings, "DEBUG_SQL") and settings.DEBUG_SQL:
        logger.info(f"\n{'='*80}")
        logger.info(f"SQL Query:")
        logger.info(f"{statement}")
        if params:
            logger.info(f"Parameters: {params}")
        logger.info(f"{'='*80}\n")
