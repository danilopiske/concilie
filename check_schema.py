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

def check_schema():
    print("Checking schema...")
    with engine.connect() as conn:
        res = conn.execute(text("DESCRIBE recebiveis_processados")).fetchall()
        for row in res:
            if row[0] == 'processamentoid':
                print(f"recebiveis_processados.processamentoid: {row[1]}")
        
        res = conn.execute(text("DESCRIBE recebiveis_filtrados")).fetchall()
        for row in res:
             if row[0] == 'processamentoid':
                print(f"recebiveis_filtrados.processamentoid: {row[1]}")

if __name__ == "__main__":
    check_schema()
