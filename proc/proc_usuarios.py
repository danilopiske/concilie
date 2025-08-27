from typing import Optional, Dict
from sqlalchemy.engine import Engine
from conf.funcoesbd import exec_sql, fetch_one
from conf.settings import sha256_hex

DDL_USUARIOS = """
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario VARCHAR(50) NOT NULL UNIQUE,
  senha CHAR(64) NOT NULL,
  nome VARCHAR(100) NOT NULL,
  empresa VARCHAR(100) NULL,
  grupo VARCHAR(50) NULL,
  funcao VARCHAR(50) NULL,
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
"""

def ensure_usuarios_table(engine: Engine) -> None:
    exec_sql(engine, DDL_USUARIOS)

def seed_admin(engine: Engine) -> None:
    sql = """
    INSERT INTO usuarios (usuario, senha, nome, empresa, grupo, funcao, ativo)
    VALUES (:usuario, :senha, :nome, :empresa, :grupo, :funcao, :ativo)
    ON DUPLICATE KEY UPDATE
      nome=VALUES(nome),
      empresa=VALUES(empresa),
      grupo=VALUES(grupo),
      funcao=VALUES(funcao),
      ativo=VALUES(ativo)
    """
    params = {
        "usuario": "admin",
        # já fornecida: SHA-256 de "1234"
        "senha": "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",
        "nome": "Administrador",
        "empresa": "Empresa XYZ",
        "grupo": "FINANCIAL",
        "funcao": "ADMIN",
        "ativo": 1
    }
    exec_sql(engine, sql, params)

def get_user_by_credentials(engine: Engine, usuario: str, senha_plana: str) -> Optional[Dict]:
    sql = """
    SELECT id, usuario, nome, empresa, grupo, funcao, ativo
      FROM usuarios
     WHERE usuario = :usuario AND senha = :senha AND ativo = 1
     LIMIT 1
    """
    params = {
        "usuario": (usuario or "").strip(),
        "senha": sha256_hex(senha_plana or ""),
    }
    return fetch_one(engine, sql, params)
