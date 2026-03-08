from app.core.database import SessionLocal
from sqlalchemy import text
import pprint

with SessionLocal() as db:
    result = db.execute(text("SELECT * FROM information_schema.innodb_trx")).fetchall()
    
    print(f"Active transactions: {len(result)}")
    for r in result:
        pprint.pprint(dict(r._mapping))
