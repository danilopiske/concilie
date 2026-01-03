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
        "SELECT Forma_de_pagamento, SUM(Valor_da_venda) as ValorTotal FROM vendas_processadas GROUP BY Forma_de_pagamento",
        engine,
    )


def get_vendas_por_mes(engine: Engine) -> pd.DataFrame:
    # View agregada: vendas por mês (MySQL)
    query = """
        SELECT DATE_FORMAT(Data_da_venda, '%Y-%m') as MesAno, COUNT(*) as Quantidade
        FROM vendas_processadas
        GROUP BY MesAno
        ORDER BY MesAno
    """

    return pd.read_sql(query, engine)


def get_valor_medio_por_bandeira(engine: Engine) -> pd.DataFrame:
    # View agregada: valor médio por bandeira
    return pd.read_sql(
        "SELECT Bandeira, AVG(Valor_da_venda) as ValorMedio FROM vendas_processadas GROUP BY Bandeira",
        engine,
    )


def get_vendas_semestral(engine: Engine) -> pd.DataFrame:
    """
    View agregada: vendas por semestre, bandeira e forma de pagamento
    Retorna: semestre (YYYY-S1/S2), bandeira, forma_pagamento, valor_total, quantidade, taxa_perc_minima
    """
    query = """
        SELECT 
            CONCAT(YEAR(Data_da_venda), '-S', IF(MONTH(Data_da_venda) <= 6, '1', '2')) as semestre,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima
        FROM vendas_processadas
        GROUP BY semestre, Bandeira, Forma_de_pagamento
        ORDER BY semestre, bandeira, forma_pagamento
    """
    return pd.read_sql(query, engine)


def get_vendas_trimestral(engine: Engine) -> pd.DataFrame:
    """
    View agregada: vendas por trimestre, bandeira e forma de pagamento
    Retorna: trimestre (YYYY-T1/T2/T3/T4), bandeira, forma_pagamento, valor_total, quantidade, taxa_perc_minima
    """
    query = """
        SELECT 
            CONCAT(YEAR(Data_da_venda), '-T', QUARTER(Data_da_venda)) as trimestre,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima
        FROM vendas_processadas
        GROUP BY trimestre, Bandeira, Forma_de_pagamento
        ORDER BY trimestre, bandeira, forma_pagamento
    """
    return pd.read_sql(query, engine)


def get_vendas_anual(engine: Engine) -> pd.DataFrame:
    """
    View agregada: vendas por ano, bandeira e forma de pagamento
    Retorna: ano (YYYY), bandeira, forma_pagamento, valor_total, quantidade, taxa_perc_minima
    """
    query = """
        SELECT 
            YEAR(Data_da_venda) as ano,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima
        FROM vendas_processadas
        GROUP BY ano, Bandeira, Forma_de_pagamento
        ORDER BY ano, bandeira, forma_pagamento
    """
    return pd.read_sql(query, engine)
