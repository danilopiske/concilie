"""
Script para criar banco SQLite limpo para distribuição do Concilie v2.0

Migra APENAS TABELAS:
1. TODAS as tabelas do MySQL (estrutura + dados)
2. EXCETO as 7 tabelas de trabalho (apenas estrutura vazia):
   - recebiveis_filtrados
   - recebiveis_processados
   - vendas_calculos
   - vendas_diversas
   - vendas_filtradas
   - vendas_processadas
   - controle_processamentos

VIEWS: Não são migradas por este script (migração manual)
"""

import sqlite3
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool
from pathlib import Path
from urllib.parse import quote_plus

# Configurações
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'C0nc!l!3@123#',
    'database': 'concilie',
    'port': 3306
}

# Banco SQLite será criado em data/
DATA_DIR = Path('data')
SQLITE_DB = DATA_DIR / 'concilie.db'

# Tabelas que serão criadas VAZIAS (apenas estrutura, sem dados)
EMPTY_TABLES = {
    'recebiveis_filtrados',
    'recebiveis_processados', 
    'vendas_calculos',
    'vendas_diversas',
    'vendas_filtradas',
    'vendas_processadas',
    'controle_processamentos'
}

def get_mysql_engine():
    """Cria engine MySQL"""
    password_encoded = quote_plus(MYSQL_CONFIG['password'])
    conn_str = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{password_encoded}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    return create_engine(conn_str, poolclass=NullPool, echo=False)

def get_sqlite_engine():
    """Cria engine SQLite"""
    # Garantir que data/ existe
    DATA_DIR.mkdir(exist_ok=True)
    
    if SQLITE_DB.exists():
        print(f"⚠️  Removendo banco existente: {SQLITE_DB}")
        SQLITE_DB.unlink()
    
    conn_str = f"sqlite:///{SQLITE_DB}"
    return create_engine(conn_str, poolclass=NullPool, echo=False)

def convert_type_to_sqlite(mysql_type: str) -> str:
    """Converte tipo MySQL para SQLite"""
    type_str = str(mysql_type).upper()
    
    if 'INT' in type_str or 'SERIAL' in type_str:
        return 'INTEGER'
    elif any(x in type_str for x in ['DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL']):
        return 'REAL'
    elif any(x in type_str for x in ['DATE', 'TIME']):
        return 'TEXT'
    elif any(x in type_str for x in ['TEXT', 'CHAR', 'VARCHAR', 'CLOB']):
        return 'TEXT'
    elif any(x in type_str for x in ['BLOB', 'BINARY']):
        return 'BLOB'
    else:
        return 'TEXT'

def get_table_ddl(mysql_engine, table_name: str) -> str:
    """Gera DDL CREATE TABLE para SQLite"""
    inspector = inspect(mysql_engine)
    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name)
    indexes = inspector.get_indexes(table_name)
    foreign_keys = inspector.get_foreign_keys(table_name)
    
    ddl_lines = [f"CREATE TABLE {table_name} ("]
    col_defs = []
    
    pk_cols = pk.get('constrained_columns', [])
    
    for col in columns:
        name = col['name']
        sqlite_type = convert_type_to_sqlite(col['type'])
        
        col_def = f"  {name} {sqlite_type}"
        
        # PRIMARY KEY (único)
        if name in pk_cols and len(pk_cols) == 1:
            col_def += " PRIMARY KEY"
            if sqlite_type == 'INTEGER' and col.get('autoincrement'):
                col_def += " AUTOINCREMENT"
        
        # NOT NULL
        if not col.get('nullable', True):
            col_def += " NOT NULL"
        
        # DEFAULT
        default = col.get('default')
        if default is not None:
            if isinstance(default, str):
                if default.upper() in ('CURRENT_TIMESTAMP', 'NOW()'):
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
                else:
                    # Remove aspas extras se já existirem
                    clean_default = default.strip("'\"")
                    # Para INTEGER, não usar aspas
                    if sqlite_type == 'INTEGER' and clean_default.isdigit():
                        col_def += f" DEFAULT {clean_default}"
                    else:
                        col_def += f" DEFAULT '{clean_default}'"
            else:
                col_def += f" DEFAULT {default}"
        
        col_defs.append(col_def)
    
    # PRIMARY KEY composta
    if len(pk_cols) > 1:
        col_defs.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")
    
    # FOREIGN KEYS
    for fk in foreign_keys:
        fk_cols = ', '.join(fk['constrained_columns'])
        ref_table = fk['referred_table']
        ref_cols = ', '.join(fk['referred_columns'])
        col_defs.append(f"  FOREIGN KEY ({fk_cols}) REFERENCES {ref_table}({ref_cols})")
    
    ddl_lines.append(",\n".join(col_defs))
    ddl_lines.append(");")
    
    ddl = "\n".join(ddl_lines)
    
    # Índices
    for idx in indexes:
        if idx['name'] != 'PRIMARY':
            cols = ', '.join(idx['column_names'])
            unique = 'UNIQUE ' if idx.get('unique') else ''
            # Criar nome único para o índice: idx_tabela_nome_original
            idx_name = f"idx_{table_name}_{idx['name']}"
            ddl += f"\nCREATE {unique}INDEX {idx_name} ON {table_name} ({cols});"
    
    return ddl

