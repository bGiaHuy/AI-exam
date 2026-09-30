"""Coordinate clip publication and reversible staging of evidence deletions."""

import json
import logging
import os
import threading
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Incident
from services.db_queue import db_write_queue

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
evidence_file_lock = threading.RLock()
MEDIA_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm", ".mkv", ".jpg", ".png"}


def _filenames(incidents):
    return {os.path.basename(path) for row in incidents
            for path in (row.video_path, row.snapshot_path) if path}


def _restore(operation: Path, evidence_dir: Path):
    """Never overwrite newer evidence when recovering an interrupted deletion."""
    for staged in operation.iterdir():
        if staged.name == "manifest.json":
            continue
        destination = evidence_dir / staged.name
        if destination.exists():
            raise RuntimeError(f"Evidence restore conflict: {staged.name}")
        staged.rename(destination)
    (operation / "manifest.json").unlink()
    operation.rmdir()


def _cleanup(operation: Path):
    failed = []
    for staged in operation.iterdir():
        if staged.name == "manifest.json":
            continue
        try:
            staged.unlink()
        except OSError:
            logger.exception("[EVIDENCE_DELETE] Cleanup failed for %s", staged.name)
            failed.append(staged.name)
    if not failed:
        try:
            (operation / "manifest.json").unlink()
            operation.rmdir()
        except OSError:
            logger.exception("[EVIDENCE_DELETE] Could not remove deletion journal %s", operation.name)
            failed.append(operation.name)
    return failed


def _recover(db: Session, evidence_dir: Path, trash_dir: Path):
    """Use SQLite as the authority after a crash between file staging and commit."""
    failed = []
    if not trash_dir.exists():
        return failed
    for operation in trash_dir.iterdir():
        if not operation.is_dir():
            continue
        manifest_path = operation / "manifest.json"
        if not manifest_path.exists():
            # Empty directories can remain after successful journal cleanup.
            if not any(operation.iterdir()):
                operation.rmdir()
                continue
            raise RuntimeError(f"Missing deletion journal: {operation.name}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ids = manifest["incident_ids"]
        rows_remain = any(db.get(Incident, incident_id) is not None for incident_id in ids)
        if rows_remain:
            logger.warning("[EVIDENCE_DELETE] Restoring uncommitted operation=%s", operation.name)
            _restore(operation, evidence_dir)
        else:
            failed.extend(_cleanup(operation))
    return failed


def delete_evidence(db: Session, evidence_dir: str, incident_id=None):
    """Stage files, commit deletion, then unlink; failed commits restore originals.

    Clip exporters share the lock and enqueue their DB writes before releasing it.
    Draining the queue here prevents purging a clip before its row becomes visible.
    A private journal outside /evidence retains any cleanup that needs a retry.
    """
    root = Path(evidence_dir).resolve()
    trash = root.parent / ".evidence-trash"
    with evidence_file_lock:
        if not db_write_queue.wait_until_idle(timeout=5.0):
            raise RuntimeError("Hàng đợi lưu bằng chứng đang bận; vui lòng thử lại.")
        operation = None
        committed = False
        try:
            db.execute(text("BEGIN IMMEDIATE"))
            failed = _recover(db, root, trash)
            if failed:
                db.rollback()
                return dict(success=False, deleted_files_count=0, deleted_records_count=0,
                            failed_files=failed, message="Chưa xóa hết tệp từ lần trước; vui lòng thử lại.")
            query = db.query(Incident)
            rows = query.filter(Incident.id == incident_id).all() if incident_id else query.all()
            if incident_id and not rows:
                db.rollback()
                return None
            names = _filenames(rows)
            if incident_id:
                names -= _filenames(query.filter(Incident.id != incident_id).all())
            elif root.exists():
                # No exporter can be writing these files while the lock is held.
                names.update(p.name for p in root.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS)
            files = [root / name for name in sorted(names) if (root / name).is_file()]
            trash.mkdir(parents=True, exist_ok=True)
            operation = trash / uuid.uuid4().hex
            operation.mkdir()
            manifest = {"incident_ids": [row.id for row in rows]}
            with (operation / "manifest.json").open("w", encoding="utf-8") as stream:
                json.dump(manifest, stream)
                stream.flush()
                os.fsync(stream.fileno())
            for path in files:
                path.rename(operation / path.name)
            for row in rows:
                db.delete(row)
            db.commit()
            committed = True
            failed = _cleanup(operation)
            logger.info("[EVIDENCE_DELETE] Committed records=%s files=%s cleanup_failed=%s",
                        len(rows), len(files), len(failed))
            return dict(success=not failed, deleted_files_count=max(0, len(files) - len(failed)),
                        deleted_records_count=len(rows), failed_files=failed,
                        message=("Đã xóa sự cố và bằng chứng." if not failed else
                                 "Đã xóa bản ghi nhưng còn tệp chờ dọn dẹp; vui lòng thử lại."))
        except Exception:
            logger.exception("[EVIDENCE_DELETE] Failed incident=%s committed=%s", incident_id or "all", committed)
            db.rollback()
            if operation is not None and not committed and (operation / "manifest.json").exists():
                try:
                    _restore(operation, root)
                except Exception:
                    logger.exception("[EVIDENCE_DELETE] Recovery required for operation=%s", operation.name)
            raise
