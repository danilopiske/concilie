
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# Simple in-memory task store (Replace with Redis for production)
# Structure: { task_id: { status: 'pending'|'processing'|'completed'|'failed', result: Any, error: str } }
TASK_STORE: Dict[str, Dict[str, Any]] = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("background_tasks")

class TaskManager:
    @staticmethod
    def create_task(task_type: str, metadata: Dict[str, Any] = None) -> str:
        """Creates a new task entry and returns its ID."""
        task_id = str(uuid4())
        TASK_STORE[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "progress": 0
        }
        return task_id

    @staticmethod
    def update_task(task_id: str, status: str, result: Any = None, error: str = None, progress: int = None):
        """Updates task status."""
        if task_id in TASK_STORE:
            TASK_STORE[task_id]["status"] = status
            TASK_STORE[task_id]["updated_at"] = datetime.now().isoformat()
            if result:
                TASK_STORE[task_id]["result"] = result
            if error:
                TASK_STORE[task_id]["error"] = error
            if progress is not None:
                TASK_STORE[task_id]["progress"] = progress

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        return TASK_STORE.get(task_id)

async def process_import_task(task_id: str, file_path: str):
    """
    Background worker for processing file imports using Polars.
    """
    from app.services.parser_service import ParserService

    logger.info(f"Starting task {task_id} for file {file_path}")
    TaskManager.update_task(task_id, "processing", progress=10)

    try:
        # Offload CPU-bound Polars work to a thread if necessary,
        # but Polars releases GIL so it's often fine directly.
        # For very large files, run in executor.
        loop = asyncio.get_event_loop()

        # 1. Parse File
        result = await loop.run_in_executor(None, ParserService.read_excel_polars, file_path)

        if not result["success"]:
            raise Exception(result.get("error", "Unknown parsing error"))

        TaskManager.update_task(task_id, "processing", progress=50)

        # 2. (Future) Save to DB Logic Here
        # For now, we just return the metadata

        final_result = {
            "rows_processed": result["rows"],
            "columns": result["columns"],
            "file_path": file_path
        }

        TaskManager.update_task(task_id, "completed", result=final_result, progress=100)
        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        TaskManager.update_task(task_id, "failed", error=str(e))
