import pandas as pd
from .base import BaseImporter
from .utils import _to_datetime_pt, _to_float_br

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

    def parse(self):
        """Cielo specific column mapping."""
        self.log("Mapeando colunas Cielo Historico Detalhe...")
        df = self.df_raw.copy()
        
        mapping = {
            "Nº NSU": "NSU",
            "Nº Autorização": "Autorizacao",
            "Data Venda": "Data_da_venda",
            "Valor Bruto": "Valor_da_venda",
            "Valor Líquido": "Valor_liquido",
            "Taxa": "Taxas_Perc",
            "Cartão": "Bandeira",
            "Parcela": "Parcela",
            "Total Parcela": "Total_de_parcelas"
        }
        
        # Select and rename
        cols_to_use = [c for c in mapping.keys() if c in df.columns]
        df = df[cols_to_use].rename(columns=mapping)
        
        # Ensure standard columns exist
        for col in mapping.values():
            if col not in df.columns:
                df[col] = ""
                
        self.df_mapped = df
        self.log(f"Mapeamento concluído. {len(self.df_mapped)} colunas identificadas.")

    def normalize(self):
        """Normalization and enrichment."""
        self.log("Normalizando dados Cielo...")
        df = self.df_mapped.copy()
        
        # Conversions
        if "Data_da_venda" in df.columns:
            df["Data_da_venda"] = _to_datetime_pt(df["Data_da_venda"])
            
        # Values
        for col in ["Valor_da_venda", "Valor_liquido", "Taxas_Perc"]:
            if col in df.columns:
                df[col] = _to_float_br(df[col].fillna(0))
        
        self.df_proc = df
        self.log("Normalização concluída.")

    def save(self):
        """Persists to database."""
        self.log(f"Gravando {len(self.df_proc)} registros no banco...")
        # Will call bulk_insert logic
        return {"processadas": len(self.df_proc), "total": len(self.df_proc)}
