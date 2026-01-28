
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.abusividade_service import AbusividadeService

router = APIRouter()

@router.get("/analise/{processamento_id:path}", response_model=List[dict])
async def analisar_abusividade_processamento(
    processamento_id: str,
    agrupamento: str = Query('hierarquico', description="Janela de agrupamento: hierarquico (completo), dia, 3dias, semana, mes"),
    db: Session = Depends(get_db)
):
    """
    Retorna lista de transações com variação de taxa para um processamento específico.
    Usado na tela de 'Análise e Correção'.
    """
    service = AbusividadeService(db)
    return service.analisar_processamento(processamento_id, agrupamento)

@router.get("/relatorio", response_model=List[dict])
async def relatorio_abusividade(
    cliente_id: int = Query(..., description="ID do Cliente"),
    ec_id: Optional[str] = Query(None, description="EC ID (Opcional)"),
    data_ini: datetime = Query(..., description="Data Início (ISO 8601)"),
    data_fim: datetime = Query(..., description="Data Fim (ISO 8601)"),
    agrupamento: str = Query("dia", description="agrupamento: dia, mes, periodo_total"),
    db: Session = Depends(get_db)
):
    """
    Gera relatório de abusividade (variação de taxas) por período.
    Usado na tela de 'Relatórios'.
    """
    service = AbusividadeService(db)
    return service.gerar_relatorio(
        cliente_id=cliente_id,
        ec_id=ec_id,
        data_ini=data_ini,
        data_fim=data_fim,
        agrupamento=agrupamento
    )
