import sys
import os
from sqlalchemy import create_engine, text

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))
from app.core.config import settings
from urllib.parse import quote_plus

encoded_password = quote_plus(settings.MYSQL_PASSWORD)
db_url = f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

engine = create_engine(db_url)

with engine.connect() as conn:
    print("\n--- Tables in Database ---")
    tables = conn.execute(text("SHOW TABLES")).fetchall()
    for table in tables:
        print(table[0])
        
    print("\n--- Columns in controle_processamentos (if exists) ---")
    try:
        columns = conn.execute(text("DESCRIBE controle_processamentos")).fetchall()
        for col in columns:
            print(f"{col[0]} ({col[1]})")
    except Exception as e:
        print(f"Table controle_processamentos not found or error: {e}")

    print("\n--- Columns in processamentos (if exists) ---")
    try:
        columns = conn.execute(text("DESCRIBE processamentos")).fetchall()
        for col in columns:
            print(f"{col[0]} ({col[1]})")
    except Exception as e:
        print(f"Table processamentos not found or error: {e}")
