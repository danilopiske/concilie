
import pymysql
import os

def run_migration():
    try:
        conn = pymysql.connect(
            host='localhost', 
            user='root', 
            password='C0nc!l!3@123#', 
            database='concilie'
        )
        with conn.cursor() as cursor:
            print("Altering vendas_calculos...")
            cursor.execute('ALTER TABLE vendas_calculos MODIFY COLUMN ec_id BIGINT')
            
            print("Altering vendas_processadas (ensuring consistency)...")
            cursor.execute('ALTER TABLE vendas_processadas MODIFY COLUMN ec_id BIGINT')
            
            print("Altering vendas_filtradas...")
            cursor.execute('ALTER TABLE vendas_filtradas MODIFY COLUMN ec_id BIGINT')
            
            conn.commit()
            print("Successfully altered columns to BIGINT")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration()
