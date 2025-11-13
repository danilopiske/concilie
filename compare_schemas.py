"""
Script para comparar schemas completos de MySQL e SQLite
"""

import json
import pandas as pd
from conf.db_manager import get_engine, set_db_mode
from sqlalchemy import inspect, text


def get_mysql_schema():
    """Extrai schema completo do MySQL"""
    set_db_mode("mysql")
    engine = get_engine()
    inspector = inspect(engine)

    schema = {}

    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            col_info = {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": str(col["default"]) if col["default"] is not None else None,
                "autoincrement": col.get("autoincrement", False),
            }
            columns.append(col_info)

        # Pegar primary keys
        pk = inspector.get_pk_constraint(table_name)

        # Pegar indexes
        indexes = []
        for idx in inspector.get_indexes(table_name):
            indexes.append(
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"],
                }
            )

        schema[table_name] = {
            "columns": columns,
            "primary_key": pk["constrained_columns"] if pk else [],
            "indexes": indexes,
        }

    return schema


def get_sqlite_schema():
    """Extrai schema completo do SQLite"""
    set_db_mode("sqlite")
    engine = get_engine()
    inspector = inspect(engine)

    schema = {}

    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            col_info = {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": str(col["default"]) if col["default"] is not None else None,
                "autoincrement": col.get("autoincrement", False),
            }
            columns.append(col_info)

        # Pegar primary keys
        pk = inspector.get_pk_constraint(table_name)

        # Pegar indexes
        indexes = []
        for idx in inspector.get_indexes(table_name):
            indexes.append(
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"],
                }
            )

        schema[table_name] = {
            "columns": columns,
            "primary_key": pk["constrained_columns"] if pk else [],
            "indexes": indexes,
        }

    return schema


def compare_schemas(mysql_schema, sqlite_schema):
    """Compara os schemas e retorna diferenças"""
    differences = {
        "tables_only_in_mysql": [],
        "tables_only_in_sqlite": [],
        "column_differences": {},
        "type_differences": {},
        "primary_key_differences": {},
    }

    mysql_tables = set(mysql_schema.keys())
    sqlite_tables = set(sqlite_schema.keys())

    differences["tables_only_in_mysql"] = list(mysql_tables - sqlite_tables)
    differences["tables_only_in_sqlite"] = list(sqlite_tables - mysql_tables)

    # Comparar tabelas comuns
    common_tables = mysql_tables & sqlite_tables

    for table in sorted(common_tables):
        mysql_table = mysql_schema[table]
        sqlite_table = sqlite_schema[table]

        mysql_cols = {col["name"]: col for col in mysql_table["columns"]}
        sqlite_cols = {col["name"]: col for col in sqlite_table["columns"]}

        mysql_col_names = set(mysql_cols.keys())
        sqlite_col_names = set(sqlite_cols.keys())

        # Colunas diferentes
        if mysql_col_names != sqlite_col_names:
            differences["column_differences"][table] = {
                "only_in_mysql": list(mysql_col_names - sqlite_col_names),
                "only_in_sqlite": list(sqlite_col_names - mysql_col_names),
            }

        # Tipos diferentes
        type_diffs = []
        for col_name in mysql_col_names & sqlite_col_names:
            mysql_type = mysql_cols[col_name]["type"]
            sqlite_type = sqlite_cols[col_name]["type"]

            # Normalizar tipos para comparação
            mysql_type_normalized = mysql_type.upper()
            sqlite_type_normalized = sqlite_type.upper()

            # Mapeamento de tipos equivalentes
            type_mapping = {
                "DECIMAL": ["NUMERIC", "REAL"],
                "VARCHAR": ["TEXT"],
                "INT": ["INTEGER"],
                "TINYINT": ["INTEGER"],
                "DATETIME": ["TEXT", "TIMESTAMP"],
                "LONGTEXT": ["TEXT"],
                "TEXT": ["TEXT", "VARCHAR"],
            }

            is_equivalent = False
            for mysql_base, sqlite_equivalents in type_mapping.items():
                if mysql_base in mysql_type_normalized:
                    if any(eq in sqlite_type_normalized for eq in sqlite_equivalents):
                        is_equivalent = True
                        break

            if not is_equivalent and mysql_type_normalized != sqlite_type_normalized:
                type_diffs.append(
                    {
                        "column": col_name,
                        "mysql_type": mysql_type,
                        "sqlite_type": sqlite_type,
                        "mysql_nullable": mysql_cols[col_name]["nullable"],
                        "sqlite_nullable": sqlite_cols[col_name]["nullable"],
                    }
                )

        if type_diffs:
            differences["type_differences"][table] = type_diffs

        # Primary keys diferentes
        if set(mysql_table["primary_key"]) != set(sqlite_table["primary_key"]):
            differences["primary_key_differences"][table] = {
                "mysql_pk": mysql_table["primary_key"],
                "sqlite_pk": sqlite_table["primary_key"],
            }

    return differences


