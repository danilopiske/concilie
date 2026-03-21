from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.processamento_repository import ProcessamentoRepository
from app.schemas.processamento import ProcessamentoFilter, ProcessamentoResponse

router = APIRouter()

@router.get("/", response_model=List[ProcessamentoResponse])
def listar_processamentos(
    cliente_id: int = None,
    status: str = None,
    simple: bool = False,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    repo = ProcessamentoRepository(db)
    filtro = ProcessamentoFilter(cliente_id=cliente_id, status=status)
    return repo.listar(skip=skip, limit=limit, filtros=filtro, simple=simple)

@router.post("/batch-delete")
def deletar_processamentos(
    ids: List[str],
    db: Session = Depends(get_db)
):
    repo = ProcessamentoRepository(db)
    return {"success": repo.deletar_lista(ids), "count": len(ids)}


@router.get("/{processamento_id}/detalhes")
def detalhes_processamento(
    processamento_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Consolida todas as informações de um processamento."""
    from app.models.abusividade_task import AbusividadeTask
    from app.models.calculo_task import CalculoTask
    from app.models.relatorio_task import RelatorioTask

    def _dt(val: Any) -> Optional[str]:
        return val.isoformat() if val and hasattr(val, "isoformat") else val

    def _serializar_calculo(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "usuario": t.usuario,
            "progress": t.progress,
        }

    def _serializar_relatorio(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "usuario": t.usuario,
            "progress": t.progress,
            "tipo_relatorio": t.tipo_relatorio,
            "result_path": t.result_path,
        }

    def _serializar_abusividade(t: Any) -> Dict[str, Any]:
        return {
            "id": t.id,
            "status": t.status,
            "created_at": _dt(t.created_at),
            "result_path": t.result_path,
        }

    calculos = (
        db.query(CalculoTask)
        .filter(CalculoTask.processamento_id == processamento_id)
        .order_by(CalculoTask.created_at.desc())
        .all()
    )
    relatorios = (
        db.query(RelatorioTask)
        .filter(RelatorioTask.processamento_id == processamento_id)
        .order_by(RelatorioTask.created_at.desc())
        .all()
    )
    abusividades = (
        db.query(AbusividadeTask)
        .filter(AbusividadeTask.processamento_id == processamento_id)
        .order_by(AbusividadeTask.created_at.desc())
        .all()
    )

    todas_tasks = (
        [t.status for t in calculos]
        + [t.status for t in relatorios]
    )

    status_geral = "sem_dados"
    if todas_tasks:
        if any(s in ("PROCESSING", "PENDING", "pending", "processing") for s in todas_tasks):
            status_geral = "em_andamento"
        elif all(s in ("SUCCESS", "ready") for s in todas_tasks):
            status_geral = "concluido"
        elif any(s in ("FAILED", "error") for s in todas_tasks):
            status_geral = "com_erro"
        else:
            status_geral = "parcial"

    return {
        "processamento_id": processamento_id,
        "status_geral": status_geral,
        "totais": {
            "importacoes": 0,
            "calculos": len(calculos),
            "relatorios": len(relatorios),
            "abusividades": len(abusividades),
        },
        "importacoes": [],
        "calculos": [_serializar_calculo(t) for t in calculos[:5]],
        "relatorios": [_serializar_relatorio(t) for t in relatorios[:5]],
        "abusividades": [_serializar_abusividade(t) for t in abusividades[:5]],
    }
