from app.core.database import SessionLocal
from sqlalchemy import text

with SessionLocal() as db:
    try:
        db.execute(text("KILL 42"))
        print("Killed thread 42")
    except Exception as e:
        print("Error killing thread 42:", e)
        
    try:
        # Just in case, kill any long running queries
        res = db.execute(text("SELECT id, time, state, info FROM information_schema.processlist WHERE time > 50")).fetchall()
        for r in res:
            print(f"Long running: {r}")
            if r.id != db.execute(text("SELECT CONNECTION_ID()")).scalar():
                db.execute(text(f"KILL {r.id}"))
                print(f"Killed {r.id}")
    except Exception as e:
        print("Error checking processlist:", e)
