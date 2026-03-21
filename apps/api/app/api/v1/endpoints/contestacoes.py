from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.contestacao import (
    ContestacaoGerar,
    ContestacaoResponse,
    ContestacaoSaveEdit,
    ContestacaoStatusUpdate,
)
from app.services import contestacao_service as svc

router = APIRouter()


@router.post("/gerar", status_code=201)
def gerar(
    body: ContestacaoGerar,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        c = svc.gerar_contestacao(body.cliente_id, body.processamento_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"contestacao_id": c.id}


@router.get("", response_model=List[ContestacaoResponse])
def listar(
    cliente_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return svc.listar(cliente_id, status, db)


@router.get("/{contestacao_id}", response_model=ContestacaoResponse)
def detalhe(
    contestacao_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = svc.obter(contestacao_id, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Contestação não encontrada")
    return obj


@router.put("/{contestacao_id}/status", response_model=ContestacaoResponse)
def atualizar_status(
    contestacao_id: str,
    body: ContestacaoStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = svc.atualizar_status(contestacao_id, body, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Contestação não encontrada")
    return obj


@router.post("/{contestacao_id}/save-edit")
def save_edit(
    contestacao_id: str,
    body: ContestacaoSaveEdit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    path = svc.save_edit(contestacao_id, body.html_content, db)
    if path is None:
        raise HTTPException(status_code=404, detail="Contestação não encontrada")
    return {"saved": True, "path": path}


@router.get("/{contestacao_id}/download")
def download(
    contestacao_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = svc.obter(contestacao_id, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Contestação não encontrada")
    html_path = svc.get_html_path(contestacao_id)
    if not html_path:
        raise HTTPException(status_code=404, detail="Arquivo HTML não encontrado")
    return FileResponse(
        str(html_path),
        media_type="text/html",
        filename=f"contestacao_{contestacao_id[:8]}.html",
    )


@router.delete("/{contestacao_id}", status_code=204)
def remover(
    contestacao_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        if not svc.remover(contestacao_id, db):
            raise HTTPException(status_code=404, detail="Contestação não encontrada")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
