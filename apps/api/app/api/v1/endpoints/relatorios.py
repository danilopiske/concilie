import logging
import os
from datetime import datetime
from typing import Any, List

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.deps import get_current_user
from app.models.usuario import Usuario
from app.core.database import engine, get_db
from app.schemas.relatorio import RelatorioOptions, RelatorioRequest, RelatorioResponse
from app.services.relatorio_service import RelatorioService


class SaveEditRequest(BaseModel):
    html_content: str

# Importar lógica legada
# O path já está configurado no main.py, então import direto deve funcionar
# Tentativa de importar lógica legada com fallbacks robustos
try:
    from modules.reports import (
        gerar_relatorio_html,
        gerar_relatorio_mensal_html,
        obter_adquirentes_distintos_processamento,
    )
except ImportError as e:
    logger.warning("Erro ao importar modules.reports: %s", e)
    try:
        import sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        from modules.reports import (
            gerar_relatorio_html,
            gerar_relatorio_mensal_html,
            obter_adquirentes_distintos_processamento,
        )
    except Exception as e2:
        logger.critical("Não foi possível importar relatórios legados: %s", e2)
        # Definir Stubs para não quebrar a API
        def generar_stub(*args, **kwargs):
            raise Exception("Módulo de relatórios indisponível (dependência 'panel' ausente)")

        gerar_relatorio_mensal_html = generar_stub
        gerar_relatorio_html = generar_stub
        obter_adquirentes_distintos_processamento = lambda *args: []

router = APIRouter()

@router.get("/opcoes", response_model=RelatorioOptions)
def get_opcoes(processamento_id: str = None):
    """
    Retorna opções de filtro.
    Se processamento_id for passado, retorna adquirentes desse processamento.
    Caso contrário, apenas lista de processamentos é relevante (frontend busca lista separada).
    """
    opcoes = {
        "processamentos": [], # Frontend usa endpoint existente de processamentos
        "adquirentes": ["Todos"]
    }

    if processamento_id:
        try:
            # Usar engine direto pois as funcoes legadas esperam engine, nao session
            adquirentes = obter_adquirentes_distintos_processamento(engine, processamento_id)
            if adquirentes:
                opcoes["adquirentes"] = ["Todos"] + sorted(adquirentes)
        except Exception as e:
            logger.warning("Erro ao buscar adquirentes: %s", e)

    return opcoes

