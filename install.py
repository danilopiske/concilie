# 🚀 INSTALADOR CONCILIE - MODO SINGLEUSER
# Sistema de Conciliação Financeira
# Versão: 2.0 (SQLite)

import os
import sys
import subprocess
import sqlite3
from pathlib import Path
import shutil

print("=" * 80)
print("CONCILIE - INSTALADOR SINGLEUSER MODE")
print("Sistema de Conciliação Financeira")
print("=" * 80)
print()

# Verificar versão do Python
print("[1/7] Verificando Python...")
python_version = sys.version_info
if python_version < (3, 8):
    print(
        f"❌ ERRO: Python 3.8+ requerido. Você tem {python_version.major}.{python_version.minor}"
    )
    sys.exit(1)
print(
    f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detectado"
)
print()

# Diretórios base
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
RELATORIOS_DIR = BASE_DIR / "relatorios"
TEMP_DIR = BASE_DIR / "temp"

# Criar estrutura de diretórios
print("[2/7] Criando estrutura de diretórios...")
directories = [
    DATA_DIR,
    DATA_DIR / "arquivos_processados",
    DATA_DIR / "lancamento_planilhas",
    DATA_DIR / "venda_planilhas",
    RELATORIOS_DIR,
    TEMP_DIR,
    ASSETS_DIR,
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {directory.relative_to(BASE_DIR)}")
print()

# Instalar dependências
print("[3/7] Instalando dependências Python...")
print("  Isso pode levar alguns minutos...")

requirements_file = BASE_DIR / "requirements.txt"
if not requirements_file.exists():
    print(f"❌ ERRO: {requirements_file} não encontrado")
    sys.exit(1)

# Primeiro, atualizar pip
print("  Atualizando pip...")
print("  " + "=" * 60)
try:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ]
    )
    print("  " + "=" * 60)
    print("  ✅ pip atualizado")
except subprocess.CalledProcessError as e:
    print(f"  ⚠️  Aviso: Não foi possível atualizar o pip: {e}")
    print("  Continuando com a versão atual...")

# Instalar dependências
print()
print("  Instalando pacotes Python...")
print("  " + "=" * 60)
print("  📦 Instalando 73 dependências (Panel, Pandas, SQLAlchemy, etc.)")
print("  ⏱️  Tempo estimado: 2-5 minutos")
print("  " + "=" * 60)
try:
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ]
    )
    print("  " + "=" * 60)
    print("✅ Dependências instaladas com sucesso")
except subprocess.CalledProcessError as e:
    print(f"❌ Erro ao instalar dependências: {e}")
    print("  Tente manualmente:")
    print(f"    python -m pip install --upgrade pip")
    print(f"    pip install -r requirements.txt")
    sys.exit(1)
print()

# Criar banco SQLite
print("[4/7] Criando banco de dados SQLite...")
db_path = DATA_DIR / "concilie.db"

