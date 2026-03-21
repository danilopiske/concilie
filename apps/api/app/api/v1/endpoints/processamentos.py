import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.processamento_repository import ProcessamentoRepository
from app.schemas.processamento import ProcessamentoFilter, ProcessamentoResponse

router = APIRouter()


@router.get("/exportar-csv")
def exportar_processamentos_csv(
    cliente_id: Optional[int] = Query(None),
    periodo: int = Query(90, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """Exporta processamentos filtrados como CSV."""
    data_limite = datetime.now(timezone.utc) - timedelta(days=periodo)
    data_ini_str = data_limite.strftime("%Y-%m-%d")

    repo = ProcessamentoRepository(db)
    filtro = ProcessamentoFilter(
        cliente_id=cliente_id,
        data_ini=data_ini_str,
    )
    items = repo.listar(skip=0, limit=10000, filtros=filtro, simple=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "cliente_id",
        "tipo_arquivo",
        "nome_arquivo",
        "status",
        "data_inicio",
        "data_fim",
        "linhas_processadas",
        "linhas_sucesso",
        "linhas_erro",
        "criado_por",
    ])
    for item in items:
        writer.writerow([
            item.id,
            item.cliente_id,
            item.tipo_arquivo,
            item.nome_arquivo,
            item.status,
            item.data_inicio.isoformat() if item.data_inicio else "",
            item.data_fim.isoformat() if item.data_fim else "",
            item.linhas_processadas,
            item.linhas_sucesso,
            item.linhas_erro,
            item.criado_por or "",
        ])

    output.seek(0)
    filename = f"processamentos_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/", response_model=List[ProcessamentoResponse])
def listar_processamentos(
    cliente_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    periodo: int = Query(90, ge=1, le=3650),
    simple: bool = False,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    data_limite = datetime.now(timezone.utc) - timedelta(days=periodo)
    data_ini_str = data_limite.strftime("%Y-%m-%d")

    repo = ProcessamentoRepository(db)
    filtro = ProcessamentoFilter(
        cliente_id=cliente_id,
        status=status,
        data_ini=data_ini_str,
    )
    return repo.listar(skip=skip, limit=limit, filtros=filtro, simple=simple)


@router.post("/batch-delete")
def deletar_processamentos(
    ids: List[str],
    db: Session = Depends(get_db)
):
    repo = ProcessamentoRepository(db)
    return {"success": repo.deletar_lista(ids), "count": len(ids)}


@router.get("/{processamento_id}/financeiro")
def sumario_financeiro(
    processamento_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Sumário financeiro de um processamento.

    Retorna totais agregados de vendas, taxas cobradas, taxas contratadas
    e a diferença financeira (valor potencial a contestar).
    """
    from sqlalchemy import func

    from app.models.vendas_calculos import VendasCalculos

    resultado = db.query(
        func.count(VendasCalculos.id).label("count_transacoes"),
        func.sum(VendasCalculos.vl_venda).label("total_vendas"),
        func.sum(VendasCalculos.desc_venda).label("total_taxa_cobrada"),
        func.sum(VendasCalculos.desc_calc).label("total_taxa_contratada"),
        func.sum(VendasCalculos.perda).label("total_diferenca"),
    ).filter(VendasCalculos.calc_id == processamento_id).one()

    count_transacoes = int(resultado.count_transacoes or 0)
    total_vendas = float(resultado.total_vendas or 0.0)
    total_taxa_cobrada = float(resultado.total_taxa_cobrada or 0.0)
    total_taxa_contratada = float(resultado.total_taxa_contratada or 0.0)
    total_diferenca = float(resultado.total_diferenca or 0.0)

    taxa_media_cobrada_pct = (
        round(total_taxa_cobrada / total_vendas * 100, 4) if total_vendas > 0 else 0.0
    )
    taxa_media_contratada_pct = (
        round(total_taxa_contratada / total_vendas * 100, 4) if total_vendas > 0 else 0.0
    )

    return {
        "processamento_id": processamento_id,
        "count_transacoes": count_transacoes,
        "total_vendas_rs": round(total_vendas, 2),
        "total_taxa_cobrada_rs": round(total_taxa_cobrada, 2),
        "total_taxa_contratada_rs": round(total_taxa_contratada, 2),
        "diferenca_rs": round(total_diferenca, 2),
        "taxa_media_cobrada_pct": taxa_media_cobrada_pct,
        "taxa_media_contratada_pct": taxa_media_contratada_pct,
        "tem_dados": count_transacoes > 0,
    }


@router.get("/{processamento_id}/detalhes")
def detalhes_processamento(
    processamento_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Consolida todas as informações de um processamento."""
    from app.models.abusividade_task import AbusividadeTask
    from app.models.calculo_task import CalculoTask
    from app.models.relatorio_task import RelatorioTask

    def _dt(val: Any) -> Optional[str]:
        return val.isoformat() if val and hasattr(val, "isoformat") else val

    def _serializar_calculo(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "usuario": t.usuario,
            "progress": t.progress,
        }

    def _serializar_relatorio(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "usuario": t.usuario,
            "progress": t.progress,
            "tipo_relatorio": t.tipo_relatorio,
            "result_path": t.result_path,
        }

    def _serializar_abusividade(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "result_path": t.result_path,
        }

    calculos = (
        db.query(CalculoTask)
        .filter(CalculoTask.processamento_id == processamento_id)
        .order_by(CalculoTask.created_at.desc())
        .all()
    )
    relatorios = (
        db.query(RelatorioTask)
        .filter(RelatorioTask.processamento_id == processamento_id)
        .order_by(RelatorioTask.created_at.desc())
        .all()
    )
    abusividades = (
        db.query(AbusividadeTask)
        .filter(AbusividadeTask.processamento_id == processamento_id)
        .order_by(AbusividadeTask.created_at.desc())
        .all()
    )

    todas_tasks = (
        [t.status for t in calculos]
        + [t.status for t in relatorios]
    )

    status_geral = "sem_dados"
    if todas_tasks:
        if any(s in ("PROCESSING", "PENDING", "pending", "processing") for s in todas_tasks):
            status_geral = "em_andamento"
        elif all(s in ("SUCCESS", "ready") for s in todas_tasks):
            status_geral = "concluido"
        elif any(s in ("FAILED", "error") for s in todas_tasks):
            status_geral = "com_erro"
        else:
            status_geral = "parcial"

    return {
        "processamento_id": processamento_id,
        "status_geral": status_geral,
        "totais": {
            "importacoes": 0,
            "calculos": len(calculos),
            "relatorios": len(relatorios),
            "abusividades": len(abusividades),
        },
        "importacoes": [],
        "calculos": [_serializar_calculo(t) for t in calculos[:5]],
        "relatorios": [_serializar_relatorio(t) for t in relatorios[:5]],
        "abusividades": [_serializar_abusividade(t) for t in abusividades[:5]],
    }