def main():
    print("Extraindo schema do MySQL...")
    mysql_schema = get_mysql_schema()

    print("Extraindo schema do SQLite...")
    sqlite_schema = get_sqlite_schema()

    # Salvar schemas completos
    with open("mysql_schema.json", "w", encoding="utf-8") as f:
        json.dump(mysql_schema, f, indent=2, ensure_ascii=False)
    print("✅ Schema MySQL salvo em: mysql_schema.json")

    with open("sqlite_schema.json", "w", encoding="utf-8") as f:
        json.dump(sqlite_schema, f, indent=2, ensure_ascii=False)
    print("✅ Schema SQLite salvo em: sqlite_schema.json")

    # Comparar schemas
    print("\nComparando schemas...")
    differences = compare_schemas(mysql_schema, sqlite_schema)

    # Salvar diferenças
    with open("schema_differences.json", "w", encoding="utf-8") as f:
        json.dump(differences, f, indent=2, ensure_ascii=False)
    print("✅ Diferenças salvas em: schema_differences.json")

    # Exibir resumo
    print("\n" + "=" * 80)
    print("RESUMO DAS DIFERENÇAS")
    print("=" * 80)

    if differences["tables_only_in_mysql"]:
        print(
            f"\n⚠️  Tabelas apenas no MySQL ({len(differences['tables_only_in_mysql'])}):"
        )
        for table in differences["tables_only_in_mysql"]:
            print(f"  - {table}")

    if differences["tables_only_in_sqlite"]:
        print(
            f"\n⚠️  Tabelas apenas no SQLite ({len(differences['tables_only_in_sqlite'])}):"
        )
        for table in differences["tables_only_in_sqlite"]:
            print(f"  - {table}")

    if differences["column_differences"]:
        print(
            f"\n⚠️  Tabelas com colunas diferentes ({len(differences['column_differences'])}):"
        )
        for table, cols in differences["column_differences"].items():
            print(f"  - {table}:")
            if cols["only_in_mysql"]:
                print(f"    MySQL: {', '.join(cols['only_in_mysql'])}")
            if cols["only_in_sqlite"]:
                print(f"    SQLite: {', '.join(cols['only_in_sqlite'])}")

    if differences["type_differences"]:
        print(
            f"\n⚠️  Tabelas com tipos de dados diferentes ({len(differences['type_differences'])}):"
        )
        for table, type_diffs in differences["type_differences"].items():
            print(f"\n  📊 {table} ({len(type_diffs)} diferenças):")
            for diff in type_diffs[:5]:  # Mostrar apenas primeiras 5
                print(f"    - {diff['column']}:")
                print(
                    f"      MySQL:  {diff['mysql_type']} (nullable={diff['mysql_nullable']})"
                )
                print(
                    f"      SQLite: {diff['sqlite_type']} (nullable={diff['sqlite_nullable']})"
                )
            if len(type_diffs) > 5:
                print(f"    ... e mais {len(type_diffs) - 5} diferenças")

    if differences["primary_key_differences"]:
        print(
            f"\n⚠️  Tabelas com PKs diferentes ({len(differences['primary_key_differences'])}):"
        )
        for table, pks in differences["primary_key_differences"].items():
            print(f"  - {table}:")
            print(f"    MySQL:  {', '.join(pks['mysql_pk'])}")
            print(f"    SQLite: {', '.join(pks['sqlite_pk'])}")

    print("\n" + "=" * 80)
    print("✅ Comparação concluída!")
    print("=" * 80)


if __name__ == "__main__":
    main()
