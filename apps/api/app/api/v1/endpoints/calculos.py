import io
import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
from fastapi import BackgroundTasks

from app.core.database import get_db
from app.repositories.calculo_repository import CalculoRepository
from app.schemas.calculo import (
    CalculoHistoryItem,
    CalculoPreviewRequest,
    CalculoRequest,
    CalculoResultado,
    CalculoStats,
)
from app.services.calculo_service import CalculoService
from app.services.reconciliation_core import ReconciliationCore

router = APIRouter()

@router.post("/preview", response_model=CalculoStats)
def preview_calculo(req: CalculoPreviewRequest, db: Session = Depends(get_db)):
    repo = CalculoRepository(db)
    return repo.preview_calculo(req)

@router.get("/historico-calculos", response_model=List[CalculoHistoryItem])
async def get_historico_calculos(
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de cálculos únicos salvos no banco.
    """
    repo = CalculoRepository(db)
    return repo.listar_historico(skip=skip, limit=limit)

@router.post("/processar")
def processar_calculo(req: CalculoRequest, db: Session = Depends(get_db)):
    """
    Runs calculation synchronously using the high-performance Polars engine.
    For very large datasets, use /processar-async.
    """
    try:
        repo = CalculoRepository(db)
        custom_id = repo.processar_calculo(req)

        engine = db.get_bind()
        result = ReconciliationCore.calculate_rates(
            engine=engine,
            proc_id=req.processamento_id,
            tipo_taxa=req.tipo_taxa,
            usar_taxa_cad=req.usar_taxa_cad,
            tem_receba_rapido=req.tem_receba_rapido,
            custom_calc_id=custom_id
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return {
            "status": "success",
            "message": f"Cálculo processado com sucesso. {result.get('rows')} registros.",
            "calc_id": custom_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/processar-async")
async def processar_calculo_async(
    req: CalculoRequest,
    background_tasks: BackgroundTasks,
    usuario: str = "api_user",
    db: Session = Depends(get_db)
):
    """Starts calculation in background and returns a task_id."""
    service = CalculoService(db)
    task = service.create_calculo_task(
        processamento_id=req.processamento_id,
        tipo_taxa=req.tipo_taxa,
        usuario=usuario,
        usar_taxa_cad=req.usar_taxa_cad,
        tem_receba_rapido=req.tem_receba_rapido,
        substituir=req.substituir
    )

    background_tasks.add_task(service.run_async_calculo, task.id)

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Cálculo iniciado em segundo plano."
    }

@router.get("/task/{task_id:path}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Returns current calculation task status."""
    service = CalculoService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "updated_at": task.updated_at,
        "processamento_id": task.processamento_id,
        "tipo_taxa": task.tipo_taxa
    }

