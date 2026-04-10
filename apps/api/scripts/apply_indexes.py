import sys
import os

# Adiciona o diretório pai ao path para conseguir importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def create_indexes():
    """
    Cria índices manualmente para colunas que foram atualizadas no modelo,
    mas que o SQLAlchemy não cria automaticamente em tabelas existentes.
    """
    print("Iniciando criação de índices para otimização de performance...")
    
    with engine.connect() as conn:
        # Lista de índices a criar (Formato: Tabela, NomeIndice, Coluna)
        # MySQL syntax
        
        indexes = [
            ("vendas_processadas", "ix_vendas_processadas_Bandeira", "Bandeira"),
            ("vendas_processadas", "ix_vendas_processadas_Forma_de_pagamento", "Forma_de_pagamento"),
            ("vendas_processadas", "ix_vendas_processadas_status_da_venda", "status_da_venda"),
        ]

        for table, idx_name, column in indexes:
            try:
                print(f"Tentando criar índice {idx_name} na tabela {table}...")
                
                # Check if index exists (MySQL specific query)
                result = conn.execute(text(f"SHOW INDEX FROM {table} WHERE Key_name = '{idx_name}'"))
                if result.fetchone():
                    print(f" -> Índice {idx_name} já existe. Pulando.")
                else:
                    # Create index
                    conn.execute(text(f"CREATE INDEX {idx_name} ON {table} ({column}(50))"))
                    print(f" -> Índice {idx_name} criado com SUCESSO.")
            except Exception as e:
                print(f" -> Erro ao criar índice {idx_name}: {e}")

        conn.commit()
    
    print("\nProcesso finalizado.")

if __name__ == "__main__":
    create_indexes()
