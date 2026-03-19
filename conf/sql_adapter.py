"""
Adaptador SQL Híbrido - MySQL/SQLite (LEGADO)

DEPRECATED: Este módulo é mantido apenas para compatibilidade com modules/reports.py
e proc/proc_importacao.py. Para novo código no FastAPI, use:
    from app.core.sql_adapter import ...

Este arquivo é uma cópia do canônico app/core/sql_adapter.py.
Não adicione novas funções aqui — adicione em app/core/sql_adapter.py.
"""

from typing import List, Tuple
from sqlalchemy.engine import Engine


def get_db_type(engine: Engine) -> str:
    """
    Detecta o tipo de banco de dados da engine.

    Args:
        engine: Engine SQLAlchemy

    Returns:
        'mysql' ou 'sqlite'
    """
    dialect_name = engine.dialect.name.lower()
    if "mysql" in dialect_name:
        return "mysql"
    elif "sqlite" in dialect_name:
        return "sqlite"
    else:
        # Fallback para MySQL (compatibilidade com código existente)
        return "mysql"


def normalize_text_compare(engine: Engine, column: str, param: str) -> str:
    """
    Retorna SQL para comparação case-insensitive de texto.

    Args:
        engine: Engine SQLAlchemy
        column: Nome da coluna a comparar
        param: Nome do parâmetro (ex: 'ctx')

    Returns:
        SQL para comparação case-insensitive
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: COLLATE NOCASE
        return f"{column} = :{param} COLLATE NOCASE"
    else:
        # MySQL: case-insensitive por padrão
        return f"{column} = :{param}"


def date_format_sql(engine: Engine, column: str, format_str: str) -> str:
    """
    Retorna SQL de formatação de data.

    Args:
        engine: Engine SQLAlchemy
        column: Nome da coluna de data
        format_str: Formato MySQL (ex: '%Y-%m-%d', '%Y-%m')

    Returns:
        SQL formatado para o banco correto
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # Converte formato MySQL para SQLite
        sqlite_format = (
            format_str.replace("%Y", "%Y").replace("%m", "%m").replace("%d", "%d")
        )
        return f"strftime('{sqlite_format}', {column})"
    else:
        # MySQL: DATE_FORMAT
        return f"DATE_FORMAT({column}, '{format_str}')"


def concat_sql(engine: Engine, *args: str) -> str:
    """
    Retorna SQL de concatenação.

    Args:
        engine: Engine SQLAlchemy
        *args: Expressões SQL a concatenar

    Returns:
        SQL de concatenação
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: usa ||
        return " || ".join(args)
    else:
        # MySQL: usa CONCAT()
        return f"CONCAT({', '.join(args)})"


def insert_ignore_sql(engine: Engine, table: str, columns: str, values: str) -> str:
    """
    Retorna SQL de INSERT IGNORE.

    Args:
        engine: Engine SQLAlchemy
        table: Nome da tabela
        columns: String com nomes das colunas
        values: String com valores/placeholders

    Returns:
        SQL de INSERT com tratamento de duplicatas
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: INSERT OR IGNORE
        return f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({values})"
    else:
        # MySQL: INSERT IGNORE
        return f"INSERT IGNORE INTO {table} ({columns}) VALUES ({values})"


def year_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair ano de uma data."""
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return f"CAST(strftime('%Y', {column}) AS INTEGER)"
    else:
        return f"YEAR({column})"


def month_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair mês de uma data."""
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return f"CAST(strftime('%m', {column}) AS INTEGER)"
    else:
        return f"MONTH({column})"


def quarter_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular trimestre de uma data."""
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: calcula trimestre baseado no mês
        month = month_sql(engine, column)
        return f"((({month} - 1) / 3) + 1)"
    else:
        return f"QUARTER({column})"


def semester_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular semestre de uma data."""
    db_type = get_db_type(engine)

    month = month_sql(engine, column)

    if db_type == "sqlite":
        # SQLite: CASE WHEN
        return f"CASE WHEN {month} <= 6 THEN '1' ELSE '2' END"
    else:
        # MySQL: IF
        return f"IF({month} <= 6, '1', '2')"


