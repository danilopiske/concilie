from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContestacaoGerar(BaseModel):
    cliente_id: int
    processamento_id: int
    periodo_inicio: Optional[date] = None
    periodo_fim: Optional[date] = None

    @field_validator("periodo_fim")
    @classmethod
    def fim_apos_inicio(cls, v: Optional[date], info) -> Optional[date]:
        inicio = info.data.get("periodo_inicio")
        if v is not None and inicio is not None and v < inicio:
            raise ValueError("periodo_fim deve ser >= periodo_inicio")
        return v


class ContestacaoStatusUpdate(BaseModel):
    status: Literal["rascunho", "enviada", "em_analise", "deferida", "indeferida"]


class ContestacaoSaveEdit(BaseModel):
    html_content: str = Field(..., max_length=500_000)


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
