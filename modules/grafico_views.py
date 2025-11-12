import pandas as pd
from sqlalchemy.engine import Engine


def get_vendas_por_bandeira(engine: Engine) -> pd.DataFrame:
    # View agregada: vendas por bandeira
    return pd.read_sql(
        "SELECT Bandeira, COUNT(*) as Quantidade FROM vendas_processadas GROUP BY Bandeira",
        engine,
    )


def get_vendas_por_forma_pagamento(engine: Engine) -> pd.DataFrame:
    # View agregada: vendas por forma de pagamento
    return pd.read_sql(
        "SELECT Forma_de_pagamento, COUNT(*) as Quantidade FROM vendas_processadas GROUP BY Forma_de_pagamento",
        engine,
    )


def get_vendas_pizza_forma_pagamento(engine: Engine) -> pd.DataFrame:
    # View agregada: soma de vendas por forma de pagamento
    return pd.read_sql(
        "SELECT Forma_de_pagamento, SUM(vl_venda) as ValorTotal FROM vendas_processadas GROUP BY Forma_de_pagamento",
        engine,
    )


def get_vendas_por_mes(engine: Engine) -> pd.DataFrame:
    # View agregada: vendas por mês
    return pd.read_sql(
        """
        SELECT DATE_FORMAT(Data_da_venda, '%Y-%m') as MesAno, COUNT(*) as Quantidade
        FROM vendas_processadas
        GROUP BY MesAno
        ORDER BY MesAno
    """,
        engine,
    )


def get_valor_medio_por_bandeira(engine: Engine) -> pd.DataFrame:
    # View agregada: valor médio por bandeira
    return pd.read_sql(
        "SELECT Bandeira, AVG(Valor_da_venda) as ValorMedio FROM vendas_processadas GROUP BY Bandeira",
        engine,
    )
