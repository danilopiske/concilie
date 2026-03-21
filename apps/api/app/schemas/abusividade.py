from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class GranularidadeItem(BaseModel):
    label: str
    taxa_media: float
    quantidade: int
    variacao_vs_media: float
    status: Literal["normal", "atencao", "critico"]


class BandeiraFormaPagamento(BaseModel):
    bandeira: str
    forma_pagamento: str
    taxa_media_geral: float
    por_dia_semana: List[GranularidadeItem]
    por_hora: List[GranularidadeItem]
    por_semana_mes: List[GranularidadeItem]


class AbusividadeDetalhadaResponse(BaseModel):
    processamento_id: str
    total_transacoes: int
    grupos: List[BandeiraFormaPagamento]


class AbusividadeRelatorioRequest(BaseModel):
    processamento_id: str
    incluir_editor: bool = True


class AbusividadeTaskResponse(BaseModel):
    id: str
    processamento_id: str
    status: str
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AbusividadeHistoricoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    processamento_id: str
    status: str
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    nome_arquivo: Optional[str] = None
