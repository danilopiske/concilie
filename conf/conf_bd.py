from sqlalchemy import create_engine
from urllib.parse import quote_plus
import os


def get_engine():
    USUARIO = "root"
    SENHA = quote_plus("C0nc!l!3@123#")
    HOST = "localhost"
    PORTA = 3306
    BANCO = "concilie"

    # Cria engine com configurações básicas
    engine = create_engine(
        f"mysql+pymysql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}",
        echo=False,
        pool_pre_ping=True,
        pool_recycle=600,
        pool_size=5,
        max_overflow=10,
        connect_args={
            # Aumenta o timeout para operações com grandes conjuntos de dados
            "connect_timeout": 60,
            # Desativa uso de cursores do lado do servidor para consultas grandes
            "client_flag": 0,
        },
    )

    # Configura diretório temporário personalizado para MySQL
    try:
        from conf.mysql_temp import set_mysql_temp_dir

        # Usa uma pasta em D: se disponível, senão cria uma pasta no diretório atual
        if os.path.exists("D:\\"):
            temp_dir = "D:\\temp\\mysql_temp"
        else:
            temp_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "temp", "mysql_temp"
            )

        set_mysql_temp_dir(engine, temp_dir)
    except Exception as e:
        print(
            f"Aviso: Não foi possível configurar diretório temporário personalizado: {e}"
        )

    return engine
