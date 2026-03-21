from typing import Any, List, Optional

from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    question: str
    context_filters: Optional[dict[str, Any]] = None

class AIAnalysisResponse(BaseModel):
    answer: str
    chart_data: Optional[dict] = None
    table_data: Optional[dict] = None
    generated_code: Optional[str] = None


class ChatRequest(BaseModel):
    mensagem: str
    processamento_id: Optional[str] = None
    cliente_id: Optional[int] = None
    historico: List[dict] = []


class ChatResponse(BaseModel):
    resposta: str
    dados_contexto: Optional[dict] = None
    sugestoes: List[str] = []
