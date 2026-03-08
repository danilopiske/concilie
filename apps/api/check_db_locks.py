from app.core.database import SessionLocal
from sqlalchemy import text

with SessionLocal() as db:
    result = db.execute(text("SHOW FULL PROCESSLIST")).fetchall()
    
    for r in result:
        print(dict(r._mapping))
