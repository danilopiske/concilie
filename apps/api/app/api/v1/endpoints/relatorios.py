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
            
    return options

@router.get("/adquirentes")
def get_adquirentes(processamento_id: str):
    """Retorna lista de adquirentes para um processamento"""
    try:
        adquirentes = obter_adquirentes_distintos_processamento(engine, processamento_id)
        return ["Todos"] + (sorted(adquirentes) if adquirentes else [])
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
        
        return RelatorioResponse(
            success=True,
            message="Relatório gerado com sucesso",
            html_path=html_path,
            excel_path=excel_path if has_excel else None,
            sintetico_path=sintetico_path if sintetico_path and os.path.exists(sintetico_path) else None,
            filename=os.path.basename(html_path)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na geração do relatório: {str(e)}")

@router.get("/download")
def download_relatorio(path: str):
    """
    Endpoint para baixar o arquivo gerado.
    Valida se o arquivo existe e está na pasta correta (segurança básica).
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Basic security check: ensure it's in reports dir
    # (Adjust logic as needed for your path structure)
    if "relatorios" not in path.lower() and "financial" not in path.lower():
         raise HTTPException(status_code=403, detail="Acesso negado a este arquivo")

    filename = os.path.basename(path)
    return FileResponse(path, filename=filename)
