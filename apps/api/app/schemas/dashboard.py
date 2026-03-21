from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class DashboardResumo(BaseModel):
    total_processamentos: int
    processamentos_mes_atual: int
    valor_total_conciliado: float
    alertas_abusividade_pendentes: int
    extratos_divergentes: int
    extratos_aguardando: int
    relatorios_gerados_mes: int
    ultimo_processamento: Optional[dict] = None


class EventoAtividade(BaseModel):
    tipo: Literal["importacao", "calculo", "relatorio", "abusividade", "extrato"]
    descricao: str
    cliente_nome: str
    created_at: datetime
    status: str  # "ok" | "alerta" | "erro"


class AtividadeRecenteResponse(BaseModel):
    eventos: List[EventoAtividade]
