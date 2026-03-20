from typing import Optional

from pydantic import BaseModel


class ImportacaoConfirmar(BaseModel):
    file_id: str
    cliente_id: int
    ec_id: str
    contexto: str
    tipo: str
    processamentoid: Optional[str] = None
