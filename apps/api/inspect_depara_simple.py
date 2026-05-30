import sqlite3
import os

db_path = r"d:\Financial  base\Financial_P\financial_.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM depara_colunas")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    print(f"Total rows: {len(rows)}")
    issues_found = False
    
    for row in rows:
        row_dict = dict(zip(columns, row))
        issues = []
        # Check required fields based on Schema
        if row_dict.get('destino_nome') is None: issues.append("destino_nome is NULL")
        if row_dict.get('contexto') is None: issues.append("contexto is NULL")
        if row_dict.get('tipo_origem') is None: issues.append("tipo_origem is NULL")
        # tipo_preenchimento is critical because default is "importado" but DB might have NULL
        if row_dict.get('tipo_preenchimento') is None: issues.append("tipo_preenchimento is NULL")
        
        if issues:
            issues_found = True
            print(f"ID {row_dict.get('id')}: {issues}")

    if not issues_found:
        print("No validation issues found in critical columns.")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
