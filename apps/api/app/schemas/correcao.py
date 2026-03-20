from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ResumoItem(BaseModel):
    valor: str
    quantidade: int
    valor_total: float

class HistoricoItem(BaseModel):
    id: int
    data_correcao: datetime
    usuario: str
    tipo_correcao: str
    valor_antigo: Optional[str] = None
    valor_novo: Optional[str] = None
    linhas_afetadas: int

class ResumoResponse(BaseModel):
    formas_pagamento: List[ResumoItem]
    bandeiras: List[ResumoItem]
    status: List[ResumoItem]
    recebiveis: List[ResumoItem]

class AtualizarRequest(BaseModel):
    processamento_id: str
    campo: str  # 'forma_pagamento', 'bandeira', 'status', 'lancamento'
    valores_antigos: List[str]
    valor_novo: str

class RemoverRequest(BaseModel):
    processamento_id: str
    campo: str  # 'forma_pagamento', 'bandeira', 'status', 'lancamento'
    valores: List[str]

class FiltrosBCResponse(BaseModel):
    formas: List[str]
    bandeiras: List[str]

class AplicarTaxaBCRequest(BaseModel):
    processamento_id: str
    forma_pagamento: str  # 'TODOS' ou valor específico
    bandeira: str         # 'TODOS' ou valor específico
    data_ini: Optional[str] = None
    data_fim: Optional[str] = None
    nova_taxa: float
    usuario: str = "sistema"
