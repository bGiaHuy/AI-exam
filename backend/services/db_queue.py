"""
================================================================================
THREAD-SAFE SEQUENTIAL DATABASE WRITE QUEUE FOR SQLITE WAL
================================================================================
Ensures thread-safe serial persistence of incidents from background threads.
Eliminates 'database is locked' operational errors in SQLite.
================================================================================
"""

import queue
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("db_queue")

class DBWriteQueue:
    """
    Dedicated worker thread consuming database write tasks sequentially.
    """
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_worker()

    def _start_worker(self):
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="DBWriteQueueWorker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info("[DB_QUEUE] Background database writer worker started.")

    def enqueue_incident(self, incident_data: Dict[str, Any]):
        """Enqueue an incident record insertion task."""
        self._queue.put(incident_data)

    def wait_until_idle(self, timeout: float = 5.0) -> bool:
        """Wait until all tasks in queue are processed."""
        import time
        start = time.time()
        while not self._queue.empty() or self._queue.unfinished_tasks > 0:
            if time.time() - start > timeout:
                return False
            time.sleep(0.05)
        return True

    def _worker_loop(self):
        from database import SessionLocal
        from models import Incident

        while not self._stop_event.is_set():
            try:
                task_data = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            db = SessionLocal()
            try:
                # Create Incident instance from task data
                incident = Incident(
                    id=task_data["id"],
                    source_id=task_data.get("source_id", "webcam_local"),
                    track_id=task_data.get("track_id"),
                    violation_type=task_data["violation_type"],
                    confidence=float(task_data.get("confidence", 0.0)),
                    level=task_data.get("level", "red"),
                    detected_at=task_data.get("detected_at", datetime.now(timezone.utc)),
                    clip_started_at=task_data.get("clip_started_at"),
                    clip_ended_at=task_data.get("clip_ended_at"),
                    video_path=task_data.get("video_path"),
                    snapshot_path=task_data.get("snapshot_path"),
                    status=task_data.get("status", "pending"),
                    proctor_notes=task_data.get("proctor_notes")
                )
                db.add(incident)
                db.commit()
                logger.info(f"[DB_QUEUE] Successfully persisted incident {incident.id} into SQLite.")
            except Exception as e:
                db.rollback()
                logger.error(f"[DB_QUEUE] Failed to insert incident {task_data.get('id')}: {e}", exc_info=True)
            finally:
                db.close()
                self._queue.task_done()

    def shutdown(self):
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

# Global singleton
db_write_queue = DBWriteQueue()
