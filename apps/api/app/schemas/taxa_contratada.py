from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class TaxaContratadaCreate(BaseModel):
    bandeira: str
    modalidade: str
    taxa_contratada: float
    vigencia_inicio: date
    vigencia_fim: Optional[date] = None
    observacao: Optional[str] = None


class TaxaContratadaUpdate(BaseModel):
    bandeira: Optional[str] = None
    modalidade: Optional[str] = None
    taxa_contratada: Optional[float] = None
    vigencia_inicio: Optional[date] = None
    vigencia_fim: Optional[date] = None
    observacao: Optional[str] = None


class TaxaContratadaResponse(BaseModel):
    id: int
    cliente_id: int
    bandeira: str
    modalidade: str
    taxa_contratada: float
    vigencia_inicio: date
    vigencia_fim: Optional[date] = None
    observacao: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DesvioTaxa(BaseModel):
    bandeira: str
    modalidade: str
    taxa_contratada: float
    taxa_media_cobrada: float
    desvio_percentual: float
    valor_total_transacoes: float
    valor_excesso_estimado: float
    status: Literal["ok", "atencao", "abusivo"]
    quantidade_transacoes: int


class ComparacaoResponse(BaseModel):
    cliente_id: int
    processamento_id: str
    desvios: List[DesvioTaxa]
    valor_excesso_total: float


class HistoricoDesvioItem(BaseModel):
    processamento_id: str
    data_processamento: Optional[datetime]
    desvios: List[DesvioTaxa]
    valor_excesso_total: float


class HistoricoDesviosResponse(BaseModel):
    cliente_id: int
    historico: List[HistoricoDesvioItem]
