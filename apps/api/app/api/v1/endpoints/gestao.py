"""
Gestao Endpoints - Management operations
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.schemas.bandeira import (
    BandeiraClienteUpdate,
    BandeiraDisponivelCreate,
    BandeiraDisponivelResponse,
    BandeiraDisponivelUpdate,
)
from app.schemas.contexto import ContextoCreate, ContextoResponse
from app.schemas.taxa import TaxaCreate, TaxaResponse
from app.schemas.termo import TermoFiltravelCreate, TermoFiltravelResponse, TermoFiltravelUpdate
from app.services.gestao_service import GestaoService

router = APIRouter()


# Contextos
@router.get("/contextos", response_model=List[ContextoResponse])
async def listar_contextos(
    incluir_inativos: bool = False, db: Session = Depends(get_db)
):
    """List contextos"""
    service = GestaoService(db)
    return service.listar_contextos(incluir_inativos)


@router.post("/contextos", response_model=dict, status_code=201)
async def criar_contexto(contexto: ContextoCreate, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))):
    """Create contexto"""
    service = GestaoService(db)
    return service.criar_contexto(contexto.model_dump())


# Bandeiras Disponiveis
@router.get("/bandeiras-disponiveis", response_model=List[BandeiraDisponivelResponse])
async def listar_bandeiras_disponiveis(db: Session = Depends(get_db)):
    """List all available bandeiras"""
    service = GestaoService(db)
    return service.listar_bandeiras_disponiveis()


@router.post("/bandeiras-disponiveis", status_code=201)
async def criar_bandeira_disponivel(
    bandeira: BandeiraDisponivelCreate, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))
):
    """Create bandeira disponivel"""
    service = GestaoService(db)
    return service.criar_bandeira_disponivel(bandeira.nome, bandeira.padrao)


@router.put("/bandeiras-disponiveis/{bandeira_id}", response_model=BandeiraDisponivelResponse)
async def atualizar_bandeira_disponivel(
    bandeira_id: int,
    bandeira: BandeiraDisponivelUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin", "operador"])),
):
    """Update bandeira disponivel"""
    service = GestaoService(db)
    result = service.atualizar_bandeira_disponivel(bandeira_id, bandeira.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Bandeira não encontrada")
    return result


@router.delete("/bandeiras-disponiveis/{bandeira_id}", status_code=204)
async def deletar_bandeira_disponivel(bandeira_id: int, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))):
    """Delete bandeira disponivel"""
    service = GestaoService(db)
    service.deletar_bandeira_disponivel(bandeira_id)


# Bandeiras por EC
@router.get("/ecs/{ec}/bandeiras", response_model=Dict[str, int])
async def listar_bandeiras_ec(
    ec: str, contexto: str = "padrao", db: Session = Depends(get_db)
):
    """List bandeiras for EC"""
    service = GestaoService(db)
    return service.listar_bandeiras_ec(ec, contexto)


@router.put("/ecs/{ec}/bandeiras", status_code=204)
async def salvar_bandeiras_ec(
    ec: str, bandeiras: BandeiraClienteUpdate, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))
):
    """Save bandeiras for EC"""
    service = GestaoService(db)
    service.salvar_bandeiras_ec(ec, bandeiras.bandeiras, bandeiras.contexto)


# Termos Filtraveis
@router.get("/ecs/{ec}/termos", response_model=List[TermoFiltravelResponse])
async def listar_termos(
    ec: str,
    contexto: str = "padrao",
    tipo: Optional[str] = Query(None, pattern="^[IE]$"),
    db: Session = Depends(get_db),
):
    """List termos for EC"""
    service = GestaoService(db)
    return service.listar_termos(ec, contexto, tipo)


@router.post("/ecs/{ec}/termos", response_model=TermoFiltravelResponse, status_code=201)
async def adicionar_termo(
    ec: str, termo: TermoFiltravelCreate, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))
):
    """Add termo"""
    service = GestaoService(db)
    return service.adicionar_termo(ec, termo.termo, termo.tipo, termo.contexto)


@router.put("/termos/{termo_id}", response_model=TermoFiltravelResponse)
async def atualizar_termo(
    termo_id: int,
    termo: TermoFiltravelUpdate,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin", "operador"])),
):
    """Update termo"""
    service = GestaoService(db)
    result = service.atualizar_termo(termo_id, termo.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Termo não encontrado")
    return result


@router.delete("/termos/{termo_id}", status_code=204)
async def excluir_termo(termo_id: int, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))):
    """Delete termo"""
    service = GestaoService(db)
    if not service.excluir_termo(termo_id):
        raise HTTPException(status_code=404, detail="Termo não encontrado")


# Taxas
@router.get("/ecs/{ec}/taxas", response_model=List[TaxaResponse])
async def listar_taxas(
    ec: str, contexto: str = "padrao", db: Session = Depends(get_db)
):
    """List taxas for EC"""
    service = GestaoService(db)
    return service.listar_taxas(ec, contexto)


@router.post("/ecs/{ec}/taxas", response_model=TaxaResponse, status_code=201)
async def adicionar_taxa(ec: str, taxa: TaxaCreate, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))):
    """Add taxa"""
    service = GestaoService(db)
    taxa_data = taxa.model_dump()
    taxa_data["ec"] = ec
    return service.adicionar_taxa(taxa_data)


@router.delete("/taxas/{taxa_id}", status_code=204)
async def excluir_taxa(taxa_id: int, db: Session = Depends(get_db), _: Any = Depends(require_role(["admin", "operador"]))):
    """Delete taxa"""
    service = GestaoService(db)
    if not service.excluir_taxa(taxa_id):
        raise HTTPException(status_code=404, detail="Taxa não encontrada")


@router.post("/taxas/copiar", response_model=dict)
async def copiar_taxas(
    ec_origem: str = Query(...),
    ecs_destino: List[str] = Query(...),
    contexto: str = "padrao",
    sobrescrever: bool = False,
    db: Session = Depends(get_db),
    _: Any = Depends(require_role(["admin", "operador"])),
):
    """Copy taxas from one EC to others"""
    service = GestaoService(db)
    return service.copiar_taxas(ec_origem, ecs_destino, contexto, sobrescrever)
