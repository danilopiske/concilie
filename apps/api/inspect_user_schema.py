from sqlalchemy import text
from app.core.database import SessionLocal

def inspect_user_table():
    db = SessionLocal()
    try:
        # Check for 'usuarios' or 'usuarioos'
        tables = db.execute(text("SHOW TABLES LIKE 'usuari%'")).fetchall()
        for t in tables:
            table_name = t[0]
            print(f"TABLE: {table_name}")
            cols = db.execute(text(f"DESCRIBE {table_name}")).fetchall()
            for c in cols:
                # Field, Type, Null, Key, Default, Extra
                print(f"  - {c[0]} ({c[1]})")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_user_table()