def get_table_columns_sql(engine: Engine, table_name: str) -> str:
    """
    Retorna SQL para buscar colunas de uma tabela.

    Args:
        engine: Engine SQLAlchemy
        table_name: Nome da tabela

    Returns:
        SQL para listar colunas
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: PRAGMA table_info
        # Nota: Esta query precisa ser executada diretamente, retornamos o PRAGMA
        return f"PRAGMA table_info({table_name})"
    else:
        # MySQL: INFORMATION_SCHEMA
        return f"""
            SELECT COLUMN_NAME AS coluna 
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """


def upsert_sql(
    engine: Engine, table: str, columns: List[str], update_columns: List[str]
) -> str:
    """
    Retorna SQL de UPSERT (INSERT com UPDATE em caso de conflito).

    Args:
        engine: Engine SQLAlchemy
        table: Nome da tabela
        columns: Lista de colunas para INSERT
        update_columns: Lista de colunas para UPDATE

    Returns:
        SQL de UPSERT
    """
    db_type = get_db_type(engine)

    cols_str = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])

    if db_type == "sqlite":
        # SQLite: INSERT OR REPLACE ou INSERT ... ON CONFLICT
        # Usando ON CONFLICT para melhor controle
        updates = ", ".join([f"{col} = excluded.{col}" for col in update_columns])
        # Assume que a primeira coluna ou 'id' é a chave primária
        # Você pode ajustar isso conforme necessário
        return f"""
            INSERT INTO {table} ({cols_str}) 
            VALUES ({placeholders})
            ON CONFLICT DO UPDATE SET {updates}
        """
    else:
        # MySQL: INSERT ... ON DUPLICATE KEY UPDATE
        updates = ", ".join([f"{col}=VALUES({col})" for col in update_columns])
        return f"""
            INSERT INTO {table} ({cols_str}) 
            VALUES ({placeholders}) 
            ON DUPLICATE KEY UPDATE {updates}
        """


def limit_sql(engine: Engine, limit: int, offset: int = 0) -> str:
    """
    Retorna SQL de LIMIT/OFFSET.

    Args:
        engine: Engine SQLAlchemy
        limit: Número máximo de registros
        offset: Número de registros para pular

    Returns:
        SQL de LIMIT
    """
    # Ambos MySQL e SQLite usam a mesma sintaxe
    if offset > 0:
        return f"LIMIT {limit} OFFSET {offset}"
    else:
        return f"LIMIT {limit}"


def auto_increment_sql(engine: Engine) -> str:
    """
    Retorna SQL para definir coluna auto-incremento.

    Returns:
        String SQL para auto-incremento
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return "AUTOINCREMENT"
    else:
        return "AUTO_INCREMENT"


def current_timestamp_sql(engine: Engine) -> str:
    """
    Retorna SQL para timestamp atual.

    Returns:
        Função SQL de timestamp atual
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return "CURRENT_TIMESTAMP"
    else:
        return "CURRENT_TIMESTAMP"


def if_null_sql(engine: Engine, column: str, default_value: str) -> str:
    """
    Retorna SQL para IFNULL/COALESCE.

    Args:
        engine: Engine SQLAlchemy
        column: Nome da coluna
        default_value: Valor padrão se NULL

    Returns:
        SQL de IFNULL/COALESCE
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: COALESCE ou IFNULL (ambos funcionam)
        return f"COALESCE({column}, {default_value})"
    else:
        # MySQL: IFNULL ou COALESCE (IFNULL é mais comum)
        return f"IFNULL({column}, {default_value})"


def quote_identifier(engine: Engine, identifier: str) -> str:
    """
    Adiciona quotes em um identificador (tabela/coluna).

    Args:
        engine: Engine SQLAlchemy
        identifier: Nome da coluna/tabela

    Returns:
        Identificador com quotes apropriados
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: usa "aspas duplas" ou [colchetes]
        # Preferimos aspas duplas por serem mais portáveis
        return f'"{identifier}"'
    else:
        # MySQL: usa `backticks`
        return f"`{identifier}`"


def get_quote_char(engine: Engine) -> str:
    """
    Retorna o caractere de quote para o banco.

    Args:
        engine: Engine SQLAlchemy

    Returns:
        Caractere de quote ("`" para MySQL, '"' para SQLite)
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return '"'
    else:
        return "`"


