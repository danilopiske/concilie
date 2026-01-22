import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.core.config import settings

# Force MySQL URL construction
from urllib.parse import quote_plus
encoded_password = quote_plus(settings.MYSQL_PASSWORD)
db_url = f"mysql+pymysql://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

engine = create_engine(db_url)
with engine.connect() as conn:
    print("Deleting existing entries in depara_config...")
    conn.execute(text("DELETE FROM depara_config"))
    conn.commit()
    print("Done. Migration will run again on next access.")
