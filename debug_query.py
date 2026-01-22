import sys
import os
from pathlib import Path
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup path
root_dir = Path(os.getcwd())
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / 'apps' / 'api'))

from app.core.config import settings
from app.models.legacy_processamento import LegacyProcessamento

def test_query():
    print(f"Connecting to: {settings.SQLALCHEMY_DATABASE_URI}")
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    print("Executing query...")
    start = time.time()
    
    try:
        # Replicate repository logic
        query = db.query(LegacyProcessamento)
        query = query.order_by(LegacyProcessamento.data_processamento.desc())
        items = query.offset(0).limit(100).all()
        
        end = time.time()
        print(f"Query returned {len(items)} items in {end - start:.4f} seconds")
        
        if items:
            print(f"First item: {items[0].id_processamento} - {items[0].data_processamento}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_query()
