from .base import BaseImporter
from .cielo import CieloHistoricoDetalheImporter
from .rede import RedeImporter
from .stone import StoneImporter
from .generic import GenericDeParaImporter
from .utils import log_with_time, safe_read_file
import os
from typing import Optional, List, Type

class ImporterFactory:
    _importers: List[Type[BaseImporter]] = [
        CieloHistoricoDetalheImporter,
        RedeImporter,
        StoneImporter,
        GenericDeParaImporter, # Fallback strategy
    ]

    @classmethod
    def get_importer(cls, engine, path, ec_id, cliente_id, contexto, usuario, tipo_arquivo="V") -> Optional[BaseImporter]:
        """Detects the best matching importer for the file."""
        log_with_time(f"Tentando detectar layout modular para {path}...", "DEBUG")
        
        # Read the first few rows to detect layout
        try:
            # We only need a small chunk for detection
            df_head, _, _ = safe_read_file(path, nrows=100)
            log_with_time(f"[DEBUG][FACTORY] Arquivo: {os.path.basename(path)} - Colunas lidas: {list(df_head.columns)[:10]}...", "DEBUG")
        except Exception as e:
            log_with_time(f"Erro ao ler cabeçalho para detecção: {str(e)}", "ERROR")
            return None

        best_match = (0, None)
        for importer_cls in cls._importers:
            score = importer_cls.detect_score(path, df_head)
            log_with_time(f"Score para {importer_cls.__name__}: {score}", "DEBUG")
            if score > best_match[0]:
                best_match = (score, importer_cls)

        if best_match[1]:
            # Reduced threshold from 10 to 3 to be more flexible with header variations
            is_generic = best_match[1] == GenericDeParaImporter
            if best_match[0] >= 3 or is_generic:
                log_with_time(f"Layout detectado: {best_match[1].__name__} (score: {best_match[0]})", "SUCCESS")
                return best_match[1](engine, ec_id, cliente_id, contexto, usuario, tipo_arquivo)
        
        log_with_time(f"Nenhum layout compatível detectado para {os.path.basename(path)}.", "WARNING")
        return None