# Se já existe, perguntar se quer recriar
if db_path.exists():
    print(f"  ⚠️  Banco de dados já existe: {db_path}")
    response = input("  Deseja recriar o banco? (s/N): ").strip().lower()
    if response == "s":
        db_path.unlink()
        print("  🗑️  Banco anterior removido")
    else:
        print("  ℹ️  Mantendo banco existente")
        print()
        # Pular criação do schema
        print("[5/7] Schema já existe, pulando...")
        print()
        print("[6/7] Criando usuário admin...")
        print("  ℹ️  Usuário já deve existir, pulando...")
        print()
        print("[7/7] Verificando instalação...")
        print("  ✅ Banco de dados: OK")
        print("  ✅ Diretórios: OK")
        print("  ✅ Dependências: OK")
        print()
        print("=" * 80)
        print("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        print()
        print("Para iniciar o sistema:")
        print()
        print("  python main.py --mode singleuser")
        print()
        print("Acesse: http://localhost:8500")
        print()
        print("Credenciais padrão:")
        print("  Usuário: admin")
        print("  Senha: admin123")
        print()
        print("=" * 80)
        sys.exit(0)

# Criar schema SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("[5/7] Criando schema do banco de dados...")

# Schema completo do sistema
schema_sql = """
-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(64) NOT NULL,
    nome VARCHAR(100),
    empresa VARCHAR(100),
    grupo VARCHAR(50),
    funcao VARCHAR(100),
    ativo INTEGER DEFAULT 1
);

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clientes (
    cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj VARCHAR(18) UNIQUE,
    razao_social VARCHAR(200),
    nome_fantasia VARCHAR(200),
    endereco TEXT,
    telefone VARCHAR(20),
    email VARCHAR(100),
    ativo INTEGER DEFAULT 1
);

-- Tabela de estabelecimentos (ECs)
CREATE TABLE IF NOT EXISTS estabelecimentos (
    ec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    numero_ec VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(200),
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
);

-- Tabela de bandeiras por EC
CREATE TABLE IF NOT EXISTS bandeiras_ec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    ec_id INTEGER,
    bandeira_nome VARCHAR(50),
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id),
    FOREIGN KEY (ec_id) REFERENCES estabelecimentos(ec_id)
);

-- Tabela de taxas
CREATE TABLE IF NOT EXISTS taxas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ec_id INTEGER,
    bandeira VARCHAR(50),
    forma_pagamento VARCHAR(50),
    taxa REAL,
    taxa_rr REAL,
    parcelas INTEGER,
    data_inicio TEXT,
    data_fim TEXT,
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY (ec_id) REFERENCES estabelecimentos(ec_id)
);

-- Tabela de contextos
CREATE TABLE IF NOT EXISTS contextos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) UNIQUE NOT NULL,
    descricao TEXT,
    ativo INTEGER DEFAULT 1
);

-- Tabela de termos de classificação
CREATE TABLE IF NOT EXISTS termos_classificacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ec_id INTEGER,
    bandeira VARCHAR(50),
    termo VARCHAR(200),
    tipo_arquivo VARCHAR(50),
    contexto VARCHAR(100),
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY (ec_id) REFERENCES estabelecimentos(ec_id)
);

-- Tabela de de-para de colunas
CREATE TABLE IF NOT EXISTS depara_colunas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origem_nome VARCHAR(100),
    destino_nome VARCHAR(100),
    contexto VARCHAR(100),
    tipo_origem VARCHAR(50),
    ativo INTEGER DEFAULT 1
);

-- Tabela de controle de colunas de vendas
CREATE TABLE IF NOT EXISTS vendas_colunas_controle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campo VARCHAR(100),
    descricao VARCHAR(200),
    contexto VARCHAR(100),
    tipo_arquivo VARCHAR(50),
    obrigatorio INTEGER DEFAULT 0,
    ativo INTEGER DEFAULT 1
);

-- Tabela de controle de processamentos
CREATE TABLE IF NOT EXISTS controle_processamentos (
    id_processamento VARCHAR(50) PRIMARY KEY,
    descricao VARCHAR(200),
    data_processamento TEXT,
    usuario VARCHAR(50),
    status VARCHAR(50),
    qtd_vendas_processadas INTEGER DEFAULT 0,
    qtd_vendas_filtradas INTEGER DEFAULT 0,
    qtd_recebiveis_processados INTEGER DEFAULT 0,
    qtd_recebiveis_filtrados INTEGER DEFAULT 0,
    data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de vendas processadas
CREATE TABLE IF NOT EXISTS vendas_processadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    Data_da_venda TEXT,
    Bandeira VARCHAR(50),
    Forma_de_pagamento VARCHAR(50),
    Valor_da_venda REAL,
    Parcelas INTEGER,
    NSU VARCHAR(50),
    Codigo_autorizacao VARCHAR(50),
    data_processamento TEXT,
    FOREIGN KEY (processamentoid) REFERENCES controle_processamentos(id_processamento)
);

-- Tabela de vendas filtradas
CREATE TABLE IF NOT EXISTS vendas_filtradas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    Data_da_venda TEXT,
    Bandeira VARCHAR(50),
    Forma_de_pagamento VARCHAR(50),
    Valor_da_venda REAL,
    Parcelas INTEGER,
    NSU VARCHAR(50),
    Codigo_autorizacao VARCHAR(50),
    data_processamento TEXT,
    FOREIGN KEY (processamentoid) REFERENCES controle_processamentos(id_processamento)
);

-- Tabela de vendas diversas
CREATE TABLE IF NOT EXISTS vendas_diversas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    Data_da_venda TEXT,
    Bandeira VARCHAR(50),
    Valor_da_venda REAL,
    Motivo_classificacao VARCHAR(200),
    data_processamento TEXT,
    FOREIGN KEY (processamentoid) REFERENCES controle_processamentos(id_processamento)
);

-- Tabela de recebíveis processados
CREATE TABLE IF NOT EXISTS recebiveis_processados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    Bandeira VARCHAR(50),
    Forma_de_pagamento VARCHAR(50),
    Data_pagamento TEXT,
    valor_recebivel REAL,
    valor_liquido REAL,
    taxa_aplicada REAL,
    data_processamento TEXT,
    FOREIGN KEY (processamentoid) REFERENCES controle_processamentos(id_processamento)
);

-- Tabela de recebíveis filtrados
CREATE TABLE IF NOT EXISTS recebiveis_filtrados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    Bandeira VARCHAR(50),
    Forma_de_pagamento VARCHAR(50),
    Data_pagamento TEXT,
    valor_recebivel REAL,
    valor_liquido REAL,
    taxa_aplicada REAL,
    data_processamento TEXT,
    FOREIGN KEY (processamentoid) REFERENCES controle_processamentos(id_processamento)
);

-- Tabela de cálculos de vendas
CREATE TABLE IF NOT EXISTS vendas_calculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda INTEGER,
    calc_id VARCHAR(50),
    calc_tipo VARCHAR(50),
    tx_venda REAL,
    vl_venda REAL,
    tx_calc REAL,
    vl_calc REAL,
    perda REAL,
    tx_rr_venda REAL,
    vl_rr_venda REAL,
    tx_rr_calc REAL,
    vl_rr_calc REAL,
    perda_rr REAL,
    FOREIGN KEY (id_venda) REFERENCES vendas_processadas(id)
);

-- Tabela de perdas de cálculos
CREATE TABLE IF NOT EXISTS venda_calculos_perdas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda INTEGER,
    processamentoid VARCHAR(50),
    ec_id INTEGER,
    bandeira VARCHAR(50),
    forma_pagamento VARCHAR(50),
    valor_venda REAL,
    perda_mdr REAL,
    perda_rr REAL,
    perda_total REAL,
    semestre VARCHAR(10),
    FOREIGN KEY (id_venda) REFERENCES vendas_processadas(id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_vendas_proc ON vendas_processadas(processamentoid);
CREATE INDEX IF NOT EXISTS idx_vendas_ec ON vendas_processadas(ec_id);
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas_processadas(Data_da_venda);
CREATE INDEX IF NOT EXISTS idx_vendas_calc ON vendas_calculos(calc_id, calc_tipo);
CREATE INDEX IF NOT EXISTS idx_recebiveis_proc ON recebiveis_processados(processamentoid);
"""

try:
    cursor.executescript(schema_sql)
    conn.commit()
    print("  ✅ Schema criado com sucesso")
except Exception as e:
    print(f"  ❌ Erro ao criar schema: {e}")
    conn.close()
    sys.exit(1)
print()

# Criar usuário admin
print("[6/7] Criando usuário admin...")

import hashlib


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


admin_password = sha256_hex("admin123")

try:
    cursor.execute(
        """
        INSERT OR IGNORE INTO usuarios (usuario, senha_hash, nome, grupo, funcao, ativo)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            "admin",
            admin_password,
            "Administrador",
            "admin",
            "Administrador do Sistema",
            1,
        ),
    )

    conn.commit()

    if cursor.rowcount > 0:
        print("  ✅ Usuário 'admin' criado com sucesso")
    else:
        print("  ℹ️  Usuário 'admin' já existe")
except Exception as e:
    print(f"  ❌ Erro ao criar usuário: {e}")
finally:
    conn.close()
print()

# Verificar instalação
print("[7/7] Verificando instalação...")

checks = {
    "Banco de dados": db_path.exists(),
    "Diretório data": DATA_DIR.exists(),
    "Diretório relatorios": RELATORIOS_DIR.exists(),
    "Diretório temp": TEMP_DIR.exists(),
    "Arquivo main.py": (BASE_DIR / "main.py").exists(),
    "Arquivo requirements.txt": requirements_file.exists(),
}

all_ok = True
for check_name, check_result in checks.items():
    status = "✅" if check_result else "❌"
    print(f"  {status} {check_name}")
    if not check_result:
        all_ok = False

print()

if not all_ok:
    print("❌ Alguns componentes estão faltando. Verifique a instalação.")
    sys.exit(1)

# Sucesso!
print("=" * 80)
print("✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 80)
print()
print("📁 Estrutura criada:")
print(f"   • Banco de dados: {db_path.relative_to(BASE_DIR)}")
print(f"   • Diretórios de dados: {DATA_DIR.relative_to(BASE_DIR)}/")
print(f"   • Relatórios: {RELATORIOS_DIR.relative_to(BASE_DIR)}/")
print()
print("🚀 Para iniciar o sistema:")
print()
print("   python main.py --mode singleuser")
print()
print("🌐 Acesse no navegador:")
print()
print("   http://localhost:8500")
print()
print("🔐 Credenciais padrão:")
print()
print("   Usuário: admin")
print("   Senha: admin123")
print()
print("⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!")
print()
print("=" * 80)
print()
print("📖 Documentação:")
print("   • README.md - Visão geral do sistema")
print("   • COMPATIBILIDADE_SQL.md - Compatibilidade MySQL/SQLite")
print("   • ANALISE_COMPLETA_SISTEMA.md - Análise técnica completa")
print()
print("=" * 80)
