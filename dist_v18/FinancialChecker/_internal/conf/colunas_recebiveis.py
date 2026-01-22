from sqlalchemy.engine import Engine
from typing import List


def listar_colunas_recebiveis_processados(engine: Engine) -> List[str]:
    """
    Lista os nomes das colunas da tabela recebiveis_processados no banco de dados MySQL.
    """
    from .funcoesbd import fetch_all

    # MySQL: usa INFORMATION_SCHEMA
    rows = fetch_all(
        engine,
        """
        SELECT COLUMN_NAME AS coluna FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'recebiveis_processados'
         ORDER BY ORDINAL_POSITION
        """,
    )
    return [r["coluna"] for r in rows]
