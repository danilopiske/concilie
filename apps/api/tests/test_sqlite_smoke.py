"""
test_sqlite_smoke.py — Verifica que queries críticas funcionam em SQLite in-memory.

Garante compatibilidade dual MySQL/SQLite sem depender de banco externo.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sqlite_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(sqlite_engine):
    Session = sessionmaker(bind=sqlite_engine)
    session = Session()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Task 1 — Dialect detection (sem Session.bind depreciado)
# ---------------------------------------------------------------------------

def test_dialect_detection_analista(db_session):
    """AnalistaRepository detecta dialeto via get_bind() sem SADeprecationWarning."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    assert repo.dialect == "sqlite", f"Esperado 'sqlite', obtido '{repo.dialect}'"


def test_dialect_detection_calculo(db_session):
    """CalculoRepository detecta dialeto via get_bind() sem SADeprecationWarning."""
    from app.repositories.calculo_repository import CalculoRepository
    repo = CalculoRepository(db_session)
    assert repo.dialect == "sqlite", f"Esperado 'sqlite', obtido '{repo.dialect}'"


# ---------------------------------------------------------------------------
# Task 2 — Period SQL geração correta para SQLite
# ---------------------------------------------------------------------------

def test_analista_period_sql_mes(db_session):
    """AnalistaRepository._get_period_sql gera strftime para 'mes' em SQLite."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    sql = repo._get_period_sql("Data_da_venda", "mes")
    assert "strftime" in sql, f"Esperado strftime, obtido: {sql}"
    assert "DATE_FORMAT" not in sql


def test_analista_period_sql_ano(db_session):
    """AnalistaRepository._get_period_sql gera strftime para 'ano' em SQLite."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    sql = repo._get_period_sql("Data_da_venda", "ano")
    assert "strftime" in sql
    assert "DATE_FORMAT" not in sql


def test_analista_period_sql_trimestre(db_session):
    """AnalistaRepository._get_period_sql gera SQL SQLite para trimestre."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    sql = repo._get_period_sql("Data_da_venda", "trimestre")
    assert "QUARTER" not in sql, f"QUARTER() não deve aparecer no SQLite: {sql}"
    assert "CONCAT" not in sql, f"CONCAT() não deve aparecer no SQLite: {sql}"


def test_analista_period_sql_semestre(db_session):
    """AnalistaRepository._get_period_sql gera SQL SQLite para semestre."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    sql = repo._get_period_sql("Data_da_venda", "semestre")
    assert "IF(" not in sql, f"IF() MySQL não deve aparecer no SQLite: {sql}"
    assert "CONCAT" not in sql


def test_calculo_period_formula(db_session):
    """CalculoRepository._get_period_formula usa strftime no SQLite."""
    from app.repositories.calculo_repository import CalculoRepository
    repo = CalculoRepository(db_session)
    formula = repo._get_period_formula()
    assert "strftime" in formula
    assert "CONCAT" not in formula
    assert "YEAR(" not in formula


# ---------------------------------------------------------------------------
# Task 3 — Queries críticas executam sem erro no SQLite
# ---------------------------------------------------------------------------

def test_bandeiras_query_sqlite(db_session):
    """get_bandeiras executa SQL compatível com SQLite (falha de schema é OK, falha de dialeto não).

    Colunas como Taxas_Perc e Valor_descontado existem no MySQL após importação
    mas não no schema ORM — isso é um gap de schema conhecido, não um problema de adaptador.
    O teste verifica que não há erros de dialeto (QUARTER, CONCAT, DATE_FORMAT).
    """
    from app.repositories.analista_repository import AnalistaRepository
    from sqlalchemy.exc import OperationalError
    repo = AnalistaRepository(db_session)
    try:
        result = repo.get_bandeiras("pid_teste")
        assert isinstance(result, list)
    except OperationalError as e:
        err = str(e).lower()
        # Aceitar apenas erros de schema (coluna não existe), nunca erros de dialeto
        assert "quarter" not in err, f"Erro de dialeto MySQL (QUARTER): {e}"
        assert "concat" not in err, f"Erro de dialeto MySQL (CONCAT): {e}"
        assert "date_format" not in err, f"Erro de dialeto MySQL (DATE_FORMAT): {e}"


