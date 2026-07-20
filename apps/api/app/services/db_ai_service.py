"""Text-to-SQL conversacional via Gemini."""
from __future__ import annotations

import json
import logging

import httpx
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession

logger = logging.getLogger(__name__)

_SCHEMA_CACHE: str | None = None
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_MAX_SESSIONS = 3
_CONTEXT_MESSAGES = 6


def get_schema_summary() -> str:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE:
        return _SCHEMA_CACHE
    inspector = inspect(engine)
    lines = []
    for table in sorted(inspector.get_table_names()):
        cols = ", ".join(c["name"] for c in inspector.get_columns(table))
        lines.append(f"- {table}: {cols}")
    _SCHEMA_CACHE = "\n".join(lines)
    return _SCHEMA_CACHE


def _call_gemini(messages: list[dict]) -> str:
    model = settings.GEMINI_MODEL or "gemini-2.5-flash"
    url = _GEMINI_URL.format(model=model)
    contents = [{"role": m["role"], "parts": [{"text": m["text"]}]} for m in messages]
    resp = httpx.post(
        url,
        params={"key": settings.GEMINI_API_KEY},
        json={"contents": contents},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── Session management ────────────────────────────────────────────────────────

def list_sessions(usuario_id: int, db: Session) -> list[dict]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.usuario_id == usuario_id)
        .order_by(ChatSession.atualizado_em.desc())
        .all()
    )
    return [{"id": s.id, "titulo": s.titulo or "Sem título", "atualizado_em": s.atualizado_em} for s in sessions]


def create_session(usuario_id: int, db: Session) -> ChatSession:
    existing = (
        db.query(ChatSession)
        .filter(ChatSession.usuario_id == usuario_id)
        .order_by(ChatSession.criado_em.asc())
        .all()
    )
    if len(existing) >= _MAX_SESSIONS:
        oldest = existing[0]
        db.query(ChatMessage).filter(ChatMessage.session_id == oldest.id).delete()
        db.delete(oldest)
        db.commit()

    session = ChatSession(usuario_id=usuario_id, titulo=None)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session(session_id: int, usuario_id: int, db: Session) -> bool:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.usuario_id == usuario_id).first()
    if not session:
        return False
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return True


def get_messages(session_id: int, db: Session) -> list[dict]:
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return [{"id": m.id, "role": m.role, "content": m.content, "sql_gerado": m.sql_gerado} for m in msgs]


# ── Query ─────────────────────────────────────────────────────────────────────

def send_message(pergunta: str, session_id: int, usuario_id: int, db: Session, file_content: str | None = None, file_name: str | None = None) -> dict:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.usuario_id == usuario_id).first()
    if not session:
        return {"erro": "Sessão não encontrada"}

    db.add(ChatMessage(session_id=session_id, role="user", content=pergunta))
    db.commit()

    if not session.titulo:
        session.titulo = pergunta[:80]
        db.commit()

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id.desc())
        .limit(_CONTEXT_MESSAGES)
        .all()
    )
    history = list(reversed(history))

    schema = get_schema_summary()
    system_prompt = f"""Você é um assistente de banco de dados MySQL especializado em conciliação financeira.
Quando o usuário fizer uma pergunta sobre dados, gere uma query SQL SELECT.
Se a pergunta for ambígua ou precisar de mais detalhes, faça uma pergunta de esclarecimento ao usuário.
Se não for sobre dados do banco, responda normalmente em texto.

Retorne SEMPRE um JSON puro (sem markdown) com os campos:
- "tipo": "sql" | "pergunta" | "texto"
- "resposta": string em português (explicação ou pergunta)
- "sql": string (apenas quando tipo == "sql")

Schema das tabelas:
{schema}"""

    messages = [{"role": "user", "text": system_prompt}]
    for m in history[:-1]:
        role = "user" if m.role == "user" else "model"
        messages.append({"role": role, "text": m.content})
    user_text = pergunta
    if file_content:
        user_text += f"\n\n[Arquivo anexado: {file_name or 'arquivo'}]\n{file_content}"
    messages.append({"role": "user", "text": user_text})

    try:
        raw = _call_gemini(messages).strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
        parsed = json.loads(raw)
    except Exception as e:
        logger.error("Erro Gemini: %s", e)
        return {"erro": f"Erro ao chamar Gemini: {e}"}

    tipo = parsed.get("tipo", "texto")
    resposta = parsed.get("resposta", "")
    sql = parsed.get("sql", "").strip() if tipo == "sql" else ""
    dados = []
    colunas = []

    if tipo == "sql" and sql:
        try:
            result = db.execute(text(sql))
            rows = result.fetchmany(200)
            colunas = list(result.keys())
            dados = [dict(zip(colunas, row)) for row in rows]
        except Exception as e:
            logger.error("Erro SQL: %s | %s", e, sql)
            resposta = f"Gerei um SQL mas ele falhou: {e}"
            tipo = "texto"
            sql = ""

    assistant_content = resposta
    db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_content, sql_gerado=sql or None))
    from datetime import datetime
    session.atualizado_em = datetime.utcnow()
    db.commit()

    return {"tipo": tipo, "resposta": resposta, "sql": sql, "colunas": colunas, "dados": dados, "total": len(dados)}
