"""
SQL Debug Helper
Utilitário para debug de queries SQL
"""

import logging
from typing import Any, Dict

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

# Logger dedicado para SQL debug
sql_logger = logging.getLogger("sql_debug")
sql_logger.setLevel(logging.INFO)

# Handler para console com formatação
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("\n%(asctime)s - SQL DEBUG\n" "%(message)s\n")
console_handler.setFormatter(formatter)
sql_logger.addHandler(console_handler)


def log_query(query: str, params: Dict[str, Any] = None, label: str = "SQL Query"):
    """
    Log formatado de query SQL

    Args:
        query: Query SQL
        params: Parâmetros da query
        label: Label para identificar a query
    """
    sql_logger.info(f"{'='*80}")
    sql_logger.info(f"{label}")
    sql_logger.info(f"{'-'*80}")
    sql_logger.info(f"{query}")
    if params:
        sql_logger.info(f"{'-'*80}")
        sql_logger.info(f"Parâmetros: {params}")
    sql_logger.info(f"{'='*80}")


def get_sql_from_query(query_obj):
    """
    Extrai SQL compilado de um objeto query SQLAlchemy

    Args:
        query_obj: Query SQLAlchemy

    Returns:
        str: SQL compilado
    """
    from sqlalchemy.dialects import mysql, sqlite

    try:
        # Tenta compilar para MySQL primeiro
        compiled = query_obj.statement.compile(
            dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}
        )
        return str(compiled)
    except:
        try:
            # Se falhar, tenta SQLite
            compiled = query_obj.statement.compile(
                dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}
            )
            return str(compiled)
        except:
            return str(query_obj)


def debug_query(db: Session, query_obj, label: str = "Debug Query"):
    """
    Debug de query antes de executar

    Args:
        db: Sessão SQLAlchemy
        query_obj: Query object
        label: Label para identificar

    Returns:
        Query object (para encadear)
    """
    sql = get_sql_from_query(query_obj)
    log_query(sql, label=label)
    return query_obj


def is_mysql(engine: Engine) -> bool:
    """Verifica se o engine é MySQL"""
    return "mysql" in str(engine.url)


def is_sqlite(engine: Engine) -> bool:
    """Verifica se o engine é SQLite"""
    return "sqlite" in str(engine.url)


def get_db_type(engine: Engine) -> str:
    """Retorna tipo do banco: 'mysql' ou 'sqlite'"""
    return "mysql" if is_mysql(engine) else "sqlite"


def format_query_for_db(query: str, engine: Engine) -> str:
    """
    Formata query SQL de acordo com o banco

    Args:
        query: Query SQL
        engine: Engine SQLAlchemy

    Returns:
        Query formatada
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite usa strftime, || para concat, etc
        return query
    else:
        # MySQL usa DATE_FORMAT, CONCAT, etc
        return query
