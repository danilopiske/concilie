import sqlite3
import os

# Path based on find_by_name result
db_path = r"d:\Financial Checker base\Financial_P\data\concilie.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='depara_colunas'")
    if not cursor.fetchone():
        print("Table 'depara_colunas' NOT FOUND")
    else:
        print("Table 'depara_colunas' FOUND")
        
        # Count rows
        cursor.execute("SELECT count(*) FROM depara_colunas")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        # Show sample data
        if count > 0:
            cursor.execute("SELECT * FROM depara_colunas LIMIT 5")
            cols = [d[0] for d in cursor.description]
            print(f"Columns: {cols}")
            for row in cursor.fetchall():
                print(dict(zip(cols, row)))

    # Check for depara_controle used by the new endpoint
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='depara_controle'")
    if cursor.fetchone():
        print("Table 'depara_controle' FOUND")
    else:
         print("Table 'depara_controle' NOT FOUND")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
