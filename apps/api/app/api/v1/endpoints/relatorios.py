from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any, List
import os
import pandas as pd
from datetime import datetime

from app.core.database import get_db, engine
from app.schemas.relatorio import RelatorioRequest, RelatorioResponse, RelatorioOptions
from app.services.relatorio_service import RelatorioService

# Importar lógica legada
# O path já está configurado no main.py, então import direto deve funcionar
# Tentativa de importar lógica legada com fallbacks robustos
try:
    from modules.reports import (
        gerar_relatorio_mensal_html, 
        gerar_relatorio_html,
        obter_adquirentes_distintos_processamento
    )
except ImportError as e:
    print(f"Erro ao importar modules.reports: {e}")
    try:
        import sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        from modules.reports import (
            gerar_relatorio_mensal_html, 
            gerar_relatorio_html,
            obter_adquirentes_distintos_processamento
        )
    except Exception as e2:
        print(f"CRÍTICO: Não foi possível importar relatórios legados: {e2}")
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
            print(f"Erro ao buscar adquirentes: {e}")
            
    return opcoes

@router.get("/adquirentes")
def get_adquirentes(processamento_id: str, calc_tipo: str = None):
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
def gerar_relatorio(req: RelatorioRequest):
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
        
        print(f"Gerando relatório {req.tipo_relatorio} para {req.processamento_id}")

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
            print(f"Erro ao gerar abusividade: {e_abs}")
            # Non-blocking error?
        
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na geração do relatório: {str(e)}")

@router.post("/gerar-async")
async def gerar_relatorio_async(
    req: RelatorioRequest,
    background_tasks: BackgroundTasks,
    usuario: str = "api_user",
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
        usuario=usuario,
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
    
    print(f"📥 Tentativa de download: {actual_path}")
    
    if not os.path.exists(actual_path):
        # Tentar resolver se for relativo à raiz do projeto
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent.parent.parent.parent
        resolved_path = root / actual_path
        if resolved_path.exists():
            actual_path = str(resolved_path)
            print(f"✅ Path resolvido para: {actual_path}")
        else:
            print(f"❌ Arquivo não encontrado: {actual_path}")
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
@router.get("/historico")
async def get_historico(
    processamento_id: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de relatórios gerados.
    """
    service = RelatorioService(db)
    tasks = service.list_tasks(skip=skip, limit=limit, processamento_id=processamento_id)
    return tasks
