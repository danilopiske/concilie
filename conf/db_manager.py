"""
Gerenciador de Banco de Dados Híbrido
Suporta MySQL (modo deploy) e SQLite (modo singleuser)
"""

import os
from sqlalchemy.engine import Engine
from typing import Literal

# Tipo de banco de dados
DBMode = Literal["mysql", "sqlite"]

# Variável global que define o modo atual
_DB_MODE: DBMode = "mysql"  # Padrão: MySQL (modo deploy)


def set_db_mode(mode: DBMode) -> None:
    """
    Define o modo de banco de dados a ser usado.

    Args:
        mode: "mysql" para modo deploy ou "sqlite" para modo singleuser
    """
    global _DB_MODE
    if mode not in ("mysql", "sqlite"):
        raise ValueError(f"Modo inválido: {mode}. Use 'mysql' ou 'sqlite'")

    _DB_MODE = mode
    print(f"[DB_MANAGER] Modo de banco definido: {mode.upper()}")


def get_db_mode() -> DBMode:
    """Retorna o modo de banco de dados atual."""
    return _DB_MODE


def get_engine() -> Engine:
    """
    Retorna a engine apropriada baseada no modo configurado.

    Returns:
        Engine SQLAlchemy (MySQL ou SQLite)
    """
    if _DB_MODE == "mysql":
        from conf.conf_bd import get_engine as get_mysql_engine

        print("[DB_MANAGER] Usando MySQL (modo deploy)")
        return get_mysql_engine()
    else:
        from conf.conf_bd_sqlite import get_engine_sqlite

        print("[DB_MANAGER] Usando SQLite (modo singleuser)")
        return get_engine_sqlite()


def is_mysql() -> bool:
    """Retorna True se o modo atual é MySQL."""
    return _DB_MODE == "mysql"


def is_sqlite() -> bool:
    """Retorna True se o modo atual é SQLite."""
    return _DB_MODE == "sqlite"


def get_quote_char() -> str:
    """
    Retorna o caractere de quote apropriado para o banco atual.

    Returns:
        "`" para MySQL, "" para SQLite
    """
    return "`" if is_mysql() else ""


def quote_identifier(identifier: str) -> str:
    """
    Adiciona quotes em um identificador se necessário.

    Args:
        identifier: Nome da coluna/tabela

    Returns:
        Identificador com quotes (MySQL) ou sem (SQLite)
    """
    if is_mysql():
        return f"`{identifier}`"
    return identifier


def adapt_sql(sql_mysql: str, sql_sqlite: str = None) -> str:
    """
    Retorna a query SQL apropriada para o banco atual.

    Args:
        sql_mysql: Query SQL para MySQL
        sql_sqlite: Query SQL para SQLite (opcional, usa sql_mysql se não fornecido)

    Returns:
        Query apropriada para o banco atual
    """
    if is_sqlite() and sql_sqlite:
        return sql_sqlite
    return sql_mysql


def get_primary_key_name() -> str:
    """
    Retorna o nome da coluna de chave primária para usar em queries.

    Returns:
        "id" para MySQL, "rowid" para SQLite
    """
    return "id" if is_mysql() else "rowid"
