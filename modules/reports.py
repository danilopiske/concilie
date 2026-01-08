import pandas as pd
import numpy as np
import os
import re
import io
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import plotly.express as px
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.engine import Engine
import panel as pn
from sqlalchemy import text

from conf.funcoesbd import (
    fetch_all,
    fetch_one,
    listar_processamentoids,
    listar_processamentos_detalhado,
)


def _convert_placeholders(engine, sql: str) -> str:
    """
    Converte placeholders SQL conforme o banco de dados.
    Para MySQL: %s funciona com pandas.read_sql
    Para SQLite: precisa converter %s para ? (placeholder posicional)

    Args:
        engine: Engine SQLAlchemy
        sql: Query SQL com placeholders %s

    Returns:
        Query com placeholders adequados ao banco
    """
    db_type = engine.dialect.name.lower()

    if "sqlite" in db_type:
        # SQLite com pandas precisa de ? ao invés de %s
        return sql.replace("%s", "?")
    else:
        # MySQL aceita %s com pandas
        return sql


def format_currency_br(value: float) -> str:
    """
    Formata valor monetário no padrão brasileiro.
    Ex: 1234567.89 -> "R$ 1.234.567,89"
    """
    if pd.isna(value) or value is None:
        return "R$ 0,00"

    # Formatar no padrão americano primeiro e depois converter
    formatted = f"R$ {float(value):,.2f}"

    # Converter para padrão brasileiro: trocar ponto por vírgula e vírgula por ponto
    # Primeiro proteger os decimais
    if "." in formatted:
        parts = formatted.rsplit(".", 1)  # Dividir pela última ocorrência do ponto
        integer_part = parts[0].replace(
            ",", "."
        )  # Trocar vírgulas por pontos nos milhares
        decimal_part = parts[1]
        return f"{integer_part},{decimal_part}"
    else:
        return formatted.replace(",", ".")


def normalizar_forma_pagamento(forma_pagamento: str) -> str:
    """
    Normaliza a forma de pagamento para o formato: modalidade + espaço + tipo
    Remove acentos e padroniza a formatação.
    Ex: 'CRÉDITO A VISTA' -> 'CREDITO A VISTA'
    """
    if not forma_pagamento or pd.isna(forma_pagamento):
        return ""

    # Converter para string e maiúscula
    forma = str(forma_pagamento).upper().strip()

    # Remover acentos e caracteres especiais
    substitutions = {
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ã": "A",
        "Ä": "A",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "Í": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",
        "Ó": "O",
        "Ò": "O",
        "Ô": "O",
        "Õ": "O",
        "Ö": "O",
        "Ú": "U",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "Ç": "C",
        "Ñ": "N",
    }

    for acento, sem_acento in substitutions.items():
        forma = forma.replace(acento, sem_acento)

    # Normalizar espaços múltiplos
    forma = re.sub(r"\s+", " ", forma).strip()

    # Padronizar formatos comuns
    padronizacoes = {
        "CREDITO A VISTA": "CREDITO A VISTA",
        "CRÉDITO A VISTA": "CREDITO A VISTA",
        "DÉBITO A VISTA": "DEBITO A VISTA",
        "DEBITO A VISTA": "DEBITO A VISTA",
        "PARCELADO LOJA": "PARCELADO LOJA",
        "PARCELADO EMISSOR": "PARCELADO EMISSOR",
        "PIX": "PIX",
    }

    # Aplicar padronizações específicas
    for original, padronizado in padronizacoes.items():
        if original in forma:
            forma = padronizado
            break

    return forma


