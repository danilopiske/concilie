from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ProcessamentoBase(BaseModel):
    cliente_id: Optional[int] = None
    tipo_arquivo: str
    nome_arquivo: str
    status: str = "Pendente"
    linhas_total: int = 0
    linhas_processadas: int = 0
    log_info: Optional[Dict[str, Any]] = None
    mensagem_erro: Optional[str] = None

class ProcessamentoResponse(ProcessamentoBase):
    id: int | str
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    linhas_sucesso: int = 0
    linhas_erro: int = 0
    criado_por: Optional[str] = None

    # New Fields for Correction Context
    ec_id: Optional[str] = None
    data_min: Optional[datetime] = None
    data_max: Optional[datetime] = None
    qtd_processadas: Optional[int] = 0
    qtd_filtradas: Optional[int] = 0
    total_linhas: Optional[int] = 0


    model_config = ConfigDict(from_attributes=True)

class ProcessamentoFilter(BaseModel):
    data_ini: Optional[str] = None
    data_fim: Optional[str] = None
    status: Optional[str] = None
    cliente_id: Optional[int] = None
