from sqlalchemy import create_engine, text
from app.core.config import settings

# Override settings to force sqlite path if needed, but assuming env is correct
# db_url = "sqlite:///d:/Financial  base/Financial_P/financial_.db"
db_url = "sqlite:///d:/Financial  base/Financial_P/financial_.db"

engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM depara_colunas"))
    columns = result.keys()
    rows = result.fetchall()
    
    print(f"Total rows: {len(rows)}")
    for row in rows:
        row_dict = dict(zip(columns, row))
        # Check for potential nulls in required fields
        issues = []
        if not row_dict.get('destino_nome'): issues.append("destino_nome is null/empty")
        if not row_dict.get('contexto'): issues.append("contexto is null/empty")
        if not row_dict.get('tipo_origem'): issues.append("tipo_origem is null/empty")
        if not row_dict.get('tipo_preenchimento'): issues.append("tipo_preenchimento is null/empty")
        
        if issues:
            print(f"ID {row_dict.get('id')}: {issues} - Row: {row_dict}")
