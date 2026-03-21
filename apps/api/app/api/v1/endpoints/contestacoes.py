from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
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


@router.get("/cliente/{cliente_id}")
def contestacoes_por_cliente(
    cliente_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista contestações de um cliente específico com dados resumidos."""
    from app.models.cliente import Cliente
    from app.models.contestacao import Contestacao

    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    contestacoes = (
        db.query(Contestacao)
        .filter(Contestacao.cliente_id == cliente_id)
        .order_by(Contestacao.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "cliente_id": cliente_id,
        "nome": cliente.nome_fantasia or cliente.razao_social or str(cliente_id),
        "total": len(contestacoes),
        "contestacoes": [
            {
                "id": c.id,
                "status": c.status,
                "adquirente": c.adquirente,
                "processamento_id": c.processamento_id,
                "periodo_inicio": c.periodo_inicio.isoformat() if c.periodo_inicio else None,
                "periodo_fim": c.periodo_fim.isoformat() if c.periodo_fim else None,
                "valor_excesso_total": c.valor_excesso_total,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in contestacoes
        ],
    }


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
    format: str = "html",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    obj = svc.obter(contestacao_id, db)
    if not obj:
        raise HTTPException(status_code=404, detail="Contestação não encontrada")
    html_path = svc.get_html_path(contestacao_id)
    if not html_path:
        raise HTTPException(status_code=404, detail="Arquivo HTML não encontrado")

    if format == "pdf":
        from app.services.pdf_service import PdfService

        html = html_path.read_text(encoding="utf-8")
        pdf_bytes = PdfService.html_to_pdf(html)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="contestacao_{contestacao_id[:8]}.pdf"'},
        )

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
