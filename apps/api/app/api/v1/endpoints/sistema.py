"""
Status e métricas do sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/status")
def status_sistema(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["admin"])),
):
    """Retorna métricas consolidadas e saúde do sistema."""
    from app.models.calculo_task import CalculoTask
    from app.models.cliente import Cliente
    from app.models.import_task import ImportTask
    from app.models.relatorio_task import RelatorioTask

    # Testar conexão DB e detectar engine
    db_ok = False
    db_engine = "mysql" if settings.DATABASE_TYPE == "mysql" else "sqlite"
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Contagens totais
    total_clientes = db.query(Cliente).count()
    total_importacoes = db.query(ImportTask).count()
    total_calculos = db.query(CalculoTask).count()
    total_relatorios = db.query(RelatorioTask).count()

    # Tarefas ativas (PROCESSING ou PENDING)
    tarefas_ativas = (
        db.query(ImportTask)
        .filter(ImportTask.status.in_(["PROCESSING", "PENDING"]))
        .count()
        + db.query(CalculoTask)
        .filter(CalculoTask.status.in_(["PROCESSING", "PENDING"]))
        .count()
        + db.query(RelatorioTask)
        .filter(RelatorioTask.status.in_(["PROCESSING", "PENDING"]))
        .count()
    )

    def serializar_task(t):
        return {
            "id": t.id,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    ultimas_importacoes = [
        serializar_task(t)
        for t in db.query(ImportTask)
        .order_by(ImportTask.created_at.desc())
        .limit(3)
        .all()
    ]
    ultimas_calculos = [
        serializar_task(t)
        for t in db.query(CalculoTask)
        .order_by(CalculoTask.created_at.desc())
        .limit(3)
        .all()
    ]
    ultimas_relatorios = [
        serializar_task(t)
        for t in db.query(RelatorioTask)
        .order_by(RelatorioTask.created_at.desc())
        .limit(3)
        .all()
    ]

    return {
        "api": "ok",
        "database": "ok" if db_ok else "erro",
        "db_engine": db_engine,
        "metricas": {
            "total_clientes": total_clientes,
            "total_importacoes": total_importacoes,
            "total_calculos": total_calculos,
            "total_relatorios": total_relatorios,
            "tarefas_ativas": tarefas_ativas,
        },
        "ultimas_tarefas": {
            "importacoes": ultimas_importacoes,
            "calculos": ultimas_calculos,
            "relatorios": ultimas_relatorios,
        },
    }