@router.get("/adquirentes")
def get_adquirentes(
    processamento_id: str,
    calc_tipo: str = None,
):
    """Retorna lista de adquirentes e período disponível para um processamento e tipo de cálculo"""
    try:
        from modules.reports import obter_adquirentes_e_periodo_processamento
        adquirentes, periodo, available_types = obter_adquirentes_e_periodo_processamento(engine, processamento_id, calc_tipo=calc_tipo)

        # Converter dates para strings para o JSON
        if periodo:
            if 'data_min' in periodo and periodo['data_min']:
                periodo['data_min'] = periodo['data_min'].isoformat() if hasattr(periodo['data_min'], 'isoformat') else str(periodo['data_min'])
            if 'data_max' in periodo and periodo['data_max']:
                periodo['data_max'] = periodo['data_max'].isoformat() if hasattr(periodo['data_max'], 'isoformat') else str(periodo['data_max'])

        return {
            "adquirentes": ["Todos"] + (sorted(adquirentes) if adquirentes else []),
            "periodo": periodo,
            "available_types": available_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gerar", response_model=RelatorioResponse)
def gerar_relatorio(
    req: RelatorioRequest,
):
    """
    Gera o relatório HTML usando a lógica legada.
    """
    try:
        # Converter adquirente 'Todos' para None
        adquirente_filtro = req.adquirente if req.adquirente and req.adquirente != "Todos" else None

        # Converter datas para datetime
        data_inicio_dt = datetime.combine(req.data_inicio, datetime.min.time()) if req.data_inicio else None
        data_fim_dt = datetime.combine(req.data_fim, datetime.max.time()) if req.data_fim else None

        html_path = None
        sintetico_path = None

        logger.info("Gerando relatório %s para %s", req.tipo_relatorio, req.processamento_id)

        if req.tipo_relatorio == "mensal":
            html_path, _, sintetico_path = gerar_relatorio_mensal_html(
                engine,
                req.processamento_id,
                calc_tipo=req.calc_tipo,
                adquirente=adquirente_filtro,
                incluir_filtradas=req.incluir_filtradas,
                incluir_recebiveis_filtrados=req.incluir_recebiveis_filtrados,
                data_inicio=data_inicio_dt,
                data_fim=data_fim_dt,
                apenas_com_perdas=req.apenas_com_perdas
            )
        else:
            # Retroativo (Padrão)
            html_path, _, sintetico_path = gerar_relatorio_html(
                engine,
                req.processamento_id,
                calc_tipo=req.calc_tipo,
                return_base=False,
                adquirente=adquirente_filtro,
                incluir_filtradas=req.incluir_filtradas,
                incluir_recebiveis_filtrados=req.incluir_recebiveis_filtrados,
                data_inicio=data_inicio_dt,
                data_fim=data_fim_dt,
                apenas_com_perdas=req.apenas_com_perdas
            )

        if not html_path or not os.path.exists(html_path):
             raise HTTPException(status_code=500, detail="Erro ao gerar arquivo de relatório")

        excel_path = html_path.replace(".html", ".xlsx")
        has_excel = os.path.exists(excel_path)

        # Gerar Relatório de Abusividade (Novo)
        abusividade_path = None
        try:
             from app.services.abusividade_relatorio_service import AbusividadeRelatorioService
             abs_service = AbusividadeRelatorioService(next(get_db())) # Hacky session if not passed properly, checking imports
             # Better way: get db session from Dependency? endpoints usage usually has access to db
             # But here we are in a function. We need the db session.
             # Wait, get_db is a generator. We should ideally pass db to this function if possible or create new.
             # Actually, `gerar_relatorio` creates its own engine connections in legacy usually.
             # Let's create a new session cleanly.

             with Session(engine) as session:
                abs_service = AbusividadeRelatorioService(session)
                abusividade_path = abs_service.gerar_html(
                    req.processamento_id,
                    data_inicio=data_inicio_dt,
                    data_fim=data_fim_dt
                )
        except Exception as e_abs:
            logger.warning("Erro ao gerar abusividade (não bloqueante): %s", e_abs)

        return RelatorioResponse(
            success=True,
            message="Relatório gerado com sucesso",
            html_path=html_path,
            excel_path=excel_path if has_excel else None,
            sintetico_path=sintetico_path if sintetico_path and os.path.exists(sintetico_path) else None,
            abusividade_path=abusividade_path,
            filename=os.path.basename(html_path)
        )

    except Exception as e:
        logger.error("Erro na geração do relatório: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na geração do relatório: {str(e)}")

@router.post("/gerar-async")
async def gerar_relatorio_async(
    req: RelatorioRequest,
    background_tasks: BackgroundTasks,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Inicia a geração do relatório em segundo plano.
    """
    service = RelatorioService(db)

    # Preparar metadados para a task
    metadata = req.dict()
    # Converter datas para string ISO para armazenamento JSON
    if metadata.get('data_inicio'):
        metadata['data_inicio'] = metadata['data_inicio'].isoformat()
    if metadata.get('data_fim'):
        metadata['data_fim'] = metadata['data_fim'].isoformat()

    # Flag para abusividade (pode vir no request ou ser inferido)
    metadata['gerar_abusividade'] = True # Padrão para este endpoint assíncrono

    task = service.create_task(
        processamento_id=req.processamento_id,
        tipo_relatorio=req.tipo_relatorio,
        usuario=getattr(current_user, 'usuario', str(current_user)), # Ensure string, not object
        metadata=metadata
    )

    background_tasks.add_task(service.run_async_report, task.id)

    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Geração de relatório iniciada em segundo plano."
    }

@router.get("/task/{task_id:path}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna o status atual de uma tarefa de relatório.
    """
    service = RelatorioService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    return {
        "id": task.id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "tipo_relatorio": task.tipo_relatorio,
        "result_path": task.result_path,
        "abusividade_path": task.abusividade_path,
        "sintetico_path": task.sintetico_path,
        "excel_path": task.excel_path,
        "updated_at": task.updated_at
    }

@router.get("/download")
def download_relatorio(path: str):
    """
    Endpoint para baixar o arquivo gerado.
    Valida se o arquivo existe e está na pasta correta (segurança básica).
    """
    # Normalizar o path para evitar problemas de encoding/barras
    import urllib.parse
    actual_path = urllib.parse.unquote(path)

    # Se for um path absoluto com backslashes vindo do Windows, normalizar
    actual_path = os.path.normpath(actual_path)

    logger.debug("Tentativa de download: %s", actual_path)

    if not os.path.exists(actual_path):
        # Tentar resolver se for relativo à raiz do projeto
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        resolved_path = root / actual_path
        if resolved_path.exists():
            actual_path = str(resolved_path)
            logger.debug("Path resolvido para: %s", actual_path)
        else:
            logger.warning("Arquivo não encontrado: %s", actual_path)
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {os.path.basename(actual_path)}")

    # Basic security check: ensure it's in a known report directory
    path_lower = actual_path.lower()
    if "relatorios" not in path_lower and "temp" not in path_lower:
         raise HTTPException(status_code=403, detail="Acesso negado a este arquivo")

    filename = os.path.basename(actual_path)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".html":
        # Abrir inline no browser; filename hint para Ctrl+S salvar corretamente
        return FileResponse(
            actual_path,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    else:
        # Excel e demais: forçar download com nome correto
        return FileResponse(actual_path, filename=filename)
@router.get("/download-pdf")
def download_relatorio_pdf(path: str, no_charts: bool = False):
    """
    Converte o HTML gerado para PDF (WeasyPrint) e retorna como download.
    Aceita o mesmo parâmetro 'path' que /download.
    Use no_charts=true para pular a conversão de gráficos Plotly (diagnóstico).
    """
    import urllib.parse
    from fastapi.responses import Response
    from app.services.pdf_service import PdfService

    actual_path = os.path.normpath(urllib.parse.unquote(path))

    if not os.path.exists(actual_path):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        resolved = root / actual_path
        if resolved.exists():
            actual_path = str(resolved)
        else:
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {os.path.basename(actual_path)}")

    path_lower = actual_path.lower()
    if "relatorios" not in path_lower and "temp" not in path_lower:
        raise HTTPException(status_code=403, detail="Acesso negado a este arquivo")

    if not actual_path.lower().endswith(".html"):
        raise HTTPException(status_code=400, detail="Apenas arquivos HTML podem ser convertidos para PDF")

    with open(actual_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    try:
        pdf_bytes = PdfService.html_to_pdf(html_content, base_url=actual_path, skip_charts=no_charts)
    except Exception as e:
        logger.error("Erro ao converter HTML para PDF: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")

    filename = os.path.basename(actual_path).replace(".html", ".pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tasks/{task_id}/download")
def download_relatorio_task(
    task_id: str,
    format: str = "html",
    db: Session = Depends(get_db),
):
    """Download do relatório por task_id. format=pdf|html"""
    from pathlib import Path

    from fastapi.responses import Response

    from app.services.relatorio_service import RelatorioService

    service = RelatorioService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task não encontrada")
    if not task.result_path:
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
            headers={"Content-Disposition": f'attachment; filename="relatorio_{task_id}.pdf"'},
        )

    return FileResponse(
        path=str(file_path),
        filename=f"relatorio_{task_id}.html",
        media_type="text/html",
    )


@router.post("/tasks/{task_id}/save-edit")
async def save_edit_relatorio(
    task_id: str,
    req: SaveEditRequest,
    db: Session = Depends(get_db),
):
    """Salva o relatório editado e atualiza o result_path da task."""
    service = RelatorioService(db)
    try:
        saved_path = service.save_edit(task_id, req.html_content)
        return {"success": True, "path": saved_path}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar edição: {str(e)}")


@router.get("/historico")
async def get_historico(
    processamento_id: str = None,
    status: str = None,
    tipo: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Retorna o histórico de relatórios gerados.
    Filtros opcionais: status (PENDING|PROCESSING|SUCCESS|FAILED), tipo (mensal|retroativo|abusividade).
    """
    service = RelatorioService(db)
    tasks = service.list_tasks(
        skip=skip,
        limit=limit,
        processamento_id=processamento_id,
        status=status,
        tipo=tipo,
    )
    return tasks
