from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.calculo_task import CalculoTask
from app.models.extrato_cliente import ExtratoCliente
from app.models.import_task import ImportTask
from app.models.processamento import Processamento
from app.models.relatorio_task import RelatorioTask
from app.schemas.dashboard import AtividadeRecenteResponse, DashboardResumo, EventoAtividade

router = APIRouter()


@router.get("/resumo", response_model=DashboardResumo)
def get_dashboard_resumo(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retorna KPIs consolidados do sistema para o dashboard executivo."""
    now = datetime.utcnow()
    mes_atual = now.strftime("%Y-%m")

    # Total e mês atual de processamentos
    total_proc = db.query(func.count(Processamento.id)).scalar() or 0
    proc_mes = (
        db.query(func.count(Processamento.id))
        .filter(func.strftime("%Y-%m", Processamento.data_inicio) == mes_atual)
        .scalar()
        or 0
    )

    # Valor total conciliado (soma de vl_venda em vendas_calculos)
    valor_conciliado_row = db.execute(
        text("SELECT COALESCE(SUM(CAST(vl_venda AS FLOAT)), 0) FROM vendas_calculos")
    ).fetchone()
    valor_conciliado = float(valor_conciliado_row[0]) if valor_conciliado_row else 0.0

    # Alertas de abusividade: processamentos com variação de taxa > 0 por bandeira/forma
    alertas_row = db.execute(
        text("""
            SELECT COUNT(*) FROM (
                SELECT calc_id
                FROM vendas_calculos
                GROUP BY calc_id, bandeira, forma_pagamento
                HAVING MAX(CAST(tx_venda AS FLOAT)) - MIN(CAST(tx_venda AS FLOAT)) > 0.0001
            ) sub
        """)
    ).fetchone()
    alertas = int(alertas_row[0]) if alertas_row else 0

    # Extratos
    extratos_div = (
        db.query(func.count(ExtratoCliente.id))
        .filter(ExtratoCliente.status == "divergente")
        .scalar()
        or 0
    )
    extratos_ag = (
        db.query(func.count(ExtratoCliente.id))
        .filter(ExtratoCliente.status == "aguardando")
        .scalar()
        or 0
    )

    # Relatórios gerados no mês atual
    rel_mes = (
        db.query(func.count(RelatorioTask.id))
        .filter(
            RelatorioTask.status == "SUCCESS",
            func.strftime("%Y-%m", RelatorioTask.created_at) == mes_atual,
        )
        .scalar()
        or 0
    )

    # Último processamento
    ultimo = (
        db.query(Processamento)
        .order_by(Processamento.data_inicio.desc())
        .first()
    )
    ultimo_dict = None
    if ultimo:
        ultimo_dict = {
            "id": ultimo.id,
            "nome_arquivo": ultimo.nome_arquivo,
            "status": ultimo.status,
            "data": ultimo.data_inicio.isoformat() if ultimo.data_inicio else None,
        }

    return DashboardResumo(
        total_processamentos=total_proc,
        processamentos_mes_atual=proc_mes,
        valor_total_conciliado=round(valor_conciliado, 2),
        alertas_abusividade_pendentes=alertas,
        extratos_divergentes=extratos_div,
        extratos_aguardando=extratos_ag,
        relatorios_gerados_mes=rel_mes,
        ultimo_processamento=ultimo_dict,
    )


@router.get("/atividade-recente", response_model=AtividadeRecenteResponse)
def get_atividade_recente(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retorna os últimos 20 eventos de atividade do sistema."""
    eventos: List[EventoAtividade] = []

    # ImportTask
    imports = (
        db.query(ImportTask)
        .order_by(ImportTask.created_at.desc())
        .limit(10)
        .all()
    )
    for t in imports:
        nome_arquivo = ""
        if t.metadata_json and isinstance(t.metadata_json, dict):
            nome_arquivo = t.metadata_json.get("filename", "")
        descricao = f"Importação {'de ' + nome_arquivo if nome_arquivo else ''} iniciada"
        status_map = {"SUCCESS": "ok", "FAILED": "erro", "PENDING": "alerta", "PROCESSING": "alerta"}
        eventos.append(EventoAtividade(
            tipo="importacao",
            descricao=descricao.strip(),
            cliente_nome=f"Cliente {t.cliente_id}",
            created_at=t.created_at or datetime.utcnow(),
            status=status_map.get(t.status, "alerta"),
        ))

    # CalculoTask
    calculos = (
        db.query(CalculoTask)
        .order_by(CalculoTask.created_at.desc())
        .limit(10)
        .all()
    )
    for t in calculos:
        status_map = {"SUCCESS": "ok", "FAILED": "erro", "PENDING": "alerta", "PROCESSING": "alerta"}
        eventos.append(EventoAtividade(
            tipo="calculo",
            descricao=f"Cálculo para processamento {t.processamento_id}",
            cliente_nome=t.usuario or "Sistema",
            created_at=t.created_at or datetime.utcnow(),
            status=status_map.get(t.status, "alerta"),
        ))

    # RelatorioTask
    relatorios = (
        db.query(RelatorioTask)
        .order_by(RelatorioTask.created_at.desc())
        .limit(10)
        .all()
    )
    for t in relatorios:
        status_map = {"SUCCESS": "ok", "FAILED": "erro", "PENDING": "alerta", "PROCESSING": "alerta"}
        eventos.append(EventoAtividade(
            tipo="relatorio",
            descricao=f"Relatório {t.tipo_relatorio or ''} gerado".strip(),
            cliente_nome=t.usuario or "Sistema",
            created_at=t.created_at or datetime.utcnow(),
            status=status_map.get(t.status, "alerta"),
        ))

    # ExtratoCliente
    extratos = (
        db.query(ExtratoCliente)
        .order_by(ExtratoCliente.uploaded_at.desc())
        .limit(10)
        .all()
    )
    for e in extratos:
        status_ev = "ok" if e.status == "importado" else "erro" if e.status == "divergente" else "alerta"
        eventos.append(EventoAtividade(
            tipo="extrato",
            descricao=f"Extrato '{e.nome_arquivo}' {e.status}",
            cliente_nome=f"Cliente {e.cliente_id}",
            created_at=e.uploaded_at or datetime.utcnow(),
            status=status_ev,
        ))

    # Ordenar todos por data desc e retornar top 20
    eventos.sort(key=lambda x: x.created_at, reverse=True)
    return AtividadeRecenteResponse(eventos=eventos[:20])
