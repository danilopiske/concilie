from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse
from app.services.ai_service import AIService

router = APIRouter()

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_data(
    request: AIAnalysisRequest,
    service: AIService = Depends(AIService)
) -> Any:
    """
    Analyze data using LangChain Pandas Agent.
    """
    try:
        response = await service.analyze(request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
