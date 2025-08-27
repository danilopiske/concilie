from sqlalchemy import create_engine
from urllib.parse import quote_plus

def get_engine():
    USUARIO = "root"
    SENHA = quote_plus("C0nc!l!3@123#")
    HOST = "localhost"
    PORTA = 3306
    BANCO = "concilie"

    return create_engine(
        f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}",
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
