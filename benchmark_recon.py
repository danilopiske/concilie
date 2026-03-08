import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))
sys.path.append(str(Path.cwd() / "apps" / "api"))

# Force SQLite for benchmark
import os
os.environ["DATABASE_TYPE"] = "sqlite"

from app.core.database import engine
from modules.reconciliation_core import ReconciliationCore
import time

def run_benchmark():
    print("Starting Reconciliation Benchmark (Polars Edition)")
    print("-" * 50)
    
    # Let's find a valid processamentoid first
    from sqlalchemy import text
    with engine.connect() as conn:
        res = conn.execute(text("SELECT DISTINCT processamentoid FROM vendas_processadas LIMIT 1")).fetchone()
        if not res:
            print("No data found in vendas_processadas. Cannot run benchmark.")
            return
        proc_id = res[0]
        print(f"Using Processamento ID: {proc_id}")

    # Run Benchmark
    start_time = time.time()
    result = ReconciliationCore.calculate_rates(
        engine=engine,
        proc_id=proc_id,
        tipo_taxa="log_mensal",
        usar_taxa_cad=True,
        tem_receba_rapido=False
    )
    end_time = time.time()
    
    if result["success"]:
        print("\nBENCHMARK COMPLETED")
        print(f"Total Time: {end_time - start_time:.4f} seconds")
        print(f"Rows Processed: {result['rows']}")
        print(f"Speed: {result['rows'] / (end_time - start_time):.0f} rows/sec")
    else:
        print(f"\nBENCHMARK FAILED: {result['error']}")

if __name__ == "__main__":
    run_benchmark()
