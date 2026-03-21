from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class ContestacaoGerar(BaseModel):
    cliente_id: int
    processamento_id: int


class ContestacaoStatusUpdate(BaseModel):
    status: Literal["rascunho", "enviada", "em_analise", "deferida", "indeferida"]


class ContestacaoSaveEdit(BaseModel):
    html_content: str


class ContestacaoResponse(BaseModel):
    id: str
    cliente_id: int
    processamento_id: Optional[int]
    adquirente: str
    periodo_inicio: date
    periodo_fim: date
    valor_excesso_total: float
    status: str
    html_carta: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
