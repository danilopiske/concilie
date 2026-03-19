"""
Database helper functions — ported from conf/funcoesbd.py.
Use these instead of importing from the legacy conf package.
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from sqlalchemy.engine import Engine
from sqlalchemy import text
from app.core.sql_adapter import normalize_text_compare, get_db_type


@contextmanager
def get_conn(engine: Engine):
    """Context manager for database connections."""
    with engine.begin() as conn:
        yield conn


def _adapt_sql(engine: Engine, sql: str) -> str:
    """Adapt raw MySQL SQL to SQLite dialect for common patterns."""
    if get_db_type(engine) != "sqlite":
        return sql

    # INSERT IGNORE → INSERT OR IGNORE
    adapted = sql.replace("INSERT IGNORE INTO", "INSERT OR IGNORE INTO")
    adapted = adapted.replace("INSERT IGNORE", "INSERT OR IGNORE")

    # IFNULL(col, val) → COALESCE(col, val)
    # Simple replacement — works for most cases without nested calls
    import re
    adapted = re.sub(r'\bIFNULL\s*\(', 'COALESCE(', adapted, flags=re.IGNORECASE)

    return adapted


def exec_sql(engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Execute a SQL statement."""
    sql = _adapt_sql(engine, sql)
    with get_conn(engine) as conn:
        if get_db_type(engine) == "mysql":
            try:
                conn.execute(text("SET SESSION innodb_lock_wait_timeout = 300"))
            except Exception:
                pass
        conn.execute(text(sql), params or {})


def fetch_one(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Fetch a single row."""
    sql = _adapt_sql(engine, sql)
    with get_conn(engine) as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def fetch_all(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Fetch all rows."""
    sql = _adapt_sql(engine, sql)
    with get_conn(engine) as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(r) for r in rows]


def normalize_compare(engine: Engine, column: str, param: str) -> str:
    """Case-insensitive text comparison SQL fragment."""
    return normalize_text_compare(engine, column, param)
