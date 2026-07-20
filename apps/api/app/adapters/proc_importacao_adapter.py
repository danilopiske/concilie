"""
Adapter temporário para proc.proc_importacao.
Centraliza o acoplamento legado em um único ponto.
Será removido quando L-01 migrar proc/ → app/ completamente.
"""

from proc.proc_importacao import (
    classificar_e_gravar_recebiveis,
    classificar_e_gravar_vendas,
    is_multisheet_rede_file,
    normalizar_dataframe_recebiveis,
    normalizar_dataframe_vendas,
    preparar_dataframe_de_arquivo,
    read_file_with_header,
    safe_read_multisheet_file,
)

__all__ = [
    "classificar_e_gravar_recebiveis",
    "classificar_e_gravar_vendas",
    "is_multisheet_rede_file",
    "normalizar_dataframe_recebiveis",
    "normalizar_dataframe_vendas",
    "preparar_dataframe_de_arquivo",
    "read_file_with_header",
    "safe_read_multisheet_file",
]
