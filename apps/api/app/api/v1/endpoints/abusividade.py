from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import Integer as SAInteger
from sqlalchemy import cast
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.abusividade_task import AbusividadeTask
from app.models.processamento import Processamento
from app.schemas.abusividade import (
    AbusividadeDetalhadaResponse,
    AbusividadeHistoricoItem,
    AbusividadeRelatorioRequest,
    AbusividadeTaskResponse,
)
from app.services.abusividade_relatorio_service import AbusividadeRelatorioService
from app.services.abusividade_service import AbusividadeService

router = APIRouter()


@router.get("/analise/{processamento_id:path}", response_model=List[dict])
async def analisar_abusividade_processamento(
    processamento_id: str,
    agrupamento: str = Query("hierarquico", description="Janela de agrupamento: dia, 3dias, semana, mes, hierarquico"),
    tolerancia: float = Query(0.0, description="Tolerância para diferença de taxas (ex: 0.1)"),
    db: Session = Depends(get_db),
):
    """Retorna lista de transações com variação de taxa para um processamento específico."""
    service = AbusividadeService(db)
    return service.analisar_processamento(processamento_id, agrupamento, tolerancia=tolerancia)


@router.get("/analise-detalhada/{processamento_id:path}", response_model=AbusividadeDetalhadaResponse)
async def analisar_detalhada(
    processamento_id: str,
    db: Session = Depends(get_db),
):
    """Análise detalhada por bandeira/forma_pagamento com granularidade temporal (dia, hora, semana)."""
    service = AbusividadeService(db)
    return service.analisar_detalhado(processamento_id)


@router.get("/relatorio", response_model=List[dict])
async def relatorio_abusividade(
    cliente_id: int = Query(..., description="ID do Cliente"),
    ec_id: Optional[str] = Query(None, description="EC ID (Opcional)"),
    data_ini: datetime = Query(..., description="Data Início (ISO 8601)"),
    data_fim: datetime = Query(..., description="Data Fim (ISO 8601)"),
    agrupamento: str = Query("dia", description="agrupamento: dia, mes, periodo_total"),
    db: Session = Depends(get_db),
):
    """Gera relatório de abusividade (variação de taxas) por período."""
    service = AbusividadeService(db)
    return service.gerar_relatorio(
        cliente_id=cliente_id,
        ec_id=ec_id,
        data_ini=data_ini,
        data_fim=data_fim,
        agrupamento=agrupamento,
    )


@router.post("/gerar-relatorio")
async def gerar_relatorio_async(
    req: AbusividadeRelatorioRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cria task e dispara geração assíncrona do relatório de abusividade."""
    task = AbusividadeTask(processamento_id=req.processamento_id)
    db.add(task)
    db.commit()
    db.refresh(task)

    service = AbusividadeRelatorioService(db)
    background_tasks.add_task(service.gerar_relatorio_async, task.id, req.processamento_id, db)

    return {"task_id": task.id, "status": "pending"}


@router.get("/tasks/{task_id}", response_model=AbusividadeTaskResponse)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
):
    """Retorna status da task de geração de relatório."""
    task = db.query(AbusividadeTask).filter(AbusividadeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    return AbusividadeTaskResponse(
        id=task.id,
        processamento_id=task.processamento_id,
        status=task.status,
        result_path=task.result_path,
        error_message=task.error_message,
        created_at=task.created_at.isoformat() if task.created_at else "",
    )


@router.post("/tasks/{task_id}/save-edit")
def save_edit(
    task_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Salva HTML editado no disco (mesmo padrão de RelatorioService.save_edit)."""
    task = db.query(AbusividadeTask).filter(AbusividadeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    if task.status != "ready" or not task.result_path:
        raise HTTPException(status_code=400, detail="Relatório não disponível para edição")

    html_content = body.get("html_content", "")
    path = Path(task.result_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return {"success": True, "path": str(path)}


@router.get("/tasks/{task_id}/download")
def download_relatorio(
    task_id: str,
    format: str = "html",
    db: Session = Depends(get_db),
):
    """Retorna HTML ou PDF do relatório de abusividade. format=pdf|html"""
    task = db.query(AbusividadeTask).filter(AbusividadeTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    if task.status != "ready" or not task.result_path:
        raise HTTPException(status_code=400, detail="Relatório não disponível")

    file_path = Path(task.result_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    if format == "pdf":
        from app.services.pdf_service import PdfService

        html = file_path.read_text(encoding="utf-8")
        pdf_bytes = PdfService.html_to_pdf(html)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="abusividade_{task.processamento_id}.pdf"'},
        )

    return FileResponse(
        path=str(file_path),
        filename=f"abusividade_{task.processamento_id}.html",
        media_type="text/html",
    )


@router.get("/historico/{cliente_id}", response_model=List[AbusividadeHistoricoItem])
def get_historico_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Retorna histórico de tasks de abusividade para um cliente, ordenado por data decrescente."""
    rows = (
        db.query(AbusividadeTask, Processamento.nome_arquivo)
        .join(
            Processamento,
            cast(AbusividadeTask.processamento_id, SAInteger) == Processamento.id,
        )
        .filter(Processamento.cliente_id == cliente_id)
        .order_by(AbusividadeTask.created_at.desc())
        .all()
    )
    result = []
    for task, nome_arquivo in rows:
        result.append(
            AbusividadeHistoricoItem(
                id=task.id,
                processamento_id=task.processamento_id,
                status=task.status,
                result_path=task.result_path,
                error_message=task.error_message,
                created_at=task.created_at.isoformat() if task.created_at else "",
                nome_arquivo=nome_arquivo,
            )
        )
    return result
