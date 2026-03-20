
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.importacao import ImportacaoConfirmar
from app.services.import_service import ImportService

router = APIRouter()

@router.post("/upload")
async def upload_arquivo_preview(
    files: List[UploadFile] = File(...),
    cliente_id: int = Form(...),
    ec_id: str = Form(...),
    contexto: str = Form(...),
    tipo: str = Form(...),
    usuario: str = Form("api_user"),
    db: Session = Depends(get_db)
):
    """
    Passo 1: Upload e Preview
    - Salva arquivo temporário
    - Retorna preview dos dados normalizados
    - Retorna file_id para confirmação
    """
    service = ImportService(db)
    return await service.preview_upload(
        files=files,
        cliente_id=cliente_id,
        ec_id=ec_id,
        contexto=contexto,
        tipo=tipo,
        usuario=usuario
    )

@router.post("/confirmar")
async def confirmar_importacao(
    dados: ImportacaoConfirmar,
    usuario: str = "api_user",
    db: Session = Depends(get_db)
):
    """
    Passo 2: Confirmar e Gravar no Banco
    - Usa file_id retornado no passo anterior
    - Processa e grava os dados definitivamente
    """
    service = ImportService(db)
    return await service.confirm_import(
        file_id=dados.file_id,
        cliente_id=dados.cliente_id,
        ec_id=dados.ec_id,
        contexto=dados.contexto,
        tipo=dados.tipo,
        usuario=usuario,
        processamentoid=dados.processamentoid
    )
