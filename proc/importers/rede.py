import pandas as pd
import os
from .base import BaseImporter
from .utils import log_with_time
from typing import Optional

class RedeImporter(BaseImporter):
    @staticmethod
    def detect_score(path: str, df_head: pd.DataFrame) -> int:
        """
        Score detection for Rede layout.
        Criteria: multi-sheet with 'capa' or specific columns.
        """
        score = 0
        
        # Check if it's a multisheet rede file using legacy logic
        try:
            from proc.proc_importacao import is_multisheet_rede_file
            if is_multisheet_rede_file(path):
                return 100 # High confidence if legacy detection matches
        except:
            pass

        # Column-based detection for single-sheet Rede
        cols_lower = [str(c).lower() for c in df_head.columns]
        if "modalidade" in cols_lower and "tipo" in cols_lower:
            score += 10
        
        return score

    def read(self, path: str, nrows: Optional[int] = None, progress_callback=None):
        """Rede-specific read: handles multi-sheet logic."""
        self.arquivo_origem = os.path.basename(path)
        
        try:
            from proc.proc_importacao import is_multisheet_rede_file, safe_read_multisheet_file
            self.is_multisheet = is_multisheet_rede_file(path)
            
            if self.is_multisheet:
                self.log("Arquivo multi-planilhas detectado. Processando todas as abas.")
                if progress_callback: progress_callback(10, "Lendo arquivo multi-planilhas Rede...")
                self.multisheet_data = safe_read_multisheet_file(
                    path, self.tipo_arquivo, self.engine, self.contexto, nrows=nrows
                )
                self.df_raw = pd.DataFrame() # Will be populated in parse
                if progress_callback: progress_callback(30, "Abas lidas com sucesso.")
            else:
                super().read(path, nrows, progress_callback)
        except Exception as e:
            self.log(f"Erro na leitura Rede: {str(e)}", "ERROR")
            raise e

    def parse(self, progress_callback=None):
        """Rede-specific parse: concatenates sheets if multi-sheet."""
        if not hasattr(self, "is_multisheet") or not self.is_multisheet:
            super().parse(progress_callback)
            self._aplicar_concatenacao_rede()
            return

        # Multi-sheet logic
        self.log(f"Processando {len(self.multisheet_data)} abas...")
        if progress_callback: progress_callback(40, "Processando abas Rede...")
        combined_dfs = []
        
        from conf.funcoesbd import depara_carregar_mapa_completo
        from proc.proc_importacao import aplicar_regras_depara
        regras = depara_carregar_mapa_completo(self.engine, contexto=self.contexto, tipo_origem=self.tipo_arquivo)

        total_sheets = len(self.multisheet_data)
        for i, (sheet_name, sheet_info) in enumerate(self.multisheet_data.items()):
            df_sheet = sheet_info["df"]
            if df_sheet is not None and not df_sheet.empty:
                self.log(f"Mapeando aba: {sheet_name}")
                if progress_callback: 
                    p = 40 + int((i / total_sheets) * 30)
                    progress_callback(p, f"Mapeando aba: {sheet_name}")
                df_mapped, _ = aplicar_regras_depara(df_sheet, regras)
                if not df_mapped.empty:
                    df_mapped["planilha_origem"] = sheet_name
                    combined_dfs.append(df_mapped)
        
        if combined_dfs:
            self.df_proc = pd.concat(combined_dfs, ignore_index=True)
            self._aplicar_concatenacao_rede()
            self.log(f"Combinação de abas concluída: {len(self.df_proc)} linhas.")
        else:
            self.df_proc = pd.DataFrame()

    def _aplicar_concatenacao_rede(self):
        """Legacy logic: Modalidade + Tipo = Forma_de_pagamento with accent normalization."""
        if self.df_proc is None or self.df_proc.empty:
            return

        cols_lower = {str(c).lower(): c for c in self.df_proc.columns}
        col_modalidade = cols_lower.get("modalidade")
        col_tipo = cols_lower.get("tipo")
        
        # Determine if we should apply concatenation
        tem_forma = "Forma_de_pagamento" in self.df_proc.columns
        
        if col_modalidade and col_tipo:
            self.log("Aplicando regra de concatenação Rede: Modalidade + Tipo.")
            self.df_proc["Forma_de_pagamento"] = (
                self.df_proc[col_modalidade].astype(str).str.upper().str.strip()
                + " "
                + self.df_proc[col_tipo].astype(str).str.upper().str.strip()
            )
            
            # Legacy accent normalization
            self.df_proc["Forma_de_pagamento"] = (
                self.df_proc["Forma_de_pagamento"]
                .str.replace("À", "A", regex=False)
                .str.replace("Á", "A", regex=False)
                .str.replace("Ã", "A", regex=False)
                .str.replace("É", "E", regex=False)
                .str.replace("Ê", "E", regex=False)
                .str.replace("Í", "I", regex=False)
                .str.replace("Ó", "O", regex=False)
                .str.replace("Ô", "O", regex=False)
                .str.replace("Ú", "U", regex=False)
                .str.replace("Ç", "C", regex=False)
                .str.replace("  ", " ", regex=False)
            )

    def normalize(self, progress_callback=None):
        """Standard normalization + Rede specific adjustments."""
        super().normalize(progress_callback)
        # Additional normalization if needed

