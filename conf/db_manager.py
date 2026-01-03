"""
Gerenciador Híbrido de Banco de Dados (MySQL/SQLite)
Sistema otimizado para MySQL com suporte completo a SQLite para distribuição

Define qual banco usar através da variável de ambiente DB_TYPE:
- DB_TYPE=mysql (padrão) -> MySQL
- DB_TYPE=sqlite -> SQLite

Para distribuição, use SQLite sem necessidade de servidor MySQL.
"""

import os
from sqlalchemy.engine import Engine
from typing import Optional

# Variável global para cache da engine
_engine_cache: Optional[Engine] = None
_db_type_cache: Optional[str] = None


def get_db_type() -> str:
    """
    Detecta o tipo de banco a ser usado.

    Ordem de verificação:
    1. Variável de ambiente DB_TYPE
    2. Arquivo .db_config (se existir)
    3. Padrão: MySQL

    Returns:
        'mysql' ou 'sqlite'
    """
    global _db_type_cache

    # Retorna cache se já detectado
    if _db_type_cache:
        return _db_type_cache

    # 1. Verificar variável de ambiente
    db_type = os.environ.get("DB_TYPE", "").lower()
    if db_type in ("mysql", "sqlite"):
        _db_type_cache = db_type
        return db_type

    # 2. Verificar arquivo de configuração
    config_file = os.path.join(os.path.dirname(__file__), "..", ".db_config")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                db_type = f.read().strip().lower()
                if db_type in ("mysql", "sqlite"):
                    _db_type_cache = db_type
                    return db_type
        except Exception as e:
            print(f"[DB_MANAGER] Aviso: Erro ao ler .db_config: {e}")

    # 3. Verificar se existe banco SQLite (indica distribuição)
    sqlite_path = os.path.join(os.path.dirname(__file__), "..", "data", "concilie.db")
    if os.path.exists(sqlite_path):
        # Se o arquivo SQLite existe e não há MySQL configurado, usa SQLite
        _db_type_cache = "sqlite"
        return "sqlite"

    # 4. Padrão: MySQL (ambiente de desenvolvimento)
    _db_type_cache = "mysql"
    return "mysql"


def set_db_type(db_type: str):
    """
    Define o tipo de banco a ser usado.

    Args:
        db_type: 'mysql' ou 'sqlite'
    """
    global _db_type_cache, _engine_cache

    if db_type not in ("mysql", "sqlite"):
        raise ValueError(f"Tipo de banco inválido: {db_type}. Use 'mysql' ou 'sqlite'")

    _db_type_cache = db_type
    _engine_cache = None  # Limpa cache da engine para recriar


def get_engine(force_new: bool = False) -> Engine:
    """
    Retorna a engine do banco de dados (MySQL ou SQLite).

    Args:
        force_new: Se True, força criação de nova engine (ignora cache)

    Returns:
        Engine SQLAlchemy (MySQL ou SQLite conforme configuração)
    """
    global _engine_cache

    # Retorna cache se disponível
    if _engine_cache and not force_new:
        return _engine_cache

    db_type = get_db_type()

    if db_type == "sqlite":
        from conf.conf_bd_sqlite import get_engine_sqlite

        print("[DB_MANAGER] Usando SQLite")
        _engine_cache = get_engine_sqlite()
    else:
        from conf.conf_bd import get_engine as get_mysql_engine

        print("[DB_MANAGER] Usando MySQL")
        _engine_cache = get_mysql_engine()

    return _engine_cache


def get_quote_char() -> str:
    """
    Retorna o caractere de quote adequado ao banco.

    Returns:
        "`" para MySQL, '"' para SQLite
    """
    db_type = get_db_type()

    if db_type == "sqlite":
        return '"'
    else:
        return "`"


def quote_identifier(identifier: str) -> str:
    """
    Adiciona quotes em um identificador (tabela/coluna).

    Args:
        identifier: Nome da coluna/tabela

    Returns:
        Identificador com quotes apropriados ao banco
    """
    quote = get_quote_char()
    return f"{quote}{identifier}{quote}"


def get_primary_key_name() -> str:
    """
    Retorna o nome da coluna de chave primária.

    Returns:
        "id" (padrão para ambos os bancos)
    """
    return "id"


def is_sqlite() -> bool:
    """
    Verifica se está usando SQLite.

    Returns:
        True se usando SQLite, False se MySQL
    """
    return get_db_type() == "sqlite"


def is_mysql() -> bool:
    """
    Verifica se está usando MySQL.

    Returns:
        True se usando MySQL, False se SQLite
    """
    return get_db_type() == "mysql"
