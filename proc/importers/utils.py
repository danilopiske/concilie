import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Any, Dict
import traceback

def log_with_time(message: str, type: str = "INFO"):
    """Logs a message with a visual timestamp indicator."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}][{type}] {message}")

def _to_datetime_pt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", dayfirst=True)

def _to_float_br(s: pd.Series) -> pd.Series:
    # Se já for float, limpa infinitos e retorna
    if pd.api.types.is_float_dtype(s):
        return s.replace([np.inf, -np.inf], np.nan)
    # Se for inteiro, converte para float
    if pd.api.types.is_integer_dtype(s):
        return s.astype(float)
    # Se for string, trata formato brasileiro
    s = s.astype(str)
    # Só remove pontos se houver vírgula (milhar)
    if not s.empty:
        has_comma = s.str.contains(",")
        s1 = s.copy()
        if has_comma.any():
            s1[has_comma] = s1[has_comma].str.replace(".", "", regex=False)
        s1 = s1.str.replace(",", ".", regex=False)
        result = pd.to_numeric(s1, errors="coerce")
    else:
        result = pd.Series([], dtype=float)
    # Limpar valores infinitos do resultado
    return result.replace([np.inf, -np.inf], np.nan)

def detectar_cabecalho(df: pd.DataFrame, max_scan: int = 100) -> int:
    """
    Detecta a linha de cabeçalho usando heurística melhorada
    """
    header_keywords = {
        "nsu", "bandeira", "autorização", "ec", "cnpj", "cpf", "valor", "transação",
        "valor líquido", "valor bruto", "data da transação", "quantidade de parcelas",
        "taxa", "desconto", "liquido", "bruto", "pagamento", "recebimento",
        "banco", "agencia", "conta", "codigo", "numero", "documento",
        "nome", "cliente", "id", "codigo", "lancamento", "recebivel", "venda",
        "status", "situacao", "tipo", "modalidade", "parcela", "cartao",
        "data", "vencimento", "liquidacao", "processamento",
    }

    best = (0, 0)
    log_with_time(f"Analisando {min(max_scan, len(df))} linhas para cabeçalho...", "DEBUG")

    for i in range(min(max_scan, len(df))):
        row = df.iloc[i]
        vals = row.astype(str).fillna("").str.strip()
        non_empty_vals = [v for v in vals if v and v.lower() not in ["nan", "none"]]
        
        if len(non_empty_vals) < 2:
            continue

        score = len(non_empty_vals)
        header_text = " ".join(non_empty_vals).lower()
        keyword_matches = 0

        for keyword in header_keywords:
            if keyword in header_text:
                score += 3
                keyword_matches += 1

        if keyword_matches >= 3:
            score += 5
        elif keyword_matches >= 2:
            score += 2

        data_penalty = 0
        for val in non_empty_vals[:5]:
            val_clean = val.replace(",", "").replace(".", "").replace("/", "").replace("-", "")
            if val_clean.isdigit() and len(val_clean) >= 4:
                data_penalty += 2
            elif "/" in val and len(val) >= 8:
                parts = val.split("/")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    data_penalty += 2

        score -= data_penalty
        if score > best[0]:
            best = (score, i)

    log_with_time(f"Cabeçalho detectado na linha {best[1]} (score: {best[0]})", "DEBUG")
    return best[1]

def safe_read_file(path: str, nrows: Optional[int] = None) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Lê um arquivo de forma robusta.
    """
    ext = Path(path).suffix.lower()
    log_with_time(f"Lendo arquivo: {path} (extensão: {ext})", "DEBUG")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    file_size = os.path.getsize(path)
    if file_size == 0:
        raise ValueError("Arquivo está vazio (0 bytes)")

    # Validação de assinatura
    if ext in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        with open(path, "rb") as f:
            if f.read(2) != b"PK":
                raise ValueError("Arquivo Excel corrompido ou inválido (ZIP signature mismatch).")
    elif ext == ".xls":
        with open(path, "rb") as f:
            if f.read(4) not in [b"\xd0\xcf\x11\xa0", b"\x09\x08\x10\x00"]:
                raise ValueError("Arquivo Excel antigo (.xls) corrompido.")

    # 1) Tenta Excel
    if ext in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        try:
            options = {
                "header": None,
                "engine": "calamine",
                "dtype": str,
                "keep_default_na": False,
                "na_filter": False,
                "nrows": nrows,
            }
            df = pd.read_excel(path, **options)
            
            # Busca cabeçalho nas primeiras 50 linhas
            for idx in range(min(50, len(df))):
                row = df.iloc[idx]
                if len(row) >= 10:
                    row_text = " ".join(str(x).lower() for x in row if str(x).strip())
                    if (("cpf" in row_text or "cnpj" in row_text) and "valor" in row_text and "data" in row_text):
                        log_with_time(f"Cabeçalho encontrado na linha {idx}", "DEBUG")
                        header_names = [str(x).strip() if str(x).strip() else f"Coluna_{i}" for i, x in enumerate(row)]
                        result_df = pd.DataFrame(df.iloc[idx + 1 :].values, columns=header_names, dtype=str)
                        return result_df.fillna(""), 0, result_df.columns.tolist()

            # Se não encontrou pelo padrão fixo, usa detectar_cabecalho
            idx_header = detectar_cabecalho(df)
            header_row = df.iloc[idx_header]
            header_names = [str(col).strip() if str(col).strip() and str(col).strip().lower() not in ["nan", "none"] else f"Coluna_{i}" for i, col in enumerate(header_row)]
            df_with_header = df.iloc[idx_header + 1 :].astype(str)
            df_with_header.columns = header_names
            df_with_header.reset_index(drop=True, inplace=True)
            return df_with_header.fillna(""), idx_header, df_with_header.columns.tolist()

        except Exception as e:
            log_with_time(f"Falha na leitura Excel básica: {e}", "WARNING")
            # Fallback logic could go here if needed, but for modular importers we want cleaner errors

    # 2) Tenta ler como texto (CSV/TXT)
    if ext not in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        try:
            with open(path, "rb") as f:
                raw = f.read(1024 * 1024) if nrows else f.read()
            
            text = raw.decode("utf-8", errors="replace")
            linhas = [l.strip() for l in text.splitlines() if l.strip()]
            
            for sep in [";", ",", "\t", "|"]:
                for i, linha in enumerate(linhas[:20]):
                    valores = linha.split(sep)
                    if len(valores) < 5:
                        continue
                        
                    texto_linha = " ".join(str(v).lower() for v in valores)
                    match_count = sum([
                        any(kw in texto_linha for kw in ["cpf", "cnpj"]),
                        any(kw in texto_linha for kw in ["valor", "venda", "transacao"]),
                        any(kw in texto_linha for kw in ["data", "vencimento"])
                    ])
                    
                    if match_count >= 2:
                        header = [v.strip() for v in valores]
                        data = [l.split(sep) for l in linhas[i + 1 :]]
                        max_cols = len(header)
                        data = [row[:max_cols] if len(row) > max_cols else row + [""] * (max_cols - len(row)) for row in data]
                        df = pd.DataFrame(data, columns=header)
                        return df.fillna(""), i, header
        except Exception as e:
            log_with_time(f"Falha ao ler como texto: {e}", "ERROR")

    raise ValueError(f"Não foi possível ler o arquivo: {ext}")

def preparar_para_tabulator(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Prepara DataFrame para exibição no frontend.
    """
    if df.empty:
        return []
        
    df_preview = df.copy()
    # Converte colunas de data
    for col in df_preview.columns:
        if "data" in col.lower():
            df_preview[col] = pd.to_datetime(df_preview[col], errors="ignore")
            if pd.api.types.is_datetime64_any_dtype(df_preview[col]):
                df_preview[col] = df_preview[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    return df_preview.fillna("").astype(str).to_dict(orient="records")
