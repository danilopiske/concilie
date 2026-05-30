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

def fix_vc_index():
    print("Fixing vendas_calculos index...")
    with engine.connect() as conn:
        # Check if index exists
        print("Checking existing indexes on vendas_calculos...")
        res = conn.execute(text("SHOW INDEX FROM vendas_calculos WHERE Column_name = 'calc_id'")).fetchall()
        if res:
            print(f"Index exists: {res}")
        else:
            print("Index on calc_id MISSING. Creating it now...")
            try:
                conn.execute(text("CREATE INDEX idx_vc_calc_id ON vendas_calculos (calc_id)"))
                print("Index idx_vc_calc_id created successfully.")
            except Exception as e:
                print(f"Error creating index: {e}")

        # Kill stuck processes again just to be safe/clean slate
        print("Cleaning up stuck processes...")
        res = conn.execute(text("SHOW FULL PROCESSLIST")).fetchall()
        for row in res:
            if row[5] > 200 and "DELETE" in str(row[7]):
                 print(f"Killing {row[0]}...")
                 try:
                     conn.execute(text(f"KILL {row[0]}"))
                 except:
                     pass

if __name__ == "__main__":
    fix_vc_index()
