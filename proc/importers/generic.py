import pandas as pd
from .base import BaseImporter

class GenericDeParaImporter(BaseImporter):
    """
    Fallback importer that leverages the standard De-Para rules 
    configured in the database via the UI.
    """
    @staticmethod
    def detect_score(path: str, head_df: pd.DataFrame) -> int:
        """
        Generic importer acts as a universal fallback with a baseline score.
        It will only be used if no specialized importer (Cielo, Rede, etc.) 
        matches with a higher score.
        """
        return 1 # Baseline score
    
    def normalize(self, progress_callback=None):
        """Applies basic normalization after De-Para mapping."""
        super().normalize(progress_callback)
        if self.df_proc is not None and not self.df_proc.empty:
            # Add any universal normalization steps here if needed
            pass
