import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.extrato_cliente import ExtratoCliente
from app.models.processamento import Processamento
from app.schemas.extrato_cliente import ExtratoClienteResponse, ExtratoStatusResumo

router = APIRouter()

ALLOWED_EXT = {".xlsx", ".xls", ".csv", ".txt", ".zip"}


@router.post("/{cliente_id}/extratos", response_model=ExtratoClienteResponse)
async def upload_extrato(
    cliente_id: int,
    file: UploadFile = File(...),
    tipo: str = Form("Outro"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Faz upload de um extrato vinculado ao cliente."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Extensão não permitida: {ext}")

    dest_dir = Path(f"extratos_clientes/{cliente_id}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    uid = str(uuid.uuid4())
    dest_path = dest_dir / f"{uid}_{file.filename}"

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    extrato = ExtratoCliente(
        cliente_id=cliente_id,
        nome_arquivo=file.filename,
        caminho_arquivo=str(dest_path),
        tipo=tipo,
        uploaded_by=current_user.login,
    )
    db.add(extrato)
    db.commit()
    db.refresh(extrato)
    return extrato


@router.get("/{cliente_id}/extratos", response_model=List[ExtratoClienteResponse])
def listar_extratos(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Lista todos os extratos de um cliente."""
    return (
        db.query(ExtratoCliente)
        .filter(ExtratoCliente.cliente_id == cliente_id)
        .order_by(ExtratoCliente.uploaded_at.desc())
        .all()
    )


@router.get("/{cliente_id}/extratos/status-resumo", response_model=ExtratoStatusResumo)
def status_resumo(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Retorna contadores de status dos extratos do cliente."""
    extratos = db.query(ExtratoCliente).filter(ExtratoCliente.cliente_id == cliente_id).all()
    return ExtratoStatusResumo(
        total=len(extratos),
        aguardando=sum(1 for e in extratos if e.status == "aguardando"),
        importado=sum(1 for e in extratos if e.status == "importado"),
        divergente=sum(1 for e in extratos if e.status == "divergente"),
    )


@router.post("/{cliente_id}/extratos/validar")
def validar_extratos(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    """Cruza extratos pendentes com processamentos existentes e atualiza status."""
    extratos = (
        db.query(ExtratoCliente)
        .filter(
            ExtratoCliente.cliente_id == cliente_id,
            ExtratoCliente.status == "aguardando",
        )
        .all()
    )
    processamentos = (
        db.query(Processamento)
        .filter(Processamento.cliente_id == cliente_id)
        .all()
    )

    atualizados = 0
    for extrato in extratos:
        match = next(
            (
                p
                for p in processamentos
                if extrato.nome_arquivo in p.nome_arquivo
                or p.nome_arquivo.endswith(extrato.nome_arquivo)
            ),
            None,
        )
        if match:
            extrato.processamento_id = match.id
            if extrato.tipo == "Outro" or match.tipo_arquivo == extrato.tipo:
                extrato.status = "importado"
            else:
                extrato.status = "divergente"
                # Notificação (não-bloqueante)
                try:
                    from app.services.notificacao_service import NotificacaoService
                    NotificacaoService.criar(
                        db,
                        tipo="extrato_divergente",
                        titulo="Extrato divergente detectado",
                        mensagem=f"O extrato '{extrato.nome_arquivo}' apresenta divergência de tipo.",
                        link=f"/clientes/{cliente_id}/extratos",
                        usuario_id=None,
                    )
                except Exception:
                    pass
            atualizados += 1

    db.commit()
    return {"atualizados": atualizados, "total_pendentes": len(extratos)}


@router.get("/{cliente_id}/extratos/{extrato_id}/download")
def download_extrato(
    cliente_id: int,
    extrato_id: str,
    db: Session = Depends(get_db),
):
    """Retorna o arquivo do extrato para download."""
    extrato = (
        db.query(ExtratoCliente)
        .filter(
            ExtratoCliente.id == extrato_id,
            ExtratoCliente.cliente_id == cliente_id,
        )
        .first()
    )
    if not extrato:
        raise HTTPException(status_code=404, detail="Extrato não encontrado")

    file_path = Path(extrato.caminho_arquivo)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    return FileResponse(
        path=str(file_path),
        filename=extrato.nome_arquivo,
        media_type="application/octet-stream",
    )


@router.delete("/{cliente_id}/extratos/{extrato_id}")
def deletar_extrato(
    cliente_id: int,
    extrato_id: str,
    db: Session = Depends(get_db),
):
    """Remove extrato (somente se status='aguardando')."""
    extrato = (
        db.query(ExtratoCliente)
        .filter(
            ExtratoCliente.id == extrato_id,
            ExtratoCliente.cliente_id == cliente_id,
        )
        .first()
    )
    if not extrato:
        raise HTTPException(status_code=404, detail="Extrato não encontrado")
    if extrato.status != "aguardando":
        raise HTTPException(
            status_code=400,
            detail="Apenas extratos com status 'aguardando' podem ser removidos",
        )

    if extrato.caminho_arquivo:
        file_path = Path(extrato.caminho_arquivo)
        if file_path.exists():
            file_path.unlink()

    db.delete(extrato)
    db.commit()
    return {"message": "Extrato removido com sucesso"}
