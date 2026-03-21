from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class CalculoPreviewRequest(BaseModel):
    processamento_id: str
    tipo_taxa: str = "log_mensal"
    usar_taxa_cad: bool = False
    tem_receba_rapido: bool = False

class CalculoRequest(CalculoPreviewRequest):
    substituir: bool = False

class CalculoStats(BaseModel):
    total_vendas: int
    valor_total: Decimal
    valor_medio: Decimal
    min_taxa_orig: Decimal
    max_taxa_orig: Decimal
    media_taxa_orig: Decimal
    vendas_com_cad: int = 0
    vendas_com_log: int = 0
    taxas_rr_count: int = 0

class CalculoResultado(BaseModel):
    id: int
    calc_id: str
    id_venda: int
    data_venda: datetime
    bandeira: str
    forma_pagamento: str
    vl_venda: Decimal
    tx_venda: Decimal
    tx_calc: Optional[Decimal]
    diff_taxa: Optional[Decimal] # tx_venda - tx_calc
    perda: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)

class PeriodoAnalise(BaseModel):
    periodo: str
    quantidade: int
    valor_total: float
    status: Literal["ok", "reduzido", "ausente"]


class AnalisePeriodosResponse(BaseModel):
    processamento_id: str
    total_periodos: int
    periodos_ausentes: int
    periodos_reduzidos: int
    mediana_quantidade: float
    periodos: List[PeriodoAnalise]


class CalculoHistoryItem(BaseModel):
    calc_id: str
    calc_tipo: str
    calc_usuario: str
    calc_data: datetime
    total_registros: int
    total_valor: Optional[Decimal] = Decimal(0)
    perda_total: Optional[Decimal] = Decimal(0)

    model_config = ConfigDict(from_attributes=True)
