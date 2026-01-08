#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Configuração de Banco de Dados
Permite alternar entre MySQL e SQLite facilmente

Uso:
    python configure_db.py mysql       # Configura para MySQL (desenvolvimento)
    python configure_db.py sqlite      # Configura para SQLite (distribuição)
    python configure_db.py status      # Mostra configuração atual
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from conf.settings import (
    set_db_type_for_distribution,
    set_db_type_for_development,
    get_db_config,
)
from conf.db_manager import get_db_type, set_db_type


def show_status():
    """Mostra a configuração atual do banco de dados."""
    print("=" * 80)
    print("STATUS DA CONFIGURAÇÃO DE BANCO DE DADOS")
    print("=" * 80)
    print()

    config = get_db_config()
    db_type = config["type"]

    print(f"Tipo de Banco: {db_type.upper()}")
    print()

    if db_type == "mysql":
        print("✓ Modo: DESENVOLVIMENTO")
        print("✓ Banco: MySQL")
        print("✓ Requer: Servidor MySQL rodando")
        print()
        print("Configuração MySQL:")
        print("  - Host: localhost")
        print("  - Porta: 3306")
        print("  - Database: concilie")
        print("  - Usuário: root")

    elif db_type == "sqlite":
        print("✓ Modo: DISTRIBUIÇÃO")
        print("✓ Banco: SQLite")
        print("✓ Requer: Arquivo concilie.db em data/")
        print()

        sqlite_path = BASE_DIR / "data" / "concilie.db"
        if sqlite_path.exists():
            size_mb = sqlite_path.stat().st_size / (1024 * 1024)
            print(f"✓ Banco encontrado: {sqlite_path}")
            print(f"  Tamanho: {size_mb:.2f} MB")
        else:
            print(f"⚠ AVISO: Banco SQLite não encontrado em {sqlite_path}")
            print(
                "  Execute a migração primeiro: python dev_tools/migrate_mysql_to_sqlite.py"
            )

    print()

    # Verifica arquivo de configuração
    config_file = BASE_DIR / ".db_config"
    if config_file.exists():
        print(f"Arquivo de configuração: {config_file}")
        with open(config_file, "r") as f:
            print(f"  Conteúdo: {f.read().strip()}")
    else:
        print("Arquivo de configuração: Não existe (usando detecção automática)")

    print()
    print("=" * 80)


def configure_mysql():
    """Configura o sistema para usar MySQL."""
    print("=" * 80)
    print("CONFIGURANDO PARA MySQL (DESENVOLVIMENTO)")
    print("=" * 80)
    print()

    # Cria arquivo .db_config com 'mysql'
    config_file = BASE_DIR / ".db_config"
    with open(config_file, "w") as f:
        f.write("mysql")
    print("✓ Arquivo .db_config criado com 'mysql'")

    # Define via settings
    set_db_type_for_development()

    # Define no db_manager (limpa cache)
    set_db_type("mysql")

    print()
    print("✓ Sistema configurado para MySQL")
    print()
    print("IMPORTANTE:")
    print("  - Certifique-se de que o servidor MySQL está rodando")
    print("  - Banco: concilie (localhost:3306)")
    print("  - Usuário: root")
    print()
    print("Para iniciar o sistema:")
    print("  python main.py")
    print()
    print("=" * 80)


def configure_sqlite():
    """Configura o sistema para usar SQLite."""
    print("=" * 80)
    print("CONFIGURANDO PARA SQLite (DISTRIBUIÇÃO)")
    print("=" * 80)
    print()

    # Verifica se o banco SQLite existe
    sqlite_path = BASE_DIR / "data" / "concilie.db"
    if not sqlite_path.exists():
        print("⚠ AVISO: Banco SQLite não encontrado!")
        print(f"  Esperado em: {sqlite_path}")
        print()
        print("VOCÊ PRECISA CRIAR O BANCO PRIMEIRO:")
        print()
        print("Opção 1 - Migrar do MySQL:")
        print("  python dev_tools/migrate_mysql_to_sqlite.py")
        print()
        print("Opção 2 - Criar banco limpo:")
        print("  python dev_tools/create_clean_sqlite.py")
        print()

        resposta = input("Deseja configurar para SQLite mesmo assim? (s/N): ")
        if resposta.lower() != "s":
            print("\nCancelado.")
            return

    # Cria arquivo .db_config
    set_db_type_for_distribution()

    # Define no db_manager
    set_db_type("sqlite")

    print()
    print("✓ Sistema configurado para SQLite")
    print()

    if sqlite_path.exists():
        size_mb = sqlite_path.stat().st_size / (1024 * 1024)
        print(f"✓ Banco SQLite encontrado: {sqlite_path}")
        print(f"  Tamanho: {size_mb:.2f} MB")

    print()
    print("VANTAGENS DO MODO SQLITE:")
    print("  ✓ Não precisa de servidor MySQL")
    print("  ✓ Portável (copia data/concilie.db e pronto)")
    print("  ✓ Ideal para distribuição")
    print("  ✓ Menor consumo de recursos")
    print()
    print("Para iniciar o sistema:")
    print("  python main.py")
    print()
    print("=" * 80)


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("Uso: python configure_db.py [mysql|sqlite|status]")
        print()
        print("Comandos:")
        print("  mysql   - Configura para MySQL (desenvolvimento)")
        print("  sqlite  - Configura para SQLite (distribuição)")
        print("  status  - Mostra configuração atual")
        print()
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == "status":
        show_status()
    elif comando == "mysql":
        configure_mysql()
    elif comando == "sqlite":
        configure_sqlite()
    else:
        print(f"Comando inválido: {comando}")
        print("Use: mysql, sqlite ou status")
        sys.exit(1)


if __name__ == "__main__":
    main()
