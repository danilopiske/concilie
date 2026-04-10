
import logging
import os
import shutil
import traceback
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile
from sqlalchemy.orm import Session

# Legacy logic imports — via adapter (L-01 isolation)
from app.adapters.proc_importacao_adapter import (
    classificar_e_gravar_recebiveis,
    classificar_e_gravar_vendas,
    normalizar_dataframe_recebiveis,
    normalizar_dataframe_vendas,
    preparar_dataframe_de_arquivo,
)
from app.core.config import settings
from app.models.import_task import ImportTask
from app.repositories.processamento_repository import gerar_novo_id as processamento_gerar_novo_id
from app.repositories.processamento_repository import salvar as processamento_salvar


class ImportService:
    def __init__(self, db: Session):
        self.db = db
        # Ensure temp directory exists
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)

    async def preview_upload(
        self,
        files: List[UploadFile],
        cliente_id: int,
        ec_id: str,
        contexto: str,
        tipo: str,
        usuario: str
    ) -> Dict[str, Any]:
        """
        Step 1: Upload and Preview
        - Saves files/extracts ZIP to temp
        - Normalizes all data
        - Returns combined preview rows and a list of file_ids
        """
        all_dfs = []
        file_ids = []
        original_names = []
        total_lines = 0

        # Directory for this batch
        batch_id = str(uuid.uuid4())
        batch_dir = self.temp_dir / batch_id
        batch_dir.mkdir(exist_ok=True)

        try:
            # Process counter to limit work in preview
            files_processed_count = 0
            MAX_FILES_PREVIEW = 5
            MAX_ROWS_PER_FILE = 2000

            for file in files:
                # 1. Save or Extract
                filename = f"{uuid.uuid4()}_{file.filename}"
                temp_path = batch_dir / filename

                with temp_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # Check if it's a ZIP
                if file.filename.lower().endswith(".zip"):
                    extract_dir = batch_dir / f"extracted_{uuid.uuid4().hex}"
                    extract_dir.mkdir(exist_ok=True)
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)

                    # Remove the ZIP itself after extraction to only process contents
                    temp_path.unlink()

                    # Add all files in ZIP to processing list (recursive)
                    for root, _, filenames in os.walk(extract_dir):
                        for f in filenames:
                            if f.lower().endswith(('.csv', '.xlsx', '.xls', '.txt')):
                                file_full_path = Path(root) / f
                                file_ids.append(str(file_full_path.relative_to(self.temp_dir)))
                                original_names.append(f)

                                # Only process for preview if below limit
                                if files_processed_count < MAX_FILES_PREVIEW:
                                    all_dfs.append(self._process_single_file(
                                        file_full_path, cliente_id, ec_id, contexto, tipo, usuario,
                                        row_limit=MAX_ROWS_PER_FILE
                                    ))
                                    files_processed_count += 1
                else:
                    # Single file
                    file_ids.append(str(temp_path.relative_to(self.temp_dir)))
                    original_names.append(file.filename)

                    if files_processed_count < MAX_FILES_PREVIEW:
                        all_dfs.append(self._process_single_file(
                            temp_path, cliente_id, ec_id, contexto, tipo, usuario,
                            row_limit=MAX_ROWS_PER_FILE
                        ))
                        files_processed_count += 1

            if not all_dfs:
                raise HTTPException(status_code=400, detail="No valid files found for processing.")

            # Combine all results for preview
            df_norm = pd.concat(all_dfs, ignore_index=True)
            total_lines_preview = len(df_norm)

            if total_lines_preview == 0:
                print(f"\n[IMPORT_SERVICE] PREVIEW EMPTY for {original_names} | Context: {contexto}")
                
                logger.warning(f"Nenhuma linha mapeada no preview para {len(original_names)} arquivos no contexto {contexto}")
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Nenhuma linha foi mapeada nos {len(original_names)} arquivos analisados. "
                        f"Isso ocorre geralmente quando o Layout ({contexto}) não possui regras de De-Para ativas "
                        "ou as colunas do arquivo não coincidem com as regras. Verifique as configurações."
                    )
                )

            # 4. Prepare Preview Data (First 50 rows)
            preview_data = df_norm.head(50).fillna("").astype(str).to_dict(orient="records")

            return {
                "file_id": batch_id,
                "file_ids": file_ids,
                "original_names": original_names,
                "total_files": len(original_names),
                "total_rows_preview": total_lines_preview,
                "preview": preview_data,
                "columns": list(df_norm.columns),
                "is_partial": len(original_names) > MAX_FILES_PREVIEW,
                "files_in_preview": files_processed_count
            }

        except Exception as e:
            logger.exception("ERROR in preview_upload: %s", e)

            # Cleanup on error
            if batch_dir.exists():
                try:
                    shutil.rmtree(batch_dir, ignore_errors=True)
                except Exception as cleanup_err:
                    logger.warning("Cleanup failed (ignored): %s", cleanup_err)

            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Failed to process files: {str(e)}")

    def _process_single_file(self, path: Path, cliente_id: int, ec_id: str, contexto: str, tipo: str, usuario: str, row_limit: Optional[int] = None) -> pd.DataFrame:
        """Helper to process a single file and return its normalized DF"""
        engine = self.db.get_bind()
        def progress_cb(val, message=None):
            logger.debug(f"[IMPORT_SERVICE_CB] Progress: {val}% - {message}")
            pass
        
        def log_cb(msg): 
            print(f"[IMPORT_SERVICE_CB] {msg}")
            
        logger.info(f"[IMPORT_SERVICE] Chamando preparar_dataframe_de_arquivo para {path.name}")

        df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
            path=str(path),
            engine=engine,
            cliente_id=cliente_id,
            ec_id=ec_id,
            usuario=usuario,
            contexto=contexto,
            tipo_origem=tipo,
            progress_callback=progress_cb,
            log_callback=log_cb,
            nrows=row_limit
        )

        # Apply row limit for preview to avoid heavy normalization on huge files
        if row_limit and len(df_mapeado) > row_limit:
            df_mapeado = df_mapeado.head(row_limit)

        # Normalize based on type
        if tipo == "R":
            df_norm = normalizar_dataframe_recebiveis(
                df_mapeado, engine, ec_id, contexto, usuario
            )
        else:
            df_proc, df_filt = normalizar_dataframe_vendas(
                df_mapeado, engine, ec_id, contexto, usuario, tipo_arquivo=tipo
            )
            df_norm = pd.concat([df_proc, df_filt], ignore_index=True) if not df_filt.empty else df_proc

        return df_norm

    def confirm_import(
        self,
        file_id: str,
        cliente_id: int,
        ec_id: str,
        contexto: str,
        tipo: str,
        usuario: str,
        processamentoid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 2: Confirm and Save
        - file_id: batch_id (folder name)
        - Reads all files in the batch folder
        - Processes and saves each to DB
        - Aggregates results
        - Deletes the whole batch folder
        """
        batch_dir = self.temp_dir / file_id

        if not batch_dir.exists():
            raise HTTPException(status_code=404, detail="Session expired or not found. Please upload again.")

        aggregated_result = {
            "processadas": 0,
            "filtradas": 0,
            "total": 0,
            "files_processed": 0,
            "processamentoid": processamentoid
        }

        try:
            engine = self.db.get_bind()

            # Find all files in the batch dir (including extracted ones)
            all_files = []
            for root, _, filenames in os.walk(batch_dir):
                for f in filenames:
                    all_files.append(Path(root) / f)

            if not all_files:
                 raise HTTPException(status_code=400, detail="No files found in batch for confirmation.")

            for file_path in all_files:
                # Re-parse
                def progress_cb(val): pass
                def log_cb(msg): pass

                df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
                    path=str(file_path),
                    engine=engine,
                    cliente_id=cliente_id,
                    contexto=contexto,
                    tipo_origem=tipo,
                    progress_callback=progress_cb,
                    log_callback=log_cb
                )

                # Process and Save
                if tipo == "R":
                    result_data = classificar_e_gravar_recebiveis(
                        engine=engine,
                        df=df_mapeado,
                        cliente_id=cliente_id,
                        ec_id=ec_id,
                        contexto=contexto,
                        usuario=usuario,
                        arquivo_origem=file_path.name,
                        processamentoid=aggregated_result["processamentoid"]
                    )
                else:
                    result_data = classificar_e_gravar_vendas(
                        engine=engine,
                        df=df_mapeado,
                        cliente_id=cliente_id,
                        ec_id=ec_id,
                        contexto=contexto,
                        usuario=usuario,
                        arquivo_origem=file_path.name,
                        processamentoid=aggregated_result["processamentoid"]
                    )

                # Update aggregated result
                aggregated_result["processadas"] += result_data.get("processadas", 0)
                aggregated_result["filtradas"] += result_data.get("filtradas", 0)
                aggregated_result["total"] += result_data.get("total", 0)
                aggregated_result["files_processed"] += 1

                # If we generated a new processamentoid in the first file, reuse it for others
                if not aggregated_result["processamentoid"]:
                    aggregated_result["processamentoid"] = result_data.get("processamentoid")

            return {
                "status": "success",
                "message": f"Successfully processed {aggregated_result['files_processed']} files.",
                "data": aggregated_result
            }

        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "... [TRUNCATED]"
            logger.error("Error saving batch to DB: %s", error_msg)
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to save data: {error_msg}")

        finally:
            # Always clean up the WHOLE batch directory
            if batch_dir.exists():
                try:
                    shutil.rmtree(batch_dir)
                except Exception:
                    pass

    def create_import_task(self, cliente_id: int, tipo_arquivo: str, contexto: str, usuario: str, file_id: str, ec_id: str = None, processamentoid: int = None) -> ImportTask:
        task = ImportTask(
            cliente_id=cliente_id,
            status="PENDING",
            progress=0,
            message="Aguardando início...",
            tipo_arquivo=tipo_arquivo,
            contexto=contexto,
            usuario=usuario,
            metadata_json={
                "file_id": file_id,
                "ec_id": ec_id,
                "processamentoid": processamentoid
            }
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[ImportTask]:
        return self.db.query(ImportTask).filter(ImportTask.id == task_id).first()

    def get_active_tasks(self, cliente_id: Optional[int] = None) -> List[ImportTask]:
        """Gets recently active tasks for the dashboard."""
        from datetime import timedelta
        recent_threshold = datetime.now() - timedelta(hours=1)
        query = self.db.query(ImportTask).filter(
            ImportTask.status.in_(["PENDING", "PROCESSING"]),
            ImportTask.updated_at >= recent_threshold
        )
        if cliente_id:
            query = query.filter(ImportTask.cliente_id == cliente_id)
        return query.all()

    async def run_async_import(self, task_id: str):
        """Worker function for async import. Runs in a separate thread to avoid blocking event loop."""
        from fastapi.concurrency import run_in_threadpool

        from app.core.database import SessionLocal

        # Create a FRESH session for the background task
        # This prevents issues with closed sessions from the original request
        with SessionLocal() as db:
            # We need to re-fetch the task using the new session
            task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                logger.warning("Task %s not found in background worker", task_id)
                return

            try:
                task.status = "PROCESSING"
                task.message = "Processando arquivo..."
                task.progress = 5
                db.commit()

                # Retrieve metadata
                meta = task.metadata_json or {}
                file_id = meta.get("file_id")
                ec_id = meta.get("ec_id")
                contexto = task.contexto
                tipo = task.tipo_arquivo
                processamentoid = meta.get("processamentoid")

                # Callback that uses the background DB session
                def progress_callback(progress_val: int, message: Optional[str] = None):
                    # Scale the underlying progress (0-100) to 5-95 range
                    scaled_progress = 5 + int(progress_val * 0.9)
                    task.progress = min(scaled_progress, 99)
                    if message:
                        task.message = message
                    try:
                        logger.debug(f"[ASYNC] Atualizando progresso no DB: {task.progress}% - {task.message}")
                        db.commit()
                        logger.debug("[ASYNC] Progresso atualizado.")
                    except Exception as e_commit:
                        db.rollback()
                        logger.error(f"[ASYNC] Erro ao commitar progresso: {e_commit}")

                # RUN HEAVY SYNC WORK IN THREADPOOL
                # This is CRITICAL to keep the FastAPI event loop free for other requests (like Status)
                await run_in_threadpool(
                    self.confirm_import_v2,
                    file_id=file_id,
                    cliente_id=task.cliente_id,
                    ec_id=ec_id,
                    contexto=contexto,
                    tipo=tipo,
                    usuario=task.usuario,
                    processamentoid=processamentoid,
                    progress_callback=progress_callback,
                    worker_db=db # Pass the background session
                )

                task.status = "SUCCESS"
                task.progress = 100
                task.message = "Importação concluída com sucesso!"
                db.commit()

                # Notificação (não-bloqueante)
                try:
                    from app.services.notificacao_service import NotificacaoService
                    NotificacaoService.criar(
                        db,
                        tipo="importacao_ok",
                        titulo="Importação concluída",
                        mensagem="Arquivo importado com sucesso.",
                        link="/importar/processamentos",
                        usuario_id=None,
                    )
                except Exception:
                    pass

            except Exception as e:
                db.rollback()
                error_msg = str(e)
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "... [TRUNCATED]"

                task.status = "FAILED"
                task.message = f"Erro: {error_msg}"[:255]
                db.commit()
                logger.error("Async Task Error: %s", error_msg)
                traceback.print_exc()

                # Notificação (não-bloqueante)
                try:
                    from app.services.notificacao_service import NotificacaoService
                    NotificacaoService.criar(
                        db,
                        tipo="importacao_erro",
                        titulo="Erro na importação",
                        mensagem=f"Ocorreu um erro durante a importação: {error_msg[:200]}",
                        link="/importar/processamentos",
                        usuario_id=None,
                    )
                except Exception:
                    pass

    def confirm_import_v2(
        self,
        file_id: str,
        cliente_id: int,
        ec_id: str,
        contexto: str,
        tipo: str,
        usuario: str,
        processamentoid: Optional[str] = None,
        progress_callback = None,
        worker_db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Refactored version of confirm_import that supports callbacks.
        worker_db: optional session to use instead of self.db (for background tasks)
        """
        # Use provided session or instance session
        db = worker_db or self.db

        batch_dir = self.temp_dir / file_id

        if not batch_dir.exists():
            raise HTTPException(status_code=404, detail="Session expired or not found. Please upload again.")

        aggregated_result = {
            "processadas": 0,
            "filtradas": 0,
            "total": 0,
            "files_processed": 0,
            "processamentoid": processamentoid
        }

        try:
            engine = db.get_bind()

            # Find all files in the batch dir (including extracted ones)
            all_files = []
            for root, _, filenames in os.walk(batch_dir):
                for f in filenames:
                    all_files.append(Path(root) / f)

            if not all_files:
                 raise HTTPException(status_code=400, detail="No files found in batch for confirmation.")

            total_files = len(all_files)
            for i, file_path in enumerate(all_files):
                if progress_callback:
                    file_progress_start = int((i / total_files) * 100)
                    progress_callback(file_progress_start, f"Processando arquivo {i+1}/{total_files}: {file_path.name}")

                # Inner callback for the processing logic
                def inner_progress(val, message=None):
                    if progress_callback:
                        # Scale the file internal progress (0-100) to its share of total progress
                        share = 100 / total_files
                        current_file_progress = file_progress_start + int(val * (share / 100))
                        progress_callback(current_file_progress, message)

                df_mapeado, transf, idx = preparar_dataframe_de_arquivo(
                    path=str(file_path),
                    engine=engine,
                    cliente_id=cliente_id,
                    contexto=contexto,
                    tipo_origem=tipo,
                    progress_callback=inner_progress,
                    log_callback=print
                )

                # Process and Save
                if tipo == "R":
                    result_data = classificar_e_gravar_recebiveis(
                        engine=engine,
                        df=df_mapeado,
                        cliente_id=cliente_id,
                        ec_id=ec_id,
                        contexto=contexto,
                        usuario=usuario,
                        arquivo_origem=file_path.name,
                        processamentoid=aggregated_result["processamentoid"],
                        progress_callback=inner_progress # Pass the callback
                    )
                else:
                    result_data = classificar_e_gravar_vendas(
                        engine=engine,
                        df=df_mapeado,
                        cliente_id=cliente_id,
                        ec_id=ec_id,
                        contexto=contexto,
                        usuario=usuario,
                        arquivo_origem=file_path.name,
                        processamentoid=aggregated_result["processamentoid"],
                        progress_callback=inner_progress # Pass the callback
                    )

                # Update aggregated result
                aggregated_result["processadas"] += result_data.get("processadas", 0)
                aggregated_result["filtradas"] += result_data.get("filtradas", 0)
                aggregated_result["total"] += result_data.get("total", 0)
                aggregated_result["files_processed"] += 1

                # If we generated a new processamentoid in the first file, reuse it for others
                if not aggregated_result["processamentoid"]:
                    aggregated_result["processamentoid"] = result_data.get("processamentoid")

            return {
                "status": "success",
                "message": f"Successfully processed {aggregated_result['files_processed']} files.",
                "data": aggregated_result
            }

        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 500:
                error_msg = error_msg[:500] + "... [TRUNCATED]"
            logger.error("Error saving batch to DB (v2): %s", error_msg)
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to save data: {error_msg}")

        finally:
            # Always clean up the WHOLE batch directory
            if batch_dir.exists():
                try:
                    shutil.rmtree(batch_dir)
                except Exception:
                    pass

