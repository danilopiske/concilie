import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.core.config import settings
from app.models.legacy_depara import DeParaColunasLegacy

print(f"Connecting to: {settings.MYSQL_USER}@{settings.MYSQL_SERVER}/{settings.MYSQL_DB}")
print(f"Database Type: {settings.DATABASE_TYPE}")

# Force MySQL URL construction manually to be sure
from urllib.parse import quote_plus
encoded_password = quote_plus(settings.MYSQL_PASSWORD)
db_url = f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
print(f"URL: {db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    print("Querying DeParaColunasLegacy...")
    results = session.query(DeParaColunasLegacy).limit(5).all()
    print(f"Found {len(results)} rows.")
    for row in results:
        print(f"Row: {row.origem_nome} -> {row.destino_nome} ({row.contexto})")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    session.close()
