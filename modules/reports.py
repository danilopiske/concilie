import os
import re
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import panel as pn
import plotly.express as px
import polars as pl
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.engine import Engine

from conf.funcoesbd import (
    fetch_all,
    fetch_one,
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


def _get_base_id(proc_id: str) -> str:
    """
    Extrai o ID base de um processamento a partir do calc_id (ex: 1234567890_anual -> 1234567890).
    Se não houver underscore, retorna o próprio ID.
    Utilizada para compatibilidade com tabelas que usam o ID curto (controle_processamentos, etc).
    """
    if not proc_id or not isinstance(proc_id, str):
        return proc_id
    
    # Se contém underscore, pode ser calc_id (ex: 1051121873_anual_...)
    # ou pode ser um ID de processamento composto (ex: 1051121873_0001 - ...)
    # Vamos retornar o prefixo numérico ou o primeiro componente
    parts = proc_id.split("_")
    if len(parts) > 1:
        # Se o primeiro pedaço for puramente numérico e longo (ex: timestamp 10 dígitos),
        # é um forte candidato a ID base.
        if parts[0].isdigit() and len(parts[0]) >= 9:
            return parts[0]
        return parts[0]
        
    return proc_id


def to_base64_url(path: str) -> str:
    """
    Converte um caminho de arquivo para uma Data URL Base64 se for imagem,
    para que possa ser incorporada diretamente no HTML.
    """
    if not path or not os.path.exists(path):
        return ""

    ext = os.path.splitext(path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg", ".gif"]:
        try:
            import base64
            import mimetypes

            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                mime_type = "image/png" if ext == ".png" else "image/jpeg"

            with open(path, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            print(f"[DEBUG] Erro ao converter para base64: {e}")

    # Fallback para file scheme
    return "file:///" + os.path.abspath(path).replace("\\", "/")


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


def filtrar_valores_rede_depara(df: Any) -> Any:
    """
    Aplica filtros específicos para valores de venda da REDE usando Polars (muito mais rápido).
    """
    if df is None:
        return df
    
    is_pandas = isinstance(df, pd.DataFrame)
    is_lazy = isinstance(df, pl.LazyFrame)
    
    # Se for pandas, converte para lazy
    if is_pandas:
        lf = pl.from_pandas(df).lazy()
    elif is_lazy:
        lf = df
    else:
        lf = df.lazy()
    
    # Identificar colunas
    cols = lf.collect_schema().names()
    valor_col = next((c for c in ["vl_venda", "Valor_da_venda", "valor_da_venda"] if c in cols), None)
    adq_col = next((c for c in ["adquirente", "Adquirente", "Bandeira", "bandeira"] if c in cols), None)

    if not valor_col:
        return df

    # Filtros base - Garantir que valor_col seja numérico para comparação
    lf = lf.with_columns(pl.col(valor_col).cast(pl.Float64, strict=False))
    
    lf = lf.filter(
        pl.col(valor_col).is_not_null(),
        pl.col(valor_col) != 0
    )

    # Filtro REDE (negativos e outliers)
    if adq_col:
        mask_rede = pl.col(adq_col).cast(pl.Utf8).str.to_uppercase().str.contains("REDE")
        
        # Remover negativos apenas para REDE
        lf = lf.filter(
            ~(mask_rede & (pl.col(valor_col) < 0))
        )
    
    # Retorno: Se entrou preguiçoso, sai preguiçoso. Se era pandas, volta pandas.
    if is_lazy:
        return lf
    
    res = lf.collect() if isinstance(lf, pl.LazyFrame) else lf
    return res.to_pandas() if is_pandas and hasattr(res, "to_pandas") else res


def calcular_previsao_pagamento_rede(df: Any) -> Any:
    """
    Calcula a previsão de pagamento para REDE usando Polars.
    Regra: Data_da_venda + 31 dias.
    """
    if df is None:
        return df

    is_pandas = isinstance(df, pd.DataFrame)
    is_lazy = isinstance(df, pl.LazyFrame)
    
    if is_pandas:
        lf = pl.from_pandas(df).lazy()
    elif is_lazy:
        lf = df
    else:
        lf = df.lazy()
    
    cols = lf.collect_schema().names()
    data_col = next((c for c in ["Data_da_venda", "data_venda"] if c in cols), None)
    adq_col = next((c for c in ["adquirente", "Adquirente", "Bandeira", "bandeira"] if c in cols), None)
    prev_col = "Previsão_de_pagamento"

    if not data_col or not adq_col:
        return df

    # Adicionar coluna se não existir
    if prev_col not in cols:
        lf = lf.with_columns(pl.lit(None).cast(pl.Date).alias(prev_col))

    # Regra REDE: +31 dias
    lf = lf.with_columns(
        pl.when(pl.col(adq_col).cast(pl.Utf8).str.to_uppercase().str.contains("REDE"))
        .then(pl.col(data_col).cast(pl.Date) + pl.duration(days=31))
        .otherwise(pl.col(prev_col))
        .alias(prev_col)
    )

    if is_lazy:
        return lf
        
    res = lf.collect() if isinstance(lf, pl.LazyFrame) else lf
    return res.to_pandas() if is_pandas and hasattr(res, "to_pandas") else res


def log_tempo_execucao(funcao_nome: str, inicio: float) -> None:
    """Log do tempo de execução de uma função"""
    tempo_decorrido = time.time() - inicio
    print(f"[DEBUG] {funcao_nome}: {tempo_decorrido:.3f}s")


def debug_log(msg):
    """Log de depuração global para geração de relatórios"""
    try:
        log_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "report_debug.log")
        with open(log_file, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{ts}] {msg}\n")
    except:
        pass
    print(f"[DEBUG_REPORT] {msg}")

def debug_to_file(msg: str):
    try:
        print(f"[DIAG] {msg}", flush=True)
    except:
        pass


def read_sql_polars(
    sql: str,
    engine: Engine,
    params: tuple = None,
) -> pl.DataFrame:
    """
    Lê dados do SQL usando PyArrow backend (Pandas 2.x) para conversão quase zero-copy
    ao Polars — elimina o triple-copy anterior (chunks → concat → from_pandas numpy).

    Fallback automático para chunked Pandas caso o backend Arrow falhe.
    """
    # Converter %s → :p1, :p2... para SQLAlchemy text()
    params_dict = {}
    if params:
        new_sql = sql
        for i, val in enumerate(params):
            new_sql = new_sql.replace("%s", f":p{i+1}", 1)
            params_dict[f"p{i+1}"] = val
        sql = new_sql
        params = params_dict
        debug_to_file(f"read_sql_polars params: {params_dict}")

    debug_to_file(f"read_sql_polars query prefix: {sql[:150]}")

    # Tentativa 1: PyArrow backend — single read, near zero-copy para Polars
    try:
        with engine.connect().execution_options(stream_results=True) as conn:
            print("[DEBUG_READ_SQL] Lendo com PyArrow backend (zero-copy)...")
            df_pd = pd.read_sql(text(sql), conn, params=params, dtype_backend="pyarrow")
            debug_to_file(f"read_sql_polars success: {len(df_pd)} rows")
            return pl.from_pandas(df_pd)
    except Exception as e:
        debug_to_file(f"read_sql_polars ERROR: {e}")
        print(f"[DEBUG_READ_SQL] PyArrow backend falhou ({e}), usando chunked fallback...")

    # Fallback: chunked Pandas (método anterior)
    try:
        chunks = []
        chunk_size = 100_000
        with engine.connect() as conn:
            print(f"[DEBUG_READ_SQL] Fallback: lendo em chunks de {chunk_size}...")
            for i, chunk in enumerate(pd.read_sql(text(sql), conn, params=params, chunksize=chunk_size)):
                chunks.append(chunk)
                if (i + 1) % 5 == 0:
                    print(f"[DEBUG_READ_SQL] {(i + 1) * chunk_size} registros no buffer...")
        if not chunks:
            return pl.DataFrame()
        print(f"[DEBUG_READ_SQL] Concatenando {len(chunks)} chunks e convertendo para Polars...")
        return pl.from_pandas(pd.concat(chunks, ignore_index=True))
    except Exception as e:
        print(f"[DEBUG_READ_SQL] FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise e


_PARQUET_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "apps", "api", "relatorios_cache")


def _cache_path(calc_id: str, calc_tipo: str) -> str:
    """Retorna o caminho do arquivo Parquet de cache para um cálculo."""
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in f"{calc_id}_{calc_tipo}")
    os.makedirs(_PARQUET_CACHE_DIR, exist_ok=True)
    return os.path.join(_PARQUET_CACHE_DIR, f"{safe}.parquet")


def invalidate_calc_cache(calc_id: str, calc_tipo: str = None) -> None:
    """Remove o cache Parquet de um cálculo (ex: após novo processamento)."""
    if calc_tipo:
        path = _cache_path(calc_id, calc_tipo)
        if os.path.exists(path):
            os.remove(path)
            print(f"[CACHE] Invalidado: {path}")
    else:
        # Remove todos os caches do calc_id
        prefix = "".join(c if c.isalnum() or c in "_-" else "_" for c in calc_id)
        if os.path.exists(_PARQUET_CACHE_DIR):
            for f in os.listdir(_PARQUET_CACHE_DIR):
                if f.startswith(prefix):
                    os.remove(os.path.join(_PARQUET_CACHE_DIR, f))
                    print(f"[CACHE] Invalidado: {f}")


def load_vendas_calculos_cached(
    engine: Engine,
    calc_id: str,
    calc_tipo: str,
    columns: list = None,
) -> pl.DataFrame:
    """
    Carrega vendas_calculos para um cálculo usando cache Parquet.

    - 1ª chamada: busca do MySQL (~50s para 3M rows) e salva .parquet
    - Chamadas seguintes: lê do .parquet (~2-3s, zero SQL)
    - Cache invalida automaticamente se o arquivo tiver >24h
    """
    cache_file = _cache_path(calc_id, calc_tipo)
    cache_ttl_hours = 24

    # Cache hit — verificar se ainda é válido
    if os.path.exists(cache_file):
        age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
        if age_hours < cache_ttl_hours:
            print(f"[CACHE] Hit: {cache_file} ({age_hours:.1f}h atrás)")
            df = pl.read_parquet(cache_file)
            if columns:
                df = df.select([c for c in columns if c in df.columns])
            return df
        else:
            print(f"[CACHE] Expirado ({age_hours:.1f}h), refazendo query...")

    # Cache miss — buscar do MySQL
    print(f"[CACHE] Miss para calc_id={calc_id}, calc_tipo={calc_tipo}. Carregando do MySQL...")
    sql = """
        SELECT id_venda, data_venda, bandeira, forma_pagamento,
               tx_rr_venda, vl_rr_venda, vl_venda, tx_venda, desc_venda,
               vl_liq_venda, tx_calc, desc_calc, vl_liq_calc, perda,
               adquirente, nsu, cod_autorizacao, perda_rr, ec_id
        FROM vendas_calculos
        WHERE calc_id = %s AND calc_tipo = %s
    """
    df = read_sql_polars(sql, engine, params=(calc_id, calc_tipo))

    if not df.is_empty():
        print(f"[CACHE] Salvando {len(df)} rows em {cache_file}...")
        df.write_parquet(cache_file, compression="zstd", compression_level=3)
        print(f"[CACHE] Salvo ({os.path.getsize(cache_file) / 1024 / 1024:.1f} MB)")

    if columns:
        df = df.select([c for c in columns if c in df.columns])
    return df


def read_sql_safe(
    sql: str,
    engine: Engine,
    params: tuple = None,
    chunksize: int = 50000,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Lê dados do SQL com proteção contra erros de timeout e packet sequence.
    Agora otimizado para usar Polars se o dataset for grande (> chunksize).
    """
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Tentativa {attempt + 1}/{max_retries} de leitura SQL")
            
            # Usar read_sql_polars que já trata parâmetros e performance
            df_pl = read_sql_polars(sql, engine, params=params)
            print(f"[DEBUG] ✓ Leitura Polars bem-sucedida: {len(df_pl)} registros")
            return df_pl.to_pandas()
        except Exception as e:
            debug_to_file(f"read_sql_safe TOTAL FAILED (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return pd.DataFrame()
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
    base_id = _get_base_id(processamento_id)
    print(f"[DEBUG] Calculando período completo para processamento: {base_id} (base de {processamento_id})")

    todas_as_datas = []
    try:
        base_id = _get_base_id(processamento_id)
        params_vendas = [f"{base_id}%"]
        vendas_sql = (
            "SELECT Data_da_venda FROM vendas_processadas WHERE processamentoid LIKE %s"
        )
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
        pl_vendas = read_sql_polars(vendas_sql, engine, params=tuple(params_vendas))
        df_vendas = pl_vendas.to_pandas()
        if not df_vendas.empty and "Data_da_venda" in df_vendas.columns:
            datas_vendas = pd.to_datetime(
                df_vendas["Data_da_venda"], errors="coerce"
            ).dropna()
            todas_as_datas.extend(datas_vendas.tolist())
            print(
                f"[DEBUG] Encontradas {len(datas_vendas)} datas de venda em vendas_processadas"
            )

        # 2. Datas das vendas filtradas
        params_filtradas = [f"{base_id}%"]
        filtradas_sql = (
            "SELECT Data_da_venda FROM vendas_filtradas WHERE processamentoId LIKE %s"
        )
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
        pl_filtradas = read_sql_polars(filtradas_sql, engine, params=tuple(params_filtradas))
        df_filtradas = pl_filtradas.to_pandas()
        if not df_filtradas.empty and "Data_da_venda" in df_filtradas.columns:
            datas_filtradas = pd.to_datetime(
                df_filtradas["Data_da_venda"], errors="coerce"
            ).dropna()
            todas_as_datas.extend(datas_filtradas.tolist())
            print(
                f"[DEBUG] Encontradas {len(datas_filtradas)} datas de venda em vendas_filtradas"
            )

        # 3. Datas dos recebíveis processados
        params_rec_proc = [f"{base_id}%"]
        rec_proc_sql = (
            "SELECT data_recebivel FROM recebiveis_processados WHERE processamentoid LIKE %s"
        )
        if adquirente:
            rec_proc_sql += " AND adquirente = %s"
            params_rec_proc.append(adquirente)
        if data_inicio:
            rec_proc_sql += " AND data_recebivel >= %s"
            params_rec_proc.append(data_inicio)
        if data_fim:
            rec_proc_sql += " AND data_recebivel <= %s"
            params_rec_proc.append(data_fim)

        rec_proc_sql = _convert_placeholders(engine, rec_proc_sql)
        pl_rec_proc = read_sql_polars(rec_proc_sql, engine, params=tuple(params_rec_proc))
        df_rec_proc = pl_rec_proc.to_pandas()
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
            params_rec_filt = [f"{base_id}%"]
            rec_filt_sql = (
                "SELECT data_recebivel FROM recebiveis_filtrados WHERE processamentoid LIKE %s"
            )
            if adquirente:
                rec_filt_sql += " AND adquirente = %s"
                params_rec_filt.append(adquirente)
            if data_inicio:
                rec_filt_sql += " AND data_recebivel >= %s"
                params_rec_filt.append(data_inicio)
            if data_fim:
                rec_filt_sql += " AND data_recebivel <= %s"
                params_rec_filt.append(data_fim)

            rec_filt_sql = _convert_placeholders(engine, rec_filt_sql)
            pl_rec_filt = read_sql_polars(rec_filt_sql, engine, params=tuple(params_rec_filt))
            df_rec_filt = pl_rec_filt.to_pandas()
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
    engine: Engine, processamento_id: str, calc_tipo: Optional[str] = None
) -> tuple[List[str], dict, List[str]]:
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
        - Lista de tipos de cálculo (calc_tipo) disponíveis para este processamento
    """
    base_id = _get_base_id(processamento_id)
    query = f"""
        SELECT DISTINCT
            adquirente,
            MIN(data_venda) OVER() as data_min,
            MAX(data_venda) OVER() as data_max
        FROM vendas_calculos
        WHERE calc_id LIKE :calc_id
        {"AND calc_tipo = :calc_tipo" if calc_tipo else ""}
        AND adquirente IS NOT NULL
        AND adquirente != ''
        ORDER BY adquirente
    """

    def _parse_date(val):
        """Converte string ou date/datetime para date."""
        from datetime import date, datetime
        if val is None:
            return None
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(str(val), fmt).date()
            except ValueError:
                continue
        return None

    try:
        print(
            f"[DEBUG obter_adquirentes_e_periodo] Buscando dados para calc_id: {processamento_id}"
        )
        with engine.connect() as conn:
            params = {"calc_id": f"{base_id}%"}
            if calc_tipo:
                params["calc_tipo"] = calc_tipo

            result = conn.execute(text(query), params)
            rows = list(result)
            print(f"[DEBUG obter_adquirentes_e_periodo] Encontradas {len(rows)} linhas para {calc_tipo or 'QUALQUER'}")

            if not rows:
                print("[DEBUG obter_adquirentes_e_periodo] Nenhuma linha encontrada")
                return [], {}, []

            adquirentes = [str(row[0]).strip() for row in rows if row[0]]
            print(f"[DEBUG obter_adquirentes_e_periodo] Adquirentes: {adquirentes}")

            # Coletar mins/maxs de vendas_calculos
            all_mins = []
            all_maxs = []
            if rows and rows[0][1]:
                d = _parse_date(rows[0][1])
                if d:
                    all_mins.append(d)
            if rows and rows[0][2]:
                d = _parse_date(rows[0][2])
                if d:
                    all_maxs.append(d)

            # Buscar MIN/MAX de tabelas auxiliares (vendas_filtradas, recebiveis_processados, recebiveis_filtrados)
            aux_queries = [
                ("vendas_filtradas",      "data_da_venda",  "processamentoid"),
                ("recebiveis_processados","data_recebivel", "processamentoid"),
                ("recebiveis_filtrados",  "data_recebivel", "processamentoid"),
            ]
            for table, date_col, id_col in aux_queries:
                try:
                    q_aux = text(
                        f"SELECT MIN({date_col}), MAX({date_col}) FROM {table} "
                        f"WHERE {id_col} LIKE :pid"
                    )
                    r_aux = conn.execute(q_aux, {"pid": f"{base_id}%"}).fetchone()
                    if r_aux:
                        d_min = _parse_date(r_aux[0])
                        d_max = _parse_date(r_aux[1])
                        if d_min:
                            all_mins.append(d_min)
                        if d_max:
                            all_maxs.append(d_max)
                        print(f"[DEBUG obter_adquirentes_e_periodo] {table}: min={d_min}, max={d_max}")
                except Exception as ex:
                    print(f"[DEBUG obter_adquirentes_e_periodo] {table} indisponível: {ex}")

            if all_mins and all_maxs:
                periodo = {"data_min": min(all_mins), "data_max": max(all_maxs)}
                print(f"[DEBUG obter_adquirentes_e_periodo] Período consolidado: {periodo}")
            else:
                periodo = {}
                print("[DEBUG obter_adquirentes_e_periodo] Período vazio")

            # Buscar todos os tipos disponíveis para este processamento ID (sem filtro de tipo)
            query_types = "SELECT DISTINCT calc_tipo FROM vendas_calculos WHERE calc_id LIKE :calc_id"
            result_types = conn.execute(text(query_types), {"calc_id": f"{base_id}%"})
            available_types = [str(r[0]) for r in result_types if r[0]]

            return adquirentes, periodo, available_types
    except Exception as e:
        print(
            f"⚠️ Erro ao buscar adquirentes e período do processamento {processamento_id}: {str(e)}"
        )
        import traceback

        traceback.print_exc()
        return [], {}, []


def obter_adquirentes_distintos_processamento(
    engine: Engine, processamento_id: str, calc_tipo: Optional[str] = None
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
    adquirentes, _, _ = obter_adquirentes_e_periodo_processamento(engine, processamento_id, calc_tipo=calc_tipo)
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

    # Filtrar taxas válidas (maiores que 0 e razoáveis < 100% para evitar outliers)
    taxas_validas = taxas[(taxas > 0) & (taxas < 100)]

    if taxas_validas.empty:
        return {"max_taxa": 0, "min_taxa": 0}

    return {"max_taxa": taxas_validas.max(), "min_taxa": taxas_validas.min()}


def calcular_perdas_por_semestre(
    df_processadas: Any,
    df_calculos: Any = None,
    incluir_faturamento: bool = False,
) -> pd.DataFrame:
    """
    Calcula perdas por semestre usando Polars (muito mais rápido).
    Se df_calculos for None, assume que df_processadas já contém os dados necessários.
    """
    if df_processadas is None or (hasattr(df_processadas, "empty") and df_processadas.empty) and df_calculos is None:
        return pd.DataFrame(columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"])

    # Converter para Polars DataFrames
    pl_proc = pl.from_pandas(df_processadas) if isinstance(df_processadas, pd.DataFrame) else df_processadas
    
    if df_calculos is not None:
        pl_calc = pl.from_pandas(df_calculos) if isinstance(df_calculos, pd.DataFrame) else df_calculos
        # Se vierem dois DFs, faz o join (semelhante ao original)
        # Identificar colunas de join
        left_on = "id" if "id" in pl_proc.columns else "venda_id"
        right_on = "id_venda" if "id_venda" in pl_calc.columns else "venda_id"
        df_pl = pl_proc.join(pl_calc, left_on=left_on, right_on=right_on, how="inner")
    else:
        df_pl = pl_proc

    if df_pl.is_empty():
        return pd.DataFrame(columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"])

    # Identificar colunas
    cols = df_pl.columns
    data_col = next((c for c in ["Data_da_venda", "data_venda", "Data"] if c in cols), None)
    perda_col = "perda"
    perda_rr_col = "perda_rr"
    faturamento_col = "vl_venda"

    if not data_col:
        return pd.DataFrame(columns=["Ano-Semestre", "Perda Monetária MDR", "Perda Total"])

    # Cálculos semestrais
    res = (
        df_pl.with_columns([
            pl.col(data_col).cast(pl.Date).alias("_date")
        ])
        .with_columns([
            (pl.col("_date").dt.year().cast(pl.Utf8) + "-" + 
             pl.when(pl.col("_date").dt.month() <= 6).then(pl.lit("1")).otherwise(pl.lit("2")))
            .alias("Ano-Semestre")
        ])
        .group_by("Ano-Semestre")
        .agg([
            pl.col(perda_col).cast(pl.Float64).sum().fill_null(0).alias("perda_monetaria_mdr"),
            pl.col(perda_rr_col).cast(pl.Float64).sum().fill_null(0).alias("perda_monetaria_rr") if perda_rr_col in cols else pl.lit(0.0).alias("perda_monetaria_rr"),
            pl.col(faturamento_col).cast(pl.Float64).sum().fill_null(0).alias("faturamento_bruto") if incluir_faturamento and faturamento_col in cols else pl.lit(0.0).alias("faturamento_bruto")
        ])
        .sort("Ano-Semestre")
    )

    # Finalizar cálculos e formatação
    res = res.with_columns([
        (pl.col("perda_monetaria_mdr") + pl.col("perda_monetaria_rr")).alias("perda_total")
    ])

    if incluir_faturamento:
        res = res.with_columns([
            (pl.when(pl.col("faturamento_bruto") > 0)
             .then(100 * pl.col("perda_total") / pl.col("faturamento_bruto"))
             .otherwise(0)).round(2).alias("% Perda")
        ])

    df_pd = res.collect().to_pandas() if isinstance(res, pl.LazyFrame) else res.to_pandas()
    
    # Adicionar linha de total geral
    if not df_pd.empty:
        total_mdr = df_pd["perda_monetaria_mdr"].sum()
        total_rr = df_pd["perda_monetaria_rr"].sum()
        total_venda = df_pd["faturamento_bruto"].sum()
        total_perda = total_mdr + total_rr
        
        linha_total = {
            "Ano-Semestre": "** TOTAL GERAL **",
            "perda_monetaria_mdr": total_mdr,
            "perda_monetaria_rr": total_rr,
            "faturamento_bruto": total_venda,
            "perda_total": total_perda
        }
        
        if incluir_faturamento:
            linha_total["% Perda"] = round(100 * total_perda / total_venda, 2) if total_venda > 0 else 0
            
        df_pd = pd.concat([df_pd, pd.DataFrame([linha_total])], ignore_index=True)
    
    # Formatação para o relatório
    df_pd["Perda Monetária MDR"] = df_pd["perda_monetaria_mdr"].apply(format_currency_br)
    df_pd["Perda Monetária RR/RA"] = df_pd["perda_monetaria_rr"].apply(format_currency_br)
    df_pd["Perda Total"] = df_pd["perda_total"].apply(format_currency_br)
    
    if incluir_faturamento:
        df_pd["Faturamento Bruto"] = df_pd["faturamento_bruto"].apply(format_currency_br)
    
    # Garantir a ordem das colunas desejada pelo usuário
    cols_order = ["Ano-Semestre", "Faturamento Bruto", "Perda Monetária MDR", "Perda Monetária RR/RA", "Perda Total", "% Perda"]
    existing_cols = [c for c in cols_order if c in df_pd.columns]
    df_pd = df_pd[existing_cols]
    
    # Remover colunas brutas que sobraram (caso existam)
    raw_cols = ["perda_monetaria_mdr", "perda_monetaria_rr", "faturamento_bruto", "perda_total"]
    existing_raw = [c for c in raw_cols if c in df_pd.columns]
    if existing_raw:
        df_pd = df_pd.drop(columns=existing_raw)
        
    return df_pd
def calcular_min_max_taxas_agrupado(df: Any) -> pd.DataFrame:
    """Calcula as taxas min e max agrupadas por Semestre, Bandeira e Forma de Pagamento usando Polars."""
    if df is None or (hasattr(df, "empty") and df.empty):
        return pd.DataFrame()

    is_pandas = isinstance(df, pd.DataFrame)
    is_lazy = isinstance(df, pl.LazyFrame)
    
    if is_pandas:
        lf = pl.from_pandas(df).lazy()
    elif is_lazy:
        lf = df
    else:
        lf = df.lazy()
    
    cols = lf.collect_schema().names()
    data_col = next((c for c in ["Data_da_venda", "data_venda"] if c in cols), "data_venda")
    bandeira_col = next((c for c in ["bandeira", "Bandeira"] if c in cols), "bandeira")
    forma_pagamento_col = next((c for c in ["forma_pagamento", "Forma_de_pagamento", "forma_de_pagamento"] if c in cols), "forma_pagamento")
    tx_col = "tx_venda"

    if not data_col or tx_col not in cols:
        return pd.DataFrame()

    res = (
        lf.filter(pl.col(tx_col).is_not_null())
        .with_columns([
            pl.col(data_col).cast(pl.Date).alias("_date")
        ])
        .with_columns([
            (pl.col("_date").dt.year().cast(pl.Utf8) + "-" + 
             pl.when(pl.col("_date").dt.month() <= 6).then(pl.lit("1")).otherwise(pl.lit("2")))
            .alias("Ano-Semestre")
        ])
        .group_by(["Ano-Semestre", bandeira_col, forma_pagamento_col])
        .agg([
            pl.col(tx_col).min().alias("Taxa_Min"),
            pl.col(tx_col).max().alias("Taxa_Max")
        ])
        .rename({bandeira_col: "Bandeira", forma_pagamento_col: "Forma_de_pagamento"})
        .sort(["Ano-Semestre", "Bandeira"])
    )

    df_pd = res.collect().to_pandas() if isinstance(res, pl.LazyFrame) else res.to_pandas()
    
    if not df_pd.empty:
        total_min = df_pd["Taxa_Min"].min()
        total_max = df_pd["Taxa_Max"].max()
        
        linha_total = pd.DataFrame([{
            "Ano-Semestre": "** TOTAL GERAL **",
            "Bandeira": "-",
            "Forma_de_pagamento": "-",
            "Taxa_Min": total_min,
            "Taxa_Max": total_max
        }])
        df_pd = pd.concat([df_pd, linha_total], ignore_index=True)

    # Garantir ordem correta das colunas
    final_cols = ["Ano-Semestre", "Bandeira", "Forma_de_pagamento", "Taxa_Min", "Taxa_Max"]
    existing_final = [c for c in final_cols if c in df_pd.columns]
    return df_pd[existing_final]


def obter_evidencias_transacoes(
    engine: Engine,
    processamento_id: str,
    calc_tipo: str = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    df: Optional[pd.DataFrame] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Busca evidências de transações para o relatório analítico.
    Se df for fornecido, usa os dados do DataFrame ao invés de consultar o banco.
    """
    print(f"[DEBUG] Buscando evidências para processamento: {processamento_id}")

    resultado = {
        "maiores_valores": pd.DataFrame(),
        "menores_valores": pd.DataFrame(),
        "maiores_taxas": pd.DataFrame(),
        "menores_taxas": pd.DataFrame(),
    }

    try:
        if df is None:
            base_id = _get_base_id(processamento_id)
            sql = """
            SELECT 
                vc.data_venda AS Data_da_venda,
                vc.bandeira AS Bandeira,
                vc.forma_pagamento,
                vc.vl_venda,
                vc.tx_venda,
                vc.nsu,
                vc.cod_autorizacao
            FROM vendas_calculos vc
            WHERE vc.calc_id LIKE %s
            """
            params = [f"{base_id}%"]

            if calc_tipo:
                sql += " AND vc.calc_tipo = %s"
                params.append(calc_tipo)

            if data_inicio:
                sql += " AND vc.data_venda >= %s"
                params.append(data_inicio)

            if data_fim:
                sql += " AND vc.data_venda <= %s"
                params.append(data_fim)

            sql = _convert_placeholders(engine, sql)
            # Usar read_sql_polars para proteção contra timeouts e eficiência
            pl_df = read_sql_polars(sql, engine, params=tuple(params))
        
        else: # df was provided
            # Se for DataFrame do Pandas, converter para Polars temporariamente para processamento RÁPIDO e LEVE
            is_pandas = isinstance(df, pd.DataFrame)
            pl_df = pl.from_pandas(df) if is_pandas else df
        
        if pl_df.is_empty():
            print("[DEBUG] Nenhuma transação encontrada para evidências")
            return resultado

        print(f"[DEBUG] {len(pl_df)} transações carregadas para evidências")

        # Identificar colunas reais no DataFrame (suportar Bandeira/bandeira, Data_da_venda/data_venda)
        cols = pl_df.columns
        data_col = next((c for c in ["Data_da_venda", "data_venda", "Data"] if c in cols), "data_venda")
        bandeira_col = next((c for c in ["Bandeira", "bandeira", "Adquirente"] if c in cols), "bandeira")
        forma_pgto_col = next((c for c in ["forma_pagamento", "Formas_de_pagamento", "Modality"] if c in cols), "forma_pagamento")
        nsu_col = next((c for c in ["nsu", "NSU"] if c in cols), "nsu")
        aut_col = next((c for c in ["cod_autorizacao", "cod_aut", "autorizacao"] if c in cols), "cod_autorizacao")

        print(f"[DEBUG] Colunas mapeadas para evidências: data={data_col}, adq={bandeira_col}")

        # Selecionar colunas necessárias e garantir tipos, fazendo ALIAS para o esperado pelo template
        # Verificação defensiva de colunas
        select_cols = []
        if data_col in pl_df.columns:
            select_cols.append(pl.col(data_col).cast(pl.Datetime).alias("Data_da_venda"))
        if bandeira_col in pl_df.columns:
            select_cols.append(pl.col(bandeira_col).cast(pl.Utf8).alias("Bandeira"))
        if forma_pgto_col in pl_df.columns:
            select_cols.append(pl.col(forma_pgto_col).cast(pl.Utf8).alias("forma_pagamento"))
        else:
            # Fallback se não encontrar a coluna de forma de pagamento
            select_cols.append(pl.lit("N/A").alias("forma_pagamento"))

        # Adicionar demais colunas obrigatórias
        for col_name, alias in [("vl_venda", "vl_venda"), ("tx_venda", "tx_venda"), ("nsu", "nsu"), ("cod_autorizacao", "cod_autorizacao")]:
            if col_name in pl_df.columns:
                # Cast para Float64 para vl_venda e tx_venda, Utf8 para nsu e cod_autorizacao
                if col_name in ["vl_venda", "tx_venda"]:
                    select_cols.append(pl.col(col_name).cast(pl.Float64).alias(alias))
                else:
                    select_cols.append(pl.col(col_name).fill_null("N/A").cast(pl.Utf8).alias(alias))
            else:
                # Fallback para colunas ausentes
                if col_name in ["vl_venda", "tx_venda"]:
                    select_cols.append(pl.lit(0.0).alias(alias))
                else:
                    select_cols.append(pl.lit("N/A").alias(alias))

        pl_df = pl_df.select(select_cols).drop_nulls(subset=["Data_da_venda", "vl_venda", "tx_venda"])

        # Função auxiliar para formatar evidências (agora aceita Polars DataFrame)
        def formatar_evidencias_pl(pl_top):
            if pl_top.is_empty(): return pd.DataFrame()
            df_top = pl_top.to_pandas()
            df_top["Data"] = df_top["Data_da_venda"].dt.strftime("%d/%m/%Y")
            df_top["Valor"] = df_top["vl_venda"].apply(format_currency_br)
            df_top["Taxa (%)"] = df_top["tx_venda"].round(2).astype(str) + "%"
            df_top = df_top.rename(columns={
                "forma_pagamento": "Forma de Pagamento",
                "nsu": "NSU",
                "cod_autorizacao": "Cód.Autorização"
            })
            return df_top[["Data", "Bandeira", "Forma de Pagamento", "Valor", "Taxa (%)", "NSU", "Cód.Autorização"]]

        # TOP 3 MAIORES VALORES
        resultado["maiores_valores"] = formatar_evidencias_pl(pl_df.sort("vl_venda", descending=True).head(3))
        
        # TOP 3 MENORES VALORES (filtrar valores > 0)
        resultado["menores_valores"] = formatar_evidencias_pl(pl_df.filter(pl.col("vl_venda") > 0).sort("vl_venda").head(3))
        
        # TOP 3 MAIORES TAXAS (filtrar taxas > 0)
        resultado["maiores_taxas"] = formatar_evidencias_pl(pl_df.filter(pl.col("tx_venda") > 0).sort("tx_venda", descending=True).head(3))
        
        # TOP 3 MENORES TAXAS (filtrar taxas > 0)
        resultado["menores_taxas"] = formatar_evidencias_pl(pl_df.filter(pl.col("tx_venda") > 0).sort("tx_venda").head(3))

        print("[DEBUG] Evidências geradas com sucesso")

    except Exception as e:
        print(f"[ERROR] Erro ao buscar evidências: {e}")
        import traceback
        traceback.print_exc()

    return resultado


def calcular_contagem_taxas_agrupado(df: Any) -> pd.DataFrame:
    """Conta as taxas agrupadas por Ano-Semestre, Bandeira e Forma de Pagamento."""
    is_pandas = isinstance(df, pd.DataFrame)
    if is_pandas:
        if df.empty: return pd.DataFrame()
        lf = pl.from_pandas(df).lazy()
    else: # Assume df is a Polars DataFrame or LazyFrame
        if df.is_empty(): return pd.DataFrame()
        lf = df.lazy() if isinstance(df, pl.DataFrame) else df

    cols = lf.collect_schema().names()
    data_col = next((c for c in ["Data_da_venda", "data_venda"] if c in cols), "data_venda")
    bandeira_col = next((c for c in ["bandeira", "Bandeira"] if c in cols), "bandeira")
    forma_pagamento_col = next((c for c in ["forma_pagamento", "Forma_de_pagamento", "forma_de_pagamento"] if c in cols), "forma_pagamento")

    res = (
        lf.filter(pl.col(data_col).is_not_null())
        .with_columns([
            pl.col(data_col).cast(pl.Date).alias("_date")
        ])
        .with_columns([
            (pl.col("_date").dt.year().cast(pl.Utf8) + "-" + 
             pl.when(pl.col("_date").dt.month() <= 6).then(pl.lit("1")).otherwise(pl.lit("2")))
            .alias("Ano-Semestre")
        ])
        .group_by(["Ano-Semestre", bandeira_col, forma_pagamento_col])
        .agg(Contagem=pl.len())
        .rename({bandeira_col: "Bandeira", forma_pagamento_col: "Forma_de_pagamento"})
        .sort(["Ano-Semestre", "Bandeira"])
        .collect()
    )

    contagem = res.to_pandas()

    # Adicionar linha de total
    if not contagem.empty:
        total_qtd = contagem["Contagem"].sum()
        linha_total = pd.DataFrame([{
            "Ano-Semestre": "** TOTAL GERAL **",
            "Bandeira": "-",
            "Forma_de_pagamento": "-",
            "Contagem": total_qtd
        }])
        contagem = pd.concat([contagem, linha_total], ignore_index=True)

    # Garantir ordem correta das colunas
    final_cols = ["Ano-Semestre", "Bandeira", "Forma_de_pagamento", "Contagem"]
    existing_final = [c for c in final_cols if c in contagem.columns]
    return contagem[existing_final]


def calcular_sumario_recebiveis(
    engine: Engine,
    processamento_id: str,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
) -> pd.DataFrame:
    base_id = _get_base_id(processamento_id)
    sql = "SELECT * FROM recebiveis_processados WHERE processamentoid LIKE %s"
    params = [f"{base_id}%"]

    if data_inicio:
        sql += " AND data_recebivel >= %s"
        params.append(data_inicio)

    if data_fim:
        sql += " AND data_recebivel <= %s"
        params.append(data_fim)
    sql = _convert_placeholders(engine, sql)
    try:
        pl_df = read_sql_polars(sql, engine, params=tuple(params))
        df = pl_df.to_pandas()
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
    df["lancamento"] = df["lancamento"].fillna("Sem classificação")

    sumario = (
        df.groupby(["Ano-Semestre", "lancamento"])
        .agg(Valor_Total=("valor_recebivel", "sum"))
        .reset_index()
    )

    # Garantir tipo numérico antes de arredondar
    sumario["Valor_Total"] = pd.to_numeric(
        sumario["Valor_Total"], errors="coerce"
    ).fillna(0)
    sumario["Valor_Total"] = sumario["Valor_Total"].round(2)
    return sumario[["Ano-Semestre", "lancamento", "Valor_Total"]].rename(
        columns={"lancamento": "Lançamento", "Valor_Total": "Valor Total"}
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
    Versão otimizada com Polars da tabela consolidada mensal.
    """
    print(f"[DEBUG] Calculando tabela consolidada mensal (Polars) para: {processamento_id}")

    # 1. Preparar perdas via Polars
    if not df_vendas_processadas.empty and not df_vendas_calculos.empty:
        pl_proc = pl.from_pandas(df_vendas_processadas[["id", "Data_da_venda"]]) if isinstance(df_vendas_processadas, pd.DataFrame) else df_vendas_processadas
        pl_calc = pl.from_pandas(df_vendas_calculos[["id_venda", "perda", "perda_rr"]]) if isinstance(df_vendas_calculos, pd.DataFrame) else df_vendas_calculos

        perdas_semestre = (
            pl_proc.join(pl_calc, left_on="id", right_on="id_venda")
            .with_columns([
                pl.col("Data_da_venda").cast(pl.Date).alias("data")
            ])
            .with_columns([
                (pl.col("data").dt.year().cast(pl.String) + "-" +
                 pl.when(pl.col("data").dt.month() <= 6).then(pl.lit("1")).otherwise(pl.lit("2"))
                ).alias("Ano-Semestre")
            ])
            .group_by("Ano-Semestre")
            .agg([
                pl.col("perda").sum().alias("perda_mdr"),
                pl.col("perda_rr").sum().alias("perda_rr")
            ])
        )
    else:
        perdas_semestre = pl.DataFrame(schema={"Ano-Semestre": pl.String, "perda_mdr": pl.Float64, "perda_rr": pl.Float64})

    # 2. Buscar e Processar Recebíveis
    df_final_pl = perdas_semestre.with_columns([pl.lit(0.0).alias("aluguel_maquinas"), pl.lit(0.0).alias("outros_recebiveis")])
    
    base_id = _get_base_id(processamento_id)
    try:
        sql_rec = "SELECT data_recebivel, lancamento, valor_recebivel FROM recebiveis_processados WHERE processamentoid LIKE %s"
        params_rec = [f"{base_id}%"]
        if data_inicio: sql_rec += " AND data_recebivel >= %s"; params_rec.append(data_inicio)
        if data_fim: sql_rec += " AND data_recebivel <= %s"; params_rec.append(data_fim)

        df_rec = read_sql_polars(_convert_placeholders(engine, sql_rec), engine, params=tuple(params_rec))

        if not df_rec.is_empty():
            palavras = ["maquina", "máquina", "aluguel", "alugel", "locacao", "locação", "pos", "equipamento"]
            regex_aluguel = "(?i)" + "|".join(palavras)

            rec_processed = df_rec.with_columns([
                pl.col("data_recebivel").cast(pl.Date).alias("data")
            ]).with_columns([
                (pl.col("data").dt.year().cast(pl.String) + "-" +
                 pl.when(pl.col("data").dt.month() <= 6).then(pl.lit("1")).otherwise(pl.lit("2"))
                ).alias("Ano-Semestre"),
                pl.col("lancamento").str.contains(regex_aluguel).fill_null(False).alias("is_aluguel")
            ])

            alugueis = rec_processed.filter(pl.col("is_aluguel")).group_by("Ano-Semestre").agg(pl.col("valor_recebivel").sum().alias("aluguel_maquinas"))
            outros = rec_processed.filter(pl.col("is_aluguel").not_()).group_by("Ano-Semestre").agg(pl.col("valor_recebivel").sum().alias("outros_recebiveis"))

            df_final_pl = (
                perdas_semestre.join(alugueis, on="Ano-Semestre", how="outer")
                .join(outros, on="Ano-Semestre", how="outer")
                .fill_null(0)
                .sort("Ano-Semestre")
            )
    except Exception as e:
        print(f"[DEBUG] Erro em calcular_tabela_consolidada_mensal: {e}")

    # 3. Formatação Final
    df_final = df_final_pl.to_pandas()
    if df_final.empty: return pd.DataFrame()
    
    total_mdr = df_final["perda_mdr"].sum()
    total_rr = df_final["perda_rr"].sum()
    total_alu = df_final["aluguel_maquinas"].sum()
    total_out = df_final["outros_recebiveis"].sum()

    df_display = pd.DataFrame()
    df_display["Ano-Semestre"] = df_final["Ano-Semestre"]
    df_display["Perda Monetária MDR"] = df_final["perda_mdr"].apply(format_currency_br)
    df_display["Perdas por Antecipações"] = df_final["perda_rr"].apply(format_currency_br)
    df_display["Aluguéis de Máquinas"] = df_final["aluguel_maquinas"].apply(format_currency_br)
    df_display["Outros Recebíveis"] = df_final["outros_recebiveis"].apply(format_currency_br)

    total_row = pd.DataFrame([{
        "Ano-Semestre": "** TOTAL GERAL **",
        "Perda Monetária MDR": format_currency_br(total_mdr),
        "Perdas por Antecipações": format_currency_br(total_rr),
        "Aluguéis de Máquinas": format_currency_br(total_alu),
        "Outros Recebíveis": format_currency_br(total_out)
    }])
    
    final_df = pd.concat([df_display, total_row], ignore_index=True)
    print(f"[DEBUG] Tabela consolidada gerada: {len(final_df)} linhas")
    return final_df


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
    base_id = _get_base_id(processamento_id)
    print(
        f"[DEBUG] Buscando dados bancários distintos para processamento: {base_id} (usando LIKE)"
    )

    params = [f"{base_id}%"]
    sql = """
        SELECT DISTINCT 
            banco as 'Banco',
            agencia as 'Agência', 
            conta as 'Conta-Corrente'
        FROM recebiveis_processados 
        WHERE processamentoid LIKE %s 
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
        pl_df = read_sql_polars(sql, engine, params=tuple(params))
        df = pl_df.to_pandas()
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

        with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
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

        print(f"[DEBUG] [OK] Excel gerado com sucesso: {excel_path}")
        return excel_path

    except Exception as e:
        print(f"[ERROR] Erro ao gerar Excel: {e}")
        import traceback

        traceback.print_exc()
        return ""


def obter_dados_processamento_v1(
    engine: Engine, processamento_id: str, max_rows: int = 100000000
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Versão antiga de obter_dados_processamento que retorna tupla."""
    try:
        from conf.check_system import verificar_espaco_temp

        if not verificar_espaco_temp():
            raise ValueError(
                "Espaço em disco insuficiente. Libere espaço e tente novamente."
            )
    except ImportError:
        pass

    base_id = _get_base_id(processamento_id)
    metadados_sql = (
        "SELECT * FROM controle_processamentos WHERE id_processamento LIKE :proc_id"
    )
    metadados_list = fetch_all(engine, metadados_sql, {"proc_id": f"{base_id}%"})
    
    if not metadados_list:
        # Fallback para metadados vazios em vez de erro fatal
        print(f"[WARNING] Processamento {base_id} não encontrado em controle_processamentos. Usando genérico.")
        metadados = {"id_processamento": processamento_id, "cliente_nome": "Cliente Genérico"}
    else:
        metadados = metadados_list[0]

    if metadados.get("cliente_id"):
        cliente_sql = "SELECT nome_fantasia, cnpj FROM clientes WHERE cliente_id = :cid"
        cliente = fetch_one(engine, cliente_sql, {"cid": metadados["cliente_id"]})
        if cliente:
            metadados["cliente_nome"] = cliente["nome_fantasia"]
            
    # Como esta função prometia retornar DataFrames, retornamos vazios
    return pd.DataFrame(), pd.DataFrame(), metadados

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
        params=(base_id, max_rows),
    )

    sql_filtradas = "SELECT * FROM vendas_filtradas WHERE processamentoid = %s LIMIT %s"
    sql_filtradas = _convert_placeholders(engine, sql_filtradas)
    df_filtradas = read_sql_safe(
        sql_filtradas,
        engine,
        params=(base_id, max_rows),
    )

    return df_processadas, df_filtradas, metadados


def criar_grafico_vendas_por_bandeira(df: pd.DataFrame) -> str:
    """Cria gráfico de pizza de vendas por bandeira com tratamento de erro."""
    try:
        # Tentar detectar coluna Bandeira de forma case-insensitive
        cols = [c for c in df.columns if c.lower() == "bandeira"]
        bandeira_col = cols[0] if cols else None

        if df.empty or not bandeira_col:
            print(f"[DEBUG] DataFrame vazio ou sem coluna Bandeira (detectada: {bandeira_col}) - pulando gráfico")
            return ""

        df_agg = df[bandeira_col].value_counts().reset_index()
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

        fig.update_layout(width=800, height=400, margin=dict(l=20, r=20, t=40, b=20))
        html_str = fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
        print("[DEBUG] Gráfico de bandeiras gerado como HTML interativo")
        return html_str
    except Exception as e:
        print(f"[AVISO] Erro ao criar gráfico de bandeiras: {e}")
        print("[AVISO] Relatório será gerado sem este gráfico")
        return ""


def criar_grafico_vendas_por_forma_pagamento(df: pd.DataFrame) -> str:
    """Cria gráfico de pizza de vendas por forma de pagamento com tratamento de erro."""
    try:
        # Tentar detectar coluna Forma de Pagamento de forma case-insensitive
        cols = [c for c in df.columns if c.lower() in ["forma_de_pagamento", "forma_pagamento", "forma de pagamento"]]
        forma_col = cols[0] if cols else None

        if df.empty or not forma_col:
            print(
                f"[DEBUG] DataFrame vazio ou sem coluna Forma de Pagamento (detectada: {forma_col}) - pulando gráfico"
            )
            return ""

        df_agg = df[forma_col].value_counts().reset_index()
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

        fig.update_layout(width=800, height=400, margin=dict(l=20, r=20, t=40, b=20))
        html_str = fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
        print("[DEBUG] Gráfico de forma de pagamento gerado como HTML interativo")
        return html_str
    except Exception as e:
        print(f"[AVISO] Erro ao criar gráfico de forma de pagamento: {e}")
        print("[AVISO] Relatório será gerado sem este gráfico")
        return ""


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
    fig.update_layout(width=800, height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


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
    fig.update_layout(width=800, height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})


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
        # Remover duplicatas e nulos
        ecs_limpos = sorted(list(set([str(ec).strip() for ec in ecs_distintos if ec and str(ec).strip()])))
        if len(ecs_limpos) == 1:
            ecs_distintos_str = ecs_limpos[0]
        elif 1 < len(ecs_limpos) <= 5:
            ecs_distintos_str = ", ".join(ecs_limpos)
        elif len(ecs_limpos) > 5:
            ecs_distintos_str = (
                f"{', '.join(ecs_limpos[:5])} e mais {len(ecs_limpos) - 5} ECs"
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
        if k in ["Cliente", "ID Processamento"]:
            html += f"<tr><td><strong>{k}</strong></td><td><strong style='color: #223a6b;'>{v}</strong></td></tr>"
        else:
            html += f"<tr><td>{k}</td><td>{v}</td></tr>"
    html += "</table></div>"

    html += '<div class="report-section"><h3>Estatísticas Gerais</h3><table class="report-table">'
    for k, v in estatisticas.items():
        if k in ["Faturamento Bruto", "Quantidade de Vendas", "Faturamento Líquido"]:
            html += f"<tr><td><strong>{k}</strong></td><td><strong style='color: #223a6b;'>{v}</strong></td></tr>"
        elif "Taxa" in k:
            color = "#9c1313" if "Maior" in k else "#223a6b"
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

        # Identificar colunas de perda (MDR ou Total)
        perda_cols = [c for c in df_trabalho.columns if "Perda Monetária" in c or "Perda Total" in c]
        faturamento_cols = [c for c in df_trabalho.columns if "Faturamento Bruto" in c]

        # Se os valores já vêm formatados como string, converter para numérico
        for col in faturamento_cols + perda_cols:
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
        agg_dict = {}
        if faturamento_cols: agg_dict[faturamento_cols[0]] = "sum"
        for pc in perda_cols: agg_dict[pc] = "sum"

        df_sumarizado = (
            df_trabalho.groupby("Ano-Semestre")
            .agg(agg_dict)
            .reset_index()
        )

        # Recalcular o percentual de perda (usando a primeira coluna de perda encontrada)
        if faturamento_cols and perda_cols:
            df_sumarizado["% Perda"] = (
                df_sumarizado[perda_cols[0]]
                / df_sumarizado[faturamento_cols[0]].replace(0, pd.NA)
            ) * 100
        else:
            df_sumarizado["% Perda"] = 0

        # Calcular totais gerais ANTES da formatação
        total_faturamento = df_sumarizado["Faturamento Bruto"].sum()
        total_perda = df_sumarizado["Perda Monetária"].sum()
        percentual_geral = (
            (total_perda / total_faturamento * 100) if total_faturamento > 0 else 0
        )

        # Formatar valores monetários dos dados sumarizados
        for col in faturamento_cols + perda_cols:
            df_sumarizado[col] = df_sumarizado[col].apply(format_currency_br)

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
    """
    debug_to_file(f"ENTROU EM gerar_demonstrativo_vendas_filtradas: {processamento_id}")
    print(
        f"[DEBUG] Gerando demonstrativo de vendas filtradas para processamento: {processamento_id}"
    )

    base_id = _get_base_id(processamento_id)
    debug_to_file(f"base_id = {base_id}")
    try:
        # Calcular vendas filtradas do processamento
        params = [f"{base_id}%"]
        # MySQL no Windows ignora case, mas usar o nome real 'processamentoId' é recomendável
        sql = """
        SELECT 
            status_da_venda,
            Bandeira,
            Forma_de_pagamento,
            COUNT(*) as Quantidade_Vendas,
            SUM(COALESCE(Valor_da_venda, 0)) as Soma_Valor_Bruto
        FROM vendas_filtradas 
        WHERE processamentoId LIKE %s
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
        pl_demonstrativo = read_sql_polars(sql, engine, params=tuple(params))
        df_demonstrativo = pl_demonstrativo.to_pandas()

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
            "Forma_de_pagamento",
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
        params_total = [f"{base_id}%"]
        sql_total = """
        SELECT SUM(COALESCE(Valor_da_venda, 0)) as total_valor
        FROM vendas_filtradas 
        WHERE processamentoId LIKE %s
        """

        if data_inicio is not None:
            sql_total += " AND Data_da_venda >= %s"
            params_total.append(data_inicio)

        if data_fim is not None:
            sql_total += " AND Data_da_venda <= %s"
            params_total.append(data_fim)

        pl_total = read_sql_polars(sql_total, engine, params=tuple(params_total))
        total_valor_df = pl_total.to_pandas()
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
                    "Forma_de_pagamento": "",
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
        base_id = _get_base_id(processamento_id)
        params_verif = [f"{base_id}%"]
        verificacao_sql = """
        SELECT COUNT(*) as total_registros 
        FROM recebiveis_filtrados 
        WHERE processamentoid LIKE %s
        """

        if data_inicio is not None:
            verificacao_sql += " AND data_recebivel >= %s"
            params_verif.append(data_inicio)

        if data_fim is not None:
            verificacao_sql += " AND data_recebivel <= %s"
            params_verif.append(data_fim)

        pl_verif = read_sql_polars(verificacao_sql, engine, params=tuple(params_verif))
        df_verificacao = pl_verif.to_pandas()
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
        params_rec = [f"{base_id}%"]
        sql = """
        SELECT 
            lancamento as Tipo_Lancamento,
            COUNT(*) as Quantidade_Recebiveis,
            SUM(COALESCE(valor_recebivel, 0)) as Soma_Valor_Recebivel,
            SUM(COALESCE(valor_liquido, 0)) as Soma_Valor_Liquido
        FROM recebiveis_filtrados 
        WHERE processamentoid LIKE %s
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
        pl_demonstrativo = read_sql_polars(sql, engine, params=tuple(params_rec))
        df_demonstrativo = pl_demonstrativo.to_pandas()

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

        pl_total_valor = read_sql_polars(sql_total, engine, params=tuple(params_total))
        total_valor_df = pl_total_valor.to_pandas()

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
    progress_callback: Optional[Any] = None,
    modelo: str = "completo",
) -> Tuple[str, Optional["pd.DataFrame"]]:
    """
    Versão otimizada com Polars para máxima performance.
    """
    debug_to_file("==============================")
    debug_to_file(f"INICIO gerar_relatorio_html | BaseID: {processamento_id}")
    debug_to_file(f"incluir_filtradas: {incluir_filtradas}")
    debug_to_file(f"incluir_rec_filtrados: {incluir_recebiveis_filtrados}")

    # Funções auxiliares para o template
    def to_file_url(path):
        return to_base64_url(path)

    # Configuração de caminhos e URLs de assets (Capa/Logos)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(project_root, "assets")
    caminho_capa = os.path.join(assets_path, "capa_relatorio.jpg")
    caminho_cabecalho = os.path.join(assets_path, "cabecalho_financial.png")

    cover_image_url = to_file_url(caminho_capa) if os.path.exists(caminho_capa) else ""
    header_image_url = to_file_url(caminho_cabecalho) if os.path.exists(caminho_cabecalho) else ""

    # Inicialização preventiva de variáveis
    grafico_bandeiras_html = ""
    grafico_forma_pagamento_html = ""
    grafico_meses_html = ""
    grafico_valores_html = ""
    primeira_venda = None
    ultima_venda = None
    quantidade = 0
    valor_total = 0
    valor_medio = 0
    valor_min = 0
    valor_max = 0
    min_taxa = 0
    max_taxa = 0
    diferenca_taxa = 0
    ecs_distintos = []
    adquirentes_distintos = []
    metadados = {}
    total_transacoes = 0
    faturamento_bruto = 0
    valor_liquido = 0
    valor_medio = 0
    total_materialidade = 0
    materialidade_percentual = 0
    adquirente_principal = adquirente or "Todos"
    
    # Inicilização de tabelas HTML
    tabela_sumario_html = ""
    tabela_perdas_semestre_html = ""
    tabela_min_max_taxas_html = ""
    tabela_contagem_taxas_html = ""
    tabela_sumario_recebiveis_html = ""
    tabela_dados_bancarios_html = ""
    tabela_vendas_filtradas_html = ""
    tabela_recebiveis_filtrados_html = ""
    tabela_evidencias_maiores_valores_html = ""
    tabela_evidencias_menores_valores_html = ""
    tabela_evidencias_maiores_taxas_html = ""
    tabela_evidencias_menores_taxas_html = ""
    
    # Inicialização de DataFrames (Excel e Cálculos)
    df_main = pl.DataFrame()
    df_perdas_sumarizado = pd.DataFrame()
    df_taxas_sumarizado = pd.DataFrame()
    df_contagem_sumarizado = pd.DataFrame()
    df_recebiveis_sumarizado = pd.DataFrame()
    df_dados_bancarios = pd.DataFrame()
    df_vendas_filtradas = pd.DataFrame()
    df_recebiveis_filtrados = pl.DataFrame() # Polars por padrão
    evidencias = {}

    import gc
    gc.collect()

    inicio_total = time.time()

    debug_log(f"START GERAÇÃO: proc='{processamento_id}', tipo='{calc_tipo}', adq='{adquirente}'")

    print("[DEBUG] === INÍCIO GERAÇÃO RELATÓRIO OTIMIZADO (POLARS) ===")
    if progress_callback: progress_callback(10, "Iniciando geração de relatório...")

    # Configurar timeouts
    with engine.connect() as conn:
        if "mysql" in str(engine.url):
            try:
                conn.execute(text("SET SESSION net_read_timeout = 600"))
                conn.execute(text("SET SESSION net_write_timeout = 600"))
                conn.commit()
            except: pass

    # 1. Metadados e Contexto (Consolidado)
    metadados = obter_dados_processamento(engine, processamento_id)
    adquirentes_distintos = obter_adquirentes_distintos_processamento(engine, processamento_id)
    ecs_distintos = obter_ecs_distintos_processamento(engine, processamento_id)
    
    # Adquirente principal
    if adquirente and adquirente not in ("Todos", "None"):
        metadados["adquirente"] = adquirente
    elif adquirentes_distintos:
        metadados["adquirente"] = ", ".join(adquirentes_distintos)
    else:
        metadados["adquirente"] = "Não identificado"

    if progress_callback: progress_callback(20, "Carregando dados financeiros via Polars...")

    # Validar ou Auto-detectar calc_tipo
    needs_detection = not calc_tipo
    if calc_tipo:
        try:
            with engine.connect() as temp_conn:
                sql_check = "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :p1 AND calc_tipo = :p2"
                count = temp_conn.execute(text(sql_check), {"p1": processamento_id, "p2": calc_tipo}).scalar()
                if count == 0:
                    print(f"[DEBUG] calc_tipo '{calc_tipo}' informado não possui registros para {processamento_id}. Tentando auto-detecção.")
                    needs_detection = True
        except Exception as e:
            print(f"[DEBUG] Erro ao validar calc_tipo: {e}")
            needs_detection = True

    if needs_detection:
        debug_log(f"Needs detection for {processamento_id}")
        try:
            with engine.connect() as temp_conn:
                sql_tipo = "SELECT calc_tipo FROM vendas_calculos WHERE calc_id = :p1 LIMIT 1"
                res_tipo = temp_conn.execute(text(sql_tipo), {"p1": processamento_id}).scalar()
                if res_tipo:
                    calc_tipo = res_tipo
                    debug_log(f"Auto-detected calc_tipo: {calc_tipo}")
                else:
                    if not calc_tipo: calc_tipo = "log_mensal" # Fallback final
                    debug_log(f"No calc_tipo found in DB. Using fallback: {calc_tipo}")
        except Exception as e:
            debug_log(f"Error during auto-detection: {e}")
            if not calc_tipo: calc_tipo = "log_mensal"
    else:
        debug_log(f"Using provided calc_tipo: {calc_tipo}")

    debug_log(f"Main query starting for {processamento_id} / {calc_tipo}")

    # 2. Busca de dados principal via cache Parquet (evita re-query do MySQL)
    # Carrega o dataset completo do cálculo; filtros de adquirente/período aplicados no Polars.
    df_cached = load_vendas_calculos_cached(engine, processamento_id, calc_tipo)

    # Fallback sem calc_tipo se cache retornou vazio
    if df_cached.is_empty() and calc_tipo:
        base_id = _get_base_id(processamento_id)
        debug_log(f"Cache vazio para calc_tipo={calc_tipo}. Tentando sem filtro de tipo com base_id={base_id}...")
        sql_fallback = "SELECT id_venda, data_venda, bandeira, forma_pagamento, tx_rr_venda, vl_rr_venda, vl_venda, tx_venda, desc_venda, vl_liq_venda, tx_calc, desc_calc, vl_liq_calc, perda, adquirente, nsu, cod_autorizacao, perda_rr, ec_id FROM vendas_calculos WHERE calc_id LIKE %s"
        df_cached = read_sql_polars(sql_fallback, engine, params=(f"{base_id}%",))

    # Usar nomes de colunas estáveis internamente
    debug_log(f"Cached data loaded: {len(df_cached)} rows")

    # Aplicar filtros no Polars (evita queries adicionais ao MySQL)
    lf_filtered = df_cached.lazy()
    if adquirente and adquirente not in ("Todos", "None", "todos"):
        lf_filtered = lf_filtered.filter(pl.col("adquirente") == adquirente)
    
    # Identificar coluna de data correta
    cols = lf_filtered.collect_schema().names()
    data_col = next((c for c in ["Data_da_venda", "data_venda", "Data"] if c in cols), "data_venda")

    if data_inicio:
        dt_ini = pl.lit(data_inicio).cast(pl.Date)
        lf_filtered = lf_filtered.filter(pl.col(data_col).cast(pl.Date) >= dt_ini)
    if data_fim:
        dt_fim = pl.lit(data_fim).cast(pl.Date)
        lf_filtered = lf_filtered.filter(pl.col(data_col).cast(pl.Date) <= dt_fim)
    
    df_pl_raw = lf_filtered.collect()

    debug_log(f"Main query result (Full for Charts): {len(df_pl_raw)} rows")
    
    if df_pl_raw.is_empty():
        debug_log(f"EMPTY result even after fallback for {processamento_id}")
        quantidade = 0
        valor_total = 0
        df_main = df_pl_raw
        df_charts = df_pl_raw # Para charts também estar vazio
    else:
        # 3. Processamento Otimizado (Polars Lazy)
        lf_full = df_pl_raw.lazy()
        lf_full = filtrar_valores_rede_depara(lf_full)
        lf_full = calcular_previsao_pagamento_rede(lf_full)
        
        # DataFrame para os Gráficos (Full)
        df_charts = lf_full.collect()
        
        # Aplicar filtro de perdas para o df_main (usado nas tabelas de evidência e estatísticas)
        if apenas_com_perdas:
            debug_log("Aplicando filtro APENAS_COM_PERDAS para tabelas/stats")
            # Considerar tanto perda de taxa quanto perda de recebimento antecipado (perda_rr)
            df_main = df_charts.filter(
                (pl.col("perda") != 0) | 
                (pl.col("perda_rr").fill_null(0) != 0)
            )
        else:
            df_main = df_charts
        
        if not df_main.is_empty():
            stats = df_main.select([
                pl.len().alias("count"),
                pl.col("vl_venda").cast(pl.Float64).sum().fill_null(0).alias("total"),
                pl.col("vl_venda").cast(pl.Float64).mean().fill_null(0).alias("mean"),
                pl.col("vl_venda").min().alias("min"),
                pl.col("vl_venda").max().alias("max"),
                pl.col("tx_venda").filter(pl.col("tx_venda") > 0).min().alias("min_taxa"),
                pl.col("tx_venda").filter(pl.col("tx_venda") > 0).max().alias("max_taxa"),
                pl.col(data_col).min().alias("primeira"),
                pl.col(data_col).max().alias("ultima")
            ]).row(0, named=True)

            quantidade = stats["count"]
            valor_total = stats["total"] or 0
            valor_medio = stats["mean"] or 0
            valor_min = stats["min"] or 0
            valor_max = stats["max"] or 0
            min_taxa = stats["min_taxa"] or 0
            max_taxa = stats["max_taxa"] or 0
            primeira_venda = stats["primeira"]
            ultima_venda = stats["ultima"]
            # Garantir que sejam objetos date
            if isinstance(primeira_venda, str): primeira_venda = datetime.strptime(primeira_venda, "%Y-%m-%d").date()
            if isinstance(ultima_venda, str): ultima_venda = datetime.strptime(ultima_venda, "%Y-%m-%d").date()
            # Garantir ordenação correta para evitar diferença negativa bizarra
            if max_taxa < min_taxa:
                print(f"[DEBUG] SWAP TAXAS: min={min_taxa}, max={max_taxa}")
                max_taxa, min_taxa = min_taxa, max_taxa
            
            diferenca_taxa = max_taxa - min_taxa
            
            # Se a diferença for absurda (>100%), algo está errado no dado ou escala
            if abs(diferenca_taxa) > 100:
                print(f"[AVISO] Diferença de taxa absurda detectada: {diferenca_taxa:.2f}% (max={max_taxa}, min={min_taxa})")
                # Se min_taxa for muito pequena perto de 0, talvez seja erro de escala
                if min_taxa < 1e-5:
                    diferenca_taxa = 0
            
            print(f"[DEBUG] Polars Stats: Qtd={quantidade}, Total={valor_total:.2f}")
        else:
            quantidade = 0
            valor_total = 0

    # Ajustar períodos se datas não vieram da query ou df_main vazio
    if not primeira_venda or not ultima_venda:
        primeira_venda, ultima_venda = calcular_periodo_completo(
            engine, processamento_id, adquirente, data_inicio, data_fim
        )

    # 4. Cálculo de Perdas (Consolidado via Polars - ZERO SQL!)
    print("[DEBUG] Calculando materialidade via Polars...")
    total_perdas = 0
    if not df_main.is_empty():
        # Sumariza perda (taxa) e perda_rr (recebimento)
        perda_taxa = df_main.select(pl.col("perda").cast(pl.Float64).sum().fill_null(0)).row(0)[0] or 0
        perda_rr = 0
        if "perda_rr" in df_main.columns:
            perda_rr = df_main.select(pl.col("perda_rr").cast(pl.Float64).sum().fill_null(0)).row(0)[0] or 0
        
        total_perdas = perda_taxa + perda_rr
    
    print(f"[DEBUG] Total Perdas (Polars): {total_perdas:.2f}")
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
        recebiveis_params = (processamento_id,)
        pl_recebiveis = read_sql_polars(recebiveis_sql, engine, params=recebiveis_params)
        recebiveis_result = pl_recebiveis.to_pandas()

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
                pl_perdas = read_sql_polars(perdas_sql, engine, params=(processamento_id, adquirente))
                perdas_result = pl_perdas.to_pandas()
            else:
                # Sem filtro de adquirente - query simples
                perdas_sql = """
                    SELECT COUNT(*) as total_perdas
                    FROM vendas_calculos 
                    WHERE calc_id = %s AND perda IS NOT NULL AND perda != 0
                """
                pl_perdas = read_sql_polars(perdas_sql, engine, params=(processamento_id,))
                perdas_result = pl_perdas.to_pandas()

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

    print("[DEBUG] Dicionário estatisticas_sumario criado:")
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
    # 4. Cálculo de Perdas por Semestre (ZERO SQL!)
    print("[DEBUG] Calculando perdas por semestre via Polars...")
    inicio_perdas = time.time()
    df_perdas_sumarizado = calcular_perdas_por_semestre(df_main, incluir_faturamento=True)
    tabela_perdas_semestre_html = gerar_tabela_html(df_perdas_sumarizado, "Análise de Perdas Estimadas por Semestre")
    log_tempo_execucao("Polars: calcular_perdas_por_semestre", inicio_perdas)

    # 5. Min/Max Taxas por Semestre (ZERO SQL!)
    inicio_taxas = time.time()
    df_taxas_sumarizado = calcular_min_max_taxas_agrupado(df_main)
    tabela_min_max_taxas_html = gerar_tabela_html(df_taxas_sumarizado, "Análise de Taxas Mínimas e Máximas por Semestre")
    log_tempo_execucao("Polars: calcular_min_max_taxas_agrupado", inicio_taxas)

    # 6. Contagem de Transações (ZERO SQL!)
    inicio_contagem = time.time()
    df_contagem_sumarizado = calcular_contagem_taxas_agrupado(df_main)
    tabela_contagem_taxas_html = gerar_tabela_html(df_contagem_sumarizado, "Contagem de Transações por Ano-Semestre, Bandeira e Modalidade")
    log_tempo_execucao("Polars: calcular_contagem_taxas_agrupado", inicio_contagem)

    # 6b. Sumário de Recebíveis com Descontos Contestáveis por Semestre
    df_sumario_recebiveis = calcular_sumario_recebiveis(engine, processamento_id, data_inicio, data_fim)
    if not df_sumario_recebiveis.empty:
        df_sumario_recebiveis = sumarizar_recebiveis_por_semestre(df_sumario_recebiveis)
        tabela_sumario_recebiveis_html = gerar_tabela_html(
            df_sumario_recebiveis, "Sumário de Registros com Descontos Contestáveis/ por Semestre"
        )

    # 6c. Dados Bancários Distintos nos Recebíveis
    df_dados_bancarios = obter_dados_bancarios_distintos(engine, processamento_id, data_inicio, data_fim)
    if df_dados_bancarios is not None and not df_dados_bancarios.empty:
        tabela_dados_bancarios_html = gerar_tabela_html(
            df_dados_bancarios, "Dados Bancários Distintos nos Recebíveis"
        )

    # 7. Evidências de Transações (ZERO SQL!)
    inicio_evidencias = time.time()
    # PASSA DIRETAMENTE O POLARS DATAFRAME para evitar conversão pesada para Pandas
    evidencias = obter_evidencias_transacoes(engine, processamento_id, calc_tipo, df=df_main)
    
    tabela_evidencias_maiores_valores_html = gerar_tabela_html(evidencias["maiores_valores"], "Top 3 Maiores Valores de Transação") if not evidencias["maiores_valores"].empty else ""
    tabela_evidencias_menores_valores_html = gerar_tabela_html(evidencias["menores_valores"], "Top 3 Menores Valores de Transação") if not evidencias["menores_valores"].empty else ""
    tabela_evidencias_maiores_taxas_html = gerar_tabela_html(evidencias["maiores_taxas"], "Top 3 Maiores Taxas Aplicadas") if not evidencias["maiores_taxas"].empty else ""
    tabela_evidencias_menores_taxas_html = gerar_tabela_html(evidencias["menores_taxas"], "Top 3 Menores Taxas Aplicadas") if not evidencias["menores_taxas"].empty else ""
    log_tempo_execucao("Polars: obter_evidencias_transacoes", inicio_evidencias)

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
        log_tempo_execucao("gerar_tabela_recebiveis_filtrados_html", inicio_rec_filtrados_tab)

    # 8. Gráficos (ZERO SQL!)
    print("[DEBUG] Gerando dados dos gráficos via Polars...")
    inicio_graficos = time.time()
    
    # Paralelizar criação de gráficos para performance
    def target_worker(df, tipo, titulo, paths_dict, key):
        print(f"[DEBUG] Thread iniciando para gráfico {tipo} (key={key}). DF shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
        paths_dict[key] = criar_grafico(df, tipo, titulo)
        print(f"[DEBUG] Thread finalizada para gráfico {tipo}. Caminho: {paths_dict[key]}")

    graficos_paths = {}
    threads = []
    
    # Dados para os gráficos via Polars - USAR df_charts (Full) em vez de df_main
    bandeira_col = next((c for c in ["bandeira", "Bandeira"] if c in df_charts.columns), "bandeira")
    forma_col = next((c for c in ["forma_pagamento", "Forma_de_pagamento"] if c in df_charts.columns), "forma_pagamento")
    
    df_g_bandeira = df_charts.group_by(bandeira_col).agg(pl.len().alias("Quantidade")).rename({bandeira_col: "Bandeira"}).to_pandas()
    df_g_forma = df_charts.group_by(forma_col).agg(pl.len().alias("Quantidade")).rename({forma_col: "Forma_de_pagamento"}).to_pandas()
    df_g_mes = df_charts.group_by(pl.col(data_col).cast(pl.Date).dt.truncate("1mo")).agg(pl.len().alias("Quantidade")).to_pandas()
    if not df_g_mes.empty:
        # Polars truncate mantém o nome original ou o date truncado
        # Se data_col for 'data_venda', o nome da coluna agrupada será 'data_venda'
        df_g_mes["MesAno"] = df_g_mes[data_col].dt.strftime("%Y-%m")
        
    df_g_valores = df_charts.group_by(bandeira_col).agg(pl.col("vl_venda").mean().alias("ValorMedio")).rename({bandeira_col: "Bandeira"}).to_pandas()

    args = [
        (df_g_bandeira, "bandeira", "Distribuição por Bandeira", graficos_paths, "bandeira"),
        (df_g_forma, "forma_pagamento", "Distribuição por Forma", graficos_paths, "forma"),
        (df_g_mes, "vendas_mes", "Vendas Mensais", graficos_paths, "mes"),
        (df_g_valores, "valor_medio_bandeira", "Ticket Médio por Bandeira", graficos_paths, "valor"),
    ]

    for a in args:
        t = threading.Thread(target=target_worker, args=a)
        threads.append(t)
        t.start()

    for t in threads: t.join()
    
    grafico_bandeiras_html = graficos_paths.get("bandeira", "")
    grafico_forma_pagamento_html = graficos_paths.get("forma", "")
    grafico_meses_html = graficos_paths.get("mes", "")
    grafico_valores_html = graficos_paths.get("valor", "")
    
    log_tempo_execucao("Polars + Threading: Gerar Gráficos", inicio_graficos)

    if progress_callback: progress_callback(80, "Finalizando relatório...")

    # 9. Materialidade (ZERO SQL para perdas!)
    inicio_materialidade = time.time()
    
    total_perdas_vendas = df_main.select(pl.col("perda").sum()).row(0)[0] or 0
    total_perdas_rr = df_main.select(pl.col("perda_rr").sum()).row(0)[0] if "perda_rr" in df_main.columns else 0
    total_perdas_rr = total_perdas_rr or 0
    
    # Única query restante: recebíveis (outra tabela)
    total_recebiveis = 0
    try:
        params_rec = [processamento_id]
        total_recebiveis = engine.connect().execute(text("SELECT SUM(COALESCE(valor_recebivel,0)) FROM recebiveis_processados WHERE processamentoid = :p1"), {"p1": processamento_id}).scalar() or 0
    except: pass

    valor_materialidade = total_perdas_vendas + total_perdas_rr + total_recebiveis
    percentual_materialidade = (valor_materialidade / valor_total * 100) if valor_total > 0 else 0
    
    # Formatação Final para Template
    materialidade_valor = format_currency_br(valor_materialidade)
    materialidade_percentual = f"{percentual_materialidade:.2f}%".replace(".", ",")
    
    log_tempo_execucao("Polars: Materialidade", inicio_materialidade)

    # 10. Renderizar Template HTML
    inicio_render = time.time()
    
    # Dados amigáveis para o template
    ps_str = primeira_venda.strftime("%d/%m/%Y") if primeira_venda else ""
    us_str = ultima_venda.strftime("%d/%m/%Y") if ultima_venda else ""
    
    context = {
        "cover_image_path": cover_image_url,
        "header_image_path": header_image_url,
        "tabela_sumario_html": tabela_sumario_html,
        "tabela_perdas_semestre_html": tabela_perdas_semestre_html,
        "tabela_min_max_taxas_html": tabela_min_max_taxas_html,
        "tabela_contagem_taxas_html": tabela_contagem_taxas_html,
        "tabela_sumario_recebiveis_html": tabela_sumario_recebiveis_html,
        "tabela_dados_bancarios_html": tabela_dados_bancarios_html,
        "tabela_evidencias_maiores_valores_html": tabela_evidencias_maiores_valores_html,
        "tabela_evidencias_menores_valores_html": tabela_evidencias_menores_valores_html,
        "tabela_evidencias_maiores_taxas_html": tabela_evidencias_maiores_taxas_html,
        "tabela_evidencias_menores_taxas_html": tabela_evidencias_menores_taxas_html,
        "tabela_vendas_filtradas_html": tabela_vendas_filtradas_html,
        "tabela_recebiveis_filtrados_html": tabela_recebiveis_filtrados_html,
        "grafico_bandeiras_html": grafico_bandeiras_html,
        "grafico_forma_pagamento_html": grafico_forma_pagamento_html,
        "grafico_meses_html": grafico_meses_html,
        "grafico_valores_html": grafico_valores_html,
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "materialidade_valor": materialidade_valor,
        "materialidade_percentual": materialidade_percentual,
        "disclaimer_text": "Todas as análises são baseadas exclusivamente nos extratos oficiais fornecidos pela Adquirente.",
        "adquirente_principal": metadados.get("adquirente", ""),
    }

    # Carregar e renderizar
    dir_path_relatorios = criar_diretorio_relatorios()
    # Tentar resolver o path de templates de forma mais robusta
    current_dir = os.path.dirname(os.path.abspath(__file__))
    _templates_dir = os.path.normpath(os.path.join(current_dir, "..", "templates"))
    if not os.path.exists(_templates_dir):
        # Fallback se estiver rodando de dentro de apps/api
        _templates_dir = os.path.normpath(os.path.join(current_dir, "..", "..", "templates"))
    
    print(f"[DEBUG] templates_dir={_templates_dir!r}")
    if not os.path.exists(_templates_dir):
        print(f"[ERROR] Templates dir not found at {_templates_dir}")
        # Tentativa desesperada: procurar na raiz do projeto
        _templates_dir = os.path.join(os.getcwd(), "templates")

    env = Environment(loader=FileSystemLoader(_templates_dir))
    template_name = "template_relatorio_sem_capa.html" if modelo == "sem_capa" else "template_relatorio.html"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        print(f"[ERROR] Template {template_name} not found in {_templates_dir}: {e}")
        # Se falhar, tentar o loader com o path absoluto do arquivo se for detectado errado
        raise e

    html_content = template.render(**context)
    
    # Salvar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_proc_id = re.sub(r"[^\w\-]", "_", processamento_id)
    html_filename = f"relatorio_{safe_proc_id}_{timestamp}.html"
    html_path = os.path.join(dir_path_relatorios, html_filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    log_tempo_execucao("Template: Render e Salvar", inicio_render)

    # 11. Excel (ZERO SQL!)
    inicio_excel = time.time()

    # Force GC before Excel generation to free memory from chart/table processing
    gc.collect()

    # IMPORTANTE: Limitar a 100.000 linhas para o Excel (suficiente para auditoria e evita OOM)
    _excel_row_limit = 100000
    df_excel_main = df_main
    if len(df_main) > _excel_row_limit:
        print(f"[WARNING] Dataset com {len(df_main)} linhas. Truncando para {_excel_row_limit} para o Excel.")
        df_excel_main = df_main.head(_excel_row_limit)
        
    df_join = df_excel_main.to_pandas()
    
    dataframes_excel = {
        "1. Vendas Completas": df_join,
        "2. Perdas por Semestre": df_perdas_sumarizado,
        "3. Taxas Min-Max": df_taxas_sumarizado,
        "4. Contagem Transações": df_contagem_sumarizado,
        "5. Sumário Recebíveis": df_recebiveis_sumarizado,
        "6. Dados Bancários": df_dados_bancarios,
        "7. Top 3 Maiores Valores": evidencias.get("maiores_valores", pd.DataFrame()),
    }

    if incluir_filtradas and not df_vendas_filtradas.empty:
        dataframes_excel["8. Vendas Filtradas"] = df_vendas_filtradas
    if not df_recebiveis_filtrados.empty:
        dataframes_excel["9. Recebíveis Filtrados"] = df_recebiveis_filtrados

    excel_filename = f"relatorio_{safe_proc_id}_{timestamp}"
    excel_path = gerar_excel_relatorio(dataframes_excel, excel_filename)
    log_tempo_execucao("Excel: Gerar arquivo", inicio_excel)

    # 12. Relatório Sintético (sem converter 3.2M rows para Pandas)
    try:
        _vl_liq = float(df_charts.select(pl.col("vl_liq_venda").sum()).item() or 0)
        # Filtrar tx_venda > 0 para média ser realista
        _tx_media_res = df_charts.select(pl.col("tx_venda").filter(pl.col("tx_venda") > 0).mean()).item()
        _tx_media = float(_tx_media_res or 0)
        _bandeiras_pl = df_charts.group_by("bandeira").agg(
            pl.len().alias("qtd"),
            pl.col("vl_venda").sum().alias("valor")
        ).to_pandas().rename(columns={"bandeira": "Bandeira"})
        sintetico_path = gerar_relatorio_sintetico_html(
            metadados=metadados,
            total_transacoes=int(quantidade),
            faturamento_bruto=float(valor_total),
            valor_liquido=_vl_liq,
            ticket_medio=float(valor_medio),
            taxa_media=_tx_media,
            total_divergencias=float(total_perdas),
            bandeiras=_bandeiras_pl,
            top_valores=evidencias.get("maiores_valores", pd.DataFrame()),
            primeira_venda=primeira_venda,
            ultima_venda=ultima_venda,
            periodo_dias=int(periodo_dias),
            adquirente=metadados.get("adquirente", ""),
            processamento_id=processamento_id
        )
    except Exception as e:
        print(f"[DEBUG] Erro no relatório sintético: {e}")
        sintetico_path = None

    print(f"[DEBUG] === RELATÓRIO COMPLETO EM {time.time() - inicio_total:.2f}s ===")
    return html_path, df_main.to_pandas() if return_base else None, sintetico_path


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

    # Preparar resumo do faturamento - Manter os separadores BR (R$ X.XXX,XX)
    resumo_faturamento = f"""No período de <strong>{periodo}</strong> ({periodo_dias} dias), foram processadas <strong>{total_transacoes:,} transações</strong> via cartão, totalizando um <strong>faturamento bruto de {faturamento_bruto_fmt}</strong>. Após descontos de taxas da operadora, o <strong>valor líquido recebido</strong> foi de <strong>{valor_liquido_fmt}</strong>, representando <strong>{percentual_liquido:.2f}% do faturamento</strong>.""".replace(
        ",", "TEMP"
    ).replace(
        ".", ","
    ).replace(
        "TEMP", "."
    )
    # Correção: O replace acima pode ter bagunçado o R$ se ele tiver . ou , mas format_currency_br é bem definido.
    # Na verdade, f"{total_transacoes:,}" gera vírgula como separador de milhar.
    # format_currency_br gera ponto como milhar e vírgula como decimal.
    # O objetivo final é: Milhar=. e Decimal=,
    # Então se total_transacoes for 1,000 -> queremos 1.000
    total_transacoes_str = f"{total_transacoes:,}".replace(",", ".")
    resumo_faturamento = f"""No período de <strong>{periodo}</strong> ({periodo_dias} dias), foram processadas <strong>{total_transacoes_str} transações</strong> via cartão, totalizando um <strong>faturamento bruto de {faturamento_bruto_fmt}</strong>. Após descontos de taxas da operadora, o <strong>valor líquido recebido</strong> foi de <strong>{valor_liquido_fmt}</strong>, representando <strong>{percentual_liquido:.2f}% do faturamento</strong>."""

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
        # Detectar colunas de forma resiliente
        cols = top_valores.columns
        data_col = next((c for c in ["Data", "data_venda", "Data_da_venda"] if c in cols), "Data")
        bandeira_col = next((c for c in ["Bandeira", "bandeira"] if c in cols), "Bandeira")
        valor_col = next((c for c in ["Valor", "vl_venda", "valor"] if c in cols), "Valor")
        taxa_col = next((c for c in ["Taxa (%)", "tx_venda", "taxa"] if c in cols), "Taxa (%)")
        nsu_col = next((c for c in ["NSU", "nsu"] if c in cols), "NSU")
        auth_col = next((c for c in ["Cód. Autorização", "cod_autorizacao", "autorizacao"] if c in cols), "Cód. Autorização")

        for idx, row in top_valores.head(3).iterrows():
            top_valores_lista.append(
                {
                    "data": row.get(data_col, ""),
                    "bandeira": row.get(bandeira_col, ""),
                    "valor": row.get(valor_col, ""),
                    "taxa": row.get(taxa_col, ""),
                    "nsu": row.get(nsu_col, ""),
                    "cod_autorizacao": row.get(auth_col, ""),
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
        os.path.dirname(os.path.dirname(__file__)), "templates"
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
        pl_res = read_sql_polars(sql, engine, params=params)
        resultado = pl_res.to_pandas()

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
    inicio = time.time()
    print(f"[DEBUG] Criando gráfico tipo '{tipo}', titulo '{titulo}'. DF empty? {df.empty if hasattr(df, 'empty') else 'N/A'}")
    if not df.empty:
        print(f"[DEBUG] Colunas do DF para {tipo}: {df.columns.tolist()}")
    
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
            fig.update_traces(textposition="none", textinfo="none")
            fig.update_layout(showlegend=True)
        fig.update_layout(width=800, height=400, margin=dict(l=20, r=20, t=40, b=20))
        html_str = fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})
        print(f"[DEBUG] ✓ Gráfico {tipo} gerado como HTML interativo ({len(html_str)} chars)")
        log_tempo_execucao(f"criar_grafico({tipo})", inicio)
        return html_str
    log_tempo_execucao(f"criar_grafico({tipo}) - vazio", inicio)
    return ""


def gerar_tabela_html(df: pd.DataFrame, titulo: str) -> str:
    if df.empty:
        return ""

    html = f'<div class="report-section"><h3>{titulo}</h3><table class="report-table">'
    html += "<tr>" + "".join(f'<th class="header-blue">{col}</th>' for col in df.columns) + "</tr>"

    for _, row in df.iterrows():
        html += "<tr>"

        # Verificar tipo de linha (checa todos os valores da linha)
        all_vals = " ".join(str(v) for v in row.values).upper()
        is_total_row = "TOTAL GERAL" in all_vals or "TOTAL:" in all_vals or "** TOTAL" in all_vals
        is_subtotal_row = ("SUBTOTAL" in all_vals or "SUB-TOTAL" in all_vals) and not is_total_row

        for col in df.columns:
            valor = row[col]
            valor_str = str(valor)

            # Heurística de formatação baseada no nome da coluna
            col_lower = col.lower()
            
            if isinstance(valor, (int, float, complex)) and not pd.isna(valor):
                # 1. Porcentagens
                if "%" in col or "taxa" in col_lower or "perc" in col_lower:
                    valor_str = f"{float(valor):.2f}%"
                # 2. Valores Monetários (se não for contagem)
                elif any(word in col_lower for word in ["valor", "vl_", "faturamento", "bruto", "liquido", "perda", "total", "mdr", "antecipacoes"]):
                    if "quantidade" not in col_lower and "contagem" not in col_lower:
                        valor_str = format_currency_br(valor)
                # 3. Quantidades / Inteiros
                elif any(word in col_lower for word in ["quantidade", "contagem", "nsu", "autorizacao", "transacoes"]):
                    try:
                        valor_str = f"{int(float(valor)):,}".replace(",", ".")
                    except:
                        valor_str = str(valor)
                # Fallback para outros números pequenos/médios
                elif isinstance(valor, float):
                    valor_str = f"{valor:.2f}".replace(".", ",")

            # Limpezas estéticas
            valor_str = valor_str.replace("R$ 0,00", "0,00").replace("CREDITO", "CRÉDITO").replace("DEBITO", "DÉBITO")
            
            # Se for R$ 0,00 sem R$, deixar -
            if valor_str == "0,00":
                valor_str = "-"

            # Aplicar alinhamento à direita para números e monetários
            style = ""
            if isinstance(valor, (int, float, complex)) and not pd.isna(valor):
                style = "text-align: right;"
            elif "R$" in valor_str or "%" in valor_str or (valor_str.replace(",", "").replace(".", "").isdigit() and len(valor_str) < 15):
                 # Heurística para strings que parecem números formatados
                 style = "text-align: right;"

            # Aplicar formatação
            if is_total_row:
                html += f"<td style='color: #9c1313; font-weight: bold; background-color: #fff0f0; {style}'>{valor_str}</td>"
            elif is_subtotal_row:
                html += f"<td style='font-weight: bold; background-color: #f0f4ff; color: #223a6b; {style}'>{valor_str}</td>"
            else:
                html += f"<td style='{style}'>{valor_str}</td>"
        
        html += "</tr>"

    html += "</table></div>"
    return html





def obter_ecs_distintos_processamento(
    engine: Engine, processamento_id: str, adquirente: str = None
) -> List[str]:
    try:
        base_id = _get_base_id(processamento_id)
        # Tentar primeiro em vendas_calculos (mais específico para o relatório)
        # Usamos o ID base com LIKE para maior resiliência
        if adquirente:
            query = "SELECT DISTINCT ec_id FROM vendas_calculos WHERE calc_id LIKE %s AND ec_id IS NOT NULL AND ec_id != '' AND adquirente = %s"
            pl_ecs = read_sql_polars(query, engine, params=(f"{base_id}%", adquirente))
            df_ecs = pl_ecs.to_pandas()
        else:
            query = "SELECT DISTINCT ec_id FROM vendas_calculos WHERE calc_id LIKE %s AND ec_id IS NOT NULL AND ec_id != ''"
            pl_ecs = read_sql_polars(query, engine, params=(f"{base_id}%",))
            df_ecs = pl_ecs.to_pandas()

        if not df_ecs.empty:
            ecs_list = df_ecs["ec_id"].dropna().astype(str).tolist()
            ecs_list = [ec.strip() for ec in ecs_list if ec.strip()]
            if ecs_list:
                ecs_list.sort()
                return sorted(list(set(ecs_list)))

        # Fallback para vendas_processadas (usa o base_id)
        base_id = _get_base_id(processamento_id)
        if adquirente:
            query = "SELECT DISTINCT ec_id FROM vendas_processadas WHERE processamentoid LIKE %s AND ec_id IS NOT NULL AND ec_id != '' AND adquirente = %s"
            pl_ecs = read_sql_polars(query, engine, params=(f"{base_id}%", adquirente))
            df_ecs = pl_ecs.to_pandas()
        else:
            query = "SELECT DISTINCT ec_id FROM vendas_processadas WHERE processamentoid LIKE %s AND ec_id IS NOT NULL AND ec_id != ''"
            pl_ecs = read_sql_polars(query, engine, params=(f"{base_id}%",))
            df_ecs = pl_ecs.to_pandas()

        if df_ecs.empty:
            return []

        ecs_list = df_ecs["ec_id"].dropna().astype(str).tolist()
        ecs_list = [ec.strip() for ec in ecs_list if ec.strip()]
        ecs_list.sort()

        return sorted(list(set(ecs_list)))
    except Exception as e:
        print(f"Erro ao buscar ECs distintos: {e}")
        return []


def obter_dados_processamento(engine: Engine, processamento_id: str) -> Dict[str, Any]:
    """Obtém metadados do processamento. Se não encontrar no banco, retorna objeto com valores padrão."""
    base_id = _get_base_id(processamento_id)
    metadados_sql = (
        "SELECT * FROM controle_processamentos WHERE id_processamento LIKE :proc_id"
    )
    
    try:
        metadados = fetch_one(engine, metadados_sql, {"proc_id": f"{base_id}%"})
    except Exception as e:
        print(f"[ERROR] Erro ao buscar metadados do processamento: {e}")
        metadados = None

    if not metadados:
        print(f"[WARNING] Processamento ID {base_id} (base de {processamento_id}) não encontrado em controle_processamentos.")
        # Em vez de levantar erro, retorna metadados mínimos para permitir a geração do relatório
        metadados = {
            "id_processamento": base_id,
            "cliente_nome": f"Cálculo {base_id}",
            "adquirente": "Todos",
            "data_inicio": None,
            "data_fim": None,
            "is_fallback": True
        }

    if metadados.get("cliente_id") and metadados.get("is_fallback") is not True:
        cliente_sql = "SELECT nome_fantasia, cnpj FROM clientes WHERE cliente_id = :cid"
        try:
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
        except Exception as e:
            print(f"[WARNING] Erro ao buscar dados do cliente para o relatório: {e}")
            
    if not metadados.get("cliente_nome"):
        metadados["cliente_nome"] = f"Cálculo {base_id}"
        
    return metadados


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
    progress_callback: Optional[Any] = None,
    modelo: str = "completo",
) -> Tuple[str, Optional["pd.DataFrame"], Optional[str]]:
    """
    Versão otimizada com Polars para o relatório mensal.
    """
    import gc
    gc.collect()

    inicio_total = time.time()
    print("[DEBUG] === INÍCIO GERAÇÃO RELATÓRIO MENSAL OTIMIZADO (POLARS) ===")

    # Funções auxiliares para o template
    def to_file_url(path):
        return to_base64_url(path)

    # Configuração de caminhos e URLs de assets (Capa/Logos)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_path = os.path.join(project_root, "assets")
    caminho_capa = os.path.join(assets_path, "capa_relatorio.jpg")
    caminho_cabecalho = os.path.join(assets_path, "cabecalho_financial.png")

    cover_image_url = to_file_url(caminho_capa) if os.path.exists(caminho_capa) else ""
    header_image_url = to_file_url(caminho_cabecalho) if os.path.exists(caminho_cabecalho) else ""

    # Inicialização preventiva de variáveis
    grafico_bandeiras_html = ""
    grafico_forma_pagamento_html = ""
    grafico_meses_html = ""
    grafico_valores_html = ""
    primeira_venda = None
    ultima_venda = None
    quantidade = 0
    valor_total = 0
    valor_medio = 0
    valor_min = 0
    valor_max = 0
    total_materialidade = 0
    materialidade_percentual = 0
    adquirente_principal = adquirente or "Todos"
    
    # Inicilização de tabelas HTML
    tabela_sumario_html = ""
    tabela_perdas_semestre_html = ""
    tabela_min_max_taxas_html = ""
    tabela_contagem_taxas_html = ""
    tabela_sumario_recebiveis_html = ""
    tabela_dados_bancarios_html = ""
    tabela_vendas_filtradas_html = ""
    tabela_recebiveis_filtrados_html = ""
    tabela_evidencias_maiores_valores_html = ""
    tabela_evidencias_menores_valores_html = ""
    tabela_evidencias_maiores_taxas_html = ""
    tabela_evidencias_menores_taxas_html = ""

    if progress_callback: progress_callback(10, "Iniciando relatório mensal...")

    # 1. Metadados e Contexto
    metadados = obter_dados_processamento(engine, processamento_id)
    adquirentes_distintos = obter_adquirentes_distintos_processamento(engine, processamento_id)
    ecs_distintos = obter_ecs_distintos_processamento(engine, processamento_id, adquirente)

    if adquirente and adquirente != "None":
        adquirente_principal = adquirente
    elif adquirentes_distintos:
        adquirente_principal = ", ".join(adquirentes_distintos)
    else:
        adquirente_principal = "Não identificado"
    # Validar ou Auto-detectar calc_tipo
    needs_detection = not calc_tipo
    if calc_tipo:
        try:
            with engine.connect() as temp_conn:
                sql_check = "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :p1 AND calc_tipo = :p2"
                count = temp_conn.execute(text(sql_check), {"p1": processamento_id, "p2": calc_tipo}).scalar()
                if count == 0:
                    needs_detection = True
        except:
            needs_detection = True

    if needs_detection:
        try:
            with engine.connect() as temp_conn:
                sql_tipo = "SELECT calc_tipo FROM vendas_calculos WHERE calc_id = :p1 LIMIT 1"
                res_tipo = temp_conn.execute(text(sql_tipo), {"p1": processamento_id}).scalar()
                if res_tipo:
                    calc_tipo = res_tipo
        except:
            if not calc_tipo: calc_tipo = "log_mensal"

    # 2. Busca de dados principal via cache Parquet (evita re-query do MySQL)
    df_cached = load_vendas_calculos_cached(engine, processamento_id, calc_tipo)

    debug_log(f"Cached data loaded: {len(df_cached)} rows")

    # Aplicar filtros no Polars
    lf_filtered = df_cached.lazy()
    if adquirente and adquirente not in ("Todos", "None", "todos"):
        lf_filtered = lf_filtered.filter(pl.col("adquirente") == adquirente)
    
    # Identificar coluna de data correta
    cols = lf_filtered.collect_schema().names()
    data_col = next((c for c in ["Data_da_venda", "data_venda", "Data"] if c in cols), "data_venda")

    if data_inicio:
        dt_ini = pl.lit(data_inicio).cast(pl.Date)
        lf_filtered = lf_filtered.filter(pl.col(data_col).cast(pl.Date) >= dt_ini)
    if data_fim:
        dt_fim = pl.lit(data_fim).cast(pl.Date)
        lf_filtered = lf_filtered.filter(pl.col(data_col).cast(pl.Date) <= dt_fim)
    if apenas_com_perdas:
        lf_filtered = lf_filtered.filter(
            (pl.col("perda") > 0) | (pl.col("perda_rr").fill_null(0) > 0)
        )
    df_pl = lf_filtered.collect()
    
    # 3. Processamento Otimizado (Polars Lazy)
    lf = df_pl.lazy()
    lf = filtrar_valores_rede_depara(lf)
    lf = calcular_previsao_pagamento_rede(lf)
    df_main = lf.collect() if isinstance(lf, pl.LazyFrame) else lf
    
    if df_main.is_empty():
        print("[DEBUG] Nenhum registro encontrado para o relatório mensal.")
        # Retorno seguro se vazio
        return "", None, None
    
    # Estatísticas Básicas
    stats = df_main.select([
        pl.len().alias("count"), 
        pl.col("vl_venda").cast(pl.Float64).sum().fill_null(0).alias("total"),
        pl.col("vl_liq_venda").cast(pl.Float64).sum().fill_null(0).alias("liquido"), 
        pl.col("vl_venda").min().alias("min"),
        pl.col("vl_venda").max().alias("max"), 
        pl.col(data_col).min().alias("primeira"),
        pl.col(data_col).max().alias("ultima")
    ]).row(0, named=True)

    total_transacoes = stats["count"]
    faturamento_bruto = stats["total"] or 0
    valor_liquido = stats["liquido"] or 0
    valor_min = stats["min"] or 0
    valor_max = stats["max"] or 0
    valor_medio = faturamento_bruto / total_transacoes if total_transacoes > 0 else 0
    primeira_venda = stats["primeira"]
    ultima_venda = stats["ultima"]
    periodo_dias = (ultima_venda - primeira_venda).days + 1 if (primeira_venda and ultima_venda) else 0

    df_join = df_main.to_pandas()

    if not mes_referencia and primeira_venda:
        meses_pt = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
                    7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}
        mes_nome = meses_pt.get(primeira_venda.month, primeira_venda.strftime("%B"))
        mes_referencia = f"{mes_nome}/{primeira_venda.year}"

    # 4. Materialidade (Polars)
    total_perdas_vendas = df_main.select(pl.col("perda").sum()).row(0)[0] or 0
    total_perdas_rr = df_main.select(pl.col("perda_rr").sum()).row(0)[0] or 0
    
    total_recebiveis = 0
    try:
        sql_rec = "SELECT SUM(COALESCE(valor_recebivel,0)) FROM recebiveis_processados WHERE processamentoid = :p1"
        total_recebiveis = engine.connect().execute(text(sql_rec), {"p1": processamento_id}).scalar() or 0
    except: pass
    
    total_materialidade = total_perdas_vendas + total_perdas_rr + total_recebiveis
    materialidade_percentual = (total_materialidade / faturamento_bruto * 100) if faturamento_bruto > 0 else 0

    # 5. Gráficos (Threading)
    graficos_paths = {}
    threads = []
    def run_g(df, func, out_dict, key): 
        try: out_dict[key] = func(df)
        except: out_dict[key] = ""
    
    t1 = threading.Thread(target=run_g, args=(df_join, criar_grafico_vendas_por_bandeira, graficos_paths, "bandeira"))
    t2 = threading.Thread(target=run_g, args=(df_join, criar_grafico_vendas_por_forma_pagamento, graficos_paths, "forma"))
    threads.extend([t1, t2]); t1.start(); t2.start()
    for t in threads: t.join()

    # 6. Tabelas HTML
    df_tabela_consolidada = calcular_tabela_consolidada_mensal(engine, processamento_id, df_main, df_main, data_inicio, data_fim)
    df_perdas = calcular_perdas_por_semestre(df_main, incluir_faturamento=True)
    df_min_max_taxas = calcular_min_max_taxas_agrupado(df_main)
    df_contagem_taxas = calcular_contagem_taxas_agrupado(df_main)
    df_dados_bancarios = obter_dados_bancarios_distintos(engine, processamento_id, data_inicio, data_fim)
    evidencias = obter_evidencias_transacoes(engine, processamento_id, calc_tipo, data_inicio, data_fim, df=df_main)

    def to_h(df, title): return gerar_tabela_html(df, title) if not (df is None or (isinstance(df, pd.DataFrame) and df.empty)) else ""
    
    ps_str = primeira_venda.strftime("%d/%m/%Y") if primeira_venda else ""
    us_str = ultima_venda.strftime("%d/%m/%Y") if ultima_venda else ""

    context = {
        "cover_image_path": cover_image_url,
        "header_image_path": header_image_url,
        "mes_referencia": mes_referencia,
        "periodo_analise": f"{ps_str} a {us_str}",
        "tabela_sumario_html": criar_tabela_sumario({"quantidade": total_transacoes, "valor_total": faturamento_bruto, "valor_medio": valor_medio, "valor_min": valor_min, "valor_max": valor_max, "valor_liquido": valor_liquido, "primeira_venda": ps_str, "ultima_venda": us_str, "periodo_dias": periodo_dias}, metadados, calcular_estatisticas_taxas(df_join), ecs_distintos, adquirentes_distintos),
        "tabela_consolidada_html": to_h(df_tabela_consolidada, "Análise Consolidada"),
        "tabela_perdas_mes_html": to_h(df_perdas, "Análise de Perdas Estimadas"),
        "tabela_min_max_taxas_html": to_h(df_min_max_taxas, "Taxas Mínimas e Máximas"),
        "tabela_contagem_taxas_html": to_h(df_contagem_taxas, "Contagem de Transações"),
        "tabela_dados_bancarios_html": to_h(df_dados_bancarios, "Dados Bancários"),
        "grafico_bandeiras_html": graficos_paths.get("bandeira", ""),
        "grafico_forma_pagamento_html": graficos_paths.get("forma", ""),
        "materialidade_valor": format_currency_br(total_materialidade),
        "materialidade_percentual": f"{materialidade_percentual:.2f}%",
        "data_processamento": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

    # Render e Salvar
    current_dir = os.path.dirname(os.path.abspath(__file__))
    _templates_dir = os.path.normpath(os.path.join(current_dir, "..", "templates"))
    if not os.path.exists(_templates_dir):
        _templates_dir = os.path.normpath(os.path.join(current_dir, "..", "..", "templates"))
    
    env = Environment(loader=FileSystemLoader(_templates_dir))
    template_name = "template_relatorio_mensal_sem_capa.html" if modelo == "sem_capa" else "template_relatorio_mensal.html"
    html_content = env.get_template(template_name).render(**context)
    
    dir_path = criar_diretorio_relatorios()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"relatorio_mensal_{processamento_id}_{timestamp}.html"
    html_path = os.path.join(dir_path, html_filename)
    with open(html_path, "w", encoding="utf-8") as f: f.write(html_content)

    # 7. Excel (ZERO SQL)
    gc.collect()
    excel_filename = f"relatorio_mensal_{processamento_id}_{timestamp}"
    _excel_row_limit = 100000
    df_join_excel = df_join.head(_excel_row_limit) if len(df_join) > _excel_row_limit else df_join
    if len(df_join) > _excel_row_limit:
        print(f"[WARNING] Mensal: Dataset com {len(df_join)} linhas. Truncando para {_excel_row_limit} para o Excel.")
    dataframes_excel = {
        "1. Vendas Completas": df_join_excel,
        "2. Análise Consolidada": df_tabela_consolidada,
        "3. Perdas Semestre": df_perdas,
        "4. Taxas Min-Max": df_min_max_taxas,
        "5. Contagem Transações": df_contagem_taxas,
        "6. Dados Bancários": df_dados_bancarios
    }
    excel_path = gerar_excel_relatorio(dataframes_excel, excel_filename)

    # 8. Relatório Sintético
    try:
        sintetico_path = gerar_relatorio_sintetico_html(
            metadados=metadados, total_transacoes=total_transacoes, faturamento_bruto=faturamento_bruto,
            valor_liquido=valor_liquido, ticket_medio=valor_medio, taxa_media=df_join["tx_venda"].mean() if not df_join.empty else 0,
            total_divergencias=total_materialidade, primeira_venda=primeira_venda, ultima_venda=ultima_venda,
            periodo_dias=periodo_dias, adquirente=metadados.get("adquirente", "Não identificado"), processamento_id=processamento_id
        )
    except: sintetico_path = None

    print(f"[DEBUG] Tempo total mensal: {time.time() - inicio_total:.2f}s")
    return html_path, None, sintetico_path
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
                f"{row['calc_id']} | {tipo_amigavel(row['calc_tipo'])}",
                (row['calc_id'], row['calc_tipo']),
            )
            for row in df_calcs.to_dict(orient="records")
        ]
        if not df_calcs.empty
        else [("Nenhum cálculo", (None, None))]
    )

    calc_select = pn.widgets.Select(
        name="Selecione o Processamento/Cálculo", options=dict(calc_options), width=400
    )

    # Atualizar opções de adquirente ao trocar processamento
    def on_calc_change(event):
        print("\n[DEBUG SEGUNDA FUNÇÃO] === on_calc_change AUTOMÁTICO ===")
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
                _, periodo, _ = obter_adquirentes_e_periodo_processamento(
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

        print("[DEBUG SEGUNDA FUNÇÃO] === FIM on_calc_change AUTOMÁTICO ===\n")

    calc_select.param.watch(on_calc_change, "value")

    # Carregar adquirentes automaticamente na inicialização da segunda função
    print("\n[DEBUG SEGUNDA FUNÇÃO] === INICIALIZANDO INTERFACE ===")
    print(f"[DEBUG SEGUNDA FUNÇÃO] calc_select criado com {len(calc_options)} opções")

    # Se há cálculos disponíveis, carregar adquirentes do primeiro
    if calc_options and calc_options[0][1] != (None, None):
        print("[DEBUG SEGUNDA FUNÇÃO] Carregando adquirentes iniciais...")
        on_calc_change(None)
    else:
        print(
            "[DEBUG SEGUNDA FUNÇÃO] Nenhum cálculo disponível para carregar adquirentes"
        )
        adquirente_select.options = ["Todos"]
        adquirente_select.value = "Todos"

    print("[DEBUG SEGUNDA FUNÇÃO] === FIM INICIALIZAÇÃO ===\n")

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
