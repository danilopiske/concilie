
import sqlalchemy
from sqlalchemy import text
import sys
import os
from urllib.parse import quote_plus

# Database config from .env
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'C0nc!l!3@123#'
MYSQL_SERVER = 'localhost'
MYSQL_PORT = 3306
MYSQL_DB = 'concilie'

def check_schema():
    encoded_password = quote_plus(MYSQL_PASSWORD)
    url = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_SERVER}:{MYSQL_PORT}/{MYSQL_DB}"
    print(f"Connecting to: {MYSQL_SERVER}:{MYSQL_PORT}/{MYSQL_DB}")
    engine = sqlalchemy.create_engine(url)
    try:
        with engine.connect() as conn:
            print("\nTable: calculo_tasks")
            result = conn.execute(text("DESCRIBE calculo_tasks")).all()
            for row in result:
                print(row)
            
            print("\nTable: relatorio_tasks")
            result = conn.execute(text("DESCRIBE relatorio_tasks")).all()
            for row in result:
                print(row)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