def filtrar_valores_rede_depara(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros específicos para valores de venda da REDE após processamento de de-para.

    Filtros aplicados:
    1. Remove valores de venda zerados ou nulos
    2. Remove valores negativos (estornos/cancelamentos)
    3. Aplica filtros específicos baseados na adquirente REDE
    4. Valida consistência entre valor_da_venda e outras colunas relacionadas
    """
    if df.empty:
        return df

    df_filtrado = df.copy()
    linhas_originais = len(df_filtrado)

    print(f"[DEBUG][REDE] Iniciando filtro de valores - {linhas_originais} registros")

    # Identificar se é processamento da REDE
    tem_rede = False
    colunas_adquirente = [
        "adquirente",
        "Adquirente",
        "ADQUIRENTE",
        "Bandeira",
        "bandeira",
    ]
    for col in colunas_adquirente:
        if col in df_filtrado.columns:
            rede_count = (
                df_filtrado[col]
                .astype(str)
                .str.upper()
                .str.contains("REDE", na=False)
                .sum()
            )
            if rede_count > 0:
                tem_rede = True
                print(
                    f"[DEBUG][REDE] Detectado {rede_count} registros da REDE na coluna {col}"
                )
                break

    if not tem_rede:
        print(
            f"[DEBUG][REDE] Nenhum registro da REDE detectado - aplicando filtros gerais"
        )

    # Filtro 1: Remover valores zerados ou nulos em Valor_da_venda
    colunas_valor = [
        "Valor_da_venda",
        "valor_da_venda",
        "vl_venda",
        "Valor da Transação",
    ]
    coluna_valor_encontrada = None

    for col in colunas_valor:
        if col in df_filtrado.columns:
            coluna_valor_encontrada = col
            break

    if coluna_valor_encontrada:
        # Converter para numérico
        df_filtrado[coluna_valor_encontrada] = pd.to_numeric(
            df_filtrado[coluna_valor_encontrada], errors="coerce"
        )

        # Remover valores nulos
        valores_nulos = df_filtrado[coluna_valor_encontrada].isnull().sum()
        if valores_nulos > 0:
            df_filtrado = df_filtrado[df_filtrado[coluna_valor_encontrada].notnull()]
            print(
                f"[DEBUG][REDE] Removidos {valores_nulos} registros com valores nulos"
            )

        # Remover valores zerados
        valores_zero = (df_filtrado[coluna_valor_encontrada] == 0).sum()
        if valores_zero > 0:
            df_filtrado = df_filtrado[df_filtrado[coluna_valor_encontrada] != 0]
            print(
                f"[DEBUG][REDE] Removidos {valores_zero} registros com valores zerados"
            )

        # Filtro específico para REDE: remover valores negativos (estornos/cancelamentos)
        if tem_rede:
            valores_negativos = (df_filtrado[coluna_valor_encontrada] < 0).sum()
            if valores_negativos > 0:
                df_filtrado = df_filtrado[df_filtrado[coluna_valor_encontrada] > 0]
                print(
                    f"[DEBUG][REDE] Removidos {valores_negativos} registros com valores negativos"
                )

        # Filtro de valores extremos (outliers) para REDE
        if tem_rede and len(df_filtrado) > 10:
            q1 = df_filtrado[coluna_valor_encontrada].quantile(0.01)
            q99 = df_filtrado[coluna_valor_encontrada].quantile(0.99)
            outliers = (
                (df_filtrado[coluna_valor_encontrada] < q1)
                | (df_filtrado[coluna_valor_encontrada] > q99)
            ).sum()

            if outliers > 0:
                df_filtrado = df_filtrado[
                    (df_filtrado[coluna_valor_encontrada] >= q1)
                    & (df_filtrado[coluna_valor_encontrada] <= q99)
                ]
                print(
                    f"[DEBUG][REDE] Removidos {outliers} outliers (valores < R$ {q1:.2f} ou > R$ {q99:.2f})"
                )

    linhas_finais = len(df_filtrado)
    linhas_removidas = linhas_originais - linhas_finais

    if linhas_removidas > 0:
        print(
            f"[DEBUG][REDE] Filtro concluído: {linhas_removidas} registros removidos ({linhas_removidas/linhas_originais*100:.2f}%)"
        )
        print(f"[DEBUG][REDE] Registros restantes: {linhas_finais}")
    else:
        print(f"[DEBUG][REDE] Nenhum registro foi filtrado")

    return df_filtrado


def calcular_previsao_pagamento_rede(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a previsão de pagamento específica para a adquirente REDE.

    Regra da REDE: Previsão de pagamento = Data_da_venda + 31 dias

    Args:
        df: DataFrame com os dados das vendas

    Returns:
        DataFrame com a coluna 'Previsão_de_pagamento' atualizada para registros da REDE
    """
    if df.empty:
        return df

    df_result = df.copy()
    linhas_originais = len(df_result)

    print(
        f"[DEBUG][REDE] Iniciando cálculo de previsão de pagamento - {linhas_originais} registros"
    )

    # Identificar registros da REDE
    tem_rede = False
    colunas_adquirente = [
        "adquirente",
        "Adquirente",
        "ADQUIRENTE",
        "Bandeira",
        "bandeira",
    ]

    mask_rede = pd.Series([False] * len(df_result), index=df_result.index)

    for col in colunas_adquirente:
        if col in df_result.columns:
            mask_col = (
                df_result[col].astype(str).str.upper().str.contains("REDE", na=False)
            )
            rede_count = mask_col.sum()
            if rede_count > 0:
                tem_rede = True
                mask_rede = mask_rede | mask_col
                print(
                    f"[DEBUG][REDE] Detectado {rede_count} registros da REDE na coluna {col}"
                )

    if not tem_rede:
        print(
            f"[DEBUG][REDE] Nenhum registro da REDE detectado - sem alterações na previsão"
        )
        return df_result

    # Buscar coluna de data da venda
    colunas_data_venda = [
        "Data_da_venda",
        "data_da_venda",
        "Data da Transação",
        "data_transacao",
    ]
    coluna_data_encontrada = None

    for col in colunas_data_venda:
        if col in df_result.columns:
            coluna_data_encontrada = col
            break

    if not coluna_data_encontrada:
        print(
            f"[DEBUG][REDE] Nenhuma coluna de data da venda encontrada - sem alterações"
        )
        return df_result

    # Garantir que existe a coluna de previsão de pagamento
    if "Previsão_de_pagamento" not in df_result.columns:
        df_result["Previsão_de_pagamento"] = pd.NaT

    # Converter data da venda para datetime
    try:
        df_result[coluna_data_encontrada] = pd.to_datetime(
            df_result[coluna_data_encontrada], errors="coerce"
        )
    except Exception as e:
        print(f"[DEBUG][REDE] Erro ao converter data da venda: {e}")
        return df_result

    # Aplicar regra da REDE: Data_da_venda + 31 dias
    registros_rede = mask_rede.sum()
    if registros_rede > 0:
        # Calcular previsão apenas para registros da REDE com data válida
        mask_data_valida = df_result[coluna_data_encontrada].notnull()
        mask_aplicar = mask_rede & mask_data_valida

        if mask_aplicar.any():
            df_result.loc[mask_aplicar, "Previsão_de_pagamento"] = df_result.loc[
                mask_aplicar, coluna_data_encontrada
            ] + pd.Timedelta(days=31)

            registros_atualizados = mask_aplicar.sum()
            print(
                f"[DEBUG][REDE] Previsão de pagamento calculada para {registros_atualizados} registros"
            )

            # Log de exemplo
            if registros_atualizados > 0:
                exemplo_idx = df_result[mask_aplicar].index[0]
                data_venda = df_result.loc[exemplo_idx, coluna_data_encontrada]
                previsao = df_result.loc[exemplo_idx, "Previsão_de_pagamento"]
                print(
                    f"[DEBUG][REDE] Exemplo: Venda {data_venda.strftime('%d/%m/%Y')} → Previsão {previsao.strftime('%d/%m/%Y')}"
                )
        else:
            print(f"[DEBUG][REDE] Nenhum registro da REDE com data válida encontrado")

    # Verificar se há registros não-REDE que precisam de tratamento diferente
    registros_nao_rede = (~mask_rede).sum()
    if registros_nao_rede > 0:
        print(
            f"[DEBUG][REDE] {registros_nao_rede} registros de outras adquirentes mantidos sem alteração"
        )

    return df_result


def log_tempo_execucao(funcao_nome: str, inicio: float) -> None:
    """Log do tempo de execução de uma função"""
    tempo_decorrido = time.time() - inicio
    print(f"[DEBUG] {funcao_nome}: {tempo_decorrido:.3f}s")


def read_sql_safe(
    sql: str,
    engine: Engine,
    params: tuple = None,
    chunksize: int = 50000,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Lê dados do SQL com proteção contra erros de timeout e packet sequence.

    - Usa chunked reading para datasets grandes
    - Retry automático em caso de erro
    - Reconexão automática se necessário

    Args:
        sql: Query SQL
        engine: Engine SQLAlchemy
        params: Parâmetros da query
        chunksize: Tamanho dos chunks (padrão: 50k)
        max_retries: Tentativas máximas (padrão: 3)

    Returns:
        DataFrame consolidado
    """
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Tentativa {attempt + 1}/{max_retries} de leitura SQL")

            # Tentar leitura em chunks primeiro
            try:
                chunks = []
                for chunk in pd.read_sql(
                    sql, engine, params=params, chunksize=chunksize
                ):
                    chunks.append(chunk)

                if chunks:
                    df = pd.concat(chunks, ignore_index=True)
                    print(
                        f"[DEBUG] ✓ Leitura em chunks bem-sucedida: {len(chunks)} chunks, {len(df)} registros"
                    )
                    return df
                else:
                    print("[DEBUG] ✓ Query retornou 0 registros")
                    return pd.DataFrame()

            except Exception as chunk_error:
                print(f"[DEBUG] Chunked reading falhou: {chunk_error}")
                print(f"[DEBUG] Tentando leitura direta...")

                # Fallback: leitura direta
                df = pd.read_sql(sql, engine, params=params)
                print(f"[DEBUG] ✓ Leitura direta bem-sucedida: {len(df)} registros")
                return df

        except Exception as e:
            error_msg = str(e).lower()

            if "packet sequence" in error_msg or "lost connection" in error_msg:
                print(
                    f"[ERROR] Erro de conexão MySQL (tentativa {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    print("[DEBUG] Aguardando 2s antes de reconectar...")
                    time.sleep(2)

                    # Tentar reconectar
                    try:
                        engine.dispose()
                        print("[DEBUG] Pool de conexões descartado - reconectando...")
                    except:
                        pass
                else:
                    print(f"[ERROR] Falha após {max_retries} tentativas")
                    raise
            else:
                # Outro tipo de erro - não retenta
                print(f"[ERROR] Erro SQL não relacionado a conexão: {e}")
                raise

    return pd.DataFrame()


def calcular_periodo_completo(
    engine: Engine,
    processamento_id: str,
    adquirente: str = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Calcula o período completo considerando todas as datas do processamento:
    - vendas_processadas (Data_da_venda)
    - vendas_filtradas (Data_da_venda)
    - recebiveis_processados (data_recebivel)
    - recebiveis_filtrados (data_recebivel)

    Retorna a menor data como inicial e a maior como final, independente da origem.

    Args:
        engine: Engine de conexão com o banco de dados
        processamento_id: ID do processamento
        adquirente: Filtro opcional por adquirente
        data_inicio: Filtro opcional por data inicial
        data_fim: Filtro opcional por data final

    Returns:
        Tupla com (primeira_data, ultima_data)
    """
    print(f"[DEBUG] Calculando período completo para processamento: {processamento_id}")

    todas_as_datas = []

    try:
        # 1. Datas das vendas processadas
        vendas_sql = (
            "SELECT Data_da_venda FROM vendas_processadas WHERE processamentoid = %s"
        )
        params_vendas = [processamento_id]
        if adquirente:
            vendas_sql += " AND adquirente = %s"
            params_vendas.append(adquirente)
        if data_inicio:
            vendas_sql += " AND Data_da_venda >= %s"
            params_vendas.append(data_inicio)
        if data_fim:
            vendas_sql += " AND Data_da_venda <= %s"
            params_vendas.append(data_fim)

        vendas_sql = _convert_placeholders(engine, vendas_sql)
        df_vendas = pd.read_sql(vendas_sql, engine, params=tuple(params_vendas))
        if not df_vendas.empty and "Data_da_venda" in df_vendas.columns:
            datas_vendas = pd.to_datetime(
                df_vendas["Data_da_venda"], errors="coerce"
            ).dropna()
            todas_as_datas.extend(datas_vendas.tolist())
            print(
                f"[DEBUG] Encontradas {len(datas_vendas)} datas de venda em vendas_processadas"
            )

        # 2. Datas das vendas filtradas
        filtradas_sql = (
            "SELECT Data_da_venda FROM vendas_filtradas WHERE processamentoid = %s"
        )
        params_filtradas = [processamento_id]
        if adquirente:
            filtradas_sql += " AND adquirente = %s"
            params_filtradas.append(adquirente)
        if data_inicio:
            filtradas_sql += " AND Data_da_venda >= %s"
            params_filtradas.append(data_inicio)
        if data_fim:
            filtradas_sql += " AND Data_da_venda <= %s"
            params_filtradas.append(data_fim)

        filtradas_sql = _convert_placeholders(engine, filtradas_sql)
        df_filtradas = pd.read_sql(
            filtradas_sql, engine, params=tuple(params_filtradas)
        )
        if not df_filtradas.empty and "Data_da_venda" in df_filtradas.columns:
            datas_filtradas = pd.to_datetime(
                df_filtradas["Data_da_venda"], errors="coerce"
            ).dropna()
            todas_as_datas.extend(datas_filtradas.tolist())
            print(
                f"[DEBUG] Encontradas {len(datas_filtradas)} datas de venda em vendas_filtradas"
            )

        # 3. Datas dos recebíveis processados
        rec_proc_sql = "SELECT data_recebivel FROM recebiveis_processados WHERE processamentoid = %s"
        rec_proc_sql = _convert_placeholders(engine, rec_proc_sql)
        df_rec_proc = pd.read_sql(rec_proc_sql, engine, params=(processamento_id,))
        if not df_rec_proc.empty and "data_recebivel" in df_rec_proc.columns:
            datas_rec_proc = pd.to_datetime(
                df_rec_proc["data_recebivel"], errors="coerce"
            ).dropna()
            todas_as_datas.extend(datas_rec_proc.tolist())
            print(
                f"[DEBUG] Encontradas {len(datas_rec_proc)} datas de recebível em recebiveis_processados"
            )

        # 4. Datas dos recebíveis filtrados (se existir a tabela)
        try:
            rec_filt_sql = "SELECT data_recebivel FROM recebiveis_filtrados WHERE processamentoid = %s"
            rec_filt_sql = _convert_placeholders(engine, rec_filt_sql)
            df_rec_filt = pd.read_sql(rec_filt_sql, engine, params=(processamento_id,))
            if not df_rec_filt.empty and "data_recebivel" in df_rec_filt.columns:
                datas_rec_filt = pd.to_datetime(
                    df_rec_filt["data_recebivel"], errors="coerce"
                ).dropna()
                todas_as_datas.extend(datas_rec_filt.tolist())
                print(
                    f"[DEBUG] Encontradas {len(datas_rec_filt)} datas de recebível em recebiveis_filtrados"
                )
        except Exception as e:
            print(f"[DEBUG] Tabela recebiveis_filtrados não encontrada ou erro: {e}")

        # Calcular período final considerando todas as datas (vendas + recebíveis)
        if todas_as_datas:
            todas_as_datas = pd.Series(todas_as_datas).sort_values()
            primeira_data = todas_as_datas.min()
            ultima_data = todas_as_datas.max()

            print(f"[DEBUG] Total de datas coletadas: {len(todas_as_datas)}")
            print(
                f"[DEBUG] Primeira data (tipo {type(primeira_data)}): {primeira_data}"
            )
            print(f"[DEBUG] Última data (tipo {type(ultima_data)}): {ultima_data}")
            print(f"[DEBUG] Período: {(ultima_data - primeira_data).days + 1} dias")
            print(f"[DEBUG] Amostra das datas: {todas_as_datas.head(3).tolist()}")

            return primeira_data, ultima_data
        else:
            print("[DEBUG] Nenhuma data encontrada nas tabelas")
            return None, None

    except Exception as e:
        print(f"[ERROR] Erro ao calcular período completo: {e}")
        return None, None


def obter_adquirentes_e_periodo_processamento(
    engine: Engine, processamento_id: str
) -> tuple[List[str], dict]:
    """
    Obtém os adquirentes únicos e o período de vendas de um processamento específico.
    Usa APENAS vendas_calculos (dados já processados e denormalizados).

    Args:
        engine: Engine do SQLAlchemy
        processamento_id: ID do processamento (calc_id)

    Returns:
        Tupla contendo:
        - Lista de adquirentes únicos, ordenada alfabeticamente
        - Dicionário com período {'data_min': date, 'data_max': date} ou vazio se sem dados
    """
    query = """
        SELECT DISTINCT 
            adquirente,
            MIN(data_venda) OVER() as data_min,
            MAX(data_venda) OVER() as data_max
        FROM vendas_calculos
        WHERE calc_id = :calc_id
        AND adquirente IS NOT NULL 
        AND adquirente != ''
        ORDER BY adquirente
    """

    try:
        print(
            f"[DEBUG obter_adquirentes_e_periodo] Buscando dados para calc_id: {processamento_id}"
        )
        with engine.connect() as conn:
            result = conn.execute(text(query), {"calc_id": processamento_id})
            rows = list(result)
            print(f"[DEBUG obter_adquirentes_e_periodo] Encontradas {len(rows)} linhas")

            if not rows:
                print("[DEBUG obter_adquirentes_e_periodo] Nenhuma linha encontrada")
                return [], {}

            adquirentes = [str(row[0]).strip() for row in rows if row[0]]
            print(f"[DEBUG obter_adquirentes_e_periodo] Adquirentes: {adquirentes}")

            # Pegar período da primeira linha (todas têm os mesmos valores devido ao OVER())
            if rows and rows[0][1] and rows[0][2]:
                from datetime import datetime, date

                # SQLite retorna strings, MySQL retorna date/datetime objects
                data_min = rows[0][1]
                data_max = rows[0][2]

                # Converter strings para date se necessário
                if isinstance(data_min, str):
                    # Tentar diferentes formatos (SQLite pode retornar com ou sem hora)
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                    ]:
                        try:
                            data_min = datetime.strptime(data_min, fmt).date()
                            break
                        except ValueError:
                            continue

                if isinstance(data_max, str):
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S.%f",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                    ]:
                        try:
                            data_max = datetime.strptime(data_max, fmt).date()
                            break
                        except ValueError:
                            continue

                periodo = {"data_min": data_min, "data_max": data_max}
                print(f"[DEBUG obter_adquirentes_e_periodo] Período: {periodo}")
            else:
                periodo = {}
                print("[DEBUG obter_adquirentes_e_periodo] Período vazio")

            return adquirentes, periodo
    except Exception as e:
        print(
            f"⚠️ Erro ao buscar adquirentes e período do processamento {processamento_id}: {str(e)}"
        )
        import traceback

        traceback.print_exc()
        return [], {}


def obter_adquirentes_distintos_processamento(
    engine: Engine, processamento_id: str
) -> List[str]:
    """
    Busca todos os adquirentes distintos associados a um processamento específico.

    Utiliza JOIN entre vendas_processadas e vendas_calculos, filtrando por calc_id.

    Mantida para compatibilidade. Usa a nova função internamente.

    Args:
        engine: Engine de conexão com o banco de dados
        processamento_id: ID do processamento para buscar adquirentes

    Returns:
        Lista de strings com os adquirentes distintos encontrados
    """
    adquirentes, _ = obter_adquirentes_e_periodo_processamento(engine, processamento_id)
    return adquirentes


def calcular_estatisticas_taxas(df_calculos: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula a maior e a menor taxa da coluna tx_venda.
    Filtra valores 0 e NULL para evitar distorção das estatísticas.
    """
    if df_calculos.empty or "tx_venda" not in df_calculos.columns:
        return {"max_taxa": 0, "min_taxa": 0}

    # Converter para numérico e remover NaN
    taxas = pd.to_numeric(df_calculos["tx_venda"], errors="coerce").dropna()

    # Filtrar taxas maiores que 0 (desconsidera NULL e 0)
    taxas_validas = taxas[taxas > 0]

    if taxas_validas.empty:
        return {"max_taxa": 0, "min_taxa": 0}

    return {"max_taxa": taxas_validas.max(), "min_taxa": taxas_validas.min()}


def calcular_perdas_por_semestre(
    df_processadas: pd.DataFrame,
    df_calculos: pd.DataFrame,
    incluir_faturamento: bool = False,
) -> pd.DataFrame:
    """
    Calcula perdas monetárias MDR e RR, e opcionalmente faturamento e percentual de perda por semestre.

    Args:
        df_processadas: DataFrame com vendas processadas
        df_calculos: DataFrame com cálculos de taxas
        incluir_faturamento: Se True, inclui colunas de faturamento bruto e % perda (padrão: False)
    """
    if df_processadas.empty or df_calculos.empty:
        print("[DEBUG] DataFrames vazios - retornando DataFrame vazio")
        return pd.DataFrame(
            columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"]
        )

    print(f"[DEBUG] Colunas df_processadas: {df_processadas.columns.tolist()}")
    print(f"[DEBUG] Colunas df_calculos: {df_calculos.columns.tolist()}")

    # Verificar se deve calcular faturamento
    calcula_faturamento = incluir_faturamento and "vl_venda" in df_calculos.columns
    if incluir_faturamento and "vl_venda" not in df_calculos.columns:
        print(
            "[DEBUG] incluir_faturamento=True mas vl_venda não disponível - não será calculado faturamento"
        )

    colunas_calculos = ["id_venda", "perda"]

    # Adicionar perda_rr se disponível
    tem_perda_rr = "perda_rr" in df_calculos.columns
    if tem_perda_rr:
        colunas_calculos.append("perda_rr")
        print("[DEBUG] perda_rr detectada - será incluída nos cálculos")
    else:
        print("[DEBUG] perda_rr não encontrada - usando apenas perda MDR")

    if calcula_faturamento:
        colunas_calculos.append("vl_venda")
        print("[DEBUG] vl_venda detectada - calculando faturamento")

    # Verificar se as colunas existem antes do merge
    if "id" not in df_processadas.columns:
        print("[ERROR] Coluna 'id' não encontrada em df_processadas")
        return pd.DataFrame(
            columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"]
        )

    if "Data_da_venda" not in df_processadas.columns:
        print("[ERROR] Coluna 'Data_da_venda' não encontrada em df_processadas")
        return pd.DataFrame(
            columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"]
        )

    # Verificar colunas do df_calculos
    missing_cols = [col for col in colunas_calculos if col not in df_calculos.columns]
    if missing_cols:
        print(f"[ERROR] Colunas ausentes em df_calculos: {missing_cols}")
        return pd.DataFrame(
            columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"]
        )

    df_merged = pd.merge(
        df_processadas[["id", "Data_da_venda"]],
        df_calculos[colunas_calculos],
        left_on="id",
        right_on="id_venda",
        how="inner",
    )

    print(f"[DEBUG] Merge realizado - {len(df_merged)} registros resultantes")

    df_merged["Data_da_venda"] = pd.to_datetime(
        df_merged["Data_da_venda"], errors="coerce"
    )
    df_merged.dropna(subset=["Data_da_venda"], inplace=True)
    df_merged["Ano"] = df_merged["Data_da_venda"].dt.year
    df_merged["Semestre"] = df_merged["Data_da_venda"].dt.month.apply(
        lambda m: 1 if m <= 6 else 2
    )
    df_merged["Ano-Semestre"] = (
        df_merged["Ano"].astype(str) + "-" + df_merged["Semestre"].astype(str)
    )

    if calcula_faturamento:
        # Agregação simples sem MultiIndex
        perdas = (
            df_merged.groupby("Ano-Semestre")
            .agg({"perda": "sum", "vl_venda": "sum"})
            .reset_index()
        )

        # Renomear colunas
        perdas.rename(
            columns={"perda": "perda_monetaria_mdr", "vl_venda": "faturamento_bruto"},
            inplace=True,
        )

        # Adicionar perda_rr se disponível
        if tem_perda_rr:
            perdas_rr = (
                df_merged.groupby("Ano-Semestre")["perda_rr"].sum().reset_index()
            )
            perdas = perdas.merge(perdas_rr, on="Ano-Semestre", how="left")
            perdas.rename(columns={"perda_rr": "perda_monetaria_rr"}, inplace=True)

        print(
            f"[DEBUG] Colunas após agregação com faturamento: {perdas.columns.tolist()}"
        )

        # Calcular totais de perda
        perdas["perda_total"] = perdas["perda_monetaria_mdr"].fillna(0).astype(float)
        if tem_perda_rr:
            perdas["perda_total"] += (
                perdas["perda_monetaria_rr"].fillna(0).astype(float)
            )

        perdas["% Perda"] = np.where(
            perdas["faturamento_bruto"] > 0,
            (100 * perdas["perda_total"] / perdas["faturamento_bruto"]),
            0,
        ).round(2)

        perdas["Faturamento Bruto"] = (
            perdas["faturamento_bruto"].round(2).apply(lambda x: format_currency_br(x))
        )

        final_columns = [
            "Ano-Semestre",
            "Faturamento Bruto",
            "Perda Monetária MDR",
        ]
        if tem_perda_rr:
            final_columns.append("Perdas por Antecipações")
        final_columns.extend(["Perda Total", "% Perda"])
    else:
        # Agregação simples sem MultiIndex
        perdas = df_merged.groupby("Ano-Semestre").agg({"perda": "sum"}).reset_index()

        # Renomear colunas
        perdas.rename(columns={"perda": "perda_monetaria_mdr"}, inplace=True)

        # Adicionar perda_rr se disponível
        if tem_perda_rr:
            perdas_rr = (
                df_merged.groupby("Ano-Semestre")["perda_rr"].sum().reset_index()
            )
            perdas = perdas.merge(perdas_rr, on="Ano-Semestre", how="left")
            perdas.rename(columns={"perda_rr": "perda_monetaria_rr"}, inplace=True)

        print(
            f"[DEBUG] Colunas após agregação sem faturamento: {perdas.columns.tolist()}"
        )

        # Calcular totais de perda
        perdas["perda_total"] = perdas["perda_monetaria_mdr"].fillna(0).astype(float)
        if tem_perda_rr:
            perdas["perda_total"] += (
                perdas["perda_monetaria_rr"].fillna(0).astype(float)
            )

        final_columns = ["Ano-Semestre", "Perda Monetária MDR"]
        if tem_perda_rr:
            final_columns.append("Perdas por Antecipações")
        final_columns.append("Perda Total")

    # Calcular totais gerais antes da formatação
    total_perda_mdr = perdas["perda_monetaria_mdr"].fillna(0).astype(float).sum()
    total_perda_total = perdas["perda_total"].fillna(0).astype(float).sum()

    if calcula_faturamento:
        # Calcular total do faturamento bruto (desformatado)
        total_faturamento_bruto = (
            perdas["faturamento_bruto"].fillna(0).astype(float).sum()
        )
        # Calcular percentual geral de perda
        percentual_geral = (
            (100 * total_perda_total / total_faturamento_bruto)
            if total_faturamento_bruto > 0
            else 0
        )

    if tem_perda_rr:
        total_perda_rr = perdas["perda_monetaria_rr"].fillna(0).astype(float).sum()

    # Formatação das colunas monetárias
    perdas["Perda Monetária MDR"] = (
        perdas["perda_monetaria_mdr"]
        .fillna(0)
        .astype(float)
        .round(2)
        .apply(format_currency_br)
    )
    if tem_perda_rr:
        perdas["Perdas por Antecipações"] = (
            perdas["perda_monetaria_rr"]
            .fillna(0)
            .astype(float)
            .round(2)
            .apply(format_currency_br)
        )
    perdas["Perda Total"] = (
        perdas["perda_total"].fillna(0).astype(float).round(2).apply(format_currency_br)
    )
    perdas.sort_values("Ano-Semestre", inplace=True)

    # Adicionar linha de total
    linha_total = {"Ano-Semestre": "** TOTAL GERAL **"}

    if calcula_faturamento:
        linha_total["Faturamento Bruto"] = format_currency_br(total_faturamento_bruto)
        linha_total["% Perda"] = f"{percentual_geral:.2f}"

    linha_total["Perda Monetária MDR"] = format_currency_br(total_perda_mdr)

    if tem_perda_rr:
        linha_total["Perdas por Antecipações"] = format_currency_br(total_perda_rr)

    linha_total["Perda Total"] = format_currency_br(total_perda_total)

    # Converter para DataFrame e adicionar
    df_total = pd.DataFrame([linha_total])
    perdas = pd.concat([perdas, df_total], ignore_index=True)

    return perdas[final_columns]


def calcular_min_max_taxas_agrupado(df_merged: pd.DataFrame) -> pd.DataFrame:
    """Calcula as taxas min e max agrupadas por Semestre, Bandeira e Forma de Pagamento."""
    required_cols = ["Data_da_venda", "Bandeira", "Forma_de_pagamento", "tx_venda"]
    if df_merged.empty or not all(col in df_merged.columns for col in required_cols):
        return pd.DataFrame()

    df = df_merged.copy()
    df["Data_da_venda"] = pd.to_datetime(df["Data_da_venda"], errors="coerce")
    df.dropna(subset=["Data_da_venda"], inplace=True)
    df["Ano"] = df["Data_da_venda"].dt.year
    df["Semestre"] = df["Data_da_venda"].dt.month.apply(lambda m: 1 if m <= 6 else 2)
    df["Ano-Semestre"] = df["Ano"].astype(str) + "-" + df["Semestre"].astype(str)

    df["tx_venda"] = pd.to_numeric(df["tx_venda"], errors="coerce")
    df.dropna(subset=["tx_venda"], inplace=True)

    agrupado = (
        df.groupby(["Ano-Semestre", "Bandeira", "Forma_de_pagamento"])
        .agg(Taxa_Min=("tx_venda", "min"), Taxa_Max=("tx_venda", "max"))
        .reset_index()
    )
    agrupado.sort_values(by=["Ano-Semestre", "Bandeira"], inplace=True)
    return agrupado


def obter_evidencias_transacoes(
    engine: Engine,
    processamento_id: str,
    calc_tipo: str = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Busca evidências de transações para o relatório analítico:
    - Top 3 maiores valores de transação
    - Top 3 menores valores de transação
    - Top 3 maiores taxas
    - Top 3 menores taxas

    Retorna dict com DataFrames formatados para cada categoria.
    """
    print(f"[DEBUG] Buscando evidências para processamento: {processamento_id}")

    resultado = {
        "maiores_valores": pd.DataFrame(),
        "menores_valores": pd.DataFrame(),
        "maiores_taxas": pd.DataFrame(),
        "menores_taxas": pd.DataFrame(),
    }

    try:
        # Query para buscar transações - SEM JOIN! Todos os campos em vendas_calculos
        sql = """
        SELECT 
            vc.data_venda AS Data_da_venda,
            vc.bandeira AS Bandeira,
            vc.forma_pagamento,
            vc.vl_venda,
            vc.tx_venda,
            vc.arquivo_origem,
            vc.nsu,
            vc.cod_autorizacao
        FROM vendas_calculos vc
        WHERE vc.calc_id = %s
        """

        params = [processamento_id]

        if calc_tipo:
            sql += " AND vc.calc_tipo = %s"
            params.append(calc_tipo)

        if data_inicio:
            sql += " AND vc.data_venda >= %s"
            params.append(data_inicio)

        if data_fim:
            sql += " AND vc.data_venda <= %s"
            params.append(data_fim)

        params = tuple(params)

        sql = _convert_placeholders(engine, sql)

        # Usar read_sql_safe para proteção contra timeouts
        df = read_sql_safe(sql, engine, params=params)

        if df.empty:
            print("[DEBUG] Nenhuma transação encontrada para evidências")
            return resultado

        print(f"[DEBUG] {len(df)} transações carregadas para evidências")

        # Converter tipos
        df["Data_da_venda"] = pd.to_datetime(df["Data_da_venda"], errors="coerce")
        df["vl_venda"] = pd.to_numeric(df["vl_venda"], errors="coerce")
        df["tx_venda"] = pd.to_numeric(df["tx_venda"], errors="coerce")

        # Remover NaN
        df.dropna(subset=["Data_da_venda", "vl_venda", "tx_venda"], inplace=True)

        # Garantir que arquivo_origem seja string e substituir nulos por "N/A"
        df["arquivo_origem"] = df["arquivo_origem"].fillna("N/A").astype(str)
        df["nsu"] = df["nsu"].fillna("N/A").astype(str)
        df["cod_autorizacao"] = df["cod_autorizacao"].fillna("N/A").astype(str)

        # Função auxiliar para formatar evidências
        def formatar_evidencias(df_top, colunas_origem):
            df_formatted = df_top[colunas_origem].copy()
            df_formatted["Data"] = df_formatted["Data_da_venda"].dt.strftime("%d/%m/%Y")
            df_formatted["Valor"] = df_formatted["vl_venda"].apply(format_currency_br)
            df_formatted["Taxa (%)"] = (
                df_formatted["tx_venda"].round(2).astype(str) + "%"
            )
            df_formatted.rename(
                columns={
                    "forma_pagamento": "Forma de Pagamento",
                    "arquivo_origem": "Arquivo Origem",
                    "nsu": "NSU",
                    "cod_autorizacao": "Cód.Autorização",
                },
                inplace=True,
            )
            return df_formatted[
                [
                    "Data",
                    "Bandeira",
                    "Forma de Pagamento",
                    "Valor",
                    "Taxa (%)",
                    "NSU",
                    "Cód.Autorização",
                    "Arquivo Origem",
                ]
            ]

        colunas_base = [
            "Data_da_venda",
            "Bandeira",
            "forma_pagamento",
            "vl_venda",
            "tx_venda",
            "nsu",
            "cod_autorizacao",
            "arquivo_origem",
        ]

        # TOP 3 MAIORES VALORES
        top_maiores_valores = df.nlargest(3, "vl_venda")
        resultado["maiores_valores"] = formatar_evidencias(
            top_maiores_valores, colunas_base
        )

        # TOP 3 MENORES VALORES (filtrar valores > 0)
        df_valores_positivos = df[df["vl_venda"] > 0]
        if not df_valores_positivos.empty:
            top_menores_valores = df_valores_positivos.nsmallest(3, "vl_venda")
            resultado["menores_valores"] = formatar_evidencias(
                top_menores_valores, colunas_base
            )

        # TOP 3 MAIORES TAXAS (filtrar taxas > 0)
        df_taxas_positivas = df[df["tx_venda"] > 0]
        if not df_taxas_positivas.empty:
            top_maiores_taxas = df_taxas_positivas.nlargest(3, "tx_venda")
            resultado["maiores_taxas"] = formatar_evidencias(
                top_maiores_taxas, colunas_base
            )

            # TOP 3 MENORES TAXAS (filtrar taxas > 0)
            top_menores_taxas = df_taxas_positivas.nsmallest(3, "tx_venda")
            resultado["menores_taxas"] = formatar_evidencias(
                top_menores_taxas, colunas_base
            )

        print(f"[DEBUG] Evidências geradas com sucesso")

    except Exception as e:
        print(f"[ERROR] Erro ao buscar evidências: {e}")
        import traceback

        traceback.print_exc()

    return resultado


def calcular_contagem_taxas_agrupado(df_merged: pd.DataFrame) -> pd.DataFrame:
    """Conta as taxas agrupadas por Ano-Semestre, Bandeira e Forma de Pagamento."""
    if df_merged.empty or "Data_da_venda" not in df_merged.columns:
        return pd.DataFrame()

    df = df_merged.copy()
    df["Data_da_venda"] = pd.to_datetime(df["Data_da_venda"], errors="coerce")
    df.dropna(subset=["Data_da_venda"], inplace=True)
    df["Ano"] = df["Data_da_venda"].dt.year
    df["Semestre"] = df["Data_da_venda"].dt.month.apply(lambda m: 1 if m <= 6 else 2)
    df["Ano-Semestre"] = df["Ano"].astype(str) + "-" + df["Semestre"].astype(str)

    contagem = (
        df.groupby(["Ano-Semestre", "Bandeira", "Forma_de_pagamento"])
        .agg(Contagem=("tx_venda", "count"))
        .reset_index()
    )
    return contagem


def calcular_sumario_recebiveis(
    engine: Engine,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """Busca e sumariza os recebíveis processados para o relatório."""
    sql = "SELECT * FROM recebiveis_processados WHERE processamentoid = %s"
    params = [processamento_id]

    if data_inicio:
        sql += " AND data_recebivel >= %s"
        params.append(data_inicio)

    if data_fim:
        sql += " AND data_recebivel <= %s"
        params.append(data_fim)
    sql = _convert_placeholders(engine, sql)
    try:
        df = pd.read_sql(sql, engine, params=tuple(params))
    except Exception as e:
        print(f"Não foi possível buscar recebíveis: {e}")
        return pd.DataFrame()

    if df.empty or "data_recebivel" not in df.columns:
        return pd.DataFrame()

    df["data_recebivel"] = pd.to_datetime(df["data_recebivel"], errors="coerce")
    df.dropna(subset=["data_recebivel"], inplace=True)
    df["Ano"] = df["data_recebivel"].dt.year
    df["Semestre"] = df["data_recebivel"].dt.month.apply(lambda m: 1 if m <= 6 else 2)
    df["Ano-Semestre"] = df["Ano"].astype(str) + "-" + df["Semestre"].astype(str)

    sumario = (
        df.groupby(["Ano-Semestre", "lancamento"])
        .agg(Valor_Total=("valor_recebivel", "sum"))
        .reset_index()
    )

    # Garantir tipo numérico antes de arredondar
    sumario["Valor_Total"] = pd.to_numeric(
        sumario["Valor_Total"], errors="coerce"
    ).fillna(0)
    sumario["Valor Total"] = sumario["Valor_Total"].round(2).apply(format_currency_br)
    return sumario[["Ano-Semestre", "lancamento", "Valor Total"]].rename(
        columns={"lancamento": "Lançamento"}
    )


def calcular_tabela_consolidada_mensal(
    engine: Engine,
    processamento_id: str,
    df_vendas_processadas: pd.DataFrame,
    df_vendas_calculos: pd.DataFrame,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Calcula tabela consolidada mensal com:
    - Ano-Semestre
    - Perda Monetária MDR
    - Perda por RR
    - Aluguéis de Máquinas
    - Outros Recebíveis

    Args:
        engine: Engine de conexão com banco
        processamento_id: ID do processamento
        df_vendas_processadas: DataFrame com vendas processadas
        df_vendas_calculos: DataFrame com cálculos de vendas

    Returns:
        DataFrame com a tabela consolidada
    """
    print(
        f"[DEBUG] Calculando tabela consolidada mensal para processamento: {processamento_id}"
    )

    # 1. Preparar base com vendas (perda MDR e perda RR)
    if not df_vendas_processadas.empty and not df_vendas_calculos.empty:
        df_merged = pd.merge(
            df_vendas_processadas[["id", "Data_da_venda", "Taxas_RR", "Valor_RR"]],
            df_vendas_calculos[["id_venda", "perda", "perda_rr"]],
            left_on="id",
            right_on="id_venda",
            how="inner",
        )

        df_merged["Data_da_venda"] = pd.to_datetime(
            df_merged["Data_da_venda"], errors="coerce"
        )
        df_merged.dropna(subset=["Data_da_venda"], inplace=True)
        df_merged["Ano"] = df_merged["Data_da_venda"].dt.year
        df_merged["Semestre"] = df_merged["Data_da_venda"].dt.month.apply(
            lambda m: 1 if m <= 6 else 2
        )
        df_merged["Ano-Semestre"] = (
            df_merged["Ano"].astype(str) + "-" + df_merged["Semestre"].astype(str)
        )

        # Agrupar perdas por semestre
        perdas_semestre = (
            df_merged.groupby("Ano-Semestre")
            .agg(perda_mdr=("perda", "sum"), perda_rr=("perda_rr", "sum"))
            .reset_index()
        )
    else:
        perdas_semestre = pd.DataFrame(
            columns=["Ano-Semestre", "perda_mdr", "perda_rr"]
        )

    # 2. Buscar recebíveis PROCESSADOS (não filtrados) para aluguéis e outros
    try:
        sql_recebiveis = """
        SELECT 
            data_recebivel,
            lancamento,
            valor_recebivel
        FROM recebiveis_processados 
        WHERE processamentoid = %s
        """
        params_rec = [processamento_id]

        if data_inicio:
            sql_recebiveis += " AND data_recebivel >= %s"
            params_rec.append(data_inicio)

        if data_fim:
            sql_recebiveis += " AND data_recebivel <= %s"
            params_rec.append(data_fim)

        sql_recebiveis = _convert_placeholders(engine, sql_recebiveis)
        df_rec_proc = pd.read_sql(sql_recebiveis, engine, params=tuple(params_rec))

        if not df_rec_proc.empty:
            df_rec_proc["data_recebivel"] = pd.to_datetime(
                df_rec_proc["data_recebivel"], errors="coerce"
            )
            df_rec_proc.dropna(subset=["data_recebivel"], inplace=True)
            df_rec_proc["Ano"] = df_rec_proc["data_recebivel"].dt.year
            df_rec_proc["Semestre"] = df_rec_proc["data_recebivel"].dt.month.apply(
                lambda m: 1 if m <= 6 else 2
            )
            df_rec_proc["Ano-Semestre"] = (
                df_rec_proc["Ano"].astype(str)
                + "-"
                + df_rec_proc["Semestre"].astype(str)
            )

            # Identificar aluguéis de máquinas (contém "maquina", "aluguel", "locacao", etc)
            palavras_aluguel = [
                "maquina",
                "máquina",
                "aluguel",
                "alugel",
                "locacao",
                "locação",
                "pos",
                "equipamento",
            ]

            def eh_aluguel_maquina(lancamento: str) -> bool:
                if pd.isna(lancamento):
                    return False
                lancamento_lower = str(lancamento).lower()
                return any(palavra in lancamento_lower for palavra in palavras_aluguel)

            df_rec_proc["eh_aluguel"] = df_rec_proc["lancamento"].apply(
                eh_aluguel_maquina
            )

            # Agrupar por semestre: aluguéis vs outros
            alugueis_semestre = (
                df_rec_proc[df_rec_proc["eh_aluguel"]]
                .groupby("Ano-Semestre")
                .agg(aluguel_maquinas=("valor_recebivel", "sum"))
                .reset_index()
            )

            outros_recebiveis_semestre = (
                df_rec_proc[~df_rec_proc["eh_aluguel"]]
                .groupby("Ano-Semestre")
                .agg(outros_recebiveis=("valor_recebivel", "sum"))
                .reset_index()
            )

            print(f"[DEBUG] Recebíveis processados encontrados: {len(df_rec_proc)}")
            print(
                f"[DEBUG] Aluguéis de máquinas: {len(df_rec_proc[df_rec_proc['eh_aluguel']])} registros"
            )
            print(
                f"[DEBUG] Outros recebíveis: {len(df_rec_proc[~df_rec_proc['eh_aluguel']])} registros"
            )
        else:
            alugueis_semestre = pd.DataFrame(
                columns=["Ano-Semestre", "aluguel_maquinas"]
            )
            outros_recebiveis_semestre = pd.DataFrame(
                columns=["Ano-Semestre", "outros_recebiveis"]
            )
            print(f"[DEBUG] Nenhum recebível processado encontrado")

    except Exception as e:
        print(f"[DEBUG] Erro ao buscar recebíveis processados: {e}")
        alugueis_semestre = pd.DataFrame(columns=["Ano-Semestre", "aluguel_maquinas"])
        outros_recebiveis_semestre = pd.DataFrame(
            columns=["Ano-Semestre", "outros_recebiveis"]
        )

    # 3. Consolidar todos os dados
    # Começar com perdas
    df_consolidado = perdas_semestre.copy()

    # Merge com aluguéis
    if not alugueis_semestre.empty:
        df_consolidado = pd.merge(
            df_consolidado, alugueis_semestre, on="Ano-Semestre", how="outer"
        )
    else:
        df_consolidado["aluguel_maquinas"] = 0

    # Merge com outros recebíveis
    if not outros_recebiveis_semestre.empty:
        df_consolidado = pd.merge(
            df_consolidado, outros_recebiveis_semestre, on="Ano-Semestre", how="outer"
        )
    else:
        df_consolidado["outros_recebiveis"] = 0

    # Preencher NaN com 0
    df_consolidado.fillna(0, inplace=True)

    # Ordenar por Ano-Semestre
    df_consolidado.sort_values("Ano-Semestre", inplace=True)

    # Calcular totais
    total_perda_mdr = df_consolidado["perda_mdr"].sum()
    total_perda_rr = df_consolidado["perda_rr"].sum()
    total_alugueis = df_consolidado["aluguel_maquinas"].sum()
    total_outros = df_consolidado["outros_recebiveis"].sum()

    print(f"\n[DEBUG] === TOTAIS DA TABELA CONSOLIDADA ===")
    print(f"Total Perda MDR: {format_currency_br(total_perda_mdr)}")
    print(f"Total Perda RR: {format_currency_br(total_perda_rr)}")
    print(f"Total Aluguéis: {format_currency_br(total_alugueis)}")
    print(f"Total Outros Recebíveis: {format_currency_br(total_outros)}")
    print(
        f"SOMA CONSOLIDADA: {format_currency_br(total_perda_mdr + total_perda_rr + total_alugueis + total_outros)}"
    )
    print(f"=" * 50 + "\n")

    # Formatar valores monetários
    df_consolidado["Perda Monetária MDR"] = df_consolidado["perda_mdr"].apply(
        format_currency_br
    )
    df_consolidado["Perdas por Antecipações"] = df_consolidado["perda_rr"].apply(
        format_currency_br
    )
    df_consolidado["Aluguéis de Máquinas"] = df_consolidado["aluguel_maquinas"].apply(
        format_currency_br
    )
    df_consolidado["Outros Recebíveis"] = df_consolidado["outros_recebiveis"].apply(
        format_currency_br
    )

    # Adicionar linha de total
    linha_total = pd.DataFrame(
        [
            {
                "Ano-Semestre": "** TOTAL GERAL **",
                "Perda Monetária MDR": format_currency_br(total_perda_mdr),
                "Perdas por Antecipações": format_currency_br(total_perda_rr),
                "Aluguéis de Máquinas": format_currency_br(total_alugueis),
                "Outros Recebíveis": format_currency_br(total_outros),
            }
        ]
    )

    # Selecionar apenas colunas formatadas
    df_final = df_consolidado[
        [
            "Ano-Semestre",
            "Perda Monetária MDR",
            "Perdas por Antecipações",
            "Aluguéis de Máquinas",
            "Outros Recebíveis",
        ]
    ]
    df_final = pd.concat([df_final, linha_total], ignore_index=True)

    print(f"[DEBUG] Tabela consolidada gerada com {len(df_final)-1} semestres + total")

    return df_final


def obter_dados_bancarios_distintos(
    engine: Engine,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Busca todas as combinações distintas de banco, agência e conta-corrente
    dos recebíveis processados para o processamento especificado.
    Exclui registros onde banco, agência ou conta estejam vazios ou com "-".

    Args:
        engine: Engine de conexão com o banco de dados
        processamento_id: ID do processamento
        data_inicio: Data inicial para filtro (opcional)
        data_fim: Data final para filtro (opcional)

    Returns:
        DataFrame com as combinações distintas de banco, agência e conta-corrente
    """
    print(
        f"[DEBUG] Buscando dados bancários distintos para processamento: {processamento_id}"
    )

    params = [processamento_id]
    sql = """
        SELECT DISTINCT 
            banco as 'Banco',
            agencia as 'Agência', 
            conta as 'Conta-Corrente'
        FROM recebiveis_processados 
        WHERE processamentoid = %s 
            AND banco IS NOT NULL 
            AND banco != ''
            AND banco != '-'
            AND agencia IS NOT NULL 
            AND agencia != ''
            AND agencia != '-'
            AND conta IS NOT NULL
            AND conta != ''
            AND conta != '-'
    """

    if data_inicio is not None:
        sql += " AND data_recebivel >= %s"
        params.append(data_inicio)

    if data_fim is not None:
        sql += " AND data_recebivel <= %s"
        params.append(data_fim)

    sql += " ORDER BY banco, agencia, conta"
    sql = _convert_placeholders(engine, sql)

    try:
        df = pd.read_sql(sql, engine, params=tuple(params))
        print(f"[DEBUG] Dados bancários encontrados: {len(df)} combinações distintas")
        return df
    except Exception as e:
        print(f"[DEBUG] Erro ao buscar dados bancários distintos: {e}")
        return pd.DataFrame()


def criar_diretorio_relatorios():
    dir_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "relatorios")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def gerar_excel_relatorio(
    dataframes_dict: Dict[str, pd.DataFrame], nome_arquivo: str
) -> str:
    """
    Gera arquivo Excel com múltiplas abas, cada uma contendo um DataFrame do relatório.

    Args:
        dataframes_dict: Dicionário com {nome_aba: dataframe}
        nome_arquivo: Nome base do arquivo (sem extensão)

    Returns:
        Caminho completo do arquivo Excel gerado
    """
    try:
        dir_path = criar_diretorio_relatorios()
        excel_path = os.path.join(dir_path, f"{nome_arquivo}.xlsx")

        print(f"[DEBUG] Gerando Excel com {len(dataframes_dict)} abas: {excel_path}")

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for nome_aba, df in dataframes_dict.items():
                if df is not None and not df.empty:
                    # Limitar nome da aba a 31 caracteres (limite do Excel)
                    nome_aba_limpo = nome_aba[:31]
                    print(
                        f"[DEBUG]   - Escrevendo aba '{nome_aba_limpo}': {len(df)} linhas"
                    )
                    df.to_excel(writer, sheet_name=nome_aba_limpo, index=False)
                else:
                    print(f"[DEBUG]   - Pulando aba '{nome_aba}': DataFrame vazio")

        print(f"[DEBUG] ✓ Excel gerado com sucesso: {excel_path}")
        return excel_path

    except Exception as e:
        print(f"[ERROR] Erro ao gerar Excel: {e}")
        import traceback

        traceback.print_exc()
        return ""


def obter_dados_processamento(
    engine: Engine, processamento_id: str, max_rows: int = 100000000
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    try:
        from conf.check_system import verificar_espaco_temp

        if not verificar_espaco_temp():
            raise ValueError(
                "Espaço em disco insuficiente. Libere espaço e tente novamente."
            )
    except ImportError:
        pass

    metadados_sql = (
        "SELECT * FROM controle_processamentos WHERE id_processamento = :proc_id"
    )
    metadados = fetch_all(engine, metadados_sql, {"proc_id": processamento_id})
    if not metadados:
        raise ValueError(f"Processamento ID {processamento_id} não encontrado.")
    metadados = metadados[0]

    if metadados.get("cliente_id"):
        cliente_sql = "SELECT nome_fantasia, cnpj FROM clientes WHERE cliente_id = :cid"
        cliente = fetch_all(engine, cliente_sql, {"cid": metadados["cliente_id"]})
        if cliente:
            nome = cliente[0]["nome_fantasia"]
            cnpj = cliente[0].get("cnpj", "")
            if cnpj:
                cnpj_digits = re.sub(r"\D", "", str(cnpj))
                if len(cnpj_digits) == 14:
                    cnpj = f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"
                nome = f"{nome} ({cnpj})"
            metadados["cliente_nome"] = nome

    sql_processadas = (
        "SELECT * FROM vendas_processadas WHERE processamentoid = %s LIMIT %s"
    )
    sql_processadas = _convert_placeholders(engine, sql_processadas)
    df_processadas = read_sql_safe(
        sql_processadas,
        engine,
        params=(processamento_id, max_rows),
    )

    sql_filtradas = "SELECT * FROM vendas_filtradas WHERE processamentoid = %s LIMIT %s"
    sql_filtradas = _convert_placeholders(engine, sql_filtradas)
    df_filtradas = read_sql_safe(
        sql_filtradas,
        engine,
        params=(processamento_id, max_rows),
    )

    return df_processadas, df_filtradas, metadados


def criar_grafico_vendas_por_bandeira(df: pd.DataFrame) -> str:
    """Cria gráfico de pizza de vendas por bandeira com tratamento de erro."""
    try:
        if df.empty or "Bandeira" not in df.columns:
            print("[DEBUG] DataFrame vazio ou sem coluna Bandeira - pulando gráfico")
            return ""

        df_agg = df["Bandeira"].value_counts().reset_index()
        df_agg.columns = ["Bandeira", "Quantidade"]
        fig = px.pie(
            df_agg,
            names="Bandeira",
            values="Quantidade",
            title="Distribuição de Vendas por Bandeira",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")

        dir_path = criar_diretorio_relatorios()
        img_path = os.path.join(
            dir_path, f'vendas_bandeira_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        )

        # Tentar escrever imagem com timeout e retry
        fig.write_image(img_path, width=800, height=600, engine="kaleido")
        print(f"[DEBUG] Gráfico de bandeiras criado: {img_path}")
        return img_path
    except Exception as e:
        print(f"[AVISO] Erro ao criar gráfico de bandeiras: {e}")
        print("[AVISO] Relatório será gerado sem este gráfico")
        return ""


def criar_grafico_vendas_por_forma_pagamento(df: pd.DataFrame) -> str:
    """Cria gráfico de pizza de vendas por forma de pagamento com tratamento de erro."""
    try:
        if df.empty or "Forma_de_pagamento" not in df.columns:
            print(
                "[DEBUG] DataFrame vazio ou sem coluna Forma_de_pagamento - pulando gráfico"
            )
            return ""

        df_agg = df["Forma_de_pagamento"].value_counts().reset_index()
        df_agg.columns = ["Forma de Pagamento", "Quantidade"]
        fig = px.pie(
            df_agg,
            names="Forma de Pagamento",
            values="Quantidade",
            title="Distribuição por Forma de Pagamento",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")

        dir_path = criar_diretorio_relatorios()
        img_path = os.path.join(
            dir_path,
            f'vendas_forma_pagamento_{datetime.now().strftime("%Y%m%d%H%M%S")}.png',
        )

        # Tentar escrever imagem com timeout e retry
        fig.write_image(img_path, width=800, height=600, engine="kaleido")
        print(f"[DEBUG] Gráfico de forma de pagamento criado: {img_path}")
        return img_path
    except Exception as e:
        print(f"[AVISO] Erro ao criar gráfico de forma de pagamento: {e}")
        print("[AVISO] Relatório será gerado sem este gráfico")
        return ""
    return img_path


def criar_grafico_vendas_por_mes(df: pd.DataFrame) -> str:
    date_col = next(
        (c for c in ["Data_da_venda", "Data da Transação"] if c in df.columns), None
    )
    if df.empty or not date_col:
        fig = px.bar(x=["Sem dados"], y=[0], title="Vendas por Mês (sem dados)")
    else:
        df_agg = df.copy()
        df_agg["MesAno"] = pd.to_datetime(
            df_agg[date_col], errors="coerce"
        ).dt.to_period("M")
        df_agg = df_agg.dropna(subset=["MesAno"])
        df_agg = df_agg["MesAno"].value_counts().reset_index()
        df_agg.columns = ["MesAno", "Quantidade"]
        df_agg = df_agg.sort_values("MesAno")
        df_agg["MesAno"] = df_agg["MesAno"].astype(str)
        fig = px.bar(
            df_agg,
            x="MesAno",
            y="Quantidade",
            title="Quantidade de Vendas por Mês",
            color_discrete_sequence=["#636EFA"],
        )
    dir_path = criar_diretorio_relatorios()
    img_path = os.path.join(
        dir_path, f'vendas_mes_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    )
    fig.write_image(img_path, width=800, height=600)
    return img_path


def criar_grafico_valor_medio_por_bandeira(df: pd.DataFrame) -> str:
    valor_col = next(
        (
            c
            for c in ["Valor_da_venda", "Valor da Transação", "vl_venda"]
            if c in df.columns
        ),
        None,
    )
    if df.empty or "Bandeira" not in df.columns or not valor_col:
        fig = px.bar(
            x=["Sem dados"], y=[0], title="Valor Médio por Bandeira (sem dados)"
        )
    else:
        df[valor_col] = pd.to_numeric(df[valor_col], errors="coerce")
        df_agg = df.groupby("Bandeira")[valor_col].mean().reset_index()
        df_agg.columns = ["Bandeira", "Valor Médio"]
        fig = px.bar(
            df_agg,
            x="Bandeira",
            y="Valor Médio",
            title="Valor Médio de Venda por Bandeira (R$)",
            color="Bandeira",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")
    dir_path = criar_diretorio_relatorios()
    img_path = os.path.join(
        dir_path, f'valor_medio_bandeira_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    )
    fig.write_image(img_path, width=800, height=600)
    return img_path


def criar_tabela_sumario(
    estatisticas_sumario: dict,
    metadados: Dict[str, Any],
    estatisticas_taxas: Dict[str, Any],
    ecs_distintos: List[str] = None,
    adquirentes_distintos: List[str] = None,
) -> str:
    # Período das transações
    periodo_str = "N/A"
    periodo_dias_str = "N/A"

    print(
        f"[DEBUG] criar_tabela_sumario - primeira_venda: '{estatisticas_sumario.get('primeira_venda')}'"
    )
    print(
        f"[DEBUG] criar_tabela_sumario - ultima_venda: '{estatisticas_sumario.get('ultima_venda')}'"
    )
    print(
        f"[DEBUG] criar_tabela_sumario - periodo_dias: {estatisticas_sumario.get('periodo_dias')}"
    )

    primeira_venda_valor = estatisticas_sumario.get("primeira_venda")
    ultima_venda_valor = estatisticas_sumario.get("ultima_venda")

    print(f"[DEBUG] primeira_venda é None? {primeira_venda_valor is None}")
    print(
        f"[DEBUG] primeira_venda é string vazia? '{primeira_venda_valor}' == ''? {primeira_venda_valor == ''}"
    )
    print(f"[DEBUG] ultima_venda é None? {ultima_venda_valor is None}")
    print(
        f"[DEBUG] ultima_venda é string vazia? '{ultima_venda_valor}' == ''? {ultima_venda_valor == ''}"
    )

    if (
        primeira_venda_valor is not None
        and ultima_venda_valor is not None
        and primeira_venda_valor != ""
        and ultima_venda_valor != ""
    ):
        try:
            # As datas já vêm formatadas como string
            primeira_data_str = estatisticas_sumario["primeira_venda"]
            ultima_data_str = estatisticas_sumario["ultima_venda"]
            periodo_str = f"{primeira_data_str} a {ultima_data_str}"
            print(f"[DEBUG] Período formatado: {periodo_str}")

            # Calcular dias entre as datas
            dias = estatisticas_sumario.get("periodo_dias", 0)
            print(f"[DEBUG] Dias calculados: {dias}")
            if dias > 0:
                periodo_dias_str = f"{dias} dias"
            else:
                periodo_dias_str = "N/A"
        except Exception as e:
            print(f"[DEBUG] Erro ao formatar período: {e}")
            periodo_str = "N/A"
            periodo_dias_str = "N/A"

    # Prepara a lista de ECs distintos para exibição
    ecs_distintos_str = "N/A"
    if ecs_distintos:
        if len(ecs_distintos) == 1:
            ecs_distintos_str = ecs_distintos[0]
        elif len(ecs_distintos) <= 5:
            ecs_distintos_str = ", ".join(ecs_distintos)
        else:
            ecs_distintos_str = (
                f"{', '.join(ecs_distintos[:5])} e mais {len(ecs_distintos) - 5} ECs"
            )

    # Garantir que data_processamento seja datetime
    data_proc = metadados.get("data_processamento", datetime.now())
    if isinstance(data_proc, str):
        try:
            data_proc = pd.to_datetime(data_proc)
        except:
            data_proc = datetime.now()

    cabecalho = {
        "ID Processamento": metadados.get("id_processamento"),
        "Cliente": metadados.get("cliente_nome"),
        "EC ID Principal": metadados.get("ec_id"),
        "ECs no Processamento": ecs_distintos_str,
        "Total de ECs Distintos": len(ecs_distintos) if ecs_distintos else 0,
        "Adquirente": metadados.get("adquirente", "Não informado"),
        "Período das Transações": periodo_str,
        "Período (Dias)": periodo_dias_str,
        "Data Processamento": data_proc.strftime("%d/%m/%Y %H:%M:%S"),
    }

    estatisticas = {
        "Quantidade de Vendas": f"{estatisticas_sumario.get('quantidade', 0):,}".replace(
            ",", "."
        ),
        "Faturamento Bruto": format_currency_br(
            estatisticas_sumario.get("valor_total", 0)
        ),
        "Valor Médio da Transação": format_currency_br(
            estatisticas_sumario.get("valor_medio", 0)
        ),
        "Menor Transação": format_currency_br(estatisticas_sumario.get("valor_min", 0)),
        "Maior Transação": format_currency_br(estatisticas_sumario.get("valor_max", 0)),
        "Menor Taxa Encontrada (%)": f"{estatisticas_taxas.get('min_taxa', 0):.2f}",
        "Maior Taxa Encontrada (%)": f"{estatisticas_taxas.get('max_taxa', 0):.2f}",
        "Diferença de Taxa (%)": f"{estatisticas_sumario.get('diferenca_taxa', 0):.2f}",
    }

    # Adicionar Faturamento Líquido apenas se disponível (relatório mensal)
    if estatisticas_sumario.get("valor_liquido") is not None:
        # Inserir logo após Faturamento Bruto
        estatisticas_temp = {}
        for key, value in estatisticas.items():
            estatisticas_temp[key] = value
            if key == "Faturamento Bruto":
                estatisticas_temp["Faturamento Líquido"] = format_currency_br(
                    estatisticas_sumario.get("valor_liquido", 0)
                )
        estatisticas = estatisticas_temp

    html = '<div class="report-section"><h3>Informações do Processamento</h3><table class="report-table">'
    for k, v in cabecalho.items():
        if k in ["Cliente", "Processamento ID"]:
            html += f"<tr><td><strong>{k}</strong></td><td><strong style='color: #223a6b;'>{v}</strong></td></tr>"
        else:
            html += f"<tr><td>{k}</td><td>{v}</td></tr>"
    html += "</table></div>"

    html += '<div class="report-section"><h3>Estatísticas Gerais</h3><table class="report-table">'
    for k, v in estatisticas.items():
        if k in ["Faturamento Bruto", "Quantidade de Vendas"]:
            html += f"<tr><td><strong>{k}</strong></td><td><strong style='color: #223a6b;'>{v}</strong></td></tr>"
        elif "Taxa" in k:
            color = "#9c1313" if "Maior" in k else "#9c1313"
            html += f"<tr><td><strong>{k}</strong></td><td><strong style='color: {color};'>{v}</strong></td></tr>"
        else:
            html += f"<tr><td>{k}</td><td>{v}</td></tr>"
    html += "</table></div>"
    return html


def sumarizar_perdas_por_semestre(df_perdas: pd.DataFrame) -> pd.DataFrame:
    """
    Sumariza os dados de perdas por semestre, agrupando por Ano-Semestre.
    """
    if df_perdas.empty:
        return pd.DataFrame()

    try:
        # Primeiro, precisamos trabalhar com valores numéricos se os dados chegam formatados
        df_trabalho = df_perdas.copy()

        # Se os valores já vêm formatados como string, converter para numérico
        for col in ["Faturamento Bruto", "Perda Monetária"]:
            if col in df_trabalho.columns:
                if df_trabalho[col].dtype == "object":
                    # Remove formatação R$, pontos e vírgulas para converter para numérico
                    df_trabalho[col] = (
                        df_trabalho[col]
                        .astype(str)
                        .str.replace("R$", "")
                        .str.replace(".", "")
                        .str.replace(",", ".")
                        .str.strip()
                    )
                    df_trabalho[col] = pd.to_numeric(df_trabalho[col], errors="coerce")

        # Agrupar por Ano-Semestre e somar os valores
        df_sumarizado = (
            df_trabalho.groupby("Ano-Semestre")
            .agg({"Faturamento Bruto": "sum", "Perda Monetária": "sum"})
            .reset_index()
        )

        # Recalcular o percentual de perda
        df_sumarizado["% Perda"] = (
            df_sumarizado["Perda Monetária"]
            / df_sumarizado["Faturamento Bruto"].replace(0, pd.NA)
        ) * 100

        # Calcular totais gerais ANTES da formatação
        total_faturamento = df_sumarizado["Faturamento Bruto"].sum()
        total_perda = df_sumarizado["Perda Monetária"].sum()
        percentual_geral = (
            (total_perda / total_faturamento * 100) if total_faturamento > 0 else 0
        )

        # Formatar valores monetários dos dados sumarizados
        df_sumarizado["Faturamento Bruto"] = df_sumarizado["Faturamento Bruto"].apply(
            format_currency_br
        )
        df_sumarizado["Perda Monetária"] = df_sumarizado["Perda Monetária"].apply(
            format_currency_br
        )
        df_sumarizado["% Perda"] = df_sumarizado["% Perda"].apply(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "0.00%"
        )

        # Adicionar linha de TOTAL
        linha_total = pd.DataFrame(
            {
                "Ano-Semestre": [
                    '<strong style="color: #1e3a8a;">TOTAL GERAL</strong>'
                ],
                "Faturamento Bruto": [
                    f'<strong style="color: #1e3a8a;">{format_currency_br(total_faturamento)}</strong>'
                ],
                "Perda Monetária": [
                    f'<strong style="color: #dc2626;">{format_currency_br(total_perda)}</strong>'
                ],
                "% Perda": [
                    f'<strong style="color: #dc2626;">{percentual_geral:.2f}%</strong>'
                ],
            }
        )

        # Combinar dados sumarizados com linha de total
        df_resultado = pd.concat([df_sumarizado, linha_total], ignore_index=True)

        return df_resultado
    except Exception as e:
        print(f"Erro ao sumarizar perdas por semestre: {e}")
        return df_perdas


def sumarizar_recebiveis_por_semestre(df_recebiveis: pd.DataFrame) -> pd.DataFrame:
    """
    Sumariza os dados de recebíveis por semestre, ignorando data_recebivel e calc_id.
    Adiciona subtotais por semestre e total geral.
    """
    if df_recebiveis.empty:
        return pd.DataFrame()

    try:
        # Remover colunas desnecessárias se existirem
        colunas_para_remover = ["calc_id", "data_recebivel"]
        df_clean = df_recebiveis.drop(
            columns=[
                col for col in colunas_para_remover if col in df_recebiveis.columns
            ]
        )

        # Agrupar por Ano-Semestre e Lançamento, somando os valores
        df_sumarizado = (
            df_clean.groupby(["Ano-Semestre", "Lançamento"])["Valor Total"]
            .sum()
            .reset_index()
        )

        # Ordenar por Ano-Semestre e depois por Lançamento
        df_sumarizado = df_sumarizado.sort_values(["Ano-Semestre", "Lançamento"])

        # Formatar valores monetários
        df_sumarizado["Valor Total"] = df_sumarizado["Valor Total"].apply(
            format_currency_br
        )

        # Adicionar subtotais por semestre
        df_resultado = []
        semestres = df_sumarizado["Ano-Semestre"].unique()
        total_geral = 0

        for semestre in sorted(semestres):
            # Dados do semestre
            df_semestre = df_sumarizado[df_sumarizado["Ano-Semestre"] == semestre]

            # Adicionar linhas do semestre
            for _, row in df_semestre.iterrows():
                df_resultado.append(
                    {
                        "Ano-Semestre": row["Ano-Semestre"],
                        "Lançamento": row["Lançamento"],
                        "Valor Total": row["Valor Total"],
                    }
                )

            # Calcular subtotal do semestre (valores não formatados)
            df_semestre_valores = (
                df_clean.groupby(["Ano-Semestre", "Lançamento"])["Valor Total"]
                .sum()
                .reset_index()
            )
            subtotal_semestre = df_semestre_valores[
                df_semestre_valores["Ano-Semestre"] == semestre
            ]["Valor Total"].sum()
            total_geral += subtotal_semestre

            # Adicionar linha de subtotal
            df_resultado.append(
                {
                    "Ano-Semestre": "",
                    "Lançamento": f"<strong>Subtotal {semestre}</strong>",
                    "Valor Total": f"<strong>{format_currency_br(subtotal_semestre)}</strong>",
                }
            )

            # Linha em branco para separação
            df_resultado.append(
                {"Ano-Semestre": "", "Lançamento": "", "Valor Total": ""}
            )

        # Adicionar total geral
        df_resultado.append(
            {
                "Ano-Semestre": "",
                "Lançamento": '<strong style="color: #9c1313;">TOTAL GERAL</strong>',
                "Valor Total": f'<strong style="color: #9c1313;">{format_currency_br(total_geral)}</strong>',
            }
        )

        return pd.DataFrame(df_resultado)

    except Exception as e:
        print(f"Erro ao sumarizar recebíveis por semestre: {e}")
        return df_recebiveis


def sumarizar_taxas_min_max_por_semestre(df_taxas: pd.DataFrame) -> pd.DataFrame:
    """
    Sumariza os dados de taxas mínimas e máximas por semestre, ignorando data_da_venda e calc_id.
    """
    if df_taxas.empty:
        return pd.DataFrame()

    try:
        # Remover colunas desnecessárias se existirem
        colunas_para_remover = ["calc_id", "data_da_venda", "Data_da_venda"]
        df_clean = df_taxas.drop(
            columns=[col for col in colunas_para_remover if col in df_taxas.columns]
        )

        # Normalizar forma de pagamento se a coluna existir
        if "Forma_de_pagamento" in df_clean.columns:
            df_clean["Forma_de_pagamento"] = df_clean["Forma_de_pagamento"].apply(
                normalizar_forma_pagamento
            )

        # Agrupar por Ano-Semestre, Bandeira e Forma_de_pagamento e recalcular min/max
        df_sumarizado = (
            df_clean.groupby(["Ano-Semestre", "Bandeira", "Forma_de_pagamento"])
            .agg({"Taxa_Min": "min", "Taxa_Max": "max"})
            .reset_index()
        )

        # Ordenar por Ano-Semestre, depois por Bandeira
        df_sumarizado = df_sumarizado.sort_values(
            ["Ano-Semestre", "Bandeira", "Forma_de_pagamento"]
        )

        # Formatar percentuais
        df_sumarizado["Taxa_Min"] = df_sumarizado["Taxa_Min"].apply(
            lambda x: f"{x:.2f}%"
        )
        df_sumarizado["Taxa_Max"] = df_sumarizado["Taxa_Max"].apply(
            lambda x: f"{x:.2f}%"
        )

        return df_sumarizado

    except Exception as e:
        print(f"Erro ao sumarizar taxas min/max por semestre: {e}")
        return df_taxas


def sumarizar_contagem_transacoes(df_contagem: pd.DataFrame) -> pd.DataFrame:
    """
    Sumariza contagem de transações por ano-semestre, bandeira e modalidade,
    removendo data_da_venda e calc_id das colunas exibidas.
    """
    try:
        if df_contagem.empty:
            return df_contagem

        df_limpo = df_contagem.copy()

        # Normalizar forma de pagamento se a coluna existir
        if "Forma_de_pagamento" in df_limpo.columns:
            df_limpo["Forma_de_pagamento"] = df_limpo["Forma_de_pagamento"].apply(
                normalizar_forma_pagamento
            )

        # Verificar se existe coluna Ano-Semestre ou Ano com valores inválidos e corrigir
        if "Ano-Semestre" in df_limpo.columns:
            # Validação já foi feita na função calcular_contagem_taxas_agrupado
            pass
        elif "Ano" in df_limpo.columns:
            # Se a coluna Ano tem valores que não são anos válidos (fora do range 1900-2100)
            anos_invalidos = df_limpo["Ano"].apply(lambda x: x < 1900 or x > 2100)
            if anos_invalidos.any():
                print(
                    f"Debug: Encontrados anos inválidos na coluna Ano: {df_limpo[anos_invalidos]['Ano'].unique()}"
                )

                # Tentar extrair ano da coluna Data_da_venda se existir
                if "Data_da_venda" in df_limpo.columns:
                    print("Debug: Corrigindo anos usando Data_da_venda")
                    df_limpo["Data_da_venda"] = pd.to_datetime(
                        df_limpo["Data_da_venda"], errors="coerce"
                    )
                    df_limpo["Ano"] = df_limpo["Data_da_venda"].dt.year
                    print(f"Debug: Anos corrigidos: {sorted(df_limpo['Ano'].unique())}")

        # Remover colunas desnecessárias se existirem
        colunas_a_remover = ["Data_da_venda", "data_da_venda", "calc_id", "Calc_id"]

        for col in colunas_a_remover:
            if col in df_limpo.columns:
                df_limpo = df_limpo.drop(columns=[col])

        # Identificar colunas de agrupamento (todas exceto contadores)
        colunas_numericas = df_limpo.select_dtypes(include=["int64", "float64"]).columns
        colunas_agrupamento = [
            col for col in df_limpo.columns if col not in colunas_numericas
        ]

        if len(colunas_agrupamento) == 0:
            return df_limpo

        # Agrupar e somar as contagens
        df_sumarizado = df_limpo.groupby(colunas_agrupamento).sum().reset_index()

        # Ordenar por ano-semestre (se existir) e depois pelas outras colunas
        colunas_ordenacao = []
        for col in ["Ano-Semestre", "Ano", "ano", "Year", "year"]:
            if col in df_sumarizado.columns:
                colunas_ordenacao.append(col)
                break

        # Adicionar outras colunas para ordenação
        for col in colunas_agrupamento:
            if col not in colunas_ordenacao:
                colunas_ordenacao.append(col)

        if colunas_ordenacao:
            df_sumarizado = df_sumarizado.sort_values(colunas_ordenacao).reset_index(
                drop=True
            )

        return df_sumarizado

    except Exception as e:
        print(f"Erro ao sumarizar contagem de transações: {e}")
        return df_contagem


def gerar_demonstrativo_vendas_filtradas(
    engine: Engine,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Gera demonstrativo de vendas filtradas agrupado por:
    - status_da_venda
    - Bandeira
    - Forma_de_pagamento
    - Quantidade de vendas
    - Soma do valor bruto da venda

    Args:
        engine: Conexão com o banco de dados
        processamento_id: ID do processamento

    Returns:
        DataFrame com o demonstrativo das vendas filtradas
    """
    print(
        f"[DEBUG] Gerando demonstrativo de vendas filtradas para processamento: {processamento_id}"
    )

    try:
        # Buscar vendas filtradas do processamento
        params = [processamento_id]
        sql = """
        SELECT 
            status_da_venda,
            Bandeira,
            Forma_de_pagamento,
            COUNT(*) as Quantidade_Vendas,
            SUM(COALESCE(Valor_da_venda, 0)) as Soma_Valor_Bruto
        FROM vendas_filtradas 
        WHERE processamentoid = %s
        """

        if data_inicio is not None:
            sql += " AND Data_da_venda >= %s"
            params.append(data_inicio)

        if data_fim is not None:
            sql += " AND Data_da_venda <= %s"
            params.append(data_fim)

        sql += """
        GROUP BY status_da_venda, Bandeira, Forma_de_pagamento
        ORDER BY status_da_venda, Bandeira, Forma_de_pagamento
        """
        sql = _convert_placeholders(engine, sql)

        df_demonstrativo = pd.read_sql(sql, engine, params=tuple(params))

        if df_demonstrativo.empty:
            print("[DEBUG] Nenhuma venda filtrada encontrada para o processamento")
            return pd.DataFrame(
                columns=[
                    "Status da Venda",
                    "Bandeira",
                    "Forma de Pagamento",
                    "Quantidade de Vendas",
                    "Valor Bruto Total",
                ]
            )

        # Renomear colunas para exibição
        df_demonstrativo.columns = [
            "Status da Venda",
            "Bandeira",
            "Forma de Pagamento",
            "Quantidade de Vendas",
            "Valor Bruto Total",
        ]

        # Formatar valor bruto em formato monetário brasileiro
        df_demonstrativo["Valor Bruto Total"] = df_demonstrativo[
            "Valor Bruto Total"
        ].apply(format_currency_br)

        # Adicionar linha de total geral
        total_quantidade = df_demonstrativo["Quantidade de Vendas"].sum()

        # Para o total do valor, precisamos recalcular sem formatação
        params_total = [processamento_id]
        sql_total = """
        SELECT SUM(COALESCE(Valor_da_venda, 0)) as total_valor
        FROM vendas_filtradas 
        WHERE processamentoid = %s
        """

        if data_inicio is not None:
            sql_total += " AND Data_da_venda >= %s"
            params_total.append(data_inicio)

        if data_fim is not None:
            sql_total += " AND Data_da_venda <= %s"
            params_total.append(data_fim)

        sql_total = _convert_placeholders(engine, sql_total)
        total_valor_df = pd.read_sql(sql_total, engine, params=tuple(params_total))
        # Case-insensitive: usar nome real da coluna
        total_valor = (
            total_valor_df.iloc[0][total_valor_df.columns[0]]
            if not total_valor_df.empty
            else 0
        )

        linha_total = pd.DataFrame(
            [
                {
                    "Status da Venda": "** TOTAL GERAL **",
                    "Bandeira": "",
                    "Forma de Pagamento": "",
                    "Quantidade de Vendas": total_quantidade,
                    "Valor Bruto Total": format_currency_br(total_valor),
                }
            ]
        )

        df_final = pd.concat([df_demonstrativo, linha_total], ignore_index=True)

        print(
            f"[DEBUG] Demonstrativo gerado com {len(df_demonstrativo)} linhas de dados + 1 linha de total"
        )

        return df_final

    except Exception as e:
        print(f"[ERROR] Erro ao gerar demonstrativo de vendas filtradas: {e}")
        return pd.DataFrame(
            columns=[
                "Status da Venda",
                "Bandeira",
                "Forma de Pagamento",
                "Quantidade de Vendas",
                "Valor Bruto Total",
            ]
        )


def gerar_demonstrativo_recebiveis_filtrados(
    engine: Engine,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Gera demonstrativo de recebíveis filtrados agrupado por:
    - status_da_venda
    - Bandeira
    - Forma_de_pagamento
    - Quantidade de recebíveis
    - Soma do valor líquido

    Args:
        engine: Conexão com o banco de dados
        processamento_id: ID do processamento
        data_inicio: Data inicial para filtro (opcional)
        data_fim: Data final para filtro (opcional)

    Returns:
        DataFrame com o demonstrativo dos recebíveis filtrados
    """
    print(
        f"[DEBUG] Gerando demonstrativo de recebíveis filtrados para processamento: {processamento_id}"
    )

    try:
        # Primeiro verificar se a tabela recebiveis_filtrados existe e tem dados
        params_verif = [processamento_id]
        verificacao_sql = """
        SELECT COUNT(*) as total_registros 
        FROM recebiveis_filtrados 
        WHERE processamentoid = %s
        """

        if data_inicio is not None:
            verificacao_sql += " AND data_recebivel >= %s"
            params_verif.append(data_inicio)

        if data_fim is not None:
            verificacao_sql += " AND data_recebivel <= %s"
            params_verif.append(data_fim)

        verificacao_sql = _convert_placeholders(engine, verificacao_sql)
        df_verificacao = pd.read_sql(
            verificacao_sql, engine, params=tuple(params_verif)
        )
        # Case-insensitive: usar nome real da coluna
        total_registros = (
            df_verificacao.iloc[0][df_verificacao.columns[0]]
            if not df_verificacao.empty
            else 0
        )

        print(
            f"[DEBUG] Total de registros em recebiveis_filtrados para processamento {processamento_id}: {total_registros}"
        )

        if total_registros == 0:
            print(
                "[DEBUG] Nenhum registro encontrado na tabela recebiveis_filtrados para este processamento"
            )
            return pd.DataFrame(
                columns=[
                    "Tipo de Lançamento",
                    "Quantidade de Recebíveis",
                    "Valor Recebível Total",
                    "Valor Líquido Total",
                ]
            )

        # Buscar recebíveis filtrados do processamento - usando estrutura real da tabela
        params_rec = [processamento_id]
        sql = """
        SELECT 
            lancamento as Tipo_Lancamento,
            COUNT(*) as Quantidade_Recebiveis,
            SUM(COALESCE(valor_recebivel, 0)) as Soma_Valor_Recebivel,
            SUM(COALESCE(valor_liquido, 0)) as Soma_Valor_Liquido
        FROM recebiveis_filtrados 
        WHERE processamentoid = %s
        """

        if data_inicio is not None:
            sql += " AND data_recebivel >= %s"
            params_rec.append(data_inicio)

        if data_fim is not None:
            sql += " AND data_recebivel <= %s"
            params_rec.append(data_fim)

        sql += """
        GROUP BY lancamento
        ORDER BY lancamento
        """
        sql = _convert_placeholders(engine, sql)

        df_demonstrativo = pd.read_sql(sql, engine, params=tuple(params_rec))

        if df_demonstrativo.empty:
            print("[DEBUG] Nenhum recebível filtrado encontrado para o processamento")
            return pd.DataFrame(
                columns=[
                    "Tipo de Lançamento",
                    "Quantidade de Recebíveis",
                    "Valor Recebível Total",
                    "Valor Líquido Total",
                ]
            )

        # Renomear colunas para exibição
        df_demonstrativo.columns = [
            "Tipo de Lançamento",
            "Quantidade de Recebíveis",
            "Valor Recebível Total",
            "Valor Líquido Total",
        ]

        # Formatar valores em formato monetário brasileiro
        df_demonstrativo["Valor Recebível Total"] = df_demonstrativo[
            "Valor Recebível Total"
        ].apply(format_currency_br)

        df_demonstrativo["Valor Líquido Total"] = df_demonstrativo[
            "Valor Líquido Total"
        ].apply(format_currency_br)

        # Adicionar linha de total geral
        total_quantidade = df_demonstrativo["Quantidade de Recebíveis"].sum()

        # Para os totais dos valores, precisamos recalcular sem formatação
        params_total = [processamento_id]
        sql_total = """
        SELECT 
            SUM(COALESCE(valor_recebivel, 0)) as total_valor_recebivel,
            SUM(COALESCE(valor_liquido, 0)) as total_valor_liquido
        FROM recebiveis_filtrados 
        WHERE processamentoid = %s
        """

        if data_inicio is not None:
            sql_total += " AND data_recebivel >= %s"
            params_total.append(data_inicio)

        if data_fim is not None:
            sql_total += " AND data_recebivel <= %s"
            params_total.append(data_fim)

        sql_total = _convert_placeholders(engine, sql_total)
        total_valor_df = pd.read_sql(sql_total, engine, params=tuple(params_total))

        if not total_valor_df.empty:
            # Case-insensitive: usar índice das colunas
            cols = total_valor_df.columns.tolist()
            total_valor_recebivel = total_valor_df.iloc[0][cols[0]]
            total_valor_liquido = total_valor_df.iloc[0][cols[1]]
        else:
            total_valor_recebivel = 0
            total_valor_liquido = 0

        linha_total = pd.DataFrame(
            [
                {
                    "Tipo de Lançamento": "** TOTAL GERAL **",
                    "Quantidade de Recebíveis": total_quantidade,
                    "Valor Recebível Total": format_currency_br(total_valor_recebivel),
                    "Valor Líquido Total": format_currency_br(total_valor_liquido),
                }
            ]
        )

        df_final = pd.concat([df_demonstrativo, linha_total], ignore_index=True)

        print(
            f"[DEBUG] Demonstrativo gerado com {len(df_demonstrativo)} linhas de dados + 1 linha de total"
        )

        return df_final

    except Exception as e:
        print(f"[ERROR] Erro ao gerar demonstrativo de recebíveis filtrados: {e}")
        return pd.DataFrame(
            columns=[
                "Tipo de Lançamento",
                "Quantidade de Recebíveis",
                "Valor Recebível Total",
                "Valor Líquido Total",
            ]
        )


def gerar_relatorio_html(
    engine: "Engine",
    processamento_id: str,
    calc_tipo: str = None,
    return_base: bool = False,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    adquirente: str = None,
    incluir_filtradas: bool = False,
    incluir_recebiveis_filtrados: bool = False,
    apenas_com_perdas: bool = False,
) -> Tuple[str, Optional["pd.DataFrame"]]:
    # Inicialização preventiva de variáveis para evitar erros de referência
    grafico_bandeiras_path = ""
    grafico_forma_pagamento_path = ""
    grafico_meses_path = ""
    grafico_valores_path = ""
    primeira_venda = None
    ultima_venda = None
    quantidade = 0
    valor_total = 0
    valor_medio = 0
    valor_min = 0
    valor_max = 0
    min_taxa = 0
    max_taxa = 0

    inicio_total = time.time()
    print(f"[DEBUG] === INÍCIO GERAÇÃO RELATÓRIO HTML ===")
    print(f"[DEBUG] Processamento ID: {processamento_id}, Tipo: {calc_tipo}")

    # Configurar timeouts maiores para evitar "Packet sequence number wrong"
    try:
        if hasattr(engine.pool, "_connect_args"):
            if "connect_timeout" not in engine.pool._connect_args:
                print("[DEBUG] Configurando timeout de conexão para 300s")
        # Para PyMySQL, ajustar read_timeout e write_timeout
        with engine.connect() as conn:
            if "mysql" in str(engine.url):
                try:
                    conn.execute(text("SET SESSION net_read_timeout = 600"))
                    conn.execute(text("SET SESSION net_write_timeout = 600"))
                    conn.execute(text("SET SESSION wait_timeout = 28800"))
                    conn.commit()
                    print(
                        "[DEBUG] Timeouts MySQL configurados: read=600s, write=600s, wait=28800s"
                    )
                except Exception as e:
                    print(f"[DEBUG] Não foi possível configurar timeouts MySQL: {e}")
    except Exception as e:
        print(f"[DEBUG] Erro ao configurar timeouts: {e}")

    inicio_metadados = time.time()
    metadados = obter_dados_processamento(engine, processamento_id)
    log_tempo_execucao("obter_dados_processamento", inicio_metadados)

    # Buscar ECs distintos no processamento (filtrado por adquirente se aplicável)
    inicio_ecs = time.time()
    ecs_distintos = obter_ecs_distintos_processamento(
        engine, processamento_id, adquirente
    )
    log_tempo_execucao("obter_ecs_distintos", inicio_ecs)

    # Buscar adquirentes distintos no processamento
    inicio_adquirentes = time.time()
    adquirentes_distintos = obter_adquirentes_distintos_processamento(
        engine, processamento_id
    )
    log_tempo_execucao("obter_adquirentes_distintos", inicio_adquirentes)

    # Preencher adquirente com base no filtro aplicado ou adquirentes encontrados no processamento
    print(f"Debug: Adquirentes distintos encontrados: {adquirentes_distintos}")
    print(f"Debug: Filtro de adquirente aplicado: {adquirente}")

    if adquirente and adquirente != "None":
        # Se um filtro específico foi aplicado, mostrar apenas o nome da adquirente
        metadados["adquirente"] = adquirente
        print(f"Debug: Filtro de adquirente aplicado: {metadados['adquirente']}")
    elif adquirentes_distintos:
        if len(adquirentes_distintos) == 1:
            metadados["adquirente"] = adquirentes_distintos[0]
            print(f"Debug: Adquirente único definido: {metadados['adquirente']}")
        else:
            # Exibir todos os adquirentes separados por vírgula
            metadados["adquirente"] = ", ".join(adquirentes_distintos)
            print(f"Debug: Múltiplos adquirentes definidos: {metadados['adquirente']}")
    else:
        metadados["adquirente"] = "Não identificado"
        print(
            f"Debug: Nenhum adquirente encontrado, definindo como: {metadados['adquirente']}"
        )

    # Buscar dados - SEM JOIN! Todos os campos já estão em vendas_calculos
    inicio_join = time.time()
    join_sql = """
        SELECT 
            id_venda AS venda_id, data_venda AS Data_da_venda, bandeira AS Bandeira, 
            forma_pagamento AS Forma_de_pagamento,
            tx_rr_venda AS Taxas_RR, vl_rr_venda AS Valor_RR, 
            vl_venda, tx_venda, desc_venda,
            vl_liq_venda, tx_calc, desc_calc, vl_liq_calc, perda
        FROM vendas_calculos
        WHERE calc_id = %s AND calc_tipo = %s
    """

    # Montar lista de parâmetros
    params = [processamento_id, calc_tipo]

    # Adiciona filtro de adquirente se fornecido
    if adquirente:
        join_sql += " AND adquirente = %s"
        params.append(adquirente)

    # Adiciona filtro de data se fornecido
    if data_inicio:
        join_sql += " AND data_venda >= %s"
        params.append(data_inicio)

    if data_fim:
        join_sql += " AND data_venda <= %s"
        params.append(data_fim)

    # Adiciona filtro para apenas vendas com perdas (perda > 0 ou perda_rr > 0)
    if apenas_com_perdas:
        join_sql += " AND (perda > 0 OR COALESCE(perda_rr, 0) > 0)"

    join_sql = _convert_placeholders(engine, join_sql)

    # Usar leitura segura com retry automático
    df_join = read_sql_safe(join_sql, engine, params=tuple(params))
    log_tempo_execucao("buscar_base_joinada", inicio_join)

    # Aplicar filtro específico para valores da REDE após de-para
    inicio_filtro_rede = time.time()
    df_join = filtrar_valores_rede_depara(df_join)
    log_tempo_execucao("filtrar_valores_rede_depara", inicio_filtro_rede)

    # Calcular previsão de pagamento específica da REDE (31 dias + data_da_venda)
    inicio_previsao_rede = time.time()
    df_join = calcular_previsao_pagamento_rede(df_join)
    log_tempo_execucao("calcular_previsao_pagamento_rede", inicio_previsao_rede)

    # Calcular agregados diretamente sobre o resultado do JOIN
    if not df_join.empty:
        datas = pd.to_datetime(df_join["Data_da_venda"], errors="coerce").dropna()
        valor_total = pd.to_numeric(df_join["vl_venda"], errors="coerce").sum()
        valor_medio = pd.to_numeric(df_join["vl_venda"], errors="coerce").mean()
        valor_min = pd.to_numeric(df_join["vl_venda"], errors="coerce").min()
        valor_max = pd.to_numeric(df_join["vl_venda"], errors="coerce").max()

        # Calcular taxas filtrando valores 0 e NULL
        taxas = pd.to_numeric(df_join["tx_venda"], errors="coerce").dropna()
        taxas_validas = taxas[taxas > 0]  # Filtrar taxas maiores que 0
        min_taxa = taxas_validas.min() if not taxas_validas.empty else 0
        max_taxa = taxas_validas.max() if not taxas_validas.empty else 0
        diferenca_taxa = max_taxa - min_taxa if not taxas_validas.empty else 0
        quantidade = len(df_join)
    else:
        valor_total = valor_medio = valor_min = valor_max = 0
        min_taxa = max_taxa = diferenca_taxa = 0
        quantidade = 0

    # Calcular período considerando filtros de data
    # Se data_inicio ou data_fim foram fornecidos, usar eles como período
    if data_inicio or data_fim:
        # Usar as datas fornecidas como filtro
        primeira_venda = data_inicio if data_inicio else None
        ultima_venda = data_fim if data_fim else None

        # Se apenas uma data foi fornecida, buscar a outra do banco
        if not primeira_venda or not ultima_venda:
            primeira_calc, ultima_calc = calcular_periodo_completo(
                engine, processamento_id, adquirente, data_inicio, data_fim
            )
            if not primeira_venda:
                primeira_venda = primeira_calc
            if not ultima_venda:
                ultima_venda = ultima_calc
    else:
        # Sem filtro de data, usar período completo do processamento
        primeira_venda, ultima_venda = calcular_periodo_completo(
            engine, processamento_id, adquirente, data_inicio, data_fim
        )

    print(
        f"[DEBUG] Período final usado: primeira={primeira_venda}, ultima={ultima_venda}"
    )

    # Calcular período em dias
    periodo_dias = 0
    if primeira_venda and ultima_venda:
        try:
            data_min = pd.to_datetime(primeira_venda)
            data_max = pd.to_datetime(ultima_venda)
            periodo_dias = (
                data_max - data_min
            ).days + 1  # +1 para incluir o dia inicial
            print(
                f"Debug: Período calculado: {periodo_dias} dias entre {primeira_venda} e {ultima_venda}"
            )
        except Exception as e:
            print(f"Erro ao calcular período: {e}")
            periodo_dias = 0

    # Buscar tipos de inconsistências (lancamentos) distintos nos recebíveis processados
    inconsistencias_str = "Nenhuma"
    tipos_lancamentos_distintos = 0
    try:
        recebiveis_sql = "SELECT DISTINCT lancamento FROM recebiveis_processados WHERE processamentoid = %s AND lancamento IS NOT NULL AND lancamento != ''"
        recebiveis_sql = _convert_placeholders(engine, recebiveis_sql)
        recebiveis_result = pd.read_sql(
            recebiveis_sql, engine, params=(processamento_id,)
        )

        # SQLite pode retornar 'Lancamento' (case preservado do schema)
        # MySQL retorna 'lancamento' (case-insensitive)
        col_lancamento = (
            recebiveis_result.columns[0]
            if not recebiveis_result.empty
            else "lancamento"
        )

        inconsistencias = [
            str(l).strip().capitalize()
            for l in recebiveis_result[col_lancamento].unique()
            if l and str(l).strip()
        ]

        # Corrigir acentuação de Crédito e Débito
        def corrige_acentuacao(s):
            s = s.replace("Credito", "Crédito").replace("Debito", "Débito")
            return s

        inconsistencias = [corrige_acentuacao(i) for i in inconsistencias]
        tipos_lancamentos_distintos = len(inconsistencias)
        # Se houver diferença de taxas, adicionar descrição especial
        if any(i.lower().startswith("diferen") for i in inconsistencias):
            variacao_taxa = diferenca_taxa if "diferenca_taxa" in locals() else 0
            inconsistencias = [
                (
                    f"Diferença de taxas: variação de {variacao_taxa:.2f}%"
                    if i.lower().startswith("diferen")
                    else i
                )
                for i in inconsistencias
            ]
        # Verificar se há perdas nas vendas calculadas (oscilações de taxa MDR)
        try:
            if adquirente:
                # Com filtro de adquirente - usar campo local de vendas_calculos
                perdas_sql = """
                    SELECT COUNT(*) as total_perdas
                    FROM vendas_calculos
                    WHERE calc_id = %s AND perda IS NOT NULL AND perda != 0
                    AND adquirente = %s
                """
                perdas_sql = _convert_placeholders(engine, perdas_sql)
                perdas_result = pd.read_sql(
                    perdas_sql, engine, params=(processamento_id, adquirente)
                )
            else:
                # Sem filtro de adquirente - query simples
                perdas_sql = """
                    SELECT COUNT(*) as total_perdas
                    FROM vendas_calculos 
                    WHERE calc_id = %s AND perda IS NOT NULL AND perda != 0
                """
                perdas_sql = _convert_placeholders(engine, perdas_sql)
                perdas_result = pd.read_sql(
                    perdas_sql, engine, params=(processamento_id,)
                )

            # SQLite pode retornar 'Total_perdas' ou 'total_perdas' dependendo do alias
            # Usar acesso seguro à primeira coluna
            total_perdas = (
                perdas_result.iloc[0][perdas_result.columns[0]]
                if not perdas_result.empty
                else 0
            )

            if total_perdas > 0:
                inconsistencias.append("Oscilações nas taxas MDR")
                filtro_info = f" (adquirente: {adquirente})" if adquirente else ""
                print(
                    f"[DEBUG] Detectadas {total_perdas} transações com perdas{filtro_info} - adicionando 'Oscilações nas taxas MDR'"
                )
        except Exception as e:
            print(f"Erro ao verificar perdas nas vendas_calculos: {e}")

        inconsistencias_str = (
            ", ".join(inconsistencias) if inconsistencias else "Nenhuma"
        )
    except Exception as e:
        print(f"Erro ao buscar tipos de inconsistências: {e}")
        inconsistencias_str = "Erro ao buscar"

    # Formatar datas para string antes de adicionar ao dicionário
    primeira_venda_str = None
    ultima_venda_str = None

    print(
        f"[DEBUG] Formatando datas - primeira_venda: {primeira_venda} (tipo: {type(primeira_venda)})"
    )
    print(
        f"[DEBUG] Formatando datas - ultima_venda: {ultima_venda} (tipo: {type(ultima_venda)})"
    )

    if primeira_venda is not None:
        try:
            # Verificar se já é string ou precisa converter
            if isinstance(primeira_venda, str):
                primeira_venda_str = primeira_venda
                print(f"[DEBUG] primeira_venda já é string: {primeira_venda_str}")
            else:
                primeira_venda_str = pd.to_datetime(primeira_venda).strftime("%d/%m/%Y")
                print(f"[DEBUG] primeira_venda formatada: {primeira_venda_str}")
        except Exception as e:
            print(f"[DEBUG] Erro ao formatar primeira_venda: {e}")
            primeira_venda_str = str(primeira_venda) if primeira_venda else None
    else:
        print("[DEBUG] primeira_venda é None - mantendo como None")

    if ultima_venda is not None:
        try:
            # Verificar se já é string ou precisa converter
            if isinstance(ultima_venda, str):
                ultima_venda_str = ultima_venda
                print(f"[DEBUG] ultima_venda já é string: {ultima_venda_str}")
            else:
                ultima_venda_str = pd.to_datetime(ultima_venda).strftime("%d/%m/%Y")
                print(f"[DEBUG] ultima_venda formatada: {ultima_venda_str}")
        except Exception as e:
            print(f"[DEBUG] Erro ao formatar ultima_venda: {e}")
            ultima_venda_str = str(ultima_venda) if ultima_venda else None
    else:
        print("[DEBUG] ultima_venda é None - mantendo como None")

    estatisticas_sumario = {
        "primeira_venda": primeira_venda_str,
        "ultima_venda": ultima_venda_str,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "valor_medio": valor_medio,
        "valor_min": valor_min,
        "valor_max": valor_max,
        "min_taxa": min_taxa,
        "max_taxa": max_taxa,
        "diferenca_taxa": diferenca_taxa,
        "tipos_lancamentos_distintos": tipos_lancamentos_distintos,
        "periodo_dias": periodo_dias,
        "inconsistencias_str": inconsistencias_str,
    }

    print(f"[DEBUG] Dicionário estatisticas_sumario criado:")
    print(f"[DEBUG] - primeira_venda: '{primeira_venda_str}'")
    print(f"[DEBUG] - ultima_venda: '{ultima_venda_str}'")
    print(f"[DEBUG] - periodo_dias: {periodo_dias}")

    estatisticas_taxas = {"min_taxa": min_taxa, "max_taxa": max_taxa}
    tabela_sumario_html = criar_tabela_sumario(
        estatisticas_sumario,
        metadados,
        estatisticas_taxas,
        ecs_distintos,
        adquirentes_distintos,
    )

    # Bloco perdas por semestre (usando dados calculados com perda_rr)
    inicio_perdas = time.time()

    # Buscar dados de vendas processadas e vendas_calculos com perda_rr
    sql_vendas_processadas = """
    SELECT id, Data_da_venda 
    FROM vendas_processadas 
    WHERE processamentoid = %s
    """
    sql_vendas_processadas = _convert_placeholders(engine, sql_vendas_processadas)

    # Usar leitura segura com retry automático
    df_vendas_proc = read_sql_safe(
        sql_vendas_processadas, engine, params=(processamento_id,)
    )

    sql_vendas_calculos = """
    SELECT id_venda, perda, perda_rr, vl_venda 
    FROM vendas_calculos 
    WHERE calc_id = %s AND calc_tipo = %s
    """
    sql_vendas_calculos = _convert_placeholders(engine, sql_vendas_calculos)

    # Usar leitura segura com retry automático
    df_vendas_calc = read_sql_safe(
        sql_vendas_calculos, engine, params=(processamento_id, calc_tipo)
    )

    # Usar a função atualizada que suporta perda_rr - COM faturamento e % perda
    df_perdas_sumarizado = calcular_perdas_por_semestre(
        df_vendas_proc, df_vendas_calc, incluir_faturamento=True
    )

    log_tempo_execucao("calcular_perdas_por_semestre_com_rr", inicio_perdas)
    inicio_perdas_tab = time.time()
    tabela_perdas_semestre_html = gerar_tabela_html(
        df_perdas_sumarizado,
        "Análise de Perdas Estimadas por Semestre",
    )
    log_tempo_execucao("gerar_tabela_perdas_semestre_html", inicio_perdas_tab)

    # Bloco min/max taxas
    inicio_taxas = time.time()
    df_taxas_raw = ler_view(
        engine, "vw_min_max_taxas_semestre", processamento_id, data_inicio, data_fim
    )
    log_tempo_execucao("ler_view(vw_min_max_taxas_semestre)", inicio_taxas)
    inicio_taxas_sum = time.time()
    df_taxas_sumarizado = sumarizar_taxas_min_max_por_semestre(df_taxas_raw)
    log_tempo_execucao("sumarizar_taxas_min_max_por_semestre", inicio_taxas_sum)
    inicio_taxas_tab = time.time()
    tabela_min_max_taxas_html = gerar_tabela_html(
        df_taxas_sumarizado,
        "Análise de Taxas Mínimas e Máximas por Semestre",
    )
    log_tempo_execucao("gerar_tabela_min_max_taxas_html", inicio_taxas_tab)

    # Bloco contagem transações - usar dados do JOIN ao invés da view para garantir precisão
    inicio_contagem = time.time()
    if not df_join.empty:
        # Usar a função correta que já gera Ano-Semestre
        df_contagem_sumarizado = calcular_contagem_taxas_agrupado(df_join)

        print(
            f"Debug: Contagem de transações calculada - {len(df_contagem_sumarizado)} grupos"
        )
        if (
            not df_contagem_sumarizado.empty
            and "Ano-Semestre" in df_contagem_sumarizado.columns
        ):
            print(
                f"Debug: Ano-Semestres encontrados: {sorted(df_contagem_sumarizado['Ano-Semestre'].unique())}"
            )
    else:
        # Fallback para view se JOIN estiver vazio
        df_contagem_raw = ler_view(
            engine,
            "vw_contagem_transacoes_ano_bandeira_modalidade",
            processamento_id,
            data_inicio,
            data_fim,
        )
        df_contagem_sumarizado = sumarizar_contagem_transacoes(df_contagem_raw)

    log_tempo_execucao("calcular_contagem_transacoes", inicio_contagem)
    inicio_contagem_tab = time.time()
    tabela_contagem_taxas_html = gerar_tabela_html(
        df_contagem_sumarizado,
        "Contagem de Transações por Ano-Semestre, Bandeira e Modalidade",
    )
    log_tempo_execucao("gerar_tabela_contagem_taxas_html", inicio_contagem_tab)

    # Sumarizar dados de recebíveis
    inicio_recebiveis = time.time()
    df_recebiveis_raw = ler_view(
        engine,
        "vw_sumario_recebiveis_semestre",
        processamento_id,
        data_inicio,
        data_fim,
    )
    log_tempo_execucao("ler_view(vw_sumario_recebiveis_semestre)", inicio_recebiveis)
    inicio_recebiveis_sum = time.time()
    df_recebiveis_sumarizado = sumarizar_recebiveis_por_semestre(df_recebiveis_raw)
    log_tempo_execucao("sumarizar_recebiveis_por_semestre", inicio_recebiveis_sum)
    inicio_recebiveis_tab = time.time()
    tabela_sumario_recebiveis_html = gerar_tabela_html(
        df_recebiveis_sumarizado,
        "Sumário de Registros com Descontos Contestáveis/ por Semestre",
    )
    log_tempo_execucao("gerar_tabela_sumario_recebiveis_html", inicio_recebiveis_tab)

    # Gerar tabela de dados bancários distintos
    inicio_dados_bancarios = time.time()
    df_dados_bancarios = obter_dados_bancarios_distintos(engine, processamento_id)
    tabela_dados_bancarios_html = gerar_tabela_html(
        df_dados_bancarios, "Dados Bancários Distintos nos Recebíveis"
    )
    log_tempo_execucao("gerar_tabela_dados_bancarios_html", inicio_dados_bancarios)

    # Gerar evidências de transações (Top 3 maiores e menores)
    inicio_evidencias = time.time()
    evidencias = obter_evidencias_transacoes(
        engine, processamento_id, calc_tipo, data_inicio, data_fim
    )

    # Gerar tabelas HTML para cada evidência
    tabela_evidencias_maiores_valores_html = (
        gerar_tabela_html(
            evidencias["maiores_valores"], "Top 3 Maiores Valores de Transação"
        )
        if not evidencias["maiores_valores"].empty
        else ""
    )

    tabela_evidencias_menores_valores_html = (
        gerar_tabela_html(
            evidencias["menores_valores"], "Top 3 Menores Valores de Transação"
        )
        if not evidencias["menores_valores"].empty
        else ""
    )

    tabela_evidencias_maiores_taxas_html = (
        gerar_tabela_html(evidencias["maiores_taxas"], "Top 3 Maiores Taxas Aplicadas")
        if not evidencias["maiores_taxas"].empty
        else ""
    )

    tabela_evidencias_menores_taxas_html = (
        gerar_tabela_html(evidencias["menores_taxas"], "Top 3 Menores Taxas Aplicadas")
        if not evidencias["menores_taxas"].empty
        else ""
    )

    log_tempo_execucao("gerar_evidencias_transacoes", inicio_evidencias)

    # Gerar demonstrativo de vendas filtradas (se solicitado)
    tabela_vendas_filtradas_html = ""
    df_vendas_filtradas = pd.DataFrame()  # Inicializar vazio
    if incluir_filtradas:
        inicio_filtradas = time.time()
        df_vendas_filtradas = gerar_demonstrativo_vendas_filtradas(
            engine, processamento_id, data_inicio, data_fim
        )
        log_tempo_execucao("gerar_demonstrativo_vendas_filtradas", inicio_filtradas)

        inicio_filtradas_tab = time.time()
        tabela_vendas_filtradas_html = gerar_tabela_html(
            df_vendas_filtradas, "Demonstrativo de Outras Vendas"
        )
        log_tempo_execucao("gerar_tabela_vendas_filtradas_html", inicio_filtradas_tab)

    # Gerar demonstrativo de recebíveis filtrados (sempre tentar)
    tabela_recebiveis_filtrados_html = ""
    inicio_rec_filtrados = time.time()
    df_recebiveis_filtrados = gerar_demonstrativo_recebiveis_filtrados(
        engine, processamento_id, data_inicio, data_fim
    )
    log_tempo_execucao("gerar_demonstrativo_recebiveis_filtrados", inicio_rec_filtrados)

    # Só gerar HTML se houver dados ou se foi explicitamente solicitado
    if not df_recebiveis_filtrados.empty or incluir_recebiveis_filtrados:
        inicio_rec_filtrados_tab = time.time()
        tabela_recebiveis_filtrados_html = gerar_tabela_html(
            df_recebiveis_filtrados, "Demonstrativo de Outros Registros de Desconto"
        )
        log_tempo_execucao(
            "gerar_tabela_recebiveis_filtrados_html", inicio_rec_filtrados_tab
        )

    # Gerar gráficos
    inicio_graficos = time.time()
    print(f"[DEBUG] Iniciando geração de gráficos")

    # Gráfico por bandeira
    inicio_grafico_bandeira = time.time()
    df_grafico_bandeira = ler_view(
        engine,
        "vw_grafico_vendas_por_bandeira",
        processamento_id,
        data_inicio,
        data_fim,
    )
    log_tempo_execucao(
        "ler_view(vw_grafico_vendas_por_bandeira)", inicio_grafico_bandeira
    )
    grafico_bandeiras_path = criar_grafico(
        df_grafico_bandeira, "bandeira", "Distribuição de Vendas por Bandeira"
    )

    # Gráfico por forma de pagamento
    inicio_grafico_forma = time.time()
    df_grafico_forma = ler_view(
        engine,
        "vw_grafico_vendas_por_forma_pagamento",
        processamento_id,
        data_inicio,
        data_fim,
    )
    log_tempo_execucao(
        "ler_view(vw_grafico_vendas_por_forma_pagamento)", inicio_grafico_forma
    )

    # Normalizar forma de pagamento nos dados do gráfico
    if not df_grafico_forma.empty and "forma_pagamento" in df_grafico_forma.columns:
        df_grafico_forma["forma_pagamento"] = df_grafico_forma["forma_pagamento"].apply(
            normalizar_forma_pagamento
        )

    grafico_forma_pagamento_path = criar_grafico(
        df_grafico_forma, "forma_pagamento", "Distribuição por Forma de Pagamento"
    )

    # Gráfico por mês
    inicio_grafico_meses = time.time()
    df_grafico_meses = ler_view(
        engine, "vw_grafico_vendas_por_mes", processamento_id, data_inicio, data_fim
    )
    log_tempo_execucao("ler_view(vw_grafico_vendas_por_mes)", inicio_grafico_meses)
    grafico_meses_path = criar_grafico(
        df_grafico_meses, "vendas_mes", "Quantidade de Vendas por Mês"
    )

    # Gráfico valor médio por bandeira
    inicio_grafico_valores = time.time()
    df_grafico_valores = ler_view(
        engine,
        "vw_grafico_valor_medio_por_bandeira",
        processamento_id,
        data_inicio,
        data_fim,
    )
    log_tempo_execucao(
        "ler_view(vw_grafico_valor_medio_por_bandeira)", inicio_grafico_valores
    )
    grafico_valores_path = criar_grafico(
        df_grafico_valores,
        "valor_medio_bandeira",
        "Valor Médio de Venda por Bandeira (R$)",
    )

    log_tempo_execucao("gerar_todos_graficos", inicio_graficos)

    # Garantir definição de variáveis obrigatórias para o template
    base_df = base_df if "base_df" in locals() else None

    # Processar template
    inicio_template = time.time()
    print(f"[DEBUG] Iniciando processamento do template")

    def to_file_url(path):
        return "file:///" + os.path.abspath(path).replace("\\", "/")

    project_root = os.path.dirname(os.path.dirname(__file__))
    assets_path = os.path.join(project_root, "assets")
    dir_path_relatorios = criar_diretorio_relatorios()

    caminho_capa = os.path.join(assets_path, "capa_relatorio.jpg")
    caminho_cabecalho = os.path.join(assets_path, "cabecalho_financial.png")

    cover_image_url = to_file_url(caminho_capa) if os.path.exists(caminho_capa) else ""
    header_image_url = (
        to_file_url(caminho_cabecalho) if os.path.exists(caminho_cabecalho) else ""
    )

    inicio_env = time.time()
    env = Environment(loader=FileSystemLoader(dir_path_relatorios))
    template = env.get_template("template_relatorio.html")
    log_tempo_execucao("carregar_template_html", inicio_env)

    # Calcular materialidade para o relatório
    inicio_materialidade = time.time()
    print(f"[DEBUG] Calculando materialidade...")

    # 1. Soma das perdas monetárias (MDR + RR)
    total_perdas = 0
    total_perdas_rr = 0
    try:
        sql_perdas = """
        SELECT 
            SUM(COALESCE(perda, 0)) as total_perdas_mdr,
            SUM(COALESCE(perda_rr, 0)) as total_perdas_rr
        FROM vendas_calculos
        WHERE calc_id = %s AND calc_tipo = %s
        """
        params_perdas = (
            (processamento_id, calc_tipo)
            if not adquirente
            else (processamento_id, calc_tipo, adquirente)
        )
        if adquirente:
            sql_perdas += " AND adquirente = %s"

        sql_perdas = _convert_placeholders(engine, sql_perdas)

        df_perdas = pd.read_sql(sql_perdas, engine, params=params_perdas)
        if not df_perdas.empty:
            # Case-insensitive: pegar os nomes reais das colunas
            cols = df_perdas.columns.tolist()
            col_mdr = cols[0] if len(cols) > 0 else "total_perdas_mdr"
            col_rr = cols[1] if len(cols) > 1 else "total_perdas_rr"
            total_perdas = df_perdas.iloc[0][col_mdr] or 0
            total_perdas_rr = df_perdas.iloc[0][col_rr] or 0

        total_perdas = total_perdas if not pd.isna(total_perdas) else 0
        total_perdas_rr = total_perdas_rr if not pd.isna(total_perdas_rr) else 0

        print(f"[DEBUG] Total de perdas MDR: {format_currency_br(total_perdas)}")
        print(f"[DEBUG] Total de perdas RR: {format_currency_br(total_perdas_rr)}")
    except Exception as e:
        print(f"[DEBUG] Erro ao calcular perdas: {e}")
        total_perdas = 0
        total_perdas_rr = 0

    # 2. Soma dos recebíveis (valores com desconto)
    total_recebiveis = 0
    try:
        sql_recebiveis = """
        SELECT SUM(COALESCE(valor_recebivel, 0)) as total_recebiveis
        FROM recebiveis_processados 
        WHERE processamentoid = %s
        """
        sql_recebiveis = _convert_placeholders(engine, sql_recebiveis)
        df_recebiveis = pd.read_sql(sql_recebiveis, engine, params=(processamento_id,))
        total_recebiveis = (
            df_recebiveis.iloc[0]["total_recebiveis"] if not df_recebiveis.empty else 0
        )
        total_recebiveis = total_recebiveis if not pd.isna(total_recebiveis) else 0

        print(
            f"[DEBUG] Total de recebíveis calculado: {format_currency_br(total_recebiveis)}"
        )
    except Exception as e:
        print(f"[DEBUG] Erro ao calcular recebíveis: {e}")
        total_recebiveis = 0

    # 3. Calcular valor total da materialidade
    valor_materialidade = total_perdas + total_perdas_rr + total_recebiveis

    # 4. Calcular percentual em relação ao faturamento bruto
    percentual_materialidade = 0
    if valor_total > 0:
        percentual_materialidade = (valor_materialidade / valor_total) * 100

    # Formatar valores para exibição
    valor_materialidade_formatado = format_currency_br(valor_materialidade)
    percentual_formatado = f"{percentual_materialidade:.2f}%".replace(".", ",")

    print(
        f"[DEBUG] Materialidade - Valor: {valor_materialidade_formatado}, Percentual: {percentual_formatado}"
    )
    log_tempo_execucao("calcular_materialidade", inicio_materialidade)

    # Texto de disclaimer/observação para o final do relatório
    disclaimer_text = "Todas as análises são realizadas com base exclusivamente nos extratos oficiais fornecidos pela Adquirente; não alteramos arquivos."

    # Formatar valores individuais das perdas
    total_perdas_formatado = format_currency_br(total_perdas)
    total_perdas_rr_formatado = format_currency_br(total_perdas_rr)
    total_recebiveis_formatado = format_currency_br(total_recebiveis)

    # Variáveis para o template (apenas valores dinâmicos)
    materialidade_valor = valor_materialidade_formatado
    materialidade_percentual = percentual_formatado
    perda_mdr_valor = total_perdas_formatado
    perda_rr_valor = total_perdas_rr_formatado
    recebiveis_valor = total_recebiveis_formatado

    inicio_render = time.time()
    html_content = template.render(
        cover_image_path=cover_image_url,
        header_image_path=header_image_url,
        tabela_sumario_html=tabela_sumario_html,
        tabela_perdas_semestre_html=tabela_perdas_semestre_html,
        tabela_min_max_taxas_html=tabela_min_max_taxas_html,
        tabela_contagem_taxas_html=tabela_contagem_taxas_html,
        tabela_sumario_recebiveis_html=tabela_sumario_recebiveis_html,
        tabela_dados_bancarios_html=tabela_dados_bancarios_html,
        tabela_evidencias_maiores_valores_html=tabela_evidencias_maiores_valores_html,
        tabela_evidencias_menores_valores_html=tabela_evidencias_menores_valores_html,
        tabela_evidencias_maiores_taxas_html=tabela_evidencias_maiores_taxas_html,
        tabela_evidencias_menores_taxas_html=tabela_evidencias_menores_taxas_html,
        tabela_vendas_filtradas_html=tabela_vendas_filtradas_html,
        tabela_recebiveis_filtrados_html=tabela_recebiveis_filtrados_html,
        grafico_bandeiras_path=to_file_url(grafico_bandeiras_path),
        grafico_forma_pagamento_path=to_file_url(grafico_forma_pagamento_path),
        grafico_meses_path=to_file_url(grafico_meses_path),
        grafico_valores_path=to_file_url(grafico_valores_path),
        data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        materialidade_valor=materialidade_valor,
        materialidade_percentual=materialidade_percentual,
        perda_mdr_valor=perda_mdr_valor,
        perda_rr_valor=perda_rr_valor,
        recebiveis_valor=recebiveis_valor,
        disclaimer_text=disclaimer_text,
        adquirente_principal=metadados.get("adquirente", ""),
    )
    log_tempo_execucao("renderizar_template_html", inicio_render)

    safe_proc_id = re.sub(r"[^\w\-]", "_", processamento_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(
        dir_path_relatorios, f"relatorio_{safe_proc_id}_{timestamp}.html"
    )

    inicio_write = time.time()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    log_tempo_execucao("escrever_arquivo_html", inicio_write)

    log_tempo_execucao("processar_template", inicio_template)
    log_tempo_execucao("=== RELATÓRIO HTML COMPLETO ===", inicio_total)
    print(f"[DEBUG] Arquivo gerado: {html_path}")

    # Buscar vendas completas de vendas_calculos para Excel
    inicio_vendas_completas = time.time()
    sql_vendas_completas = """
        SELECT 
            vc.id,
            vc.id_venda,
            vc.calc_id,
            vc.calc_tipo,
            vc.forma_pagamento,
            vc.vl_venda,
            vc.tx_venda,
            vc.desc_venda,
            vc.vl_liq_venda,
            vc.tx_calc,
            vc.desc_calc,
            vc.vl_liq_calc,
            vc.perda,
            vc.perda_rr,
            vc.data_venda AS Data_da_venda,
            vc.bandeira AS Bandeira,
            vc.arquivo_origem
        FROM vendas_calculos vc
        WHERE vc.calc_id = %s AND vc.calc_tipo = %s
    """

    params_completas = [processamento_id, calc_tipo]

    if adquirente:
        sql_vendas_completas += " AND vc.adquirente = %s"
        params_completas.append(adquirente)

    if data_inicio:
        sql_vendas_completas += " AND vc.data_venda >= %s"
        params_completas.append(data_inicio)

    if data_fim:
        sql_vendas_completas += " AND vc.data_venda <= %s"
        params_completas.append(data_fim)

    if apenas_com_perdas:
        sql_vendas_completas += " AND (vc.perda > 0 OR COALESCE(vc.perda_rr, 0) > 0)"

    sql_vendas_completas += " ORDER BY vc.data_venda, vc.bandeira"
    sql_vendas_completas = _convert_placeholders(engine, sql_vendas_completas)

    df_vendas_completas = read_sql_safe(
        sql_vendas_completas, engine, params=tuple(params_completas)
    )
    log_tempo_execucao("buscar_vendas_completas_excel", inicio_vendas_completas)
    print(f"[DEBUG] Vendas completas carregadas: {len(df_vendas_completas)} registros")

    # Gerar Excel com todas as abas (DataFrames do relatório)
    inicio_excel = time.time()
    dataframes_excel = {
        "1. Vendas Completas": df_vendas_completas,
        "2. Resumo Geral": (
            df_join[
                [
                    "Data_da_venda",
                    "Bandeira",
                    "Forma_de_pagamento",
                    "vl_venda",
                    "tx_venda",
                    "perda",
                ]
            ]
            if not df_join.empty
            else pd.DataFrame()
        ),
        "3. Perdas por Semestre": df_perdas_sumarizado,
        "4. Taxas Min-Max": df_taxas_sumarizado,
        "5. Contagem Transações": df_contagem_sumarizado,
        "6. Sumário Recebíveis": df_recebiveis_sumarizado,
        "7. Dados Bancários": df_dados_bancarios,
        "8. Top 3 Maiores Valores": evidencias.get("maiores_valores", pd.DataFrame()),
        "9. Top 3 Maiores Taxas": evidencias.get("maiores_taxas", pd.DataFrame()),
    }

    # Adicionar vendas filtradas se solicitado
    if (
        incluir_filtradas
        and "df_vendas_filtradas" in locals()
        and not df_vendas_filtradas.empty
    ):
        dataframes_excel["10. Vendas Filtradas"] = df_vendas_filtradas

    # Adicionar recebíveis filtrados se houver dados
    if "df_recebiveis_filtrados" in locals() and not df_recebiveis_filtrados.empty:
        dataframes_excel["11. Recebíveis Filtrados"] = df_recebiveis_filtrados

    excel_path = gerar_excel_relatorio(
        dataframes_excel, f"relatorio_{safe_proc_id}_{timestamp}"
    )
    log_tempo_execucao("gerar_excel_relatorio", inicio_excel)

    if excel_path:
        print(f"[DEBUG] ✓ Excel gerado: {excel_path}")

    # Gerar relatório sintético automaticamente
    print(f"[DEBUG] Gerando relatório sintético...")
    try:
        sintetico_path = gerar_relatorio_sintetico_html(
            metadados=metadados,
            total_transacoes=quantidade,
            faturamento_bruto=valor_total,
            valor_liquido=df_join["vl_liq_venda"].sum() if not df_join.empty else 0,
            ticket_medio=valor_medio,
            taxa_media=df_join["tx_venda"].mean() if not df_join.empty else 0,
            total_divergencias=(
                df_perdas["perda_total"].sum()
                if not df_perdas.empty and "perda_total" in df_perdas.columns
                else 0
            ),
            bandeiras=(
                df_join.groupby("Bandeira")
                .agg({"Bandeira": "count", "vl_venda": "sum"})
                .rename(columns={"Bandeira": "qtd", "vl_venda": "valor"})
                .reset_index()
                if not df_join.empty
                else pd.DataFrame()
            ),
            top_valores=(
                evidencias["maiores_valores"].head(3)
                if not evidencias["maiores_valores"].empty
                else pd.DataFrame()
            ),
            primeira_venda=primeira_venda,
            ultima_venda=ultima_venda,
            periodo_dias=periodo_dias,
            adquirente=metadados.get("adquirente", "Não identificado"),
            processamento_id=processamento_id,
        )
        print(f"[DEBUG] ✓ Relatório sintético gerado: {sintetico_path}")
    except Exception as e:
        print(f"[DEBUG] ⚠️ Erro ao gerar relatório sintético: {e}")
        sintetico_path = None

    return html_path, base_df if return_base else None, sintetico_path


def gerar_relatorio_sintetico_html(
    metadados: Dict,
    total_transacoes: int,
    faturamento_bruto: float,
    valor_liquido: float,
    ticket_medio: float,
    taxa_media: float,
    total_divergencias: float,
    bandeiras: pd.DataFrame,
    top_valores: pd.DataFrame,
    primeira_venda,
    ultima_venda,
    periodo_dias: int,
    adquirente: str,
    processamento_id: str,
) -> str:
    """
    Gera relatório sintético HTML a partir dos dados do relatório analítico.

    Returns:
        Caminho do arquivo HTML gerado
    """
    print("[DEBUG] Iniciando geração do relatório sintético...")

    # Calcular período
    if primeira_venda and ultima_venda:
        if isinstance(primeira_venda, str):
            primeira_venda_dt = pd.to_datetime(primeira_venda)
        else:
            primeira_venda_dt = primeira_venda

        if isinstance(ultima_venda, str):
            ultima_venda_dt = pd.to_datetime(ultima_venda)
        else:
            ultima_venda_dt = ultima_venda

        periodo = f"{primeira_venda_dt.strftime('%d/%m/%Y')} a {ultima_venda_dt.strftime('%d/%m/%Y')}"
    else:
        periodo = "Período não disponível"

    # Calcular percentual líquido
    percentual_liquido = (
        (valor_liquido / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
    )

    # Formatar valores
    ticket_medio_fmt = format_currency_br(ticket_medio)
    taxa_media_fmt = f"{taxa_media:.2f}"
    total_divergencias_fmt = format_currency_br(total_divergencias)
    faturamento_bruto_fmt = format_currency_br(faturamento_bruto)
    valor_liquido_fmt = format_currency_br(valor_liquido)

    # Preparar resumo do faturamento
    resumo_faturamento = f"""No período de <strong>{periodo}</strong> ({periodo_dias} dias), foram processadas <strong>{total_transacoes:,} transações</strong> via cartão, totalizando um <strong>faturamento bruto de {faturamento_bruto_fmt}</strong>. Após descontos de taxas da operadora, o <strong>valor líquido recebido</strong> foi de <strong>{valor_liquido_fmt}</strong>, representando <strong>{percentual_liquido:.2f}% do faturamento</strong>.""".replace(
        ",", "."
    )

    # Preparar bandeiras
    bandeiras_lista = []
    total_faturamento = faturamento_bruto
    if not bandeiras.empty and len(bandeiras) > 0:
        for idx, row in bandeiras.iterrows():
            percentual = (
                (row["valor"] / total_faturamento * 100) if total_faturamento > 0 else 0
            )
            bandeiras_lista.append(
                {
                    "nome": row["Bandeira"],
                    "qtd": int(row["qtd"]),
                    "valor": format_currency_br(row["valor"]),
                    "percentual": f"{percentual:.1f}",
                }
            )

    # Preparar top valores
    top_valores_lista = []
    if not top_valores.empty:
        for idx, row in top_valores.head(3).iterrows():
            top_valores_lista.append(
                {
                    "data": row.get("Data", ""),
                    "bandeira": row.get("Bandeira", ""),
                    "valor": row.get("Valor", ""),
                    "taxa": row.get("Taxa (%)", ""),
                }
            )

    # Gerar destaques automáticos
    destaques = []

    # Verificar conformidade de taxa
    if total_divergencias == 0:
        destaques.append(
            {
                "tipo": "success",
                "icone": "✅",
                "titulo": "Zero divergências detectadas",
                "descricao": "Não foram identificadas perdas monetárias por variação de taxas MDR ou cobranças indevidas, demonstrando boa conformidade operacional.",
            }
        )
    else:
        perc_divergencia = (
            (total_divergencias / faturamento_bruto * 100)
            if faturamento_bruto > 0
            else 0
        )
        destaques.append(
            {
                "tipo": "warning",
                "icone": "⚠️",
                "titulo": f"Divergências detectadas ({perc_divergencia:.2f}%)",
                "descricao": f"Foram identificadas perdas no valor de {total_divergencias_fmt}, representando {perc_divergencia:.2f}% do faturamento total.",
            }
        )

    # Taxa média
    destaques.append(
        {
            "tipo": "success",
            "icone": "📊",
            "titulo": "Taxa média aplicada",
            "descricao": f"A taxa média de {taxa_media_fmt}% foi aplicada nas transações do período.",
        }
    )

    # Conclusão e recomendações
    if total_divergencias == 0:
        conclusao = f"A conciliação do período apresentou <strong>excelente conformidade</strong>, com <strong>0% de divergências</strong> identificadas. O ticket médio de {ticket_medio_fmt} e o faturamento bruto de {faturamento_bruto_fmt} em {periodo_dias} dias indicam boa movimentação operacional."
        recomendacoes = [
            "Manter monitoramento contínuo para detectar variações futuras nas taxas aplicadas.",
            "Continuar a conciliação periódica mesmo sem divergências detectadas.",
            "Documentar transações extremas para validar autenticidade das operações.",
        ]
    else:
        perc_div = (
            (total_divergencias / faturamento_bruto * 100)
            if faturamento_bruto > 0
            else 0
        )
        conclusao = f"A conciliação do período identificou divergências no valor de {total_divergencias_fmt}, correspondendo a {perc_div:.2f}% do faturamento. Recomenda-se atenção especial às transações com variação de taxas."
        recomendacoes = [
            f"Revisar as transações com divergências ({total_divergencias_fmt}) junto à adquirente.",
            "Solicitar renegociação de taxas caso o padrão de divergências se mantenha.",
            "Implementar monitoramento em tempo real para detectar cobranças indevidas.",
        ]

    # Renderizar template
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "relatorios"
    )
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("template_relatorio_sintetico.html")

    html_content = template.render(
        cliente_nome=metadados.get("cliente_nome", "Cliente"),
        periodo=periodo,
        adquirente=adquirente,
        data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        ticket_medio=ticket_medio_fmt,
        taxa_media=taxa_media_fmt,
        total_divergencias=total_divergencias_fmt,
        total_divergencias_num=total_divergencias,
        resumo_faturamento=resumo_faturamento,
        total_transacoes=f"{total_transacoes:,}".replace(",", "."),
        faturamento_bruto=faturamento_bruto_fmt,
        valor_liquido=valor_liquido_fmt,
        percentual_liquido=f"{percentual_liquido:.2f}",
        bandeiras=bandeiras_lista,
        destaques=destaques,
        top_valores=top_valores_lista,
        conclusao=conclusao,
        recomendacoes=recomendacoes,
        disclaimer="Todas as análises são baseadas exclusivamente nos dados fornecidos pela adquirente.",
    )

    # Salvar arquivo
    dir_path = criar_diretorio_relatorios()

    # Sanitizar nome do cliente
    cliente_nome = metadados.get("cliente_nome", "cliente")
    caracteres_invalidos = [
        "<",
        ">",
        ":",
        '"',
        "/",
        "\\",
        "|",
        "?",
        "*",
        "(",
        ")",
        ".",
        ",",
    ]
    for char in caracteres_invalidos:
        cliente_nome = cliente_nome.replace(char, "")
    cliente_nome = cliente_nome.replace(" ", "_")[:50]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"relatorio_sintetico_{cliente_nome}_{timestamp}.html"
    html_path = os.path.join(dir_path, html_filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[DEBUG] Relatório sintético salvo em: {html_path}")
    return html_path


def ler_view(
    engine: Engine,
    view_name: str,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Lê dados de uma view no banco, aplicando filtros de processamento e data.
    Para SQLite, usa queries diretas já que as views podem não existir.
    """
    inicio = time.time()
    print(f"[DEBUG] Iniciando leitura da view: {view_name}")

    db_type = engine.dialect.name.lower()

    # Queries de substituição para views que não existem no SQLite
    view_queries_sqlite = {
        "vw_grafico_vendas_por_bandeira": """
            SELECT bandeira AS Bandeira, COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY bandeira
        """,
        "vw_grafico_vendas_por_forma_pagamento": """
            SELECT forma_pagamento AS Forma_de_pagamento, COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY forma_pagamento
        """,
        "vw_grafico_vendas_por_mes": """
            SELECT 
                strftime('%Y-%m', data_venda) AS MesAno,
                COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY strftime('%Y-%m', data_venda)
            ORDER BY MesAno
        """,
        "vw_grafico_valor_medio_por_bandeira": """
            SELECT 
                bandeira AS Bandeira,
                AVG(vl_venda) AS ValorMedio
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY bandeira
        """,
    }

    view_queries_mysql = {
        "vw_grafico_vendas_por_bandeira": """
            SELECT bandeira AS Bandeira, COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY bandeira
        """,
        "vw_grafico_vendas_por_forma_pagamento": """
            SELECT forma_pagamento AS Forma_de_pagamento, COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY forma_pagamento
        """,
        "vw_grafico_vendas_por_mes": """
            SELECT 
                DATE_FORMAT(data_venda, '%Y-%m') AS MesAno,
                COUNT(*) AS Quantidade
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY DATE_FORMAT(data_venda, '%Y-%m')
            ORDER BY MesAno
        """,
        "vw_grafico_valor_medio_por_bandeira": """
            SELECT 
                bandeira AS Bandeira,
                AVG(vl_venda) AS ValorMedio
            FROM vendas_calculos
            WHERE calc_id = %s
            GROUP BY bandeira
        """,
    }

    # Escolher queries conforme banco
    view_queries = view_queries_sqlite if "sqlite" in db_type else view_queries_mysql

    params = (processamento_id,)
    date_column_map = {
        "vw_perdas_por_semestre": "Data_da_venda",
        "vw_min_max_taxas_semestre": "Data_da_venda",
        "vw_contagem_transacoes_ano_bandeira_modalidade": "Data_da_venda",
        "vw_sumario_recebiveis_semestre": "data_recebivel",
        "vendas_processadas": "Data_da_venda",
        "vw_grafico_vendas_por_bandeira": "data_venda",
        "vw_grafico_vendas_por_forma_pagamento": "data_venda",
        "vw_grafico_vendas_por_mes": "data_venda",
        "vw_grafico_valor_medio_por_bandeira": "data_venda",
    }

    # Map different filter columns for different tables/views
    filter_column_map = {
        "vendas_processadas": "processamentoid",
        "vw_perdas_por_semestre": "calc_id",
        "vw_min_max_taxas_semestre": "calc_id",
        "vw_contagem_transacoes_ano_bandeira_modalidade": "calc_id",
        "vw_sumario_recebiveis_semestre": "calc_id",
        "vw_grafico_vendas_por_bandeira": "calc_id",
        "vw_grafico_vendas_por_forma_pagamento": "calc_id",
        "vw_grafico_vendas_por_mes": "calc_id",
        "vw_grafico_valor_medio_por_bandeira": "calc_id",
    }

    date_column = date_column_map.get(view_name)
    filter_column = filter_column_map.get(view_name, "calc_id")

    # Usar query direta se for uma view de gráfico e não existir como view
    if view_name in view_queries:
        sql = view_queries[view_name]

        # Adicionar filtro de data se fornecido
        if data_inicio and data_fim and date_column:
            sql = sql.replace(
                "WHERE calc_id = %s",
                f"WHERE calc_id = %s AND {date_column} BETWEEN %s AND %s",
            )
            params = params + (data_inicio, data_fim)
    else:
        sql = f"SELECT * FROM {view_name} WHERE {filter_column} = %s"

        if data_inicio and data_fim and date_column:
            sql += f" AND {date_column} BETWEEN %s AND %s"
            params = params + (data_inicio, data_fim)

    sql = _convert_placeholders(engine, sql)

    try:
        resultado = pd.read_sql(sql, engine, params=params)

        # Aplicar filtro específico da REDE para views que contêm dados de vendas
        views_com_valores = [
            "vw_grafico_vendas_por_bandeira",
            "vw_grafico_valor_medio_por_bandeira",
            "vw_grafico_vendas_por_forma_pagamento",
            "vw_grafico_vendas_por_mes",
        ]

        if view_name in views_com_valores and not resultado.empty:
            inicio_filtro = time.time()
            resultado = filtrar_valores_rede_depara(resultado)
            log_tempo_execucao(
                f"filtrar_valores_rede_depara({view_name})", inicio_filtro
            )

        log_tempo_execucao(f"ler_view({view_name}) - {len(resultado)} linhas", inicio)
        return resultado
    except Exception as e:
        print(f"Erro ao ler view {view_name}: {e}")
        log_tempo_execucao(f"ler_view({view_name}) - ERRO", inicio)
        return pd.DataFrame()


def criar_grafico(df: pd.DataFrame, tipo: str, titulo: str) -> str:
    """Função genérica para criar e salvar gráficos a partir de um DataFrame."""
    inicio = time.time()
    print(f"[DEBUG] Criando gráfico: {tipo}")
    fig = None
    if df.empty:
        df_placeholder = pd.DataFrame([{"label": "Sem dados", "value": 1}])
        fig = px.pie(
            df_placeholder, names="label", values="value", title=f"{titulo} (Sem dados)"
        )

    if tipo == "bandeira" and not df.empty:
        fig = px.pie(
            df,
            names="Bandeira",
            values="Quantidade",
            title=titulo,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
    elif tipo == "forma_pagamento" and not df.empty:
        fig = px.pie(
            df,
            names="Forma_de_pagamento",
            values="Quantidade",
            title=titulo,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
    elif tipo == "vendas_mes" and not df.empty:
        df = df.sort_values("MesAno")
        fig = px.bar(
            df,
            x="MesAno",
            y="Quantidade",
            title=titulo,
            color_discrete_sequence=["#636EFA"],
        )
    elif tipo == "valor_medio_bandeira" and not df.empty:
        fig = px.bar(
            df,
            x="Bandeira",
            y="ValorMedio",
            title=titulo,
            color="Bandeira",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat=",.2f")

    if fig:
        if "pie" in str(type(fig.data[0])).lower():
            # Remover rótulos de dentro da pizza, manter apenas na legenda
            fig.update_traces(textposition="none", textinfo="none")
            fig.update_layout(showlegend=True)
        dir_path = criar_diretorio_relatorios()
        img_path = os.path.join(
            dir_path, f'grafico_{tipo}_{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        )
        try:
            # Primeiro, tentar salvar normalmente
            fig.write_image(img_path, width=800, height=600, engine="kaleido")
            log_tempo_execucao(f"criar_grafico({tipo})", inicio)
            return img_path
        except Exception as e:
            print(f"[WARNING] Erro ao salvar gráfico {tipo} com kaleido: {e}")
            try:
                # Tentar com engine alternativo
                import plotly.io as pio

                pio.write_image(fig, img_path, width=800, height=600, format="png")
                log_tempo_execucao(f"criar_grafico({tipo}) - fallback", inicio)
                return img_path
            except Exception as e2:
                print(f"[ERROR] Erro fatal ao salvar gráfico {tipo}: {e2}")
                log_tempo_execucao(f"criar_grafico({tipo}) - erro fatal", inicio)
                # Retornar caminho vazio mas não falhar o relatório
                return ""
    log_tempo_execucao(f"criar_grafico({tipo}) - vazio", inicio)
    return ""


def gerar_tabela_html(df: pd.DataFrame, titulo: str) -> str:
    if df.empty:
        return f'<div class="report-section"><h3>{titulo}</h3><p>Sem dados suficientes para esta análise.</p></div>'

    html = f'<div class="report-section"><h3>{titulo}</h3><table class="report-table">'
    html += "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>"

    for _, row in df.iterrows():
        html += "<tr>"

        # Verificar se é linha de total
        is_total_row = "TOTAL GERAL" in str(row.iloc[0])

        for col in df.columns:
            valor = row[col]
            # Formatação numérica
            if isinstance(valor, (int, float)):
                # Se é coluna de contagem, formatar como inteiro
                if "Contagem" in col or "Quantidade" in col:
                    valor_str = f"{int(valor):,}".replace(",", ".")
                elif 0.0001 < abs(valor) < 1000:
                    valor_str = format_currency_br(valor).replace("R$ ", "")
                else:
                    valor_str = str(int(valor)) if valor == int(valor) else str(valor)
            else:
                valor_str = str(valor)

            valor_str = valor_str.replace("CREDITO", "CRÉDITO").replace(
                "DEBITO", "DÉBITO"
            )

            # Aplicar formatação
            if is_total_row:
                # Toda linha de total: vermelha e negrito
                html += (
                    f"<td style='color: #9c1313; font-weight: bold;'>{valor_str}</td>"
                )
            else:
                # Célula normal (sem formatação especial para colunas de perda)
                html += f"<td>{valor_str}</td>"
        html += "</tr>"

    html += "</table></div>"
    return html


def criar_diretorio_relatorios():
    dir_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "relatorios")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def obter_ecs_distintos_processamento(
    engine: Engine, processamento_id: str, adquirente: str = None
) -> List[str]:
    """Busca todos os EC IDs distintos presentes em um processamento, opcionalmente filtrado por adquirente."""
    try:
        # Busca ECs distintos nas vendas processadas
        if adquirente:
            query = "SELECT DISTINCT ec_id FROM vendas_processadas WHERE processamentoid = %s AND ec_id IS NOT NULL AND adquirente = %s"
            query = _convert_placeholders(engine, query)
            df_ecs = pd.read_sql(query, engine, params=(processamento_id, adquirente))
        else:
            query = "SELECT DISTINCT ec_id FROM vendas_processadas WHERE processamentoid = %s AND ec_id IS NOT NULL"
            query = _convert_placeholders(engine, query)
            df_ecs = pd.read_sql(query, engine, params=(processamento_id,))

        if df_ecs.empty:
            return []

        # Remove valores nulos e converte para lista
        ecs_list = df_ecs["ec_id"].dropna().astype(str).tolist()

        # Remove valores vazios e ordena
        ecs_list = [ec.strip() for ec in ecs_list if ec.strip()]
        ecs_list.sort()

        return ecs_list
    except Exception as e:
        print(f"Erro ao buscar ECs distintos: {e}")
        return []


def obter_dados_processamento(engine: Engine, processamento_id: str) -> Dict[str, Any]:
    metadados_sql = (
        "SELECT * FROM controle_processamentos WHERE id_processamento = :proc_id"
    )
    metadados = fetch_one(engine, metadados_sql, {"proc_id": processamento_id})
    if not metadados:
        raise ValueError(f"Processamento ID {processamento_id} não encontrado.")

    if metadados.get("cliente_id"):
        cliente_sql = "SELECT nome_fantasia, cnpj FROM clientes WHERE cliente_id = :cid"
        cliente = fetch_one(engine, cliente_sql, {"cid": metadados["cliente_id"]})
        if cliente:
            nome = cliente["nome_fantasia"]
            cnpj = cliente.get("cnpj", "")
            if cnpj:
                cnpj_digits = re.sub(r"\D", "", str(cnpj))
                if len(cnpj_digits) == 14:
                    cnpj = f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"
                nome = f"{nome} ({cnpj})"
            metadados["cliente_nome"] = nome
    return metadados

    # Gera gráficos
    grafico_bandeiras_path = criar_grafico(
        ler_view(
            engine,
            "vw_grafico_vendas_por_bandeira",
            processamento_id,
            data_inicio,
            data_fim,
        ),
        "bandeira",
        "Distribuição de Vendas por Bandeira",
    )
    grafico_forma_pagamento_path = criar_grafico(
        ler_view(
            engine,
            "vw_grafico_vendas_por_forma_pagamento",
            processamento_id,
            data_inicio,
            data_fim,
        ),
        "forma_pagamento",
        "Distribuição por Forma de Pagamento",
    )
    grafico_meses_path = criar_grafico(
        ler_view(
            engine,
            "vw_grafico_vendas_por_mes",
            processamento_id,
            data_inicio,
            data_fim,
        ),
        "vendas_mes",
        "Quantidade de Vendas por Mês",
    )
    grafico_valores_path = criar_grafico(
        ler_view(
            engine,
            "vw_grafico_valor_medio_por_bandeira",
            processamento_id,
            data_inicio,
            data_fim,
        ),
        "valor_medio_bandeira",
        "Valor Médio de Venda por Bandeira (R$)",
    )

    # Buscar ECs distintos no processamento
    ecs_distintos = obter_ecs_distintos_processamento(engine, processamento_id)

    # Buscar adquirentes distintos no processamento
    adquirentes_distintos = obter_adquirentes_distintos_processamento(
        engine, processamento_id
    )

    # Obter metadados do processamento
    metadados = obter_dados_processamento(engine, processamento_id)

    # The estatisticas_sumario and tabela_sumario_html are already created above

    # Configuração do Template
    def to_file_url2(path):
        return "file:///" + os.path.abspath(path).replace("\\", "/")

    project_root2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path2 = os.path.join(project_root2, "assets")
    dir_path_relatorios2 = criar_diretorio_relatorios()

    caminho_capa3 = os.path.join(assets_path2, "capa_relatorio.jpg")
    caminho_cabecalho3 = os.path.join(assets_path2, "cabecalho_financial.png")

    cover_image_url3 = (
        to_file_url2(caminho_capa3) if os.path.exists(caminho_capa3) else ""
    )
    header_image_url3 = (
        to_file_url2(caminho_cabecalho3) if os.path.exists(caminho_cabecalho3) else ""
    )

    if not cover_image_url:
        print(f"[AVISO] Imagem de capa não encontrada em: {caminho_capa}")
    if not header_image_url:
        print(f"[AVISO] Imagem de cabeçalho não encontrada em: {caminho_cabecalho}")

    # Texto de disclaimer/observação para o final do relatório
    disclaimer_text2 = "Todas as análises são realizadas com base exclusivamente nos extratos oficiais fornecidos pela Adquirente; não alteramos arquivos."

    # Inicializar variáveis de tabela se não existirem (valores padrão)
    if "tabela_dados_bancarios_html" not in locals():
        tabela_dados_bancarios_html = ""
    if "tabela_vendas_filtradas_html" not in locals():
        tabela_vendas_filtradas_html = ""
    if "tabela_recebiveis_filtrados_html" not in locals():
        tabela_recebiveis_filtrados_html = ""

    env2 = Environment(loader=FileSystemLoader(dir_path_relatorios))
    template2 = env2.get_template("template_relatorio.html")

    html_content2 = template2.render(
        cover_image_path=cover_image_url,
        header_image_path=header_image_url,
        tabela_sumario_html=tabela_sumario_html,
        tabela_perdas_semestre_html=tabela_perdas_semestre_html,
        tabela_min_max_taxas_html=tabela_min_max_taxas_html,
        tabela_contagem_taxas_html=tabela_contagem_taxas_html,
        tabela_sumario_recebiveis_html=tabela_sumario_recebiveis_html,
        tabela_dados_bancarios_html=tabela_dados_bancarios_html,
        tabela_vendas_filtradas_html=tabela_vendas_filtradas_html,
        tabela_recebiveis_filtrados_html=tabela_recebiveis_filtrados_html,
        grafico_bandeiras_path=to_file_url(grafico_bandeiras_path),
        grafico_forma_pagamento_path=to_file_url(grafico_forma_pagamento_path),
        grafico_meses_path=to_file_url(grafico_meses_path),
        grafico_valores_path=to_file_url(grafico_valores_path),
        data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        materialidade_valor="R$ 0,00",
        materialidade_percentual="0,00%",
        perda_mdr_valor="R$ 0,00",
        perda_rr_valor="R$ 0,00",
        recebiveis_valor="R$ 0,00",
        disclaimer_text=disclaimer_text2,
        adquirente_principal=metadados.get("adquirente", ""),
    )

    # Geração do HTML
    safe_proc_id = re.sub(r"[^\w\-]", "_", processamento_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = os.path.join(
        dir_path_relatorios, f"relatorio_{safe_proc_id}_{timestamp}.html"
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[INFO] Relatório HTML gerado em: {html_path}")
    return html_path, None


def gerar_relatorio_mensal_html(
    engine: "Engine",
    processamento_id: str,
    calc_tipo: str = None,
    mes_referencia: str = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    adquirente: str = None,
    incluir_filtradas: bool = False,
    incluir_recebiveis_filtrados: bool = False,
    apenas_com_perdas: bool = False,
) -> Tuple[str, Optional["pd.DataFrame"]]:
    """
    Gera relatório mensal de conciliação usando template específico.

    Args:
        engine: Conexão com banco de dados
        processamento_id: ID do processamento
        calc_tipo: Tipo de cálculo (log_mensal, cad, etc)
        mes_referencia: String no formato "Mês/Ano" (ex: "Janeiro/2025")
        data_inicio: Data inicial do período
        data_fim: Data final do período
        adquirente: Filtro por adquirente
        incluir_filtradas: Se deve incluir tabela de vendas filtradas
        incluir_recebiveis_filtrados: Se deve incluir tabela de recebíveis filtrados

    Returns:
        Tupla (caminho_html, dataframe_base)
    """
    print(f"[DEBUG] === INÍCIO GERAÇÃO RELATÓRIO MENSAL ===")
    print(f"[DEBUG] Processamento ID: {processamento_id}, Tipo: {calc_tipo}")
    print(f"[DEBUG] Mês Referência: {mes_referencia}")

    inicio_total = time.time()

    # Buscar metadados do processamento
    metadados = obter_dados_processamento(engine, processamento_id)

    # Buscar ECs e adquirentes distintos
    ecs_distintos = obter_ecs_distintos_processamento(
        engine, processamento_id, adquirente
    )
    adquirentes_distintos = obter_adquirentes_distintos_processamento(
        engine, processamento_id
    )

    # Determinar adquirente principal
    if adquirente and adquirente != "None":
        adquirente_principal = adquirente
    elif adquirentes_distintos:
        if len(adquirentes_distintos) == 1:
            adquirente_principal = adquirentes_distintos[0]
        else:
            adquirente_principal = ", ".join(adquirentes_distintos)
    else:
        adquirente_principal = "Não identificado"

    # Atualizar metadados com adquirente
    metadados["adquirente"] = adquirente_principal

    # Buscar dados - SEM JOIN! Todos os campos já estão em vendas_calculos
    join_sql = """
        SELECT 
            id_venda AS venda_id, data_venda AS Data_da_venda, bandeira AS Bandeira, 
            forma_pagamento AS Forma_de_pagamento,
            tx_rr_venda AS Taxas_RR, vl_rr_venda AS Valor_RR, 
            vl_venda, tx_venda, desc_venda,
            vl_liq_venda, tx_calc, desc_calc, vl_liq_calc, perda
        FROM vendas_calculos
        WHERE calc_id = %s AND calc_tipo = %s
    """

    # Montar lista de parâmetros
    params = [processamento_id, calc_tipo]

    if adquirente:
        join_sql += " AND adquirente = %s"
        params.append(adquirente)

    # Adiciona filtro de data se fornecido
    if data_inicio:
        join_sql += " AND data_venda >= %s"
        params.append(data_inicio)

    if data_fim:
        join_sql += " AND data_venda <= %s"
        params.append(data_fim)

    # Adiciona filtro para apenas vendas com perdas (perda > 0 ou perda_rr > 0)
    if apenas_com_perdas:
        join_sql += " AND (perda > 0 OR COALESCE(perda_rr, 0) > 0)"

    join_sql = _convert_placeholders(engine, join_sql)
    df_join = pd.read_sql(join_sql, engine, params=tuple(params))
    df_join = filtrar_valores_rede_depara(df_join)
    df_join = calcular_previsao_pagamento_rede(df_join)

    # Calcular estatísticas do mês
    total_transacoes = len(df_join)
    faturamento_bruto = df_join["vl_venda"].sum() if not df_join.empty else 0
    valor_liquido = df_join["vl_liq_venda"].sum() if not df_join.empty else 0

    # Calcular valores min, max e médio
    if not df_join.empty:
        valor_min = pd.to_numeric(df_join["vl_venda"], errors="coerce").min()
        valor_max = pd.to_numeric(df_join["vl_venda"], errors="coerce").max()
        valor_medio = (
            faturamento_bruto / total_transacoes if total_transacoes > 0 else 0
        )
    else:
        valor_min = valor_max = valor_medio = 0

    # Calcular período considerando filtros de data
    # Se data_inicio ou data_fim foram fornecidos, usar eles como período
    if data_inicio or data_fim:
        # Usar as datas fornecidas como filtro
        primeira_venda = data_inicio if data_inicio else None
        ultima_venda = data_fim if data_fim else None

        # Se apenas uma data foi fornecida, buscar a outra do banco
        if not primeira_venda or not ultima_venda:
            primeira_calc, ultima_calc = calcular_periodo_completo(
                engine, processamento_id, adquirente, data_inicio, data_fim
            )
            if not primeira_venda:
                primeira_venda = primeira_calc
            if not ultima_venda:
                ultima_venda = ultima_calc
    else:
        # Sem filtro de data, usar período completo do processamento
        primeira_venda, ultima_venda = calcular_periodo_completo(
            engine, processamento_id, adquirente, data_inicio, data_fim
        )

    print(
        f"[DEBUG] Período final usado: primeira={primeira_venda}, ultima={ultima_venda}"
    )

    # Calcular período em dias
    periodo_dias = 0
    if primeira_venda and ultima_venda:
        try:
            data_min = pd.to_datetime(primeira_venda)
            data_max = pd.to_datetime(ultima_venda)
            periodo_dias = (
                data_max - data_min
            ).days + 1  # +1 para incluir o dia inicial
            print(f"[DEBUG] Período em dias: {periodo_dias}")
        except Exception as e:
            print(f"[DEBUG] Erro ao calcular período em dias: {e}")
            periodo_dias = 0

    # Calcular materialidade corretamente: soma das perdas reais
    print("\n" + "=" * 80)
    print("[DEBUG] CÁLCULO DE MATERIALIDADE MENSAL")
    print(f"[DEBUG] Processamento ID: {processamento_id}")
    print(f"[DEBUG] Faturamento Bruto: {format_currency_br(faturamento_bruto)}")
    print("=" * 80)

    # 1. Perdas em vendas: diferença entre vl_liq_venda e vl_liq_calc
    total_perdas_vendas = 0
    if not df_join.empty and "vl_liq_calc" in df_join.columns:
        df_join["perda_real"] = df_join["vl_liq_venda"] - df_join["vl_liq_calc"]
        total_perdas_vendas = df_join["perda_real"].sum()

        # Estatísticas detalhadas das perdas
        perdas_positivas = df_join[df_join["perda_real"] > 0]["perda_real"].sum()
        perdas_negativas = df_join[df_join["perda_real"] < 0]["perda_real"].sum()
        qtd_com_perda = len(df_join[df_join["perda_real"] != 0])

        print(f"\n[VENDAS] Análise de Perdas:")
        print(f"  • Total de transações analisadas: {len(df_join):,}")
        print(f"  • Transações com divergência: {qtd_com_perda:,}")
        print(
            f"  • Faturamento Bruto (vl_venda): {format_currency_br(faturamento_bruto)}"
        )
        print(
            f"  • Faturamento Líquido Real (vl_liq_venda): {format_currency_br(valor_liquido)}"
        )
        print(
            f"  • Faturamento Líquido Calculado (vl_liq_calc): {format_currency_br(df_join['vl_liq_calc'].sum())}"
        )
        print(
            f"  • Perdas positivas (a mais cobrado): {format_currency_br(perdas_positivas)}"
        )
        print(
            f"  • Perdas negativas (a menos cobrado): {format_currency_br(perdas_negativas)}"
        )
        print(f"  ► TOTAL PERDAS EM VENDAS: {format_currency_br(total_perdas_vendas)}")

    # 2. Recebíveis processados
    total_recebiveis = 0
    try:
        sql_recebiveis = """
        SELECT 
            lancamento,
            COUNT(*) as quantidade,
            SUM(COALESCE(valor_recebivel, 0)) as total
        FROM recebiveis_processados 
        WHERE processamentoid = %s
        GROUP BY lancamento
        ORDER BY total DESC
        """
        sql_recebiveis = _convert_placeholders(engine, sql_recebiveis)
        df_recebiveis_mat = pd.read_sql(
            sql_recebiveis, engine, params=(processamento_id,)
        )

        if not df_recebiveis_mat.empty:
            total_recebiveis = df_recebiveis_mat["total"].sum()

            print(f"\n[RECEBÍVEIS] Análise Detalhada:")
            print(f"  • Total de tipos de lançamentos: {len(df_recebiveis_mat)}")

            for _, row in df_recebiveis_mat.iterrows():
                lancamento = row["lancamento"] if row["lancamento"] else "Sem descrição"
                quantidade = (
                    int(row["quantidade"]) if not pd.isna(row["quantidade"]) else 0
                )
                valor = row["total"] if not pd.isna(row["total"]) else 0
                print(
                    f"  • {lancamento}: {quantidade} lançamento(s) = {format_currency_br(valor)}"
                )

            print(f"  ► TOTAL RECEBÍVEIS: {format_currency_br(total_recebiveis)}")
        else:
            print(f"\n[RECEBÍVEIS] Nenhum recebível encontrado")
            total_recebiveis = 0

    except Exception as e:
        print(f"\n[RECEBÍVEIS] Erro ao calcular: {e}")
        total_recebiveis = 0

    # Total de inconformidades
    total_materialidade = total_perdas_vendas + total_recebiveis

    print("\n" + "-" * 80)
    print("[MATERIALIDADE TOTAL]")
    print(f"  • Perdas em Vendas: {format_currency_br(total_perdas_vendas)}")
    print(f"  • Recebíveis Processados: {format_currency_br(total_recebiveis)}")
    print(f"  ► TOTAL MATERIALIDADE: {format_currency_br(total_materialidade)}")
    print(
        f"  ► Percentual sobre Faturamento: {(total_materialidade / faturamento_bruto * 100) if faturamento_bruto > 0 else 0:.2f}%"
    )
    print("-" * 80)
    print(f"COMPOSIÇÃO DA MATERIALIDADE DE {format_currency_br(total_materialidade)}:")
    print(f"  - Perdas MDR (vendas): {format_currency_br(total_perdas_vendas)}")
    print(f"  - Recebíveis (taxas/descontos): {format_currency_br(total_recebiveis)}")
    print("=" * 80 + "\n")

    # Determinar período em português baseado nas transações reais
    meses_pt = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    if not mes_referencia:
        # Usar primeira_venda para determinar o mês de referência (período das transações)
        if primeira_venda:
            try:
                # primeira_venda pode ser string ou datetime
                if isinstance(primeira_venda, str):
                    data_ref = pd.to_datetime(primeira_venda)
                else:
                    data_ref = primeira_venda
                mes_nome = meses_pt.get(data_ref.month, data_ref.strftime("%B"))
                mes_referencia = f"{mes_nome}/{data_ref.year}"
                print(
                    f"[DEBUG] Mês de referência calculado das transações: {mes_referencia}"
                )
            except Exception as e:
                print(f"[DEBUG] Erro ao determinar mês de transações: {e}")
                # Fallback para data_inicio se fornecida
                if data_inicio:
                    mes_nome = meses_pt.get(
                        data_inicio.month, data_inicio.strftime("%B")
                    )
                    mes_referencia = f"{mes_nome}/{data_inicio.year}"
                else:
                    agora = datetime.now()
                    mes_nome = meses_pt.get(agora.month, agora.strftime("%B"))
                    mes_referencia = f"{mes_nome}/{agora.year}"
        elif data_inicio:
            mes_nome = meses_pt.get(data_inicio.month, data_inicio.strftime("%B"))
            mes_referencia = f"{mes_nome}/{data_inicio.year}"
        else:
            agora = datetime.now()
            mes_nome = meses_pt.get(agora.month, agora.strftime("%B"))
            mes_referencia = f"{mes_nome}/{agora.year}"

    periodo_analise = f"{data_inicio.strftime('%d/%m/%Y') if data_inicio else 'N/A'} a {data_fim.strftime('%d/%m/%Y') if data_fim else 'N/A'}"

    # Status da conciliação
    materialidade_percentual = (
        (total_materialidade / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
    )

    if materialidade_percentual < 1:
        status_conciliacao = "✓ Conforme"
        status_class = "status-ok"
    elif materialidade_percentual < 3:
        status_conciliacao = "⚠ Atenção"
        status_class = "status-alert"
    else:
        status_conciliacao = "✗ Crítico"
        status_class = "status-alert"

    # Gerar gráficos (apenas pizzas para relatório mensal)
    grafico_bandeiras_path = ""
    grafico_forma_pagamento_path = ""

    try:
        print("[DEBUG] Tentando gerar gráfico de bandeiras...")
        grafico_bandeiras_path = criar_grafico_vendas_por_bandeira(df_join)
    except Exception as e:
        print(f"[AVISO] Falha ao gerar gráfico de bandeiras: {e}")
        grafico_bandeiras_path = ""

    try:
        print("[DEBUG] Tentando gerar gráfico de forma de pagamento...")
        grafico_forma_pagamento_path = criar_grafico_vendas_por_forma_pagamento(df_join)
    except Exception as e:
        print(f"[AVISO] Falha ao gerar gráfico de forma de pagamento: {e}")
        grafico_forma_pagamento_path = ""

    # Gerar tabelas HTML
    estatisticas_taxas = calcular_estatisticas_taxas(df_join)

    # Buscar recebíveis
    df_recebiveis = calcular_sumario_recebiveis(
        engine, processamento_id, data_inicio, data_fim
    )

    # Preparar DataFrames para calcular perdas (adaptar estrutura esperada pela função)
    df_processadas_adapted = df_join.copy()
    df_processadas_adapted["id"] = df_processadas_adapted["venda_id"]

    df_calculos_adapted = df_join[["venda_id", "perda"]].copy()
    df_calculos_adapted["id_venda"] = df_calculos_adapted["venda_id"]

    # Adicionar coluna perda_rr se existir no df_join
    if "Taxas_RR" in df_join.columns and "Valor_RR" in df_join.columns:
        # Calcular perda_rr se não existir
        if "perda_rr" not in df_join.columns:
            df_join["perda_rr"] = df_join["Valor_RR"].fillna(0)
        df_calculos_adapted["perda_rr"] = df_join["perda_rr"].fillna(0)
    else:
        df_calculos_adapted["perda_rr"] = 0

    # NOVA: Calcular tabela consolidada mensal
    df_tabela_consolidada = calcular_tabela_consolidada_mensal(
        engine,
        processamento_id,
        df_processadas_adapted,
        df_calculos_adapted,
        data_inicio,
        data_fim,
    )

    # Calcular perdas por semestre - COM faturamento no relatório mensal
    try:
        df_perdas = calcular_perdas_por_semestre(
            df_processadas_adapted, df_calculos_adapted, incluir_faturamento=True
        )
    except Exception as e:
        print(f"[DEBUG] Erro ao calcular perdas: {e}")
        # Criar DataFrame vazio se houver erro
        df_perdas = pd.DataFrame()

    # Calcular min/max taxas
    df_min_max_taxas = calcular_min_max_taxas_agrupado(df_join)

    # Calcular contagem de taxas
    df_contagem_taxas = calcular_contagem_taxas_agrupado(df_join)

    # Buscar dados bancários
    df_dados_bancarios = obter_dados_bancarios_distintos(
        engine, processamento_id, data_inicio, data_fim
    )

    # Gerar evidências de transações (Top 3)
    evidencias = obter_evidencias_transacoes(
        engine, processamento_id, calc_tipo, data_inicio, data_fim
    )

    # Gerar tabelas HTML para cada evidência (4 tipos)
    tabela_evidencias_maiores_valores_html = (
        gerar_tabela_html(
            evidencias["maiores_valores"], "Top 3 Maiores Valores de Transação"
        )
        if not evidencias["maiores_valores"].empty
        else ""
    )

    tabela_evidencias_menores_valores_html = (
        gerar_tabela_html(
            evidencias["menores_valores"], "Top 3 Menores Valores de Transação"
        )
        if not evidencias["menores_valores"].empty
        else ""
    )

    tabela_evidencias_maiores_taxas_html = (
        gerar_tabela_html(evidencias["maiores_taxas"], "Top 3 Maiores Taxas Aplicadas")
        if not evidencias["maiores_taxas"].empty
        else ""
    )

    tabela_evidencias_menores_taxas_html = (
        gerar_tabela_html(evidencias["menores_taxas"], "Top 3 Menores Taxas Aplicadas")
        if not evidencias["menores_taxas"].empty
        else ""
    )

    # Garantir que primeira_venda e ultima_venda sejam datetime
    primeira_venda_str = ""
    if primeira_venda:
        if isinstance(primeira_venda, str):
            try:
                primeira_venda_str = pd.to_datetime(primeira_venda).strftime("%d/%m/%Y")
            except:
                primeira_venda_str = primeira_venda
        else:
            primeira_venda_str = primeira_venda.strftime("%d/%m/%Y")

    ultima_venda_str = ""
    if ultima_venda:
        if isinstance(ultima_venda, str):
            try:
                ultima_venda_str = pd.to_datetime(ultima_venda).strftime("%d/%m/%Y")
            except:
                ultima_venda_str = ultima_venda
        else:
            ultima_venda_str = ultima_venda.strftime("%d/%m/%Y")

    tabela_sumario_html = criar_tabela_sumario(
        {
            "quantidade": total_transacoes,
            "valor_total": faturamento_bruto,
            "valor_medio": valor_medio,
            "valor_min": valor_min,
            "valor_max": valor_max,
            "valor_liquido": valor_liquido,
            "primeira_venda": primeira_venda_str,
            "ultima_venda": ultima_venda_str,
            "periodo_dias": periodo_dias,
        },
        metadados,
        estatisticas_taxas,
        ecs_distintos,
        adquirentes_distintos,
    )

    tabela_perdas_mes_html = (
        gerar_tabela_html(df_perdas, "Análise de Perdas Estimadas")
        if not df_perdas.empty
        else ""
    )

    tabela_min_max_taxas_html = (
        gerar_tabela_html(df_min_max_taxas, "Taxas Mínimas e Máximas por Bandeira")
        if not df_min_max_taxas.empty
        else ""
    )

    tabela_contagem_taxas_html = (
        gerar_tabela_html(df_contagem_taxas, "Contagem de Transações por Bandeira")
        if not df_contagem_taxas.empty
        else ""
    )

    tabela_sumario_recebiveis_html = (
        gerar_tabela_html(df_recebiveis, "Resumo de Recebíveis")
        if not df_recebiveis.empty
        else ""
    )

    tabela_dados_bancarios_html = (
        gerar_tabela_html(df_dados_bancarios, "Dados Bancários")
        if not df_dados_bancarios.empty
        else ""
    )

    # Tabelas filtradas (opcionais)
    tabela_vendas_filtradas_html = ""
    tabela_recebiveis_filtrados_html = ""
    df_vendas_filtradas = pd.DataFrame()  # Inicializar vazio
    df_recebiveis_filtrados = pd.DataFrame()  # Inicializar vazio

    if incluir_filtradas:
        df_vendas_filtradas = gerar_demonstrativo_vendas_filtradas(
            engine, processamento_id, data_inicio, data_fim
        )
        if not df_vendas_filtradas.empty:
            tabela_vendas_filtradas_html = gerar_tabela_html(
                df_vendas_filtradas, "Demonstrativo de Outras Vendas"
            )

    if incluir_recebiveis_filtrados:
        df_recebiveis_filtrados = gerar_demonstrativo_recebiveis_filtrados(
            engine, processamento_id, data_inicio, data_fim
        )
        if not df_recebiveis_filtrados.empty:
            tabela_recebiveis_filtrados_html = gerar_tabela_html(
                df_recebiveis_filtrados, "Demonstrativo de Outros Recebíveis"
            )  # Identificar divergências
    divergencias_encontradas = []
    if not df_perdas.empty and "perda_total" in df_perdas.columns:
        perdas_valores = df_perdas["perda_total"].dropna()
        if len(perdas_valores) > 0:
            divergencias_encontradas.append(
                {
                    "tipo": "Taxas MDR",
                    "descricao": "Divergências entre taxas cadastradas e aplicadas",
                    "quantidade": len(perdas_valores),
                    "impacto": format_currency_br(perdas_valores.sum()),
                }
            )

    # Recomendações
    recomendacoes = []
    if materialidade_percentual > 2:
        recomendacoes.append(
            {
                "prioridade": "🔴 Alta",
                "descricao": "Revisar taxas aplicadas pela adquirente e solicitar ajustes contratuais",
            }
        )
    if materialidade_percentual > 1:
        recomendacoes.append(
            {
                "prioridade": "🟡 Média",
                "descricao": "Monitorar transações com taxas variáveis e solicitar padronização",
            }
        )

    # Preparar contexto para template
    context = {
        "cover_image_path": os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "capa_relatorio.jpg"
        ),
        "header_image_path": os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "cabecalho_financial.png",
        ),
        "mes_referencia": mes_referencia,
        "periodo_analise": periodo_analise,
        "tabela_sumario_html": tabela_sumario_html,
        "tabela_consolidada_html": (
            gerar_tabela_html(df_tabela_consolidada, "Análise Consolidada")
            if not df_tabela_consolidada.empty
            else ""
        ),
        "tabela_contagem_taxas_html": tabela_contagem_taxas_html,
        "tabela_sumario_recebiveis_html": tabela_sumario_recebiveis_html,
        "tabela_dados_bancarios_html": tabela_dados_bancarios_html,
        "tabela_evidencias_maiores_valores_html": tabela_evidencias_maiores_valores_html,
        "tabela_evidencias_menores_valores_html": tabela_evidencias_menores_valores_html,
        "tabela_evidencias_maiores_taxas_html": tabela_evidencias_maiores_taxas_html,
        "tabela_evidencias_menores_taxas_html": tabela_evidencias_menores_taxas_html,
        "tabela_recebiveis_filtrados_html": tabela_recebiveis_filtrados_html,
        "tabela_vendas_filtradas_html": tabela_vendas_filtradas_html,
        "grafico_bandeiras_path": (
            grafico_bandeiras_path if grafico_bandeiras_path else ""
        ),
        "grafico_forma_pagamento_path": (
            grafico_forma_pagamento_path if grafico_forma_pagamento_path else ""
        ),
        "materialidade_valor": format_currency_br(total_materialidade),
        "materialidade_percentual": f"{materialidade_percentual:.2f}%",
        "data_processamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "disclaimer_text": "Este relatório é baseado exclusivamente nos dados fornecidos pela adquirente e tem caráter informativo. Recomenda-se análise detalhada dos valores apresentados.",
    }

    # Renderizar template
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "relatorios"
    )
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("template_relatorio_mensal.html")
    html_content = template.render(**context)

    # Salvar HTML
    dir_path = criar_diretorio_relatorios()

    # Sanitizar nome do cliente removendo caracteres inválidos para Windows
    cliente_nome = metadados.get("cliente_nome", "cliente")
    # Remover caracteres problemáticos: < > : " / \ | ? * ( ) . ,
    caracteres_invalidos = [
        "<",
        ">",
        ":",
        '"',
        "/",
        "\\",
        "|",
        "?",
        "*",
        "(",
        ")",
        ".",
        ",",
    ]
    for char in caracteres_invalidos:
        cliente_nome = cliente_nome.replace(char, "")
    # Substituir espaços por underscores e limitar tamanho
    cliente_nome = cliente_nome.replace(" ", "_")[:50]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitizar mês de referência
    mes_ref_safe = (
        mes_referencia.replace("/", "_").replace(" ", "_")
        if mes_referencia
        else "atual"
    )

    html_filename = f"relatorio_mensal_{cliente_nome}_{mes_ref_safe}_{timestamp}.html"
    html_path = os.path.join(dir_path, html_filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[DEBUG] Relatório mensal salvo em: {html_path}")
    print(f"[DEBUG] Tempo total: {time.time() - inicio_total:.2f}s")

    # Buscar vendas completas de vendas_calculos para Excel
    inicio_vendas_completas = time.time()
    sql_vendas_completas = """
        SELECT 
            vc.id,
            vc.id_venda,
            vc.calc_id,
            vc.calc_tipo,
            vc.forma_pagamento,
            vc.vl_venda,
            vc.tx_venda,
            vc.desc_venda,
            vc.vl_liq_venda,
            vc.tx_calc,
            vc.desc_calc,
            vc.vl_liq_calc,
            vc.perda,
            vc.perda_rr,
            vc.data_venda AS Data_da_venda,
            vc.bandeira AS Bandeira,
            vc.arquivo_origem
        FROM vendas_calculos vc
        WHERE vc.calc_id = %s AND vc.calc_tipo = %s
    """

    params_completas = [processamento_id, calc_tipo]

    if adquirente:
        sql_vendas_completas += " AND vc.adquirente = %s"
        params_completas.append(adquirente)

    if data_inicio:
        sql_vendas_completas += " AND vc.data_venda >= %s"
        params_completas.append(data_inicio)

    if data_fim:
        sql_vendas_completas += " AND vc.data_venda <= %s"
        params_completas.append(data_fim)

    if apenas_com_perdas:
        sql_vendas_completas += " AND (vc.perda > 0 OR COALESCE(vc.perda_rr, 0) > 0)"

    sql_vendas_completas += " ORDER BY vc.data_venda, vc.bandeira"
    sql_vendas_completas = _convert_placeholders(engine, sql_vendas_completas)

    df_vendas_completas_mensal = read_sql_safe(
        sql_vendas_completas, engine, params=tuple(params_completas)
    )
    log_tempo_execucao("buscar_vendas_completas_excel_mensal", inicio_vendas_completas)
    print(
        f"[DEBUG] Vendas completas carregadas: {len(df_vendas_completas_mensal)} registros"
    )

    # Gerar Excel com todas as abas (DataFrames do relatório mensal)
    inicio_excel = time.time()
    dataframes_excel = {
        "1. Vendas Completas": df_vendas_completas_mensal,
        "2. Resumo Geral": (
            df_join[
                [
                    "Data_da_venda",
                    "Bandeira",
                    "Forma_de_pagamento",
                    "vl_venda",
                    "tx_venda",
                    "perda",
                ]
            ]
            if not df_join.empty
            else pd.DataFrame()
        ),
        "3. Tabela Consolidada": df_tabela_consolidada,
        "4. Perdas Estimadas": df_perdas,
        "5. Taxas Min-Max": df_min_max_taxas,
        "6. Contagem Transações": df_contagem_taxas,
        "7. Sumário Recebíveis": df_recebiveis,
        "8. Dados Bancários": df_dados_bancarios,
        "9. Top 3 Maiores Valores": evidencias.get("maiores_valores", pd.DataFrame()),
        "10. Top 3 Menores Valores": evidencias.get("menores_valores", pd.DataFrame()),
        "11. Top 3 Maiores Taxas": evidencias.get("maiores_taxas", pd.DataFrame()),
        "12. Top 3 Menores Taxas": evidencias.get("menores_taxas", pd.DataFrame()),
    }

    # Adicionar vendas filtradas se solicitado
    if (
        incluir_filtradas
        and "df_vendas_filtradas" in locals()
        and not df_vendas_filtradas.empty
    ):
        dataframes_excel["13. Vendas Filtradas"] = df_vendas_filtradas

    # Adicionar recebíveis filtrados se houver dados
    if (
        incluir_recebiveis_filtrados
        and "df_recebiveis_filtrados" in locals()
        and not df_recebiveis_filtrados.empty
    ):
        dataframes_excel["14. Recebíveis Filtrados"] = df_recebiveis_filtrados

    excel_filename = f"relatorio_mensal_{cliente_nome}_{mes_ref_safe}_{timestamp}"
    excel_path = gerar_excel_relatorio(dataframes_excel, excel_filename)
    log_tempo_execucao("gerar_excel_relatorio_mensal", inicio_excel)

    if excel_path:
        print(f"[DEBUG] ✓ Excel mensal gerado: {excel_path}")

    # Gerar relatório sintético automaticamente
    print(f"[DEBUG] Gerando relatório sintético mensal...")
    try:
        sintetico_path = gerar_relatorio_sintetico_html(
            metadados=metadados,
            total_transacoes=total_transacoes,
            faturamento_bruto=faturamento_bruto,
            valor_liquido=valor_liquido,
            ticket_medio=valor_medio,
            taxa_media=df_join["tx_venda"].mean() if not df_join.empty else 0,
            total_divergencias=(
                df_perdas["perda_total"].sum()
                if not df_perdas.empty and "perda_total" in df_perdas.columns
                else 0
            ),
            bandeiras=(
                df_join.groupby("Bandeira")
                .agg({"Bandeira": "count", "vl_venda": "sum"})
                .rename(columns={"Bandeira": "qtd", "vl_venda": "valor"})
                .reset_index()
                if not df_join.empty
                else pd.DataFrame()
            ),
            top_valores=(
                evidencias["maiores_valores"].head(3)
                if not evidencias["maiores_valores"].empty
                else pd.DataFrame()
            ),
            primeira_venda=primeira_venda,
            ultima_venda=ultima_venda,
            periodo_dias=periodo_dias,
            adquirente=metadados.get("adquirente", "Não identificado"),
            processamento_id=processamento_id,
        )
        print(f"[DEBUG] ✓ Relatório sintético mensal gerado: {sintetico_path}")
    except Exception as e:
        print(f"[DEBUG] ⚠️ Erro ao gerar relatório sintético mensal: {e}")
        sintetico_path = None

    return html_path, None, sintetico_path


def criar_interface_relatorio(engine: Engine) -> Any:
    pn.extension("tabulator")
    titulo = pn.pane.Markdown("### Geração de Relatórios HTML")

    # Widget de seleção de tipo de relatório
    tipo_relatorio_select = pn.widgets.Select(
        name="Tipo de Relatório",
        options={
            "Conciliação Retroativa (Completo)": "retroativo",
            "Conciliação Mensal": "mensal",
        },
        value="retroativo",
        width=300,
    )

    # Widget de seleção de adquirente
    adquirente_select = pn.widgets.Select(
        name="Filtrar por Adquirente", options=[], width=300
    )

    # Widget para mostrar o período de vendas
    periodo_info = pn.pane.Markdown(
        "",
        styles={
            "background-color": "#e3f2fd",
            "padding": "10px",
            "border-radius": "5px",
            "margin": "10px 0",
        },
        visible=False,
    )

    # Widgets de filtro de data
    data_inicial_input = pn.widgets.DatePicker(
        name="Data Inicial (opcional)", width=200
    )

    data_final_input = pn.widgets.DatePicker(name="Data Final (opcional)", width=200)

    # Checkbox para incluir vendas filtradas (apenas para retroativo)
    incluir_filtradas_check = pn.widgets.Checkbox(
        name="Incluir Demonstrativo de Vendas Filtradas", value=False, width=300
    )

    # Checkbox para incluir recebíveis filtrados (apenas para retroativo)
    incluir_recebiveis_filtrados_check = pn.widgets.Checkbox(
        name="Incluir Demonstrativo de Recebíveis Filtrados", value=False, width=300
    )

    # Checkbox para filtrar apenas vendas com perdas
    apenas_com_perdas_check = pn.widgets.Checkbox(
        name="Apenas vendas com perdas (perda > 0 ou perda_rr > 0)",
        value=False,
        width=350,
    )

    def get_adquirentes(processamento_id):
        if not processamento_id:
            return []
        return obter_adquirentes_distintos_processamento(engine, processamento_id)

    with engine.connect() as conn:
        df_calcs = pd.read_sql(
            "SELECT DISTINCT calc_id, calc_tipo FROM vendas_calculos ORDER BY calc_id DESC, calc_tipo",
            conn,
        )

    tipo_map = {"log_mensal": "Taxa Lógica Mensal", "cad": "Taxa Cadastrada"}

    def tipo_amigavel(tipo):
        return tipo_map.get(str(tipo).lower(), str(tipo))

    calc_options = (
        [
            (
                f"{row.calc_id} | {tipo_amigavel(row.calc_tipo)}",
                (row.calc_id, row.calc_tipo),
            )
            for _, row in df_calcs.iterrows()
        ]
        if not df_calcs.empty
        else [("Nenhum cálculo", (None, None))]
    )

    calc_select = pn.widgets.Select(
        name="Selecione o Processamento/Cálculo", options=dict(calc_options), width=400
    )

    # Atualizar opções de adquirente ao trocar processamento
    def on_calc_change(event):
        print(f"\n[DEBUG SEGUNDA FUNÇÃO] === on_calc_change AUTOMÁTICO ===")
        calc_id_tipo = calc_select.value
        print(f"[DEBUG SEGUNDA FUNÇÃO] calc_select.value = {calc_id_tipo}")

        if not calc_id_tipo or not all(calc_id_tipo):
            print(
                "[DEBUG SEGUNDA FUNÇÃO] Limpando adquirente_select - sem cálculo válido"
            )
            adquirente_select.options = ["Todos"]
            adquirente_select.value = "Todos"
            adquirente_select.disabled = False
            return

        processamento_id, _ = calc_id_tipo
        print(f"[DEBUG SEGUNDA FUNÇÃO] Processamento ID: {processamento_id}")

        try:
            # ⏳ Desabilitar selectbox durante carregamento
            adquirente_select.disabled = True
            adquirente_select.name = "Carregando adquirentes..."

            print("[DEBUG SEGUNDA FUNÇÃO] Chamando get_adquirentes...")
            adquirentes = get_adquirentes(processamento_id)
            print(f"[DEBUG SEGUNDA FUNÇÃO] Adquirentes encontrados: {adquirentes}")

            # Buscar período de vendas
            try:
                _, periodo = obter_adquirentes_e_periodo_processamento(
                    engine, processamento_id
                )

                if periodo and "data_min" in periodo and "data_max" in periodo:
                    data_min_str = periodo["data_min"].strftime("%d/%m/%Y")
                    data_max_str = periodo["data_max"].strftime("%d/%m/%Y")
                    periodo_info.object = (
                        f"📅 **Período de vendas:** {data_min_str} até {data_max_str}"
                    )
                    periodo_info.visible = True
                    print(
                        f"[DEBUG SEGUNDA FUNÇÃO] Período: {data_min_str} até {data_max_str}"
                    )
                else:
                    periodo_info.visible = False
                    print("[DEBUG SEGUNDA FUNÇÃO] Nenhum período encontrado")
            except Exception as e:
                print(f"[DEBUG SEGUNDA FUNÇÃO] Erro ao buscar período: {str(e)}")
                periodo_info.visible = False

            if adquirentes:
                new_options = ["Todos"] + adquirentes
                adquirente_select.options = new_options
                adquirente_select.value = "Todos"
                print(
                    f"[DEBUG SEGUNDA FUNÇÃO] ✅ Selectbox atualizado com {len(adquirentes)} adquirentes: {new_options}"
                )
            else:
                adquirente_select.options = ["Todos"]
                adquirente_select.value = "Todos"
                print(
                    "[DEBUG SEGUNDA FUNÇÃO] ⚠️ Nenhum adquirente encontrado - usando apenas 'Todos'"
                )
        except Exception as e:
            print(f"[DEBUG SEGUNDA FUNÇÃO] ❌ Erro ao carregar adquirentes: {str(e)}")
            adquirente_select.options = ["Todos"]
            adquirente_select.value = "Todos"
        finally:
            # ✅ Reabilitar selectbox após carregamento
            adquirente_select.disabled = False
            adquirente_select.name = "Filtrar por Adquirente"

        print(f"[DEBUG SEGUNDA FUNÇÃO] === FIM on_calc_change AUTOMÁTICO ===\n")

    calc_select.param.watch(on_calc_change, "value")

    # Carregar adquirentes automaticamente na inicialização da segunda função
    print(f"\n[DEBUG SEGUNDA FUNÇÃO] === INICIALIZANDO INTERFACE ===")
    print(f"[DEBUG SEGUNDA FUNÇÃO] calc_select criado com {len(calc_options)} opções")

    # Se há cálculos disponíveis, carregar adquirentes do primeiro
    if calc_options and calc_options[0][1] != (None, None):
        print(f"[DEBUG SEGUNDA FUNÇÃO] Carregando adquirentes iniciais...")
        on_calc_change(None)
    else:
        print(
            f"[DEBUG SEGUNDA FUNÇÃO] Nenhum cálculo disponível para carregar adquirentes"
        )
        adquirente_select.options = ["Todos"]
        adquirente_select.value = "Todos"

    print(f"[DEBUG SEGUNDA FUNÇÃO] === FIM INICIALIZAÇÃO ===\n")

    btn_gerar = pn.widgets.Button(
        name="🔍 Gerar Relatório HTML", button_type="primary", width=200
    )

    status = pn.pane.Markdown("")
    btn_abrir_relatorio = pn.widgets.Button(
        name="📂 Abrir HTML", button_type="success", width=200, visible=False
    )
    btn_baixar_excel = pn.widgets.Button(
        name="📊 Baixar Excel", button_type="success", width=200, visible=False
    )
    btn_abrir_sintetico = pn.widgets.Button(
        name="📄 Abrir Sintético", button_type="primary", width=200, visible=False
    )

    def on_gerar_relatorio(event):
        calc_id_tipo = calc_select.value
        if not calc_id_tipo or not all(calc_id_tipo):
            status.object = "⚠️ Por favor, selecione um cálculo válido."
            return

        processamento_id, calc_tipo = calc_id_tipo

        # Capturar tipo de relatório
        tipo_relatorio = tipo_relatorio_select.value

        # Capturar o valor do adquirente selecionado
        adquirente_selecionado = (
            adquirente_select.value if adquirente_select.value != "Todos" else None
        )

        # Capturar datas selecionadas e converter para datetime se necessário
        data_inicio = data_inicial_input.value
        data_fim = data_final_input.value

        # Converter de date para datetime se necessário
        if data_inicio:
            from datetime import datetime

            if not isinstance(data_inicio, datetime):
                data_inicio = datetime.combine(data_inicio, datetime.min.time())
        if data_fim:
            from datetime import datetime

            if not isinstance(data_fim, datetime):
                data_fim = datetime.combine(data_fim, datetime.max.time())

        status.object = (
            f"⏳ Gerando relatório {tipo_relatorio_select.name}... Por favor, aguarde."
        )
        btn_abrir_relatorio.visible = False
        btn_baixar_excel.visible = False
        btn_abrir_sintetico.visible = False

        try:
            if tipo_relatorio == "mensal":
                # Gerar relatório mensal
                html_path, _, sintetico_path = gerar_relatorio_mensal_html(
                    engine,
                    processamento_id,
                    calc_tipo=calc_tipo,
                    adquirente=adquirente_selecionado,
                    incluir_filtradas=incluir_filtradas_check.value,
                    incluir_recebiveis_filtrados=incluir_recebiveis_filtrados_check.value,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    apenas_com_perdas=apenas_com_perdas_check.value,
                )
                tipo_msg = "Mensal"
            else:
                # Gerar relatório retroativo (padrão)
                html_path, _, sintetico_path = gerar_relatorio_html(
                    engine,
                    processamento_id,
                    calc_tipo=calc_tipo,
                    return_base=False,
                    adquirente=adquirente_selecionado,
                    incluir_filtradas=incluir_filtradas_check.value,
                    incluir_recebiveis_filtrados=incluir_recebiveis_filtrados_check.value,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    apenas_com_perdas=apenas_com_perdas_check.value,
                )
                tipo_msg = "Retroativo"

            btn_abrir_relatorio.visible = True
            btn_abrir_relatorio.html_path = html_path

            # Verificar se o Excel foi gerado e armazenar o caminho
            excel_path = html_path.replace(".html", ".xlsx")
            if os.path.exists(excel_path):
                btn_baixar_excel.visible = True
                btn_baixar_excel.excel_path = excel_path

            # Verificar se o relatório sintético foi gerado
            if sintetico_path and os.path.exists(sintetico_path):
                btn_abrir_sintetico.visible = True
                btn_abrir_sintetico.sintetico_path = sintetico_path

            # Mostrar no status qual adquirente foi usado no filtro
            filtro_info = (
                f" (Filtrado por: {adquirente_select.value})"
                if adquirente_selecionado
                else " (Todos os adquirentes)"
            )

            # Adicionar info de período se filtrado
            if data_inicio or data_fim:
                periodo_info = f" | Período: {data_inicio.strftime('%d/%m/%Y') if data_inicio else 'Início'} até {data_fim.strftime('%d/%m/%Y') if data_fim else 'Fim'}"
                filtro_info += periodo_info

            status.object = f"✅ Relatório {tipo_msg} gerado com sucesso!{filtro_info} <br> **Arquivo salvo em:** `{html_path}`"
        except Exception as e:
            status.object = f"❌ Erro ao gerar relatório: {e}"
            import traceback

            traceback.print_exc()
            btn_abrir_relatorio.visible = False
            btn_baixar_excel.visible = False
            btn_abrir_sintetico.visible = False

    def on_abrir_relatorio(event):
        if hasattr(btn_abrir_relatorio, "html_path") and btn_abrir_relatorio.html_path:
            os.startfile(btn_abrir_relatorio.html_path)

    def on_baixar_excel(event):
        if hasattr(btn_baixar_excel, "excel_path") and btn_baixar_excel.excel_path:
            os.startfile(btn_baixar_excel.excel_path)

    def on_abrir_sintetico(event):
        if (
            hasattr(btn_abrir_sintetico, "sintetico_path")
            and btn_abrir_sintetico.sintetico_path
        ):
            os.startfile(btn_abrir_sintetico.sintetico_path)

    btn_gerar.on_click(on_gerar_relatorio)
    btn_abrir_relatorio.on_click(on_abrir_relatorio)
    btn_baixar_excel.on_click(on_baixar_excel)
    btn_abrir_sintetico.on_click(on_abrir_sintetico)

    return pn.Column(
        titulo,
        pn.layout.Divider(),
        pn.Row(tipo_relatorio_select),
        pn.Row(calc_select, adquirente_select),
        periodo_info,
        pn.Row(data_inicial_input, data_final_input),
        pn.Row(incluir_filtradas_check),
        pn.Row(incluir_recebiveis_filtrados_check),
        pn.Row(apenas_com_perdas_check),
        pn.Row(btn_gerar),
        status,
        pn.layout.Divider(),
        pn.Row(btn_abrir_relatorio, btn_abrir_sintetico, btn_baixar_excel),
        sizing_mode="stretch_width",
    )
