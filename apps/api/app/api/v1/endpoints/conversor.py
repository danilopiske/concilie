"""Endpoint de conversão de extratos Rede TXT → XLSX."""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.services.conversor.conver_service import converter_arquivos

router = APIRouter()

_MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.post("/rede")
async def converter_rede(files: Optional[list[UploadFile]] = File(default=None)) -> Response:
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    arquivos = []
    for f in files:
        nome = f.filename or "extrato.txt"
        if not nome.lower().endswith(".txt"):
            raise HTTPException(
                status_code=422,
                detail=f"Arquivo inválido: '{nome}' não é um extrato Rede (.txt).",
            )
        conteudo = await f.read()
        arquivos.append((nome, conteudo))

    xlsx_bytes, nome_saida = converter_arquivos(arquivos)

    return Response(
        content=xlsx_bytes,
        media_type=_MIME_XLSX,
        headers={"Content-Disposition": f'attachment; filename="{nome_saida}"'},
    )
