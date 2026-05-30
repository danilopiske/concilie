import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.database import engine
from app.models.base import Base
from app.models.import_task import ImportTask

print(f"Criando tabela {ImportTask.__tablename__} no banco de dados...")
Base.metadata.create_all(bind=engine, tables=[ImportTask.__table__])
print("Tabela criada com sucesso!")
