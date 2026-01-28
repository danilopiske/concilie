from typing import Optional, List
from pydantic import BaseModel
from datetime import date

class RelatorioOptions(BaseModel):
    processamentos: List[dict] # {id: str, label: str}
    adquirentes: List[str]

class RelatorioRequest(BaseModel):
    processamento_id: str
    calc_tipo: Optional[str] = "log_mensal"
    tipo_relatorio: str = "retroativo" # 'mensal' | 'retroativo'
    
    # Filtros
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    adquirente: Optional[str] = None
    
    # Opções
    incluir_filtradas: bool = False
    incluir_recebiveis_filtrados: bool = False
    apenas_com_perdas: bool = False

class RelatorioResponse(BaseModel):
    success: bool
    message: str
    html_path: Optional[str] = None
    excel_path: Optional[str] = None
    sintetico_path: Optional[str] = None
    abusividade_path: Optional[str] = None
    filename: Optional[str] = None
