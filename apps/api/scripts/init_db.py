"""
Script para inicializar banco de dados
Cria todas as tabelas necessárias usando SQLAlchemy models
"""

import sys
from pathlib import Path

# Adicionar apps/api ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, init_db, get_db_info
from app.models import Base


def main():
    """Criar todas as tabelas no banco de dados"""

    print("=" * 80)
    print("INICIALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 80)

    # Mostrar informações do banco
    db_info = get_db_info()
    print(f"\n📊 Banco de dados: {db_info['type'].upper()}")
    print(f"🔗 Conexão: {db_info['url']}")
    print(f"🔧 Dialect: {db_info['dialect']}")
    print(f"🚗 Driver: {db_info['driver']}")

    print("\n" + "=" * 80)
    print("Criando tabelas...")
    print("=" * 80 + "\n")

    # Criar todas as tabelas
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!\n")

        # Listar tabelas criadas
        print("📋 Tabelas criadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")

        print("\n" + "=" * 80)
        print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERRO ao criar tabelas: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
