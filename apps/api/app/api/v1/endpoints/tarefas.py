"""
Endpoint de resumo de tarefas em background.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.abusividade_task import AbusividadeTask
from app.models.calculo_task import CalculoTask
from app.models.import_task import ImportTask
from app.models.relatorio_task import RelatorioTask

router = APIRouter()


@router.get("/resumo")
def resumo_tarefas(db: Session = Depends(get_db)):
    """Retorna as últimas 5 tasks de cada tipo para o Centro de Progresso."""

    importacoes = (
        db.query(ImportTask)
        .order_by(ImportTask.created_at.desc())
        .limit(5)
        .all()
    )

    calculos = (
        db.query(CalculoTask)
        .order_by(CalculoTask.created_at.desc())
        .limit(5)
        .all()
    )

    relatorios = (
        db.query(RelatorioTask)
        .order_by(RelatorioTask.created_at.desc())
        .limit(5)
        .all()
    )

    abusividades = (
        db.query(AbusividadeTask)
        .order_by(AbusividadeTask.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "importacoes": [
            {
                "id": t.id,
                "status": t.status,
                "progress": t.progress,
                "usuario": t.usuario,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in importacoes
        ],
        "calculos": [
            {
                "id": t.id,
                "status": t.status,
                "progress": t.progress,
                "usuario": t.usuario,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in calculos
        ],
        "relatorios": [
            {
                "id": t.id,
                "status": t.status,
                "progress": t.progress,
                "usuario": t.usuario,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in relatorios
        ],
        "abusividades": [
            {
                "id": t.id,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in abusividades
        ],
    }