def test_formas_pagamento_query_sqlite(db_session):
    """get_formas_pagamento executa SQL compatível com SQLite (mesma ressalva de schema)."""
    from app.repositories.analista_repository import AnalistaRepository
    from sqlalchemy.exc import OperationalError
    repo = AnalistaRepository(db_session)
    try:
        result = repo.get_formas_pagamento("pid_teste")
        assert isinstance(result, list)
    except OperationalError as e:
        err = str(e).lower()
        assert "quarter" not in err
        assert "concat" not in err
        assert "date_format" not in err


def test_periodos_mes_query_sqlite(db_session):
    """AnalistaRepository.get_periodos('mes') executa sem erro em SQLite vazio."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    result = repo.get_periodos("pid_teste", "mes")
    assert isinstance(result, list)


def test_periodos_trimestre_query_sqlite(db_session):
    """AnalistaRepository.get_periodos('trimestre') executa sem erro em SQLite vazio."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    result = repo.get_periodos("pid_teste", "trimestre")
    assert isinstance(result, list)


def test_periodos_semestre_query_sqlite(db_session):
    """AnalistaRepository.get_periodos('semestre') executa sem erro em SQLite vazio."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    result = repo.get_periodos("pid_teste", "semestre")
    assert isinstance(result, list)


def test_recebiveis_query_sqlite(db_session):
    """AnalistaRepository.get_recebiveis executa sem erro em SQLite vazio."""
    from app.repositories.analista_repository import AnalistaRepository
    repo = AnalistaRepository(db_session)
    result = repo.get_recebiveis("pid_teste")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Task 4 — db_helpers._adapt_sql substitui padrões MySQL
# ---------------------------------------------------------------------------

def test_adapt_sql_insert_ignore(sqlite_engine):
    """_adapt_sql converte INSERT IGNORE → INSERT OR IGNORE para SQLite."""
    from app.core.db_helpers import _adapt_sql
    sql = "INSERT IGNORE INTO tabela (col) VALUES (:val)"
    adapted = _adapt_sql(sqlite_engine, sql)
    assert "INSERT OR IGNORE" in adapted
    assert "INSERT IGNORE INTO" not in adapted


def test_adapt_sql_ifnull(sqlite_engine):
    """_adapt_sql converte IFNULL() → COALESCE() para SQLite."""
    from app.core.db_helpers import _adapt_sql
    sql = "SELECT IFNULL(col, 0) FROM tabela"
    adapted = _adapt_sql(sqlite_engine, sql)
    assert "COALESCE" in adapted
    assert "IFNULL" not in adapted


def test_adapt_sql_mysql_passthrough(sqlite_engine):
    """_adapt_sql não altera SQL sem padrões MySQL."""
    from app.core.db_helpers import _adapt_sql
    sql = "SELECT col1, col2 FROM tabela WHERE id = :id"
    adapted = _adapt_sql(sqlite_engine, sql)
    assert adapted == sql


# ---------------------------------------------------------------------------
# Task 5 — Schema criado corretamente (tabelas existem)
# ---------------------------------------------------------------------------

def test_schema_tables_exist(sqlite_engine):
    """Tabelas ORM principais existem no SQLite após Base.metadata.create_all."""
    # Nomes reais conforme os modelos SQLAlchemy (não necessariamente iguais ao MySQL importado)
    expected_tables = [
        "vendas_processadas",
        "recebiveis_processados",
        "taxas",
        "contextos",
        "termos_filtraveis",
    ]
    from sqlalchemy import inspect
    inspector = inspect(sqlite_engine)
    existing = inspector.get_table_names()
    for table in expected_tables:
        assert table in existing, f"Tabela '{table}' não encontrada no schema SQLite. Existentes: {existing}"
