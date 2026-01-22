from pydantic import BaseModel
from typing import Optional

class ImportacaoConfirmar(BaseModel):
    file_id: str
    cliente_id: int
    ec_id: str
    contexto: str
    tipo: str
    processamentoid: Optional[str] = None
