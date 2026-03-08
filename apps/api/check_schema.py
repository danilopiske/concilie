from app.core.database import SessionLocal
from sqlalchemy import text

with SessionLocal() as db:
    result = db.execute(text("SHOW CREATE TABLE vendas_processadas")).fetchone()
    with open("schema.txt", "w", encoding="utf-8") as f:
        f.write(result[1])
    print("Schema written to schema.txt")
