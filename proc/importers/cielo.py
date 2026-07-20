import pandas as pd
from .base import BaseImporter

class CieloHistoricoDetalheImporter(BaseImporter):
    @staticmethod
    def detect_score(path: str, head_df: pd.DataFrame) -> int:
        """Detects if the file matches Cielo Historico Detalhe layout."""
        if head_df.empty: return 0
        cols_text = " ".join(head_df.columns).lower()
        # Look for specific Cielo Detalhe headers
        keywords = ["resumo de venda", "nº pv", "nº rlv", "nº ro", "cartão", "nº nsu"]
        score = sum(3 for kw in keywords if kw in cols_text)
        return score

    def normalize(self, progress_callback=None):
        """Normalization and enrichment."""
        super().normalize(progress_callback)
        # Cielo specific extra normalization here if needed
        # (Standard columns already handled by super)

    def save(self, progress_callback=None):
        """Persists to database."""
        result = super().save(progress_callback)
        return {
            "processadas": result.get("vendas", 0),
            "total": result.get("total", 0),
            "processamentoid": result.get("processamentoid")
        }
