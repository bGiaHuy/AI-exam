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

    Lazy-start design: the worker thread is NOT started on construction or import.
    It starts on the first call to enqueue_incident() or explicitly via start().
    This prevents database side-effects during unit-test import.
    """
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_lock = threading.Lock()
        self._started: bool = False
        self.failed_writes_count: int = 0
        self.successful_writes_count: int = 0
        self.dead_letter_queue: list = []
        self.last_error: Optional[str] = None

    def start(self):
        """Explicitly start the worker thread. Safe to call multiple times."""
        with self._start_lock:
            if self._started:
                return
            self._started = True
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="DBWriteQueueWorker",
                daemon=True
            )
            self._worker_thread.start()
            logger.info("[DB_QUEUE] Background database writer worker started.")

    def get_metrics(self) -> Dict[str, Any]:
        """Return real-time telemetry metrics of the write queue."""
        return {
            "queue_size": self._queue.qsize(),
            "successful_writes": self.successful_writes_count,
            "failed_writes": self.failed_writes_count,
            "dead_letter_count": len(self.dead_letter_queue),
            "last_error": self.last_error,
        }

    def get_dead_letter_queue(self) -> list:
        """Return a copy of all failed / rejected tasks."""
        return list(self.dead_letter_queue)

    def enqueue_incident(self, incident_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Enqueue an incident record insertion task. Starts the worker on first call."""
        self.start()  # lazy-start on first real use
        data = dict(incident_data) if incident_data else {}
        data.update(kwargs)
        self._queue.put(data)

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
        try:
            from confidence import normalize_confidence, InvalidConfidenceError
        except ImportError:
            from backend.confidence import normalize_confidence, InvalidConfidenceError

        while not self._stop_event.is_set():
            try:
                task_data = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            db = SessionLocal()
            try:
                # Canonical confidence normalization: canonical stored value in [0.0, 1.0]
                # Reject invalid values strictly: no clamping, rollback transaction, log to dead letter queue
                raw_conf = task_data.get("confidence")
                try:
                    conf_val = normalize_confidence(raw_conf)
                except (InvalidConfidenceError, Exception) as ce:
                    db.rollback()
                    self.failed_writes_count += 1
                    err_msg = str(ce)
                    self.last_error = err_msg
                    task_id = task_data.get("id") or task_data.get("incident_id")
                    err_entry = {
                        "task_id": task_id,
                        "raw_confidence": raw_conf,
                        "error": err_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "payload": {k: v for k, v in task_data.items() if k not in ("current_frame", "peak_frame")}
                    }
                    self.dead_letter_queue.append(err_entry)
                    logger.error(
                        f"[DB_QUEUE] [REJECTED_INVALID_CONFIDENCE] Task {task_id} rejected due to invalid confidence ({raw_conf!r}): {err_msg}"
                    )
                    continue

                inc_id = task_data.get("id") or task_data.get("incident_id")
                det_at = task_data.get("detected_at")
                if isinstance(det_at, (int, float)):
                    det_at = datetime.fromtimestamp(det_at, timezone.utc)
                elif not isinstance(det_at, datetime):
                    det_at = datetime.now(timezone.utc)

                clip_start = task_data.get("clip_started_at")
                if isinstance(clip_start, (int, float)):
                    clip_start = datetime.fromtimestamp(clip_start, timezone.utc)
                elif clip_start is not None and not isinstance(clip_start, datetime):
                    clip_start = None

                clip_end = task_data.get("clip_ended_at")
                if isinstance(clip_end, (int, float)):
                    clip_end = datetime.fromtimestamp(clip_end, timezone.utc)
                elif clip_end is not None and not isinstance(clip_end, datetime):
                    clip_end = None

                # Create Incident instance from task data
                incident = Incident(
                    id=inc_id,
                    source_id=task_data.get("source_id", "cam1"),
                    source_label=task_data.get("source_label", "Camera 1"),
                    source_type=task_data.get("source_type", "browser_ws"),
                    session_id=task_data.get("session_id"),
                    track_id=task_data.get("track_id"),
                    violation_type=task_data["violation_type"],
                    confidence=conf_val,
                    level=task_data.get("level", "red"),
                    detected_at=det_at,
                    clip_started_at=clip_start,
                    clip_ended_at=clip_end,
                    video_path=task_data.get("video_path"),
                    snapshot_path=task_data.get("snapshot_path"),
                    status=task_data.get("status", "pending"),
                    proctor_notes=task_data.get("proctor_notes")
                )
                db.add(incident)
                db.commit()
                self.successful_writes_count += 1
                logger.info(f"[DB_QUEUE] Successfully persisted incident {incident.id} into SQLite (confidence={conf_val:.4f}).")
            except Exception as e:
                db.rollback()
                self.failed_writes_count += 1
                self.last_error = str(e)
                task_id = task_data.get("id") or task_data.get("incident_id")
                err_entry = {
                    "task_id": task_id,
                    "raw_confidence": task_data.get("confidence"),
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": {k: v for k, v in task_data.items() if k not in ("current_frame", "peak_frame")}
                }
                self.dead_letter_queue.append(err_entry)
                logger.error(f"[DB_QUEUE] Failed to insert incident {task_id}: {e}", exc_info=True)
            finally:
                db.close()
                self._queue.task_done()

    def shutdown(self):
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

# Global singleton — NOT started on import (lazy-start on first enqueue_incident call)
db_write_queue = DBWriteQueue()