import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Any, Dict

def log_with_time(message: str, type: str = "INFO"):
    """Logs a message with a visual timestamp indicator."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{now}][{type}] {message}"
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback for Windows consoles that don't support UTF-8 emojis/chars
        print(msg.encode('ascii', 'replace').decode())
    log_to_debug_file(msg)

def log_to_debug_file(message: str):
    try:
        # Explicitly use encoding='utf-8' to prevent crashes on Windows with emojis or special chars
        with open("e:/Financial_P/apps/api/debug_import.log", "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"CRITICAL: Failed to write to debug log: {e}")

def _to_datetime_pt(s: pd.Series) -> pd.Series:
    res = pd.to_datetime(s, errors="coerce", dayfirst=True)
    # MySQL datetime range is 1000-01-01 to 9999-12-31
    # Clamping dates outside this range to NaT to avoid "Data truncated" error
    if not res.empty:
        mask_too_early = res < pd.Timestamp(1000, 1, 1)
        res[mask_too_early] = pd.NaT
    return res

def _to_float_br(s: pd.Series) -> pd.Series:
    if pd.api.types.is_float_dtype(s):
        return s.replace([np.inf, -np.inf], np.nan)
    if pd.api.types.is_integer_dtype(s):
        return s.astype(float)
    s = s.astype(str)
    if not s.empty:
        has_comma = s.str.contains(",")
        s1 = s.copy()
        if has_comma.any():
            s1[has_comma] = s1[has_comma].str.replace(".", "", regex=False)
        s1 = s1.str.replace(",", ".", regex=False)
        result = pd.to_numeric(s1, errors="coerce")
    else:
        result = pd.Series([], dtype=float)
    return result.replace([np.inf, -np.inf], np.nan)

def detectar_cabecalho(df: pd.DataFrame, max_scan: int = 50) -> Tuple[int, int]:
    """
    Detecta a linha de cabeçalho usando heurística de palavras-chave.
    Retorna (indice_linha, score).
    """
    header_keywords = {
        "nsu", "bandeira", "autorização", "ec", "cnpj", "cpf", "valor", "transação",
        "valor líquido", "valor bruto", "data da transação", "taxa", "desconto", 
        "pagamento", "recebimento", "banco", "agencia", "conta", "venda", "detalhe",
        "cartão", "parcela", "bruto", "líquido", "status", "situação"
    }
    
    best_idx = 0
    max_score = 0
    
    for i in range(min(max_scan, len(df))):
        row = df.iloc[i]
        non_empty_vals = [str(v).strip().lower() for v in row if str(v).strip()]
        
        if len(non_empty_vals) < 2:
            continue
            
        score = sum(1 for v in non_empty_vals if any(kw in v for kw in header_keywords))
        
        # Bônus para densidade de palavras-chave
        if len(non_empty_vals) > 5:
            score += 1

        if score > max_score:
            max_score = score
            best_idx = i
            
    return best_idx, max_score

def safe_read_file(path: str, nrows: Optional[int] = None) -> Tuple[pd.DataFrame, int, List[str]]:
    """
    Lê um arquivo de forma robusta, detectando cabeçalho.
    """
    ext = Path(path).suffix.lower()
    log_with_time(f"Lendo arquivo: {path} (extensão: {ext})", "DEBUG")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    # Validação Básica de Excel
    if ext in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        with open(path, "rb") as f:
            if f.read(2) != b"PK":
                raise ValueError("Arquivo Excel corrompido ou inválido (ZIP signature mismatch).")
    elif ext == ".xls":
        with open(path, "rb") as f:
            if f.read(4) not in [b"\xd0\xcf\x11\xa0", b"\x09\x08\x10\x00"]:
                raise ValueError("Arquivo Excel antigo (.xls) corrompido.")

    # 1) Tenta Excel
    excel_error: Exception | None = None
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
            try:
                df = pd.read_excel(path, **options)
            except Exception:
                try:
                    options["engine"] = "openpyxl"
                    df = pd.read_excel(path, **options)
                except Exception:
                    # Fallback final: leitura direta do XML interno do xlsx via zipfile
                    # Bypassa completamente o openpyxl (evita erros de estilos/inf/NaN)
                    import zipfile, xml.etree.ElementTree as ET
                    NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

                    with zipfile.ZipFile(path, "r") as z:
                        # Shared strings
                        shared: list[str] = []
                        if "xl/sharedStrings.xml" in z.namelist():
                            with z.open("xl/sharedStrings.xml") as f:
                                root_ss = ET.parse(f).getroot()
                                for si in root_ss.findall(f"{{{NS}}}si"):
                                    t_el = si.find(f".//{{{NS}}}t")
                                    shared.append(t_el.text if t_el is not None and t_el.text else "")

                        # Primeira planilha — busca flexível (qualquer case/nome)
                        all_files = z.namelist()
                        sheet_names = [n for n in all_files if n.lower().startswith("xl/worksheets/") and n.lower().endswith(".xml") and "sheet" in n.lower()]
                        if not sheet_names:
                            # Último recurso: qualquer XML dentro de worksheets/
                            sheet_names = [n for n in all_files if "worksheets" in n.lower() and n.lower().endswith(".xml")]
                        if not sheet_names:
                            raise ValueError(f"Nenhuma planilha encontrada. Arquivos no ZIP: {all_files}")
                        with z.open(sorted(sheet_names)[0]) as f:
                            root_ws = ET.parse(f).getroot()

                    rows = []
                    for row_el in root_ws.findall(f".//{{{NS}}}row"):
                        row_data: list[str] = []
                        for c in row_el.findall(f"{{{NS}}}c"):
                            t = c.get("t", "")
                            v_el = c.find(f"{{{NS}}}v")
                            if v_el is None or v_el.text is None:
                                row_data.append("")
                            elif t == "s":
                                try:
                                    row_data.append(shared[int(v_el.text)])
                                except (IndexError, ValueError):
                                    row_data.append(v_el.text)
                            elif t == "inlineStr":
                                t_el = c.find(f".//{{{NS}}}t")
                                row_data.append(t_el.text if t_el is not None and t_el.text else "")
                            elif t == "b":
                                row_data.append("TRUE" if v_el.text == "1" else "FALSE")
                            else:
                                row_data.append(v_el.text)
                        rows.append(row_data)

                    if not rows:
                        raise ValueError("Planilha vazia após leitura via XML.")
                    max_cols = max(len(r) for r in rows)
                    rows = [r + [""] * (max_cols - len(r)) for r in rows]
                    df = pd.DataFrame(rows, dtype=str)

            log_with_time(f"[DEBUG][SAFE_READ] Excel lido. Shape bruto: {df.shape}", "DEBUG")

            # Detectar cabeçalho
            header_idx, score = detectar_cabecalho(df)
            log_with_time(f"[DEBUG][SAFE_READ] Heurística: Linha {header_idx} (score {score})", "DEBUG")

            header_row = df.iloc[header_idx]
            header_names = [str(col).strip() if str(col).strip() and str(col).strip().lower() not in ["nan", "none"] else f"Coluna_{i}" for i, col in enumerate(header_row)]

            df_final = df.iloc[header_idx + 1 :].astype(str)
            df_final.columns = header_names
            df_final.reset_index(drop=True, inplace=True)

            log_with_time(f"[DEBUG][SAFE_READ] DataFrame finalizado. Linhas: {len(df_final)} | Cols: {list(df_final.columns)[:5]}...", "DEBUG")
            return df_final.fillna(""), header_idx, df_final.columns.tolist()

        except Exception as e:
            excel_error = e
            log_with_time(f"Falha na leitura Excel: {e}", "ERROR")

    # 2) Tenta ler como texto (CSV/TXT)
    try:
        with open(path, "rb") as f:
            raw = f.read(1024 * 1024) if nrows else f.read()

        text = raw.decode("utf-8", errors="replace")
        linhas = [l.strip() for l in text.splitlines() if l.strip()]

        for sep in [";", ",", "\t", "|"]:
            for i, linha in enumerate(linhas[:20]):
                valores = [v.strip() for v in linha.split(sep)]
                if len(valores) < 5: continue

                texto_linha = " ".join(v.lower() for v in valores)
                # Heurística simples para CSV
                if any(kw in texto_linha for kw in ["data", "valor", "nsu", "cnpj", "venda"]):
                    data = [l.split(sep) for l in linhas[i + 1 :]]
                    max_cols = len(valores)
                    data = [row[:max_cols] if len(row) > max_cols else row + [""] * (max_cols - len(row)) for row in data]
                    df = pd.DataFrame(data, columns=valores)
                    return df.fillna(""), i, valores
    except Exception as e:
        log_with_time(f"Falha ao ler como texto: {e}", "ERROR")

    # Detectar arquivo protegido por senha (padrão do openpyxl)
    nome_arquivo = Path(path).name
    if excel_error is not None:
        erro_str = str(excel_error).lower()
        if "encrypted" in erro_str or "password" in erro_str or "workbook is encrypted" in erro_str:
            raise ValueError(f"O arquivo '{nome_arquivo}' está protegido por senha e não pode ser lido automaticamente.")
        raise ValueError(f"Não foi possível ler o arquivo '{nome_arquivo}': {excel_error}")

    raise ValueError(f"Formato não suportado ou arquivo vazio: '{nome_arquivo}' ({ext})")

def preparar_para_tabulator(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty: return []
    df_preview = df.copy()
    for col in df_preview.columns:
        if "data" in col.lower():
            df_preview[col] = pd.to_datetime(df_preview[col], errors="ignore")
            if pd.api.types.is_datetime64_any_dtype(df_preview[col]):
                df_preview[col] = df_preview[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_preview.fillna("").astype(str).to_dict(orient="records")
