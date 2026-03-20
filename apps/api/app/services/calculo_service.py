import logging

from sqlalchemy.orm import Session

from app.models.calculo_task import CalculoTask

logger = logging.getLogger(__name__)
from typing import Optional

from app.services.reconciliation_core import ReconciliationCore


class CalculoService:
    def __init__(self, db: Session):
        self.db = db

    def create_calculo_task(self, processamento_id: str, tipo_taxa: str, usuario: str, usar_taxa_cad: bool, tem_receba_rapido: bool, substituir: bool = False) -> CalculoTask:
        task = CalculoTask(
            processamento_id=processamento_id,
            status="PENDING",
            progress=0,
            message="Aguardando início...",
            tipo_taxa=tipo_taxa,
            usuario=usuario,
            metadata_json={
                "usar_taxa_cad": usar_taxa_cad,
                "tem_receba_rapido": tem_receba_rapido,
                "substituir": substituir
            }
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[CalculoTask]:
        return self.db.query(CalculoTask).filter(CalculoTask.id == task_id).first()

    def list_tasks(self, skip: int = 0, limit: int = 100, processamento_id: str = None) -> list[CalculoTask]:
        query = self.db.query(CalculoTask)
        if processamento_id:
            query = query.filter(CalculoTask.processamento_id == processamento_id)
        return query.order_by(CalculoTask.created_at.desc()).offset(skip).limit(limit).all()

    async def run_async_calculo(self, task_id: str):
        """Worker function for async calculation."""
        from fastapi.concurrency import run_in_threadpool

        from app.core.database import SessionLocal

        with SessionLocal() as db:
            task = db.query(CalculoTask).filter(CalculoTask.id == task_id).first()
            if not task:
                return

            try:
                task.status = "PROCESSING"
                task.message = "Iniciando reconciliação..."
                task.progress = 5
                db.commit()

                meta = task.metadata_json or {}
                usar_taxa_cad = meta.get("usar_taxa_cad", True)
                tem_receba_rapido = meta.get("tem_receba_rapido", False)

                def progress_callback(progress_val: int, message: Optional[str] = None):
                    task.progress = progress_val
                    if message:
                        task.message = message
                    db.commit()

                engine = db.get_bind()

                from app.repositories.calculo_repository import CalculoRepository
                from app.schemas.calculo import CalculoRequest
                repo = CalculoRepository(db)

                # 1. Prepare/Clean and generate ID
                req = CalculoRequest(
                    processamento_id=task.processamento_id,
                    tipo_taxa=task.tipo_taxa,
                    usar_taxa_cad=meta.get("usar_taxa_cad", True),
                    tem_receba_rapido=meta.get("tem_receba_rapido", False),
                    substituir=meta.get("substituir", False)
                )
                custom_id = repo.processar_calculo(req, usuario_logado=task.usuario)

                # 2. Heavy work in threadpool
                result = await run_in_threadpool(
                    ReconciliationCore.calculate_rates,
                    engine=engine,
                    proc_id=task.processamento_id,
                    tipo_taxa=task.tipo_taxa,
                    usar_taxa_cad=req.usar_taxa_cad,
                    tem_receba_rapido=req.tem_receba_rapido,
                    progress_callback=progress_callback,
                    custom_calc_id=custom_id
                )

                if result.get("success"):
                    task.status = "SUCCESS"
                    task.progress = 100
                    task.message = f"Cálculo concluído! {result.get('rows')} registros processados em {result.get('time'):.2f}s."
                else:
                    task.status = "FAILED"
                    task.message = f"Erro: {result.get('error')}"

                db.commit()

            except Exception as e:
                db.rollback()
                task.status = "FAILED"
                task.message = f"Erro inesperado: {str(e)}"[:255]
                db.commit()
                logger.exception("Erro inesperado na task de cálculo")
