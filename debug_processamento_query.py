import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.core.config import settings
from app.models.legacy_processamento import LegacyProcessamento
from datetime import datetime
from urllib.parse import quote_plus

encoded_password = quote_plus(settings.MYSQL_PASSWORD)
db_url = f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    print("Querying LegacyProcessamento...")
    items = session.query(LegacyProcessamento).limit(5).all()
    print(f"Found {len(items)} items.")
    
    for item in items:
        print(f"Processing ID: {item.id_processamento}")
        print(f"  Cliente ID (Raw): {item.cliente_id}")
        
        # Test conversion
        c_id = int(item.cliente_id) if item.cliente_id and item.cliente_id.isdigit() else None
        print(f"  Cliente ID (Conv): {c_id}")
        print(f"  Data: {item.data_processamento}")
        print(f"  Adquirente: {item.adquirente}")
        
    print("Test finished successfully.")

except Exception as e:
    print(f"CRASH: {e}")
