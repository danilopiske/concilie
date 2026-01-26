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

def check_rec():
    print("Checking receivables...")
    with engine.connect() as conn:
        tables = ["recebiveis_processados", "recebiveis_filtrados"]
        for t in tables:
            print(f"\n--- {t} ---")
            # Indexes
            try:
                res = conn.execute(text(f"SHOW INDEX FROM {t}")).fetchall()
                found = False
                for row in res:
                    if row[4] == 'processamentoid':
                        print(f"Index on processamentoid found: {row[2]}")
                        found = True
                if not found:
                    print("!!! INDEX ON processamentoid MISSING !!!")
                    try:
                        print(f"Creating index on {t}...")
                        conn.execute(text(f"CREATE INDEX idx_{t}_proc ON {t} (processamentoid)"))
                        print("Created.")
                    except Exception as e:
                        print(f"Error creating: {e}")
            except Exception as e:
                print(f"Error checking indexes: {e}")

        # Check counts for a sample stuck ID if known, or just top processors
        print("\n--- Data Volume Check ---")
        try:
            sql = "SELECT processamentoid, COUNT(*) as qtd FROM vendas_processadas GROUP BY processamentoid ORDER BY qtd DESC LIMIT 5"
            res = conn.execute(text(sql)).fetchall()
            print("Top 5 largest processamentos (vendas):")
            for r in res:
                print(f"PID: {r[0]} - Count: {r[1]}")
        except:
             pass

if __name__ == "__main__":
    check_rec()