@router.get("/resultados/{calc_id:path}", response_model=List[CalculoResultado])
def listar_resultados(
    calc_id: str,
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    logger.debug("Buscando resultados para calc_id: %s", calc_id)
    repo = CalculoRepository(db)
    return repo.listar_resultados(calc_id, skip, limit)


@router.get("/export/{calc_id:path}")
def export_calculo_excel(calc_id: str, db: Session = Depends(get_db)):
    """Exporta todos os resultados de um cálculo para Excel (2 sheets: Resumo + Detalhamento)."""
    from app.models.vendas_calculos import VendasCalculos

    registros = (
        db.query(VendasCalculos)
        .filter(VendasCalculos.calc_id == calc_id)
        .order_by(VendasCalculos.perda.asc())
        .all()
    )
    if not registros:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado para este cálculo.")

    wb = Workbook()

    # ── Cores e estilos ─────────────────────────────────────────────────────
    HEADER_FILL = PatternFill("solid", fgColor="223A6B")
    HEADER_FONT = Font(bold=True, color="FFFFFF")
    LOSS_FILL   = PatternFill("solid", fgColor="FFE5E5")
    TOTAL_FONT  = Font(bold=True)

    def _style_header(ws, row=1):
        for cell in ws[row]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center")

    def _autofit(ws):
        for col_cells in ws.columns:
            length = max((len(str(c.value or "")) for c in col_cells), default=10)
            ws.column_dimensions[get_column_letter(col_cells[0].column)].width = min(length + 4, 40)

    # ── Sheet 1: Resumo ──────────────────────────────────────────────────────
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"

    total_valor   = sum(float(r.vl_venda or 0) for r in registros)
    total_perda   = sum(float(r.perda or 0) for r in registros)
    com_perda     = sum(1 for r in registros if r.perda is not None and r.perda < 0)
    media_tx_vend = sum(float(r.tx_venda or 0) for r in registros) / len(registros)
    media_tx_calc = (
        sum(float(r.tx_calc or 0) for r in registros if r.tx_calc is not None)
        / max(sum(1 for r in registros if r.tx_calc is not None), 1)
    )

    resumo_rows = [
        ("Parâmetro", "Valor"),
        ("Cálculo ID", registros[0].calc_id),
        ("Tipo de Taxa", registros[0].calc_tipo or "-"),
        ("Usuário", registros[0].calc_usuario or "-"),
        ("Data do Cálculo", str(registros[0].calc_data)[:19] if registros[0].calc_data else "-"),
        ("", ""),
        ("Total de Registros", len(registros)),
        ("Total Valor de Venda (R$)", round(total_valor, 2)),
        ("Total Perda/Ganho (R$)", round(total_perda, 2)),
        ("Registros com Perda", com_perda),
        ("Média Taxa Cobrada (%)", round(media_tx_vend, 4)),
        ("Média Taxa Calculada (%)", round(media_tx_calc, 4)),
    ]

    for row in resumo_rows:
        ws_resumo.append(list(row))

    _style_header(ws_resumo, row=1)
    _autofit(ws_resumo)

    # ── Sheet 2: Detalhamento ────────────────────────────────────────────────
    ws_det = wb.create_sheet("Detalhamento")

    headers = [
        "Data Venda", "Bandeira", "Forma Pagamento", "Adquirente",
        "NSU", "Cód. Autorização", "Vl. Venda (R$)",
        "Tx. Cobrada (%)", "Desc. Cobrado (R$)", "Vl. Líq. Cobrado (R$)",
        "Tx. Calculada (%)", "Desc. Calculado (R$)", "Vl. Líq. Calculado (R$)",
        "Diferença Taxa (%)", "Perda/Ganho (R$)",
    ]
    ws_det.append(headers)
    _style_header(ws_det, row=1)

    for r in registros:
        diff_taxa = (
            float(r.tx_venda) - float(r.tx_calc)
            if r.tx_venda is not None and r.tx_calc is not None
            else None
        )
        row_data = [
            str(r.data_venda)[:10] if r.data_venda else "",
            r.bandeira or "",
            r.forma_pagamento or "",
            r.adquirente or "",
            r.nsu or "",
            r.cod_autorizacao or "",
            float(r.vl_venda) if r.vl_venda is not None else None,
            float(r.tx_venda) if r.tx_venda is not None else None,
            float(r.desc_venda) if r.desc_venda is not None else None,
            float(r.vl_liq_venda) if r.vl_liq_venda is not None else None,
            float(r.tx_calc) if r.tx_calc is not None else None,
            float(r.desc_calc) if r.desc_calc is not None else None,
            float(r.vl_liq_calc) if r.vl_liq_calc is not None else None,
            round(diff_taxa, 4) if diff_taxa is not None else None,
            float(r.perda) if r.perda is not None else None,
        ]
        ws_det.append(row_data)
        # Destacar linhas com perda
        if r.perda is not None and float(r.perda) < 0:
            for cell in ws_det[ws_det.max_row]:
                cell.fill = LOSS_FILL

    # Linha de totais
    total_row = ws_det.max_row + 1
    ws_det.cell(total_row, 1, "TOTAL")
    ws_det.cell(total_row, 7, round(total_valor, 2))
    ws_det.cell(total_row, 15, round(total_perda, 2))
    for col in [1, 7, 15]:
        ws_det.cell(total_row, col).font = TOTAL_FONT

    _autofit(ws_det)

    # ── Serializar e retornar ────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"calculo_{calc_id.replace('/', '_')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{calc_id:path}")
async def delete_calculo(
    calc_id: str,
    db: Session = Depends(get_db)
):
    """
    Deleta um cálculo específico do banco de dados.
    """
    repo = CalculoRepository(db)
    repo.deletar_calculo(calc_id)
    return {"status": "success", "message": f"Cálculo {calc_id} deletado."}

@router.get("/historico")
async def get_historico(
    processamento_id: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de TAREFAS de cálculo (async).
    """
    service = CalculoService(db)
    tasks = service.list_tasks(skip=skip, limit=limit, processamento_id=processamento_id)
    return tasks