def migrate_table_data(mysql_engine, sqlite_engine, table_name: str):
    """Migra dados de uma tabela"""
    from decimal import Decimal
    
    with mysql_engine.connect() as mysql_conn:
        result = mysql_conn.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.mappings().all()
        
        if not rows:
            return 0
        
        # Usar conexão raw do SQLite para inserir com placeholders posicionais
        raw_conn = sqlite_engine.raw_connection()
        cursor = raw_conn.cursor()
        
        try:
            cols = list(rows[0].keys())
            placeholders = ', '.join(['?' for _ in cols])
            col_names = ', '.join(cols)
            
            insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
            
            for row in rows:
                values = []
                for col in cols:
                    val = row[col]
                    # Converter Decimal para float (SQLite não suporta Decimal)
                    if isinstance(val, Decimal):
                        val = float(val)
                    values.append(val)
                
                cursor.execute(insert_sql, values)
            
            raw_conn.commit()
            return len(rows)
        finally:
            cursor.close()
            raw_conn.close()

def get_all_tables(mysql_engine) -> list:
    """Lista todas as TABELAS do MySQL (excluindo views)"""
    with mysql_engine.connect() as conn:
        result = conn.execute(text(f"SHOW FULL TABLES IN {MYSQL_CONFIG['database']} WHERE Table_type = 'BASE TABLE'"))
        return [row[0] for row in result.fetchall()]

def main():
    print("=" * 80)
    print("CONCILIE - MIGRAÇÃO MYSQL → SQLITE")
    print("=" * 80)
    print()
    
    try:
        # Conectar
        print("[1/4] Conectando ao MySQL...")
        mysql_engine = get_mysql_engine()
        print(f"  ✅ MySQL: {MYSQL_CONFIG['database']}")
        
        print("\n[2/4] Criando banco SQLite...")
        sqlite_engine = get_sqlite_engine()
        print(f"  ✅ SQLite: {SQLITE_DB}")
        
        # Obter todas as tabelas
        all_tables = get_all_tables(mysql_engine)
        migrate_tables = [t for t in all_tables if t not in EMPTY_TABLES]
        
        print(f"\n[3/4] Migrando tabelas...")
        print(f"  📋 Total: {len(all_tables)} tabelas")
        print(f"  📊 Com dados: {len(migrate_tables)} tabelas")
        print(f"  📝 Vazias: {len(EMPTY_TABLES)} tabelas")
        print()
        
        # Tabelas COM dados
        for i, table in enumerate(migrate_tables, 1):
            print(f"  [{i}/{len(migrate_tables)}] {table}")
            
            with sqlite_engine.connect() as conn:
                # Criar estrutura
                ddl = get_table_ddl(mysql_engine, table)
                for stmt in ddl.split(';'):
                    if stmt.strip():
                        conn.execute(text(stmt))
                conn.commit()
                print(f"      ✅ Estrutura criada")
                
                # Migrar dados (pular views - começam com vw_)
                if table.startswith('vw_'):
                    print(f"      ℹ️  View - dados não migrados")
                else:
                    count = migrate_table_data(mysql_engine, sqlite_engine, table)
                    print(f"      ✅ {count} registros migrados")
        
        # Tabelas VAZIAS (apenas estrutura)
        print(f"\n  Criando tabelas vazias ({len(EMPTY_TABLES)} tabelas)...")
        for i, table in enumerate(sorted(EMPTY_TABLES), 1):
            print(f"  [{i}/{len(EMPTY_TABLES)}] {table}")
            
            with sqlite_engine.connect() as conn:
                ddl = get_table_ddl(mysql_engine, table)
                for stmt in ddl.split(';'):
                    if stmt.strip():
                        conn.execute(text(stmt))
                conn.commit()
                print(f"      ✅ Estrutura criada (vazia)")
        
        # Resumo
        print("\n[4/4] Finalizando...")
        print("\n" + "=" * 80)
        print("✅ MIGRAÇÃO DE TABELAS CONCLUÍDA!")
        print("=" * 80)
        
        inspector = inspect(sqlite_engine)
        final_tables = inspector.get_table_names()
        
        print(f"\n📊 Estatísticas:")
        print(f"  • Tabelas criadas: {len(final_tables)}")
        print(f"\n📁 Arquivo: {SQLITE_DB.absolute()}")
        print(f"📦 Tamanho: {SQLITE_DB.stat().st_size / 1024:.2f} KB")
        print()
        
        # Contagem de registros nas principais tabelas
        print("📋 Registros migrados:")
        with sqlite_engine.connect() as conn:
            for table in ['usuarios', 'empresas', 'clientes']:
                if table in final_tables:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    print(f"  • {table}: {count}")
        
        print()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
