from typing import Any, Optional

from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    question: str
    context_filters: Optional[dict[str, Any]] = None

class AIAnalysisResponse(BaseModel):
    answer: str
    chart_data: Optional[dict] = None
    table_data: Optional[dict] = None
    generated_code: Optional[str] = None