def last_insert_id_sql(engine: Engine) -> str:
    """
    Retorna SQL para obter o último ID inserido.

    Returns:
        SQL para last insert ID
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        return "SELECT last_insert_rowid()"
    else:
        return "SELECT LAST_INSERT_ID()"


def convert_placeholder_syntax(engine: Engine, sql: str) -> str:
    """
    Converte placeholders MySQL (:param) para sintaxe do banco correto.

    Args:
        engine: Engine SQLAlchemy
        sql: Query SQL com placeholders :param

    Returns:
        SQL com placeholders convertidos (se necessário)
    """
    db_type = get_db_type(engine)

    # Tanto MySQL quanto SQLite com SQLAlchemy usam :param
    # Esta função existe para futuras expansões se necessário
    return sql


def database_name_sql(engine: Engine) -> str:
    """
    Retorna SQL para obter o nome do banco de dados atual.

    Returns:
        SQL para obter nome do banco
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite não tem conceito de "banco de dados" da mesma forma
        # Retorna o caminho do arquivo
        return "SELECT 'main' AS database_name"
    else:
        return "SELECT DATABASE() AS database_name"


def drop_table_if_exists_sql(engine: Engine, table_name: str) -> str:
    """
    Retorna SQL para DROP TABLE IF EXISTS.

    Args:
        engine: Engine SQLAlchemy
        table_name: Nome da tabela

    Returns:
        SQL para drop table
    """
    # Mesma sintaxe para ambos
    return f"DROP TABLE IF EXISTS {table_name}"


def create_index_sql(
    engine: Engine,
    index_name: str,
    table_name: str,
    columns: List[str],
    unique: bool = False,
) -> str:
    """
    Retorna SQL para criar índice.

    Args:
        engine: Engine SQLAlchemy
        index_name: Nome do índice
        table_name: Nome da tabela
        columns: Lista de colunas do índice
        unique: Se True, cria índice UNIQUE

    Returns:
        SQL para criar índice
    """
    unique_str = "UNIQUE " if unique else ""
    cols_str = ", ".join(columns)

    # Mesma sintaxe para ambos
    return f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({cols_str})"


# ==========================================
# Funções de Compatibilidade de Tipos
# ==========================================


def get_decimal_type(engine: Engine):
    """
    Retorna o tipo SQLAlchemy adequado para DECIMAL/NUMERIC.

    Returns:
        Tipo SQLAlchemy (DECIMAL para MySQL, REAL para SQLite)
    """
    from sqlalchemy.types import DECIMAL, REAL

    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite não tem DECIMAL nativo, usa REAL
        return REAL
    else:
        # MySQL usa DECIMAL
        return DECIMAL


def get_datetime_type(engine: Engine):
    """
    Retorna o tipo SQLAlchemy adequado para DATETIME.

    Returns:
        Tipo SQLAlchemy DateTime
    """
    from sqlalchemy.types import DateTime

    # Ambos usam DateTime
    return DateTime


def get_text_type(engine: Engine, length: int = None):
    """
    Retorna o tipo SQLAlchemy adequado para TEXT/VARCHAR.

    Args:
        length: Comprimento máximo (se None, usa TEXT)

    Returns:
        Tipo SQLAlchemy String ou Text
    """
    from sqlalchemy.types import String, Text

    if length:
        return String(length)
    else:
        return Text


# ==========================================
# Funções de Utilitários
# ==========================================


def supports_json(engine: Engine) -> bool:
    """
    Verifica se o banco suporta tipo JSON nativo.

    Returns:
        True se suporta JSON
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite 3.38+ tem suporte JSON, mas vamos retornar False
        # para usar TEXT como fallback seguro
        return False
    else:
        # MySQL 5.7+ suporta JSON
        return True


def get_regexp_operator(engine: Engine) -> str:
    """
    Retorna o operador de REGEXP.

    Returns:
        Operador REGEXP do banco
    """
    db_type = get_db_type(engine)

    if db_type == "sqlite":
        # SQLite usa REGEXP (mas requer função custom)
        return "REGEXP"
    else:
        # MySQL usa REGEXP
        return "REGEXP"
