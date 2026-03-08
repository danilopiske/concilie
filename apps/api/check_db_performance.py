import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_SERVER = os.getenv("MYSQL_SERVER", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "concilie")

def check_performance():
    try:
        conn = pymysql.connect(
            host=MYSQL_SERVER,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        cursor = conn.cursor()
        
        tables = ["vendas_processadas", "vendas_filtradas", "controle_processamentos", "recebiveis_processados"]
        
        print(f"{'Table':<30} | {'Rows':<15} | {'Indexes'}")
        print("-" * 80)
        
        for table in tables:
            try:
                # Count rows
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                rows = cursor.fetchone()[0]
                
                # Check indexes
                cursor.execute(f"SHOW INDEX FROM {table}")
                indexes = cursor.fetchall()
                index_info = [f"{idx[2]}:{idx[4]}" for idx in indexes]
                
                print(f"Table: {table}")
                print(f"Rows: {rows:,}")
                print(f"Indexes: {', '.join(index_info)}")
                print("-" * 20)
                
            except Exception as e:
                print(f"Error checking {table}: {e}")
                
        # Check slow processes
        print("\nActive processes (showing long-running):")
        cursor.execute("SHOW PROCESSLIST")
        procs = cursor.fetchall()
        for proc in procs:
            if proc[5] > 10: # Time > 10s
                print(proc)
                
        conn.close()
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_performance()
