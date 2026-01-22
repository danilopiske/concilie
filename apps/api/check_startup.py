import sys
import os

# Add apps/api to path
sys.path.append(os.getcwd())

print("Attempting to import config...")
try:
    from app.core.config import settings
    print(f"Config loaded. DB Path: {settings.SQLITE_DB_PATH}")
    print(f"DB Exists? {os.path.exists(settings.SQLITE_DB_PATH)}")
except Exception as e:
    print(f"Failed to import config: {e}")
    sys.exit(1)

print("Attempting to import schemas...")
try:
    from app.schemas.depara import DeParaBase
    print("Schemas loaded.")
except Exception as e:
    print(f"Failed to import schemas: {e}")
    sys.exit(1)

print("Attempting to load main app...")
try:
    from app.main import app
    print("Main app loaded successfully.")
except Exception as e:
    print(f"Failed to load main app: {e}")
    sys.exit(1)
