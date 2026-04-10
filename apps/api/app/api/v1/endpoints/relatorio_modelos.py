"""
Endpoints para pré-processamento de relatórios e gestão de modelos.

Fluxo:
  POST /relatorios/preprocessar        → pré-processa e salva parquets
  GET  /relatorios/preprocessar/status → verifica se parquet existe
  POST /relatorios/emitir              → emite modelo(s) selecionado(s)
  GET  /relatorios/modelos             → lista modelos ativos do banco
  POST /relatorios/modelos             → cria novo modelo
  PATCH /relatorios/modelos/{id}       → atualiza modelo
  DELETE /relatorios/modelos/{id}      → desativa modelo (ativo=False)
"""

import json
import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import engine, get_db
from app.models.modelo_relatorio import ModeloRelatorio
from app.models.usuario import Usuario
from app.services.preprocessamento_service import (
    emitir_modelo,
    invalidar_parquet,
    preprocessar_relatorio,
    status_parquet,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PreprocessarRequest(BaseModel):
    processamento_id: str
    calc_tipo: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    adquirente: Optional[str] = None  # None/"Todos" = sem filtro; "Cielo" = só Cielo


class OpcaoEmissao(BaseModel):
    adquirente: Optional[str] = None  # None ou "Todos" = sem filtro
    incluir_filtradas: bool = False
    incluir_recebiveis_filtrados: bool = False
    apenas_com_perdas: bool = False


class EmitirRequest(BaseModel):
    processamento_id: str
    modelo_ids: List[int]
    opcoes: OpcaoEmissao = OpcaoEmissao()


class ModeloCreate(BaseModel):
    nome: str
    template_arquivo: Optional[str] = None
    tipo: str  # html | xml
    secoes_necessarias: List[str]
    ativo: bool = True


class ModeloUpdate(BaseModel):
    nome: Optional[str] = None
    template_arquivo: Optional[str] = None
    tipo: Optional[str] = None
    secoes_necessarias: Optional[List[str]] = None
    ativo: Optional[bool] = None


# ---------------------------------------------------------------------------
# Pré-processamento
# ---------------------------------------------------------------------------

@router.post("/preprocessar")
def preprocessar(
    request: PreprocessarRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executa o pré-processamento completo para um processamento.
    Salva cada seção como .parquet em parquet_cache/{processamento_id}/.
    """
    try:
        db.close()
    except Exception:
        pass
    try:
        resultado = preprocessar_relatorio(
            engine=engine,
            processamento_id=request.processamento_id,
            calc_tipo=request.calc_tipo,
            data_inicio=request.data_inicio,
            data_fim=request.data_fim,
            adquirente=request.adquirente,
        )
        return {
            "message": "Pré-processamento concluído",
            "secoes_geradas": resultado["secoes_geradas"],
            "erros": resultado["erros"],
            "gerado_em": resultado["meta"]["gerado_em"],
        }
    except Exception as e:
        logger.error(f"Erro no pré-processamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preprocessar/status")
def status_preprocessamento(
    processamento_id: str,
    adquirente: Optional[str] = None,
    current_user: Usuario = Depends(get_current_user),
):
    """
    Verifica se o parquet já existe para o combo (processamento_id + adquirente).
    adquirente=None/"Todos" verifica o slot 'todos'.
    """
    return status_parquet(processamento_id, adquirente)


@router.post("/preprocessar/invalidar")
def invalidar(
    processamento_id: str,
    current_user: Usuario = Depends(get_current_user),
    _: Any = Depends(require_role(["admin", "operador"])),
):
    """
    Invalida manualmente o cache parquet de um processamento.
    """
    invalidar_parquet(processamento_id)
    return {"message": f"Cache invalidado para {processamento_id}"}


# ---------------------------------------------------------------------------
# Emissão
# ---------------------------------------------------------------------------

@router.post("/emitir")
def emitir(
    request: EmitirRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Emite os modelos selecionados (por checkbox) lendo os parquets.
    Retorna lista de arquivos gerados.
    """
    # Fechar a sessão DB antes da operação pesada — evita "Lost connection"
    # durante geração de relatórios longos (a sessão só era usada para auth)
    try:
        db.close()
    except Exception:
        pass

    status = status_parquet(request.processamento_id, request.opcoes.adquirente)
    if not status["existe"]:
        raise HTTPException(
            status_code=400,
            detail="Parquet não encontrado. Execute o pré-processamento antes de emitir.",
        )

    arquivos = []
    erros = []
    for modelo_id in request.modelo_ids:
        try:
            path = emitir_modelo(
                processamento_id=request.processamento_id,
                modelo_id=modelo_id,
                engine=engine,
                opcoes=request.opcoes.model_dump(),
            )
            arquivos.append({"modelo_id": modelo_id, "arquivo": path})
        except Exception as e:
            erros.append({"modelo_id": modelo_id, "erro": str(e)})
            logger.error(f"Erro ao emitir modelo {modelo_id}: {e}")

    return {"arquivos": arquivos, "erros": erros}


@router.get("/emitir/download")
def download_arquivo(
    path: str,
    current_user: Usuario = Depends(get_current_user),
):
    """
    Download de um arquivo gerado pelo endpoint /emitir.
    """
    import os
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, filename=os.path.basename(path))


# ---------------------------------------------------------------------------
# CRUD de Modelos
# ---------------------------------------------------------------------------

@router.get("/modelos")
def listar_modelos(
    apenas_ativos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista modelos de relatório cadastrados no banco."""
    query = db.query(ModeloRelatorio)
    if apenas_ativos:
        query = query.filter(ModeloRelatorio.ativo == True)
    modelos = query.order_by(ModeloRelatorio.id).all()
    return [
        {
            "id": m.id,
            "nome": m.nome,
            "template_arquivo": m.template_arquivo,
            "tipo": m.tipo,
            "secoes_necessarias": json.loads(m.secoes_necessarias),
            "ativo": m.ativo,
        }
        for m in modelos
    ]


@router.post("/modelos")
def criar_modelo(
    data: ModeloCreate,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin"])),
):
    """Cria novo modelo de relatório."""
    modelo = ModeloRelatorio(
        nome=data.nome,
        template_arquivo=data.template_arquivo,
        tipo=data.tipo,
        secoes_necessarias=json.dumps(data.secoes_necessarias),
        ativo=data.ativo,
    )
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return {"id": modelo.id, "message": "Modelo criado com sucesso"}


@router.patch("/modelos/{modelo_id}")
def atualizar_modelo(
    modelo_id: int,
    data: ModeloUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin"])),
):
    """Atualiza campos de um modelo de relatório."""
    modelo = db.query(ModeloRelatorio).filter(ModeloRelatorio.id == modelo_id).first()
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")

    if data.nome is not None:
        modelo.nome = data.nome
    if data.template_arquivo is not None:
        modelo.template_arquivo = data.template_arquivo
    if data.tipo is not None:
        modelo.tipo = data.tipo
    if data.secoes_necessarias is not None:
        modelo.secoes_necessarias = json.dumps(data.secoes_necessarias)
    if data.ativo is not None:
        modelo.ativo = data.ativo

    db.commit()
    return {"message": "Modelo atualizado com sucesso"}


@router.delete("/modelos/{modelo_id}")
def desativar_modelo(
    modelo_id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin"])),
):
    """Desativa um modelo (soft delete — ativo=False)."""
    modelo = db.query(ModeloRelatorio).filter(ModeloRelatorio.id == modelo_id).first()
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    modelo.ativo = False
    db.commit()
    return {"message": "Modelo desativado"}
