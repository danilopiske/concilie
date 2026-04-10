"""
Atualiza o modelo Excel no banco para incluir vendas_filtradas e recebiveis_filtrados.
Executar: cd apps/api && python scripts/update_modelo_excel.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import ModeloRelatorio

NOVAS_SECOES = [
    "vendas_calculos", "perdas_semestre", "taxas_minmax",
    "contagem_transacoes", "dados_bancarios",
    "vendas_filtradas", "recebiveis_filtrados"
]

db = SessionLocal()
try:
    modelo = db.query(ModeloRelatorio).filter(ModeloRelatorio.nome == "Excel").first()
    if not modelo:
        print("[UPDATE] Modelo 'Excel' não encontrado.")
    else:
        modelo.secoes_necessarias = json.dumps(NOVAS_SECOES)
        db.commit()
        print(f"[UPDATE] Modelo 'Excel' (id={modelo.id}) atualizado com seções: {NOVAS_SECOES}")
finally:
    db.close()
