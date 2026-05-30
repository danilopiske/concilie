"""
Configurações globais do sistema Financial 
Inclui configurações de banco de dados, segurança e aplicação
"""

import hashlib
import os

# ==========================================
# Informações da Aplicação
# ==========================================
APP_TITLE = "Concilie"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Sistema de Conciliação Financeira"

# ==========================================
# Configurações de Banco de Dados
# ==========================================


def get_db_config():
    """
    Retorna a configuração de banco de dados baseado no ambiente.

    Ordem de verificação:
    1. Variável de ambiente DB_TYPE
    2. Arquivo .db_config
    3. Detecção automática (SQLite se arquivo existir)
    4. Padrão: MySQL

    Returns:
        dict com configurações do banco
    """
    db_type = os.environ.get("DB_TYPE", "").lower()

    if not db_type:
        # Tenta ler arquivo de configuração
        config_file = os.path.join(os.path.dirname(__file__), "..", ".db_config")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    db_type = f.read().strip().lower()
            except:
                pass

    # Se ainda não tem db_type, usa detecção automática
    if not db_type:
        # Detecção automática: se existe concilie.db, usa SQLite
        sqlite_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "concilie.db"
        )
        if os.path.exists(sqlite_path):
            db_type = "sqlite"
        else:
            db_type = "mysql"

    return {
        "type": db_type,
        "is_sqlite": db_type == "sqlite",
        "is_mysql": db_type == "mysql",
    }


def set_db_type_for_distribution():
    """
    Configura o sistema para usar SQLite (modo distribuição).
    Cria arquivo .db_config com 'sqlite'.
    """
    config_file = os.path.join(os.path.dirname(__file__), "..", ".db_config")
    with open(config_file, "w") as f:
        f.write("sqlite")
    print("[SETTINGS] Sistema configurado para SQLite (distribuição)")


def set_db_type_for_development():
    """
    Configura o sistema para usar MySQL (modo desenvolvimento).
    Cria arquivo .db_config com 'mysql'.
    """
    config_file = os.path.join(os.path.dirname(__file__), "..", ".db_config")
    with open(config_file, "w") as f:
        f.write("mysql")
    print("[SETTINGS] Sistema configurado para MySQL (desenvolvimento)")


# ==========================================
# Segurança e Autenticação
# ==========================================


def sha256_hex(s: str) -> str:
    """
    Gera hash SHA256 de uma string.

    Args:
        s: String para gerar hash

    Returns:
        Hash SHA256 em hexadecimal
    """
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ==========================================
# Configurações de Sistema
# ==========================================

# Diretórios do sistema
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

# Criar diretórios se não existirem
for directory in [DATA_DIR, TEMP_DIR, RELATORIOS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configurações de processamento
DEFAULT_CHUNK_SIZE = 10000  # Tamanho padrão de lote para operações em massa
MAX_RETRIES = 3  # Número máximo de tentativas em caso de erro

# Configurações de performance
ENABLE_QUERY_CACHE = True
QUERY_CACHE_SIZE = 100

# Modo debug
DEBUG_MODE = os.environ.get("DEBUG", "False").lower() == "true"
