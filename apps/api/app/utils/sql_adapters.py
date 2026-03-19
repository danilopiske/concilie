# DEPRECATED: Use app.core.sql_adapter (funções standalone) em vez desta classe.
# Este módulo não é usado internamente — mantido apenas por compatibilidade externa.
from typing import List
from sqlalchemy.engine import Engine


class SQLAdapter:
    """
    Adaptador para diferenças de sintaxe SQL entre bancos (MySQL/SQLite)
    """
    def __init__(self, engine: Engine):
        self.engine = engine
        self.is_mysql = "mysql" in str(engine.url)
        self.is_sqlite = "sqlite" in str(engine.url)

    def date_format(self, column: str, fmt: str) -> str:
        """
        Retorna sintaxe para formatar data
        MySQL: DATE_FORMAT(col, '%Y-%m-%d')
        SQLite: strftime('%Y-%m-%d', col)
        """
        if self.is_mysql:
            return f"DATE_FORMAT({column}, '{fmt}')"
        return f"strftime('{fmt}', {column})"

    def concat(self, parts: List[str]) -> str:
        """
        Retorna sintaxe para concatenação
        MySQL: CONCAT(a, b)
        SQLite: a || b
        """
        if self.is_mysql:
            return f"CONCAT({', '.join(parts)})"
        return " || ".join(parts)

    def cast_decimal(self, column: str, precision: int = 18, scale: int = 2) -> str:
        """
        Cast para DECIMAL
        MySQL: CAST(col AS DECIMAL(p,s))
        SQLite: CAST(col AS DECIMAL) -- SQLite ignora precisão mas é bom manter sintaxe
        """
        if self.is_mysql:
            return f"CAST({column} AS DECIMAL({precision},{scale}))"
        return f"CAST({column} AS DECIMAL)"

    def json_extract(self, column: str, path: str) -> str:
        """
        Extração de JSON
        MySQL: JSON_EXTRACT(col, '$.path')
        SQLite: json_extract(col, '$.path')
        """
        # Sintaxe é igual na maioria dos casos recentes
        return f"json_extract({column}, '{path}')"
