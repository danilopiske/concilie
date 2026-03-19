import os
import shutil
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.relatorio_task import RelatorioTask
from app.core.database import engine
from app.services.abusividade_relatorio_service import AbusividadeRelatorioService

# Legacy imports
from modules.reports import gerar_relatorio_html, gerar_relatorio_mensal_html

class RelatorioService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, processamento_id: str, tipo_relatorio: str, usuario: str, metadata: dict = None) -> RelatorioTask:
        task = RelatorioTask(
            processamento_id=processamento_id,
            tipo_relatorio=tipo_relatorio,
            usuario=usuario,
            status="PENDING",
            progress=0,
            message="Aguardando início...",
            metadata_json=metadata
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> RelatorioTask:
        return self.db.query(RelatorioTask).filter(RelatorioTask.id == task_id).first()

    def list_tasks(self, skip: int = 0, limit: int = 100, processamento_id: str = None) -> list[RelatorioTask]:
        query = self.db.query(RelatorioTask)
        if processamento_id:
            query = query.filter(RelatorioTask.processamento_id == processamento_id)
        return query.order_by(RelatorioTask.created_at.desc()).offset(skip).limit(limit).all()

    def update_task_progress(self, task_id: str, progress: int, message: str):
        # Usar nova sessão para evitar conflitos de transação no background
        with Session(engine) as session:
            task = session.query(RelatorioTask).filter(RelatorioTask.id == task_id).first()
            if task:
                task.progress = progress
                task.message = message
                session.commit()

    def run_async_report(self, task_id: str):
        # Usar uma nova sessão dedicada para todo o processo em background
        # Isso evita usar a sessão do request original que é fechada quando a API responde
        with Session(engine) as session:
            try:
                # Buscar a task com a nova sessão
                task = session.get(RelatorioTask, task_id)
                if not task: 
                    print(f"Task {task_id} não encontrada para processamento async")
                    return

                def update_progress(pct, msg):
                    task.progress = pct
                    task.message = msg
                    session.commit()

                task.status = "PROCESSING"
                update_progress(5, "Preparando ambiente...")

                metadata = task.metadata_json or {}
                
                # Extract filters from metadata
                calc_tipo = metadata.get('calc_tipo')
                adquirente = metadata.get('adquirente')
                data_inicio = metadata.get('data_inicio')
                data_fim = metadata.get('data_fim')
                incluir_filtradas = metadata.get('incluir_filtradas', False)
                incluir_recebiveis_filtrados = metadata.get('incluir_recebiveis_filtrados', False)
                apenas_com_perdas = metadata.get('apenas_com_perdas', False)
                mes_referencia = metadata.get('mes_referencia')

                # Convert date strings back to objects if they are strings
                if isinstance(data_inicio, str):
                    data_inicio = datetime.fromisoformat(data_inicio.split('T')[0])
                if isinstance(data_fim, str):
                    data_fim = datetime.fromisoformat(data_fim.split('T')[0])

                html_path = None
                sintetico_path = None
                abusividade_path = None

                # Callback para funções legadas
                def progress_callback(pct, msg):
                    update_progress(pct, msg)

                if task.tipo_relatorio == "mensal":
                    html_path, _, sintetico_path = gerar_relatorio_mensal_html(
                        engine,
                        str(task.processamento_id),
                        calc_tipo=calc_tipo,
                        mes_referencia=mes_referencia,
                        adquirente=adquirente,
                        incluir_filtradas=incluir_filtradas,
                        incluir_recebiveis_filtrados=incluir_recebiveis_filtrados,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        apenas_com_perdas=apenas_com_perdas,
                        progress_callback=progress_callback
                    )
                else:
                    # Retroativo / Geral
                    html_path, _, sintetico_path = gerar_relatorio_html(
                        engine,
                        str(task.processamento_id),
                        calc_tipo=calc_tipo,
                        adquirente=adquirente,
                        incluir_filtradas=incluir_filtradas,
                        incluir_recebiveis_filtrados=incluir_recebiveis_filtrados,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        apenas_com_perdas=apenas_com_perdas,
                        progress_callback=progress_callback
                    )

                # Gerar Abusividade se solicitado no background
                if metadata.get('gerar_abusividade'):
                    update_progress(95, "Gerando demonstrativo de abusividade...")
                    # Passar a sessão do background para o serviço de abusividade
                    abs_service = AbusividadeRelatorioService(session)
                    abusividade_path = abs_service.gerar_html(
                        str(task.processamento_id),
                        data_inicio=data_inicio,
                        data_fim=data_fim
                    )

                # Finalize task using the SAME background session
                task.status = "SUCCESS"
                task.progress = 100
                task.message = "Relatório concluído!"
                task.result_path = html_path
                task.sintetico_path = sintetico_path
                task.abusividade_path = abusividade_path
                if html_path:
                    task.excel_path = html_path.replace(".html", ".xlsx")
                session.commit()

            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error in async report: {e}\n{error_trace}")
                # Recarregar task se possível para marcar erro
                try:
                    # session.rollback() # Limpar estado se houver erro
                    task = session.get(RelatorioTask, task_id)
                    if task:
                        task.status = "FAILED"
                        task.message = f"Erro: {str(e)}"
                        session.commit()
                except:
                    pass
