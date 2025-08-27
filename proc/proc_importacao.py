# proc/proc_importacao.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import pandas as pd
from sqlalchemy.engine import Engine

from conf.funcoesbd import (
    depara_carregar_mapa,
    processamento_gerar_novo_id,
    processamento_salvar,
    bandeiras_por_ec,
    termos_listar,
    vendas_processadas_bulk_insert,
    vendas_filtradas_bulk_insert,
    vendas_remover_duplicadas,
)


def detectar_cabecalho(df: pd.DataFrame, min_preenchidos: int = 10) -> int:
    """
    Retorna o índice (0-based) da primeira linha cujo número de campos não nulos
    seja > min_preenchidos. Se não encontrar, retorna 0.
    """
    for i in range(len(df)):
        if df.iloc[i].notna().sum() > min_preenchidos:
            return i
    return 0


def aplicar_depara(colunas: List[str], mapa: Dict[str, str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Aplica o de-para de nomes de colunas.
    Retorna (novas_colunas, transformacoes_realizadas), onde transformacoes_realizadas
    é um dict {origem: destino}.
    """
    transformacoes: Dict[str, str] = {}
    novas: List[str] = []
    for c in colunas:
        c_limpo = (str(c) if c is not None else "").strip()
        if c_limpo in mapa:
            novas.append(mapa[c_limpo])
            transformacoes[c_limpo] = mapa[c_limpo]
        else:
            novas.append(c_limpo)
    return novas, transformacoes


def preparar_dataframe_de_arquivo(
    path: str,
    engine: Engine,
    contexto: str = "",
    tipo_origem: str = "V",
    sheet_name: Optional[str] = None,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, str], int]:
    """
    1) Lê Excel/CSV sem cabeçalho.
    2) Detecta a linha de cabeçalho (> min_preenchidos).
    3) Define as colunas a partir da linha detectada.
    4) Aplica o de-para vindo do banco (depara_carregar_mapa).

    Retorna: (df_tratado, transformacoes, idx_header)
    """
    # Leitura
    if path.lower().endswith((".xlsx", ".xls")):
        df_raw = pd.read_excel(path, header=None, sheet_name=sheet_name)
    else:
        # tenta inferir separador se não informado
        if delimiter is None:
            df_raw = pd.read_csv(path, header=None, encoding=encoding or "utf-8", sep=None, engine="python")
        else:
            df_raw = pd.read_csv(path, header=None, encoding=encoding or "utf-8", sep=delimiter)

    # Cabeçalho
    idx_header = detectar_cabecalho(df_raw, min_preenchidos=10)
    header = df_raw.iloc[idx_header].tolist()
    df = df_raw.iloc[idx_header + 1 :].reset_index(drop=True)
    df.columns = [str(x).strip() if x is not None else "" for x in header]

    # De-Para (carregado do banco)
    mapa = depara_carregar_mapa(engine, contexto=(contexto or ""), tipo_origem=tipo_origem)
    novas_cols, transformacoes = aplicar_depara(list(df.columns), mapa)
    df.columns = novas_cols

    return df, transformacoes, idx_header


def normalizar_dataframe_vendas(df: pd.DataFrame, usuario: str = "desconhecido") -> pd.DataFrame:
    """
    - Converte colunas de data (formato dd/mm/yyyy) para datetime
    - Converte números com vírgula para float
    - Atribui colunas de auditoria (data_processamento, usuario_processamento)
    """
    # Datas
    colunas_data = [
        "Data_da_venda",
        "Data_da_autorização_da_venda",
        "Previsão_de_pagamento",
    ]
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")

    # Números com vírgula como separador decimal
    colunas_float = [
        "Taxas_Perc", "Taxas_RR", "Taxa_de_embarque",
        "Valor_da_venda", "Valor_descontado", "Valor_RR", "Valor_líquido_da_venda",
        "Comissão_Mínima", "Valor_da_entrada", "Valor_do_saque",
    ]
    for col in colunas_float:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                      .str.replace(",", ".", regex=False)
                      .str.replace(" ", "", regex=False)
                      .replace("", "0")
                      .astype(float)
            )

    # Auditoria
    df["data_processamento"] = datetime.now()
    df["usuario_processamento"] = usuario or "desconhecido"

    return df

def _texto_para_filtragem(df: pd.DataFrame) -> pd.Series:
    """
    Constrói um texto base para busca dos termos bloqueados.
    Priorizamos colunas textuais mais comuns; se alguma não existir, ela é ignorada.
    """
    candidatos = [
        "Resumo_da_operação",
        "Forma_de_pagamento",
        "Canal_de_venda",
        "Status",
    ]
    partes = []
    for c in candidatos:
        if c in df.columns:
            partes.append(df[c].astype(str))
    if not partes:
        # fallback: concatena tudo em string (mais pesado, mas robusto)
        return df.astype(str).agg(" ".join, axis=1)
    txt = partes[0]
    for p in partes[1:]:
        txt = txt.str.cat(p, sep=" ")
    return txt


def classificar_por_bandeira_e_termos(
    df: pd.DataFrame, engine: Engine, ec_id: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Retorna (df_processadas, df_filtradas) aplicando regras:
      - Se coluna 'Bandeira' existir:
          * vai para filtradas quando a bandeira NÃO está ativa para o EC
      - Termos bloqueados (termos_filtraveis.ec = ec_id):
          * se o termo aparecer no texto base, vai para filtradas
      - Caso 'Bandeira' não exista, não filtramos por bandeira (apenas por termos).
    """
    df = df.copy()

    # Bandeiras ativas do EC
    mapa_bandeiras = bandeiras_por_ec(engine, str(ec_id))
    bandeiras_ativas = {b for b, ativo in mapa_bandeiras.items() if int(ativo or 0) == 1}

    # Termos bloqueados (lower)
    termos = [t.strip().lower() for t in termos_listar(engine, str(ec_id))]
    padrao_termos = None
    if termos:
        # regex OR escapado, case-insensitive
        padrao_termos = re.compile("|".join(map(re.escape, termos)), flags=re.IGNORECASE)

    # --- máscaras ---
    # bandeira
    if "Bandeira" in df.columns:
        mask_bandeira_ok = df["Bandeira"].astype(str).isin(bandeiras_ativas)
    else:
        mask_bandeira_ok = pd.Series([True] * len(df), index=df.index)

    # termos
    if padrao_termos:
        base_txt = _texto_para_filtragem(df).str.lower()
        mask_termo_bloqueado = base_txt.str.contains(padrao_termos, na=False)
    else:
        mask_termo_bloqueado = pd.Series([False] * len(df), index=df.index)

    mask_filtrado = (~mask_bandeira_ok) | (mask_termo_bloqueado)

    df_filtradas = df.loc[mask_filtrado].copy()
    df_processadas = df.loc[~mask_filtrado].copy()

    # Flag opcional
    df_filtradas["Filtrado"] = 1
    df_processadas["Filtrado"] = 0

    return df_processadas, df_filtradas


