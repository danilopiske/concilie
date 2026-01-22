from app.core.database import engine, get_database_url
from app.repositories.depara_repository import DeParaRepository
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

print(f"CWD: {os.getcwd()}")
print(f"Configured DB URL: {get_database_url()}")

# Check where the file actually is if sqlite
if "sqlite" in get_database_url():
    path = get_database_url().replace("sqlite:///", "")
    print(f"Looking for DB at: {path}")
    print(f"Exists? {os.path.exists(path)}")
    print(f"Abs Path: {os.path.abspath(path)}")

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Test Raw SQL via ORM
    result = db.execute(text("SELECT count(*) FROM depara_colunas")).scalar()
    print(f"Raw SQL count via Engine: {result}")

    # Test Repository
    repo = DeParaRepository(db)
    items = repo.listar()
    print(f"Repo.listar() count: {len(items)}")
    
    if len(items) > 0:
        print(f"Sample item: {items[0].__dict__}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
