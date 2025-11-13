"""
Script de Migração: MySQL -> SQLite

Este script migra todos os dados do banco MySQL 'concilie' para SQLite.
Preserva estrutura de tabelas, índices e dados com mapeamento correto de tipos.

Uso:
    python migrate_mysql_to_sqlite.py

"""

import pandas as pd
import numpy as np
from sqlalchemy import (
    create_engine,
    inspect,
    text,
    MetaData,
    Table,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
)
from sqlalchemy.types import TypeDecorator
from conf.conf_bd import get_engine as get_mysql_engine
from conf.conf_bd_sqlite import get_engine_sqlite, get_db_path
import os
import sys
from datetime import datetime

# ============================================================================
# SISTEMA DE LOG PARA DEBUG
# ============================================================================


class DebugLogger:
    """Logger que escreve tanto no console quanto em arquivo debug.txt"""

    def __init__(self, filename="debug.txt"):
        self.terminal = sys.stdout
        self.log_file = open(filename, "w", encoding="utf-8")
        self.log(f"{'='*80}")
        self.log(f"MIGRAÇÃO MySQL -> SQLite - DEBUG LOG")
        self.log(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*80}\n")

    def log(self, message):
        """Escreve mensagem no console e arquivo"""
        self.terminal.write(message + "\n")
        self.terminal.flush()
        self.log_file.write(message + "\n")
        self.log_file.flush()

    def error(self, message, exception=None):
        """Log de erro com traceback opcional"""
        error_msg = f"[ERRO] {message}"
        self.log(error_msg)

        if exception:
            import traceback

            tb = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
            self.log(f"Traceback completo:\n{tb}")

    def close(self):
        """Fecha o arquivo de log"""
        self.log(f"\n{'='*80}")
        self.log(f"Término: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"{'='*80}")
        self.log_file.close()


# Instância global do logger
logger = None


def print_log(message):
    """Função helper para facilitar logging"""
    if logger:
        logger.log(message)
    else:
        print(message)


# Mapeamento de tipos MySQL -> SQLite
TYPE_MAPPING = {
    "TINYINT": Boolean,  # TINYINT(1) geralmente é boolean
    "SMALLINT": Integer,
    "MEDIUMINT": Integer,
    "INT": Integer,
    "INTEGER": Integer,
    "BIGINT": Integer,
    "DECIMAL": Float,
    "NUMERIC": Float,
    "FLOAT": Float,
    "DOUBLE": Float,
    "DATE": DateTime,
    "DATETIME": DateTime,
    "TIMESTAMP": DateTime,
    "TIME": String,  # TIME como string no SQLite
    "YEAR": Integer,
    "CHAR": String,
    "VARCHAR": String,
    "TEXT": String,
    "TINYTEXT": String,
    "MEDIUMTEXT": String,
    "LONGTEXT": String,
    "BINARY": String,
    "VARBINARY": String,
    "BLOB": String,
    "TINYBLOB": String,
    "MEDIUMBLOB": String,
    "LONGBLOB": String,
    "ENUM": String,
    "SET": String,
    "JSON": String,
}


def convert_mysql_type_to_sqlite(mysql_type_str):
    """
    Converte string de tipo MySQL para tipo SQLAlchemy SQLite.

    Args:
        mysql_type_str: String do tipo MySQL (ex: "TINYINT(1)", "VARCHAR(255)")

    Returns:
        Tipo SQLAlchemy apropriado
    """
    # Remove tamanho e parâmetros
    base_type = mysql_type_str.split("(")[0].upper()

    sqlite_type = TYPE_MAPPING.get(base_type, String)

    # Caso especial: TINYINT(1) é boolean
    if base_type == "TINYINT" and "(1)" in mysql_type_str:
        return Boolean

    return sqlite_type


def prepare_dataframe_for_sqlite(df, table_name, mysql_table):
    """
    Prepara DataFrame para inserção no SQLite, convertendo tipos apropriadamente.

    Args:
        df: DataFrame com dados do MySQL
        table_name: Nome da tabela
        mysql_table: Objeto Table do SQLAlchemy com metadados MySQL

    Returns:
        DataFrame ajustado para SQLite
    """
    if logger:
        logger.log(f"[CONVERT] Convertendo tipos de dados para tabela {table_name}...")

    df_copy = df.copy()

    for col in mysql_table.columns:
        col_name = col.name
        if col_name not in df_copy.columns:
            continue

        mysql_type_str = str(col.type)

        # Converte TINYINT(1) para boolean
        if "TINYINT(1)" in mysql_type_str or "BOOL" in mysql_type_str.upper():
            df_copy[col_name] = df_copy[col_name].fillna(0).astype(bool)
            if logger:
                logger.log(f"  - {col_name}: {mysql_type_str} -> Boolean")

        # Converte DATETIME/TIMESTAMP para datetime e depois para string ISO
        elif any(
            t in mysql_type_str.upper() for t in ["DATETIME", "TIMESTAMP", "DATE"]
        ):
            # Converte para datetime primeiro
            df_copy[col_name] = pd.to_datetime(df_copy[col_name], errors="coerce")
            # Converte para string ISO format (SQLite aceita strings de data)
            df_copy[col_name] = df_copy[col_name].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
            if logger:
                logger.log(f"  - {col_name}: {mysql_type_str} -> DateTime (ISO string)")

        # Converte DECIMAL/NUMERIC para float
        elif any(
            t in mysql_type_str.upper()
            for t in ["DECIMAL", "NUMERIC", "DOUBLE", "FLOAT"]
        ):
            df_copy[col_name] = pd.to_numeric(df_copy[col_name], errors="coerce")
            if logger:
                logger.log(f"  - {col_name}: {mysql_type_str} -> Float")

        # Converte INT/BIGINT para integer
        elif any(
            t in mysql_type_str.upper()
            for t in ["INT", "INTEGER", "BIGINT", "SMALLINT", "MEDIUMINT"]
        ):
            df_copy[col_name] = pd.to_numeric(
                df_copy[col_name], errors="coerce", downcast="integer"
            )
            if logger:
                logger.log(f"  - {col_name}: {mysql_type_str} -> Integer")

    # Passo final: garantir que não há tipos incompatíveis com SQLite
    # Substitui NaN por None (NULL) para compatibilidade
    df_copy = df_copy.where(pd.notna(df_copy), None)

    return df_copy


def get_mysql_tables(mysql_engine):
    """Retorna lista de todas as tabelas do MySQL."""
    inspector = inspect(mysql_engine)
    tables = inspector.get_table_names()
    print(f"\n[MySQL] Encontradas {len(tables)} tabelas:")
    for table in tables:
        print(f"  - {table}")
    return tables


def get_table_row_count(engine, table_name):
    """Retorna contagem de linhas em uma tabela."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as count FROM `{table_name}`"))
            count = result.fetchone()[0]
            print_log(f"[COUNT] {table_name}: {count:,} registros")
            return count
    except Exception as e:
        error_msg = f"Erro ao contar linhas de {table_name}: {e}"
        if logger:
            logger.error(error_msg, e)
        else:
            print(f"[ERRO] {error_msg}")
        return 0


def migrate_table_schema(mysql_engine, sqlite_engine, table_name):
    """
    Cria tabela no SQLite com schema correto (PKs, indexes, constraints).
    """
    print_log(f"\n[SCHEMA] Preparando tabela: {table_name}")

    # SQLAlchemy reflete a estrutura do MySQL
    mysql_metadata = MetaData()
    mysql_metadata.reflect(bind=mysql_engine, only=[table_name])
    mysql_table = mysql_metadata.tables[table_name]

    print_log(f"[SCHEMA] Tabela {table_name} tem {len(mysql_table.columns)} colunas")

    # Verifica se tabela já existe no SQLite
    sqlite_inspector = inspect(sqlite_engine)
    if table_name in sqlite_inspector.get_table_names():
        print_log(
            f"[SCHEMA] Tabela {table_name} já existe no SQLite - usando existente"
        )
        if logger:
            logger.log("[SCHEMA] Estrutura da tabela MySQL:")
            for col in mysql_table.columns:
                logger.log(f"  - {col.name}: {col.type} (nullable={col.nullable})")
        return mysql_table

    # Cria tabela no SQLite com schema correto
    print_log(f"[SCHEMA] Criando tabela {table_name} no SQLite com constraints...")

    # Obter informações de constraints do MySQL
    mysql_inspector = inspect(mysql_engine)
    pk_constraint = mysql_inspector.get_pk_constraint(table_name)
    pk_columns = pk_constraint.get("constrained_columns", [])
    unique_constraints = mysql_inspector.get_unique_constraints(table_name)
    indexes = mysql_inspector.get_indexes(table_name)

    # Gerar DDL SQLite
    ddl_parts = [f'CREATE TABLE "{table_name}" (']
    column_defs = []

    # Detectar se é PRIMARY KEY composta (múltiplas colunas)
    is_composite_pk = len(pk_columns) > 1

    for col in mysql_table.columns:
        col_name = col.name
        mysql_type = str(col.type)

        # Converter tipo MySQL para SQLite
        if any(
            t in mysql_type.upper()
            for t in ["INT", "SERIAL", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT"]
        ):
            sqlite_type = "INTEGER"
        elif "DECIMAL" in mysql_type.upper() or "NUMERIC" in mysql_type.upper():
            sqlite_type = "REAL"  # Tipos numéricos devem ser REAL no SQLite
        elif (
            "FLOAT" in mysql_type.upper()
            or "DOUBLE" in mysql_type.upper()
            or "REAL" in mysql_type.upper()
        ):
            sqlite_type = "REAL"
        elif any(
            t in mysql_type.upper() for t in ["DATE", "TIME", "TIMESTAMP", "DATETIME"]
        ):
            sqlite_type = "TEXT"  # SQLite armazena datas como texto ISO
        elif "BOOL" in mysql_type.upper() or "TINYINT(1)" in mysql_type:
            sqlite_type = "INTEGER"
        else:
            sqlite_type = "TEXT"

        col_def = f'  "{col_name}" {sqlite_type}'

        # PRIMARY KEY - só aplicar inline se for PK simples (1 coluna)
        if col_name in pk_columns and not is_composite_pk:
            col_def += " PRIMARY KEY"
            # AUTOINCREMENT para INTEGER PRIMARY KEY
            if sqlite_type == "INTEGER" and col.autoincrement:
                col_def += " AUTOINCREMENT"

        # NOT NULL - marcar colunas de PK composta como NOT NULL
        if not col.nullable and col_name not in pk_columns:
            col_def += " NOT NULL"
        elif col_name in pk_columns and is_composite_pk:
            # PKs compostas precisam ser NOT NULL
            col_def += " NOT NULL"

        # DEFAULT
        if col.default is not None:
            default_val = (
                str(col.default.arg)
                if hasattr(col.default, "arg")
                else str(col.default)
            )
            default_val = default_val.strip("'\"")

            if default_val.upper() in ("CURRENT_TIMESTAMP", "NOW()"):
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif sqlite_type == "TEXT":
                col_def += f" DEFAULT '{default_val}'"
            else:
                col_def += f" DEFAULT {default_val}"

        column_defs.append(col_def)

    ddl_parts.append(",\n".join(column_defs))

    # PRIMARY KEY composta (se tiver mais de 1 coluna)
    if is_composite_pk:
        pk_cols = ", ".join([f'"{c}"' for c in pk_columns])
        ddl_parts.append(f",\n  PRIMARY KEY ({pk_cols})")

    # UNIQUE constraints (se não for a PK)
    for unique_const in unique_constraints:
        cols = unique_const["column_names"]
        if cols != pk_columns:
            unique_cols = ", ".join([f'"{c}"' for c in cols])
            ddl_parts.append(f",\n  UNIQUE ({unique_cols})")

    ddl_parts.append("\n);")
    ddl = "".join(ddl_parts)

    # Executar DDL
    with sqlite_engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()

    print_log(f"[SCHEMA] ✓ Tabela {table_name} criada com constraints")

    # Criar indexes
    for idx in indexes:
        if not idx["unique"]:  # Unique já foi tratado como constraint
            idx_name = idx["name"]
            idx_cols = ", ".join([f'"{c}"' for c in idx["column_names"]])
            idx_ddl = f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table_name}" ({idx_cols});'

            try:
                with sqlite_engine.connect() as conn:
                    conn.execute(text(idx_ddl))
                    conn.commit()
                print_log(f"[SCHEMA] ✓ Criado index: {idx_name}")
            except Exception as e:
                if logger:
                    logger.log(f"[AVISO] Erro ao criar index {idx_name}: {e}")

    # Log detalhado
    if logger:
        logger.log("[SCHEMA] Estrutura da tabela criada:")
        for col in mysql_table.columns:
            pk_mark = " (PK)" if col.name in pk_columns else ""
            logger.log(f"  - {col.name}: {col.type}{pk_mark} (nullable={col.nullable})")

    return mysql_table


def migrate_table_data(
    mysql_engine, sqlite_engine, table_name, mysql_table, chunk_size=10000
):
    """
    Migra dados de uma tabela do MySQL para SQLite em chunks com conversão de tipos.

    Args:
        mysql_engine: Engine MySQL
        sqlite_engine: Engine SQLite
        table_name: Nome da tabela
        mysql_table: Objeto Table com metadados MySQL
        chunk_size: Tamanho do chunk para processamento
    """
    print_log(f"\n[DATA] Iniciando migração de dados: {table_name}")

    # Conta total de registros
    total_rows = get_table_row_count(mysql_engine, table_name)
    print_log(f"[DATA] Total de registros: {total_rows:,}")

    if total_rows == 0:
        print_log(f"[DATA] Tabela {table_name} está vazia - pulando")
        return 0

    # Ajusta chunk_size para tabelas muito grandes
    original_chunk_size = chunk_size
    if total_rows > 500000:
        chunk_size = min(5000, chunk_size)  # Reduz para tabelas grandes
        print_log(f"[DATA] Chunk size ajustado para {chunk_size:,} (tabela grande)")

    try:
        # Lê dados em chunks do MySQL
        print_log(f"[DATA] Lendo dados do MySQL em chunks de {chunk_size:,}...")

        # Query completa da tabela
        query = f"SELECT * FROM `{table_name}`"

        migrated_rows = 0
        failed_chunks = 0
        start_time = datetime.now()

        for chunk_num, chunk_df in enumerate(
            pd.read_sql(query, mysql_engine, chunksize=chunk_size), 1
        ):
            chunk_start = datetime.now()

            try:
                if logger:
                    logger.log(
                        f"[CHUNK {chunk_num}] Processando {len(chunk_df):,} registros..."
                    )

                # Converte tipos de dados para SQLite
                chunk_df = prepare_dataframe_for_sqlite(
                    chunk_df, table_name, mysql_table
                )

                # Escreve no SQLite com batch size menor para evitar erros
                batch_size = min(1000, len(chunk_df))

                if logger:
                    logger.log(
                        f"[CHUNK {chunk_num}] Inserindo no SQLite (batch_size={batch_size})..."
                    )

                # Sempre usar 'append' já que a tabela foi criada com schema correto
                chunk_df.to_sql(
                    name=table_name,
                    con=sqlite_engine,
                    if_exists="append",  # Sempre append, tabela já existe com schema correto
                    index=False,
                    chunksize=batch_size,
                    method="multi",
                )

                migrated_rows += len(chunk_df)

                # Calcula estatísticas
                elapsed = (datetime.now() - start_time).total_seconds()
                chunk_time = (datetime.now() - chunk_start).total_seconds()
                rows_per_sec = migrated_rows / elapsed if elapsed > 0 else 0
                eta_seconds = (
                    (total_rows - migrated_rows) / rows_per_sec
                    if rows_per_sec > 0
                    else 0
                )
                eta_str = (
                    f"{int(eta_seconds//60)}m {int(eta_seconds%60)}s"
                    if eta_seconds > 0
                    else "calculando..."
                )

                # Progress bar
                progress_pct = migrated_rows / total_rows * 100
                bar_length = 40
                filled = int(bar_length * migrated_rows / total_rows)
                bar = "█" * filled + "░" * (bar_length - filled)

                progress_msg = (
                    f"[DATA] [{bar}] {progress_pct:.1f}% | "
                    f"{migrated_rows:,}/{total_rows:,} | "
                    f"{rows_per_sec:.0f} rows/s | "
                    f"ETA: {eta_str} | "
                    f"Chunk: {chunk_time:.1f}s"
                )
                print_log(progress_msg)

            except Exception as chunk_error:
                failed_chunks += 1
                error_msg = f"Chunk {chunk_num} falhou: {chunk_error}"
                if logger:
                    logger.error(error_msg, chunk_error)
                else:
                    print(f"[ERRO] {error_msg}")

                # Se muitos chunks falharem, para
                if failed_chunks > 3:
                    msg = f"Muitos chunks falharam ({failed_chunks}), abortando tabela"
                    print_log(f"[ERRO] {msg}")
                    raise Exception(msg)

        print_log(f"[DATA] ✓ Tabela {table_name} migrada: {migrated_rows:,} registros")
        if failed_chunks > 0:
            print_log(f"[AVISO] {failed_chunks} chunks falharam durante a migração")
        return migrated_rows

    except Exception as e:
        error_msg = f"Falha ao migrar {table_name}: {e}"
        if logger:
            logger.error(error_msg, e)
        else:
            print(f"[ERRO] {error_msg}")
            import traceback

            traceback.print_exc()
        return 0


def verify_migration(mysql_engine, sqlite_engine, table_name):
    """Verifica se a migração foi bem-sucedida comparando contagens."""
    mysql_count = get_table_row_count(mysql_engine, table_name)
    sqlite_count = get_table_row_count(sqlite_engine, table_name)

    if mysql_count == sqlite_count:
        print_log(f"[VERIFY] ✓ {table_name}: {mysql_count:,} registros (OK)")
        return True
    else:
        print_log(
            f"[VERIFY] ✗ {table_name}: MySQL={mysql_count:,}, SQLite={sqlite_count:,} (DIVERGÊNCIA)"
        )
        return False


def main():
    """Função principal de migração."""
    global logger

    # Inicializa o logger
    logger = DebugLogger("debug.txt")

    print_log("=" * 80)
    print_log("MIGRAÇÃO MySQL -> SQLite")
    print_log("=" * 80)
    print_log(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Verifica se banco SQLite existe e pergunta se deseja deletar
        db_path = get_db_path()

        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            print_log(f"\n⚠️  Banco SQLite existente encontrado: {db_path}")
            print_log(f"    Tamanho: {size_mb:.2f} MB")

            delete = (
                input("\n🗑️  Deseja DELETAR o banco existente e criar do zero? (s/n): ")
                .lower()
                .strip()
            )

            if delete == "s":
                print_log(f"\n[DELETE] Deletando banco existente...")
                os.remove(db_path)
                print_log(f"[DELETE] ✓ Banco deletado com sucesso")
            else:
                print_log(
                    f"\n[INFO] Mantendo banco existente - apenas tabelas novas serão criadas"
                )

        # Conecta aos bancos
        print_log("\n[1] Conectando aos bancos de dados...")
        mysql_engine = get_mysql_engine()
        sqlite_engine = get_engine_sqlite()

        print_log(f"[SQLite] Arquivo do banco: {db_path}")

        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / 1024 / 1024
            print_log(f"[SQLite] Tamanho atual: {size_mb:.2f} MB")
        else:
            print_log("[SQLite] Banco novo será criado")

        # Lista tabelas do MySQL
        print_log("\n[2] Listando tabelas do MySQL...")
        tables = get_mysql_tables(mysql_engine)

        if not tables:
            print_log("[ERRO] Nenhuma tabela encontrada no MySQL!")
            return

        # Pergunta confirmação
        print_log(f"\n[CONFIRMAÇÃO] Serão migradas {len(tables)} tabelas.")
        confirm = input("Deseja continuar? (s/n): ").lower().strip()

        if confirm != "s":
            print_log("[CANCELADO] Migração cancelada pelo usuário.")
            return

        # Migra cada tabela
        print_log("\n[3] Iniciando migração de tabelas...")
        print_log("=" * 80)

        migration_summary = {}
        total_start = datetime.now()

        # Verifica quais tabelas já foram migradas
        print_log("\n[VERIFICAÇÃO] Checando tabelas já migradas...")
        sqlite_metadata = MetaData()
        sqlite_metadata.reflect(bind=sqlite_engine)
        already_migrated = set(sqlite_metadata.tables.keys())

        if already_migrated:
            print_log(f"[INFO] {len(already_migrated)} tabelas já existem no SQLite:")
            for table in sorted(already_migrated):
                count = get_table_row_count(sqlite_engine, table)
                print_log(f"  - {table}: {count:,} registros")

            skip_existing = (
                input("\n[OPÇÃO] Pular tabelas já migradas? (s/n): ").lower().strip()
            )
            if skip_existing == "s":
                tables = [t for t in tables if t not in already_migrated]
                print_log(f"[INFO] {len(tables)} tabelas restantes para migrar")

        for idx, table in enumerate(tables, 1):
            print_log(f"\n{'='*80}")
            print_log(f"Tabela {idx}/{len(tables)}: {table}")
            print_log(f"{'='*80}")

            table_start = datetime.now()

            # Migra esquema e dados
            try:
                mysql_table = migrate_table_schema(mysql_engine, sqlite_engine, table)
                rows_migrated = migrate_table_data(
                    mysql_engine, sqlite_engine, table, mysql_table
                )

                # Verifica migração
                verification_ok = verify_migration(mysql_engine, sqlite_engine, table)

                table_duration = (datetime.now() - table_start).total_seconds()

                migration_summary[table] = {
                    "rows": rows_migrated,
                    "duration": table_duration,
                    "verified": verification_ok,
                }

                print_log(f"[TEMPO] Tabela {table} concluída em {table_duration:.2f}s")

            except Exception as e:
                print_log(f"[ERRO] Falha crítica na tabela {table}: {e}")
                migration_summary[table] = {
                    "rows": 0,
                    "duration": 0,
                    "verified": False,
                    "error": str(e),
                }

        # Resumo final
        total_duration = (datetime.now() - total_start).total_seconds()

        print_log("\n" + "=" * 80)
        print_log("RESUMO DA MIGRAÇÃO")
        print_log("=" * 80)

        total_rows = sum(info["rows"] for info in migration_summary.values())
        successful_tables = sum(
            1 for info in migration_summary.values() if info["verified"]
        )
        failed_tables = len(migration_summary) - successful_tables

        print_log(f"\nTabelas processadas: {len(migration_summary)}")
        print_log(f"  ✓ Sucesso: {successful_tables}")
        print_log(f"  ✗ Falhas: {failed_tables}")
        print_log(f"\nTotal de registros migrados: {total_rows:,}")
        print_log(f"Tempo total: {total_duration:.2f}s ({total_duration/60:.2f} min)")

        if total_duration > 0:
            print_log(
                f"Velocidade média: {total_rows/total_duration:.0f} registros/segundo"
            )

        if os.path.exists(db_path):
            final_size = os.path.getsize(db_path) / 1024 / 1024
            print_log(f"Tamanho final do banco SQLite: {final_size:.2f} MB")

        print_log("\nDetalhes por tabela:")
        print_log(f"{'Tabela':<30} {'Status':<10} {'Registros':<15} {'Tempo':<12}")
        print_log("-" * 70)

        for table, info in sorted(migration_summary.items()):
            status = "✓ OK" if info["verified"] else "✗ FALHOU"
            rows_str = f"{info['rows']:,}"
            time_str = f"{info['duration']:.1f}s"

            print_log(f"{table:<30} {status:<10} {rows_str:<15} {time_str:<12}")

            if "error" in info:
                print_log(f"  └─ Erro: {info['error'][:60]}...")

        # Lista tabelas que falharam
        if failed_tables > 0:
            print_log("\n⚠️  TABELAS COM FALHAS:")
            for table, info in migration_summary.items():
                if not info["verified"]:
                    print_log(f"  - {table}")
                    if "error" in info:
                        print_log(f"    Erro: {info['error']}")
        else:
            print_log("\n✓ Todas as tabelas foram migradas com sucesso!")

        print_log("\n" + "=" * 80)
        print_log(f"Término: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print_log("=" * 80)

        # Fecha conexões
        mysql_engine.dispose()
        sqlite_engine.dispose()

    except Exception as main_error:
        logger.error("Erro fatal na migração", main_error)
        raise
    finally:
        # Fecha o logger
        if logger:
            logger.close()
            print(f"\n✓ Log detalhado salvo em: debug.txt")


if __name__ == "__main__":
    main()
