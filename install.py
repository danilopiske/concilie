#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de instalação simplificado do sistema Financial Checker
Apenas verifica requisitos e testa o banco SQLite incluído
"""

import sys
import subprocess
from pathlib import Path

# Diretórios do sistema
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
RELATORIOS_DIR = BASE_DIR / "relatorios"
TEMP_DIR = BASE_DIR / "temp"

print("=" * 80)
print("INSTALAÇÃO DO SISTEMA FINANCIAL CHECKER")
print("=" * 80)
print()

# [1/5] Verificar Python
print("[1/5] Verificando versão do Python...")
if sys.version_info < (3, 8):
    print(f"  ❌ Python 3.8+ é necessário. Versão atual: {sys.version}")
    sys.exit(1)

python_version = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)
print(f"  ✅ Python {python_version}")

# Aviso para versões muito recentes
if sys.version_info >= (3, 14):
    print()
    print("  ⚠️  AVISO: Python 3.14+ pode ter problemas de compatibilidade")
    print("  ℹ️  Versões recomendadas: Python 3.11 ou 3.12")
    print("  ℹ️  Alguns pacotes (numpy) podem falhar na compilação")
    print()
print()

# [2/5] Criar diretórios necessários
print("[2/5] Criando diretórios...")
for dir_path in [DATA_DIR, RELATORIOS_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {dir_path.name}/")
print()

# [3/5] Instalar dependências
print("[3/5] Instalando dependências Python...")
requirements_file = BASE_DIR / "requirements.txt"

if not requirements_file.exists():
    print(f"  ❌ Arquivo requirements.txt não encontrado!")
    sys.exit(1)

# Atualizar pip primeiro
print("  ℹ️  Atualizando pip...")
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
        capture_output=True,
    )
    print("  ✅ pip atualizado")
except:
    print("  ⚠️  Não foi possível atualizar pip (continuando...)")

print()
print("  ℹ️  Instalando pacotes (pode demorar alguns minutos)...")
print("  ℹ️  Aguarde enquanto o pip baixa e instala as dependências...")
print()

# Tentar instalar requirements.txt completo
install_failed = False
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
        check=True,
    )
    print()
    print("  ✅ Pacotes instalados com sucesso")
except subprocess.CalledProcessError as e:
    install_failed = True
    print()
    print("  ⚠️  AVISO: Alguns pacotes falharam no requirements.txt")
    print()

# Se falhou, tentar instalar pacotes essenciais individualmente
if install_failed:
    print("  ℹ️  Tentando instalar pacotes essenciais individualmente...")
    print("  ℹ️  Isso pode demorar alguns minutos por pacote...")
    print()

    essential = ["panel", "pandas", "sqlalchemy", "plotly", "openpyxl", "psutil"]
    for package in essential:
        try:
            print(f"    Instalando {package}...", flush=True)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
            )
            print(f"    ✅ {package} instalado")
        except:
            print(f"    ❌ {package} falhou")

    print()
    print("  ⚠️  Instalação parcial concluída")
    print("  ℹ️  Pacotes como numpy podem ter falhado (Python 3.14)")
    print()
    response = input("  Deseja continuar mesmo assim? (s/N): ").strip().lower()
    if response != "s":
        sys.exit(1)

print()

# [4/5] Verificar banco de dados
print("[4/5] Verificando banco de dados...")
db_path = DATA_DIR / "concilie.db"

if not db_path.exists():
    print(f"  ❌ Banco de dados não encontrado!")
    print(f"  ℹ️  Esperado em: {db_path}")
    print(f"  ℹ️  O arquivo concilie.db deveria estar no ZIP de distribuição")
    sys.exit(1)

# Testar conexão
import sqlite3

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar tabela usuarios
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    user_count = cursor.fetchone()[0]

    # Verificar total de tabelas
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]

    conn.close()

    print(f"  ✅ Banco: {db_path}")
    print(f"  ✅ Tabelas: {table_count}")
    print(f"  ✅ Usuários: {user_count}")
except Exception as e:
    print(f"  ❌ Erro ao conectar no banco: {e}")
    sys.exit(1)
print()

# [5/5] Verificação final
print("[5/5] Verificando instalação...")

checks = {
    "Banco de dados": db_path.exists(),
    "Diretório data/": DATA_DIR.exists(),
    "Diretório relatorios/": RELATORIOS_DIR.exists(),
    "Diretório temp/": TEMP_DIR.exists(),
    "Arquivo main.py": (BASE_DIR / "main.py").exists(),
    "Arquivo requirements.txt": requirements_file.exists(),
}

all_ok = True
for item, status in checks.items():
    symbol = "✅" if status else "❌"
    print(f"  {symbol} {item}")
    if not status:
        all_ok = False

# Verificar pacotes Python essenciais
print()
print("  Verificando pacotes Python:")
essential_packages = ["panel", "pandas", "sqlalchemy", "plotly", "openpyxl", "psutil"]
missing_packages = []

for package in essential_packages:
    try:
        __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ❌ {package} - NÃO INSTALADO")
        missing_packages.append(package)
        all_ok = False

print()

if not all_ok:
    print("=" * 80)
    print("❌ INSTALAÇÃO INCOMPLETA - Verifique os itens acima")
    print("=" * 80)

    if missing_packages:
        print()
        print("⚠️  PACOTES FALTANDO:")
        print(f"   {', '.join(missing_packages)}")
        print()
        print("Possíveis soluções:")
        print("  1. Use Python 3.11 ou 3.12 (não 3.14)")
        print("  2. Tente instalar manualmente:")
        print(f"     .venv\\Scripts\\activate")
        print(f"     pip install {' '.join(missing_packages)}")
        print()

    sys.exit(1)

# Sucesso!
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
print("  Senha: 1234")
print()
print("=" * 80)
