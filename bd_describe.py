from sqlalchemy import text
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import json
import os


def engine_bd():
    """Cria engine para o banco de dados local concilie"""
    USUARIO = "root"
    SENHA = quote_plus("C0nc!l!3@123#")
    HOST = "localhost"
    PORTA = 3306
    BANCO = "concilie"

    engine = create_engine(
        f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}",
        pool_pre_ping=True,
        pool_recycle=1800,
    )

    return engine


print("Conectando ao banco de dados local 'concilie'...")

engine = engine_bd()

with engine.begin() as conn:
    # Obter todas as tabelas
    print("Obtendo lista de tabelas...")
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result.fetchall()]

    print(f"Encontradas {len(tables)} tabelas: {', '.join(tables)}")

    db_structure = {}
    for table in tables:
        print(f"  Descrevendo tabela: {table}")
        describe_result = conn.execute(text(f"DESCRIBE {table}"))
        columns = [dict(row._mapping) for row in describe_result.fetchall()]
        db_structure[table] = columns

# Criar diretório se não existir
os.makedirs("bd_structures", exist_ok=True)

# Salvar em arquivo
filename = "bd_structures/db_structure_concilie.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(db_structure, f, indent=4, ensure_ascii=False)

print(f"\n✅ Estrutura do banco 'concilie' salva em: {filename}")
print(f"Total de tabelas processadas: {len(tables)}")
