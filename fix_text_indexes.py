import sys
import os
from sqlalchemy import create_engine, text

# Add app to path
try:
    sys.path.append(os.getcwd())
    from apps.api.app.core.database import engine
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))
    from apps.api.app.core.database import engine

def fix_text_indexes():
    print("Fixing TEXT indexes...")
    with engine.connect() as conn:
        tables = ["recebiveis_processados", "recebiveis_filtrados"]
        for t in tables:
            print(f"Creating index on {t}...")
            try:
                # Specify length 100 for TEXT column indexing
                conn.execute(text(f"CREATE INDEX idx_{t}_proc ON {t} (processamentoid(100))"))
                print(f"Index idx_{t}_proc created.")
            except Exception as e:
                if "Duplicate key" in str(e) or "already exists" in str(e):
                    print("Index already exists.")
                else:
                    print(f"Error creating index: {e}")

if __name__ == "__main__":
    fix_text_indexes()
