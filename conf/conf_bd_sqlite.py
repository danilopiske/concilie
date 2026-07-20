from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
import os


def get_engine_sqlite(db_path: str = None):
    """
    Cria e retorna uma engine SQLAlchemy para SQLite.

    Args:
        db_path: Caminho para o arquivo do banco SQLite.
                 Se None, usa o padrão './data/concilie.db'

    Returns:
        Engine SQLAlchemy configurada para SQLite
    """
    if db_path is None:
        # Define caminho padrão no diretório data
        project_root = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(project_root, "data")

        # Cria diretório data se não existir
        os.makedirs(data_dir, exist_ok=True)

        db_path = os.path.join(data_dir, "concilie.db")

    # Garante que o diretório do banco existe
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # Cria engine SQLite
    # file:// é importante para caminhos absolutos
    db_uri = f"sqlite:///{db_path}"

    engine = create_engine(
        db_uri,
        echo=False,  # Mude para True para debug SQL
        pool_pre_ping=True,
        pool_recycle=3600,
        # SQLite específico
        connect_args={
            "check_same_thread": False,  # Permite uso em múltiplas threads
            "timeout": 30,  # Timeout para locks em segundos
        },
    )

    # Habilita foreign keys no SQLite (desabilitadas por padrão)
    # IMPORTANTE: Aplicar event APENAS nesta engine específica, não em todas
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(
            "PRAGMA journal_mode=WAL"
        )  # Write-Ahead Logging para melhor concorrência
        cursor.execute(
            "PRAGMA synchronous=NORMAL"
        )  # Balance entre performance e segurança
        cursor.execute("PRAGMA cache_size=10000")  # Cache maior
        cursor.execute("PRAGMA temp_store=MEMORY")  # Armazenar temporários em memória
        cursor.close()

    print(f"[SQLite] Engine criada: {db_path}")
    print(f"[SQLite] Banco existe: {os.path.exists(db_path)}")

    return engine


def get_db_path():
    """Retorna o caminho padrão do banco SQLite."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(project_root, "data")
    return os.path.join(data_dir, "concilie.db")
