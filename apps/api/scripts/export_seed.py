"""
export_seed.py — Exporta dados de referência do MySQL para SQLite (seed de distribuição).

Uso:
    cd apps/api
    python scripts/export_seed.py [--output ../../data/concilie.db]

O seed gerado é usado pelo dist_main.py para inicializar o banco do cliente
na primeira execução da distribuição desktop.
"""

import os
import sys
import argparse
import sqlite3
import logging
from pathlib import Path

# Garantir que o projeto está no path
_api_dir = Path(__file__).resolve().parent.parent
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from dotenv import load_dotenv

# Carregar .env do diretório da api
load_dotenv(_api_dir / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Tabelas de referência exportadas para o seed
SEED_TABLES = [
    "bandeiras",
    "formas_pagamento",
    "taxas",
    "contextos",
    "termos_filtraveis",
    "usuarios",
]

# Tabelas de processamento — NUNCA devem ser incluídas no seed
FORBIDDEN_TABLES = {
    "vendas_processadas",
    "recebiveis_processados",
    "vendas_calculos",
    "controle_processamentos",
    "import_tasks",
    "relatorio_tasks",
}


def get_mysql_engine():
    """Cria engine MySQL a partir das configurações de ambiente."""
    from app.core.config import settings
    from sqlalchemy import create_engine
    from urllib.parse import quote_plus

    if settings.DATABASE_TYPE != "mysql":
        raise RuntimeError(
            f"DATABASE_TYPE={settings.DATABASE_TYPE}. "
            "export_seed.py requer DATABASE_TYPE=mysql no .env ativo."
        )

    encoded_password = quote_plus(settings.MYSQL_PASSWORD)
    url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}"
        f"@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
    )
    engine = create_engine(url, pool_pre_ping=True)
    log.info(f"Conectado ao MySQL: {settings.MYSQL_SERVER}/{settings.MYSQL_DB}")
    return engine


def export_table(mysql_conn, sqlite_conn: sqlite3.Connection, table: str) -> int:
    """Exporta uma tabela do MySQL para o SQLite. Retorna número de linhas exportadas."""
    from sqlalchemy import text

    # Buscar dados do MySQL
    rows = mysql_conn.execute(text(f"SELECT * FROM `{table}`")).mappings().all()
    if not rows:
        log.info(f"  {table}: 0 registros (tabela vazia)")
        return 0

    rows = [dict(r) for r in rows]
    columns = list(rows[0].keys())

    # Criar tabela no SQLite se não existir (via schema do MySQL)
    # Usamos INSERT OR REPLACE para idempotência
    placeholders = ", ".join(["?" for _ in columns])
    col_names = ", ".join([f'"{c}"' for c in columns])
    insert_sql = f'INSERT OR REPLACE INTO "{table}" ({col_names}) VALUES ({placeholders})'

    values = [tuple(r[c] for c in columns) for r in rows]
    sqlite_conn.executemany(insert_sql, values)

    count = len(values)
    log.info(f"  {table}: {count} registros exportados")
    return count


def create_sqlite_schema(mysql_engine, sqlite_path: Path):
    """Cria o schema SQLite usando os modelos SQLAlchemy."""
    from app.models import Base
    from sqlalchemy import create_engine

    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    Base.metadata.create_all(bind=sqlite_engine)
    sqlite_engine.dispose()
    log.info(f"Schema criado em: {sqlite_path}")


def main():
    parser = argparse.ArgumentParser(description="Exporta seed MySQL → SQLite")
    parser.add_argument(
        "--output",
        default=str(_api_dir.parent.parent / "data" / "concilie.db"),
        help="Caminho do arquivo SQLite de saída (default: ../../data/concilie.db)",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=SEED_TABLES,
        help="Tabelas a exportar (default: tabelas de referência padrão)",
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()

    # Validar tabelas solicitadas
    forbidden = set(args.tables) & FORBIDDEN_TABLES
    if forbidden:
        log.error(
            f"ABORTADO: As seguintes tabelas de processamento NÃO devem ser "
            f"incluídas no seed: {', '.join(forbidden)}"
        )
        sys.exit(1)

    log.info(f"=== export_seed.py ===")
    log.info(f"Destino: {output_path}")
    log.info(f"Tabelas: {', '.join(args.tables)}")

    # Remover seed antigo para garantir idempotência
    if output_path.exists():
        output_path.unlink()
        log.info("Seed anterior removido.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Criar schema no SQLite
    create_sqlite_schema(None, output_path)

    # Conectar ao MySQL e exportar
    mysql_engine = get_mysql_engine()
    sqlite_conn = sqlite3.connect(str(output_path))

    try:
        total = 0
        with mysql_engine.connect() as mysql_conn:
            for table in args.tables:
                try:
                    count = export_table(mysql_conn, sqlite_conn, table)
                    total += count
                except Exception as e:
                    log.warning(f"  {table}: ERRO — {e}")

        sqlite_conn.commit()
        log.info(f"\n✅ Seed gerado com sucesso: {total} registros totais")
        log.info(f"   Arquivo: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")

    except Exception as e:
        log.error(f"Erro durante exportação: {e}")
        sqlite_conn.close()
        if output_path.exists():
            output_path.unlink()
        sys.exit(1)
    finally:
        sqlite_conn.close()
        mysql_engine.dispose()


if __name__ == "__main__":
    main()
