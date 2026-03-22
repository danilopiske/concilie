from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.abusividade_task import AbusividadeTask
from app.models.calculo_task import CalculoTask
from app.models.cliente import Cliente
from app.models.contestacao import Contestacao
from app.models.extrato_cliente import ExtratoCliente
from app.models.import_task import ImportTask
from app.models.processamento import Processamento
from app.models.relatorio_task import RelatorioTask
from app.models.vendas import Venda
from app.schemas.dashboard import (
    AtividadeRecenteResponse,
    DashboardKpis,
    DashboardResumo,
    EventoAtividade,
)

router = APIRouter()


@router.get("/kpis", response_model=DashboardKpis)
def get_dashboard_kpis(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "operador", "visualizador"])),
):
    """Retorna KPIs executivos consolidados do sistema."""
    now = datetime.utcnow()
    inicio_mes = datetime(now.year, now.month, 1)

    # Total de clientes
    total_clientes = db.query(func.count(Cliente.cliente_id)).scalar() or 0

    # Vendas no mês atual
    total_vendas_mes = (
        db.query(func.count(Venda.id))
        .filter(Venda.data_processamento >= inicio_mes)
        .scalar()
        or 0
    )

    # Valor total de vendas no mês
    valor_total_vendas_mes_row = (
        db.query(func.coalesce(func.sum(Venda.valor_venda), 0))
        .filter(Venda.data_processamento >= inicio_mes)
        .scalar()
    )
    valor_total_vendas_mes = float(valor_total_vendas_mes_row or 0)

    # Contestações abertas (não resolvido, fechado ou improcedente)
    total_contestacoes_abertas = (
        db.query(func.count(Contestacao.id))
        .filter(Contestacao.status.notin_(["resolvido", "fechado", "improcedente"]))
        .scalar()
        or 0
    )

    # Taxa de recuperação média (média de tx_venda em vendas_calculos)
    taxa_row = db.execute(
        text("SELECT COALESCE(AVG(CAST(tx_venda AS FLOAT)), 0) FROM vendas_calculos")
    ).fetchone()
    taxa_recuperacao_media = round(float(taxa_row[0]) if taxa_row else 0.0, 4)

    # Divergências abertas
    total_divergencias_abertas = (
        db.query(func.count(ExtratoCliente.id))
        .filter(ExtratoCliente.status == "divergente")
        .scalar()
        or 0
    )

    # Abusividades críticas (status='error')
    total_abusividades_criticas = (
        db.query(func.count(AbusividadeTask.id))
        .filter(AbusividadeTask.status == "error")
        .scalar()
        or 0
    )

    # Processamentos (ImportTask) no mês atual
    processamentos_mes = (
        db.query(func.count(ImportTask.id))
        .filter(ImportTask.created_at >= inicio_mes)
        .scalar()
        or 0
    )

    return DashboardKpis(
        total_clientes=total_clientes,
        total_vendas_mes=total_vendas_mes,
        valor_total_vendas_mes=round(valor_total_vendas_mes, 2),
        total_contestacoes_abertas=total_contestacoes_abertas,
        taxa_recuperacao_media=taxa_recuperacao_media,
        total_divergencias_abertas=total_divergencias_abertas,
        total_abusividades_criticas=total_abusividades_criticas,
        processamentos_mes=processamentos_mes,
    )


@router.get("/resumo", response_model=DashboardResumo)
def get_dashboard_resumo(
    periodo: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "operador", "visualizador"])),
):
    """Retorna KPIs consolidados do sistema para o dashboard executivo."""
    now = datetime.utcnow()
    mes_atual = now.strftime("%Y-%m")
    data_limite = now - timedelta(days=periodo)

    # Total e mês atual de processamentos
    total_proc = db.query(func.count(Processamento.id)).scalar() or 0
    proc_mes = (
        db.query(func.count(Processamento.id))
        .filter(Processamento.data_inicio >= data_limite)
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
    inicio_mes_dt = datetime(now.year, now.month, 1)
    rel_mes = (
        db.query(func.count(RelatorioTask.id))
        .filter(
            RelatorioTask.status == "SUCCESS",
            RelatorioTask.created_at >= inicio_mes_dt,
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
    current_user=Depends(require_role(["admin", "operador", "visualizador"])),
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


@router.get("/atividade-semanal")
def get_atividade_semanal(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin", "operador", "visualizador"])),
):
    """Retorna contagem de importações por semana nas últimas 4 semanas."""
    agora = datetime.utcnow()
    semanas = []
    for i in range(4):
        fim = agora - timedelta(weeks=i)
        inicio = fim - timedelta(weeks=1)
        count = (
            db.query(func.count(ImportTask.id))
            .filter(
                ImportTask.created_at >= inicio,
                ImportTask.created_at < fim,
            )
            .scalar()
            or 0
        )
        semanas.append({
            "label": "Esta" if i == 0 else f"S-{i}",
            "count": count,
        })
    return {"semanas": list(reversed(semanas))}
