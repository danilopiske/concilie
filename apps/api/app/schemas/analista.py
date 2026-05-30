from typing import List, Optional

from pydantic import BaseModel


class AgregacaoBase(BaseModel):
    quantidade: int
    valor_total: float
    valor_medio: Optional[float] = 0.0
    valor_min: Optional[float] = 0.0
    valor_max: Optional[float] = 0.0

class AgregacaoBandeira(AgregacaoBase):
    bandeira: str
    taxa_perc_media: Optional[float] = 0.0
    taxa_valor_total: Optional[float] = 0.0
    vl_rr_total: Optional[float] = 0.0

class AgregacaoFormaPagamento(AgregacaoBase):
    forma_pagamento: str
    taxa_perc_media: Optional[float] = 0.0
    taxa_valor_total: Optional[float] = 0.0
    vl_rr_total: Optional[float] = 0.0

class AgregacaoRecebivel(BaseModel):
    tipo_recebivel: str
    quantidade: int
    valor_total: float

class AgregacaoPeriodo(AgregacaoBase):
    tipo_periodo: str  # mes, trimestre, semestre, ano
    periodo: str

class AgregacaoFormaPagamentoAno(BaseModel):
    ano: str
    forma_pagamento: str
    quantidade: int
    valor_total: float
    valor_medio: float
    taxa_perc_minima: Optional[float] = 0.0
    taxa_perc_maxima: Optional[float] = 0.0

class AgregacaoBandeiraForma(BaseModel):
    bandeira: str
    forma_pagamento: str
    quantidade: int
    valor_total: float
    valor_medio: Optional[float] = 0.0
    taxa_perc_media: Optional[float] = 0.0
    taxa_valor_total: Optional[float] = 0.0
    vl_rr_total: Optional[float] = 0.0

class AnaliseDetalhadaItem(BaseModel):
    periodo: str
    bandeira: str
    forma_pagamento: str
    quantidade: int
    valor_total: float
    valor_medio: float
    taxa_media: float

class ConformidadeBandeiraForma(BaseModel):
    bandeira: str
    forma_pagamento: str
    quantidade: int
    faturamento: float
    cielo_liquido: float
    cielo_taxa_media: Optional[float] = 0.0
    cielo_retido: float
    calc_liquido: float
    calc_taxa_media: Optional[float] = 0.0
    calc_retido: float
    nao_conformidade: float
    nao_conformidade_perc: Optional[float] = 0.0
    perda_rr: Optional[float] = 0.0
