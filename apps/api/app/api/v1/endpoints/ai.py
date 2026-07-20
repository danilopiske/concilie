from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse, ChatRequest, ChatResponse
from app.services.ai_service import AIService, check_rate_limit

router = APIRouter()


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_data(
    request: AIAnalysisRequest,
    service: AIService = Depends(AIService),
) -> Any:
    """
    Analyze data using LangChain Pandas Agent.
    """
    try:
        response = await service.analyze(request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Chat contextual por linguagem natural sobre um processamento."""
    user_id = str(getattr(current_user, "id", current_user))
    if not check_rate_limit(user_id):
        raise HTTPException(status_code=429, detail="Limite de 10 mensagens por minuto atingido.")

    service = AIService()

    contexto = ""
    dados_contexto = None
    if body.processamento_id:
        contexto, dados_contexto = service.montar_contexto(body.processamento_id, db)

    resposta, sugestoes = service.chat(body.mensagem, contexto, body.historico)

    return ChatResponse(
        resposta=resposta,
        dados_contexto=dados_contexto,
        sugestoes=sugestoes,
    )
