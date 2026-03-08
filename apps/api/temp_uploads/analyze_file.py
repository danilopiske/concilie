import pandas as pd
import sys
import os
from pathlib import Path

# Mocking parts of proc_importacao for analysis
def detectar_cabecalho(df, max_scan=25):
    header_keywords = {
        "nsu", "bandeira", "autorização", "ec", "cnpj", "cpf", "valor", "transação", 
        "valor líquido", "valor bruto", "data da transação", "quantidade de parcelas", 
        "taxa", "desconto", "liquido", "bruto", "pagamento", "recebimento", "data"
    }
    best = (0, 0)
    for i in range(min(max_scan, len(df))):
        row = df.iloc[i]
        vals = row.astype(str).fillna("").str.strip()
        non_empty_vals = [v for v in vals if v and v.lower() not in ["nan", "none"]]
        if len(non_empty_vals) < 2: continue
        score = len(non_empty_vals)
        header_text = " ".join(non_empty_vals).lower()
        keyword_matches = 0
        for keyword in header_keywords:
            if keyword in header_text:
                score += 3
                keyword_matches += 1
        if score > best[0]:
            best = (score, i)
    return best

file_path = r"d:\Financial Checker base\Financial_P\apps\api\temp_uploads\91a37626-d665-4911-a763-0439c688d294_03 Vendas 18.11.2022 a 17.11.2023.xlsx"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

try:
    print(f"Analyzing {file_path}")
    xl = pd.ExcelFile(file_path, engine="openpyxl")
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\n--- Analyzing sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=150, engine="openpyxl", dtype=str)
        print(f"First 20 rows of {sheet}:")
        for i, row in df.head(20).iterrows():
            print(f"Row {i}: {row.tolist()[:10]}")
        
        score, idx = detectar_cabecalho(df, max_scan=100)
        print(f"detectar_cabecalho (max_scan=100) result: idx={idx}, score={score}")
        if score > 0:
            print(f"Detected header row ({idx}):")
            print(df.iloc[idx].tolist()[:10])
            
except Exception as e:
    print(f"Error: {e}")