def classificar_e_gravar_vendas(
    engine: Engine,
    df: pd.DataFrame,
    *,
    cliente_id: int,
    ec_id: int,
    contexto: str,
    usuario: str,
    arquivo_origem: str = "",
    remover_duplicadas: bool = True,
) -> Dict[str, int]:
    """
    - Classifica df em processadas/filtradas (bandeiras ativas + termos).
    - Gera processamentoid, preenche colunas de auditoria/cabecalho.
    - Insere em vendas_processadas e vendas_filtradas.
    - (Opcional) remove duplicadas por processamento.

    Retorna: dict com contagens.
    """
    now = datetime.now()
    processamentoid, _ = processamento_gerar_novo_id(engine, ec_id, now)
    processamento_salvar(
        engine,
        ec_id=ec_id,
        cliente_id=cliente_id,
        id_processamento=processamentoid,
        descricao=f"Importação {contexto or '-'} ({arquivo_origem or 'arquivo'})",
        data_processamento=now,
    )

    # Classificação
    df_proc, df_filt = classificar_por_bandeira_e_termos(df, engine, ec_id)

    # Campos de auditoria/cabecalho
    for _df in (df_proc, df_filt):
        if "arquivo_origem" not in _df.columns:
            _df["arquivo_origem"] = arquivo_origem or ""
        _df["processamentoid"] = processamentoid
        _df["cliente_id"] = int(cliente_id)
        _df["ec_id"] = int(ec_id)
        if "data_processamento" not in _df.columns:
            _df["data_processamento"] = now
        if "usuario_processamento" not in _df.columns:
            _df["usuario_processamento"] = usuario or "desconhecido"

    # Gravação
    n_proc = len(df_proc)
    n_filt = len(df_filt)
    if n_proc:
        vendas_processadas_bulk_insert(engine, df_proc)
    if n_filt:
        vendas_filtradas_bulk_insert(engine, df_filt)

    # Dedup (opcional)
    if remover_duplicadas:
        if n_proc:
            vendas_remover_duplicadas(engine, "vendas_processadas", processamentoid)
        if n_filt:
            vendas_remover_duplicadas(engine, "vendas_filtradas", processamentoid)

    return {
        "processadas": n_proc,
        "filtradas": n_filt,
        "total": n_proc + n_filt,
        "processamentoid": processamentoid,
    }
