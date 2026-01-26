import sys
import os
from sqlalchemy import create_engine, text

try:
    sys.path.append(os.getcwd())
    from apps.api.app.core.database import engine
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))
    from apps.api.app.core.database import engine

def debug_locks():
    print("Checking locks and processes...")
    with engine.connect() as conn:
        # Check process list
        res = conn.execute(text("SHOW FULL PROCESSLIST")).fetchall()
        print("\n--- Processes > 10s ---")
        for row in res:
            if row[5] > 10: 
                print(f"ID: {row[0]}, Time: {row[5]}, State: {row[6]}, Info: {row[7]}")
                if "DELETE" in str(row[7]):
                    print(f"!!! Found stuck DELETE process {row[0]}, killing it...")
                    try:
                        conn.execute(text(f"KILL {row[0]}"))
                        print("Killed.")
                    except Exception as e:
                        print(f"Failed to kill: {e}")

        # Re-verify index on vendas_calculos
        print("\n--- Indexes on vendas_calculos ---")
        res = conn.execute(text("SHOW INDEX FROM vendas_calculos")).fetchall()
        for row in res:
            if row[4] == 'calc_id':
                print(f"Index on calc_id found: {row[2]}")

if __name__ == "__main__":
    debug_locks()
