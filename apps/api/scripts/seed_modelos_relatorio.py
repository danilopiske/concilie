"""
Seed inicial para tabela modelos_relatorio.
Executar uma vez após init_db:
  cd apps/api && python scripts/seed_modelos_relatorio.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models import Base, ModeloRelatorio

MODELOS = [
    {
        "nome": "Analítico",
        "template_arquivo": "template_relatorio.html",
        "tipo": "html",
        "secoes_necessarias": json.dumps([
            "vendas_calculos", "perdas_semestre", "taxas_minmax",
            "contagem_transacoes", "recebiveis_sumario", "dados_bancarios", "evidencias",
            "vendas_filtradas", "recebiveis_filtrados"
        ]),
        "ativo": True,
    },
    {
        "nome": "Analítico Sem Capa",
        "template_arquivo": "template_relatorio_sem_capa.html",
        "tipo": "html",
        "secoes_necessarias": json.dumps([
            "vendas_calculos", "perdas_semestre", "taxas_minmax",
            "contagem_transacoes", "recebiveis_sumario", "dados_bancarios", "evidencias",
            "vendas_filtradas", "recebiveis_filtrados"
        ]),
        "ativo": True,
    },
    {
        "nome": "Sintético",
        "template_arquivo": "template_relatorio_sintetico.html",
        "tipo": "html",
        "secoes_necessarias": json.dumps([
            "vendas_calculos", "perdas_semestre", "taxas_minmax",
            "contagem_transacoes", "dados_bancarios", "recebiveis_sumario"
        ]),
        "ativo": True,
    },
    {
        "nome": "Excel",
        "template_arquivo": "template_excel.xml",
        "tipo": "xml",
        "secoes_necessarias": json.dumps([
            "vendas_calculos", "perdas_semestre", "taxas_minmax",
            "contagem_transacoes", "dados_bancarios",
            "vendas_filtradas", "recebiveis_filtrados"
        ]),
        "ativo": True,
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existentes = db.query(ModeloRelatorio).count()
        if existentes > 0:
            print(f"[SEED] Já existem {existentes} modelos cadastrados. Pulando seed.")
            return

        for dados in MODELOS:
            modelo = ModeloRelatorio(**dados)
            db.add(modelo)

        db.commit()
        print(f"[SEED] {len(MODELOS)} modelos inseridos com sucesso.")
    except Exception as e:
        db.rollback()
        print(f"[SEED] Erro: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
