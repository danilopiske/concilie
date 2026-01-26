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

def check_all():
    print("Checking ALL indexes...")
    tables = [
        "vendas_calculos", 
        "recebiveis_processados", 
        "recebiveis_filtrados"
    ]
    
    with engine.connect() as conn:
        for table in tables:
            print(f"\n--- Indexes on {table} ---")
            try:
                res = conn.execute(text(f"SHOW INDEX FROM {table}")).fetchall()
                for row in res:
                    print(f"Key_name: {row[2]}, Column_name: {row[4]}")
            except Exception as e:
                print(f"Error checking {table}: {e}")

        print("\n--- Long Running Processes ---")
        try:
            res = conn.execute(text("SHOW FULL PROCESSLIST")).fetchall()
            for row in res:
                if row[5] > 0: # Time > 0
                    print(f"ID: {row[0]}, Time: {row[5]}, State: {row[6]}, Info: {row[7]}")
        except Exception as e:
            print(f"Error checking processlist: {e}")

if __name__ == "__main__":
    check_all()
