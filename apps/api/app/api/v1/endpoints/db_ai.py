"""Endpoints de chat IA com banco de dados via Gemini."""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.usuario import Usuario
from app.services.db_ai_service import (
    create_session,
    delete_session,
    get_messages,
    list_sessions,
    send_message,
)

router = APIRouter()


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return list_sessions(current_user.id, db)


@router.post("/sessions")
def new_session(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    session = create_session(current_user.id, db)
    return {"id": session.id, "titulo": session.titulo, "atualizado_em": session.atualizado_em}


@router.delete("/sessions/{session_id}")
def remove_session(session_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if not delete_session(session_id, current_user.id, db):
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"ok": True}


@router.get("/sessions/{session_id}/messages")
def session_messages(session_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return get_messages(session_id, db)


@router.post("/sessions/{session_id}/message")
async def message(
    session_id: int,
    pergunta: str = Form(...),
    file: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    file_content: Optional[str] = None
    file_name: Optional[str] = None

    if file and file.filename:
        file_name = file.filename
        raw = await file.read()
        ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""

        if ext in ("txt", "csv"):
            file_content = raw.decode("utf-8", errors="replace")[:20_000]
        elif ext in ("xlsx", "xls"):
            try:
                import io
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
                ws = wb.active
                rows = []
                for i, row in enumerate(ws.iter_rows(values_only=True)):
                    if i > 200:
                        break
                    rows.append(",".join(str(c) if c is not None else "" for c in row))
                file_content = "\n".join(rows)
            except Exception as e:
                file_content = f"[Erro ao ler XLSX: {e}]"
        else:
            file_content = raw.decode("utf-8", errors="replace")[:10_000]

    return send_message(pergunta, session_id, current_user.id, db, file_content=file_content, file_name=file_name)
