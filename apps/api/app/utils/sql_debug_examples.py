"""
Exemplo de uso do SQL Debug Helper
"""

from sqlalchemy.orm import Session

from app.core.database import engine, get_db
from app.models.cliente import Cliente
from app.utils.sql_debug import debug_query, get_db_type, log_query


def exemplo_debug_basico():
    """Exemplo básico de debug de query"""

    db: Session = next(get_db())

    # Exemplo 1: Debug de query simples
    query = db.query(Cliente).filter(Cliente.ativo == True)
    debug_query(db, query, label="Listar Clientes Ativos")

    # Executar a query
    clientes = query.all()
    print(f"Encontrados {len(clientes)} clientes")


def exemplo_debug_manual():
    """Exemplo de log manual de query SQL"""

    sql = """
    SELECT 
        c.cliente_id,
        c.nome_razao_social,
        COUNT(ec.ec_id) as total_ecs
    FROM clientes c
    LEFT JOIN ecs ec ON c.cliente_id = ec.cliente_id
    WHERE c.ativo = :ativo
    GROUP BY c.cliente_id, c.nome_razao_social
    """

    params = {"ativo": True}

    log_query(sql, params, label="Clientes com Total de ECs")


def exemplo_verificar_banco():
    """Exemplo de verificação de tipo de banco"""

    db_type = get_db_type(engine)
    print(f"Banco de dados ativo: {db_type.upper()}")

    from app.utils.sql_debug import is_mysql, is_sqlite

    if is_mysql(engine):
        print("✅ Conectado ao MySQL")
        print("   - Suporta: CONCAT, DATE_FORMAT, etc")
    elif is_sqlite(engine):
        print("✅ Conectado ao SQLite")
        print("   - Suporta: ||, strftime, etc")


if __name__ == "__main__":
    print("=" * 80)
    print("EXEMPLOS DE USO - SQL DEBUG HELPER")
    print("=" * 80)

    exemplo_verificar_banco()
    print("\n")

    exemplo_debug_manual()
    print("\n")

    # exemplo_debug_basico()  # Descomente para testar com DB real
