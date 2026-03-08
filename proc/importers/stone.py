import pandas as pd
import os
from .base import BaseImporter
from typing import Optional

class StoneImporter(BaseImporter):
    @staticmethod
    def detect_score(path: str, df_head: pd.DataFrame) -> int:
        """
        Score detection for Stone layout.
        Criteria: specific headers found in Stone files.
        """
        score = 0
        
        # Characteristic columns for Stone
        cols_lower = [str(c).lower() for c in df_head.columns]
        
        if any("stone" in col for col in cols_lower):
            score += 20
            
        stone_keywords = ["serial number", "valor bruto", "valor líquido", "taxa de antecipação"]
        
        matches = sum(1 for kw in stone_keywords if any(kw in col for col in cols_lower))
        score += matches * 2
        
        # Require at least the word 'stone' or almost all specific keywords
        if score < 6 and not any("stone" in col for col in cols_lower):
            return 0
            
        return score


    def normalize(self):
        """Stone-specific normalization."""
        super().normalize()
        
        if self.df_proc is not None and not self.df_proc.empty:
            # Add Stone-specific normalization if any
            pass

