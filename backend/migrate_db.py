"""
================================================================================
HARDENED TRANSACTION-SAFE DATABASE MIGRATION SCRIPT - AI EXAM CONTROL
================================================================================
Ensures safe migration to minimal identity-free schema with transactional safety.
Features:
  1. Unique timestamped backups (never overwrites old backups)
  2. Strict backup verification (file exists, size matches, sqlite integrity check)
  3. Atomic transaction execution with automatic rollback on error
  4. Full rollback and restore capability if migration encounters any error
  5. Idempotent: re-running on already migrated database preserves all records
================================================================================
"""

import os
import sys
import uuid
import shutil
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [migrate_db]: %(message)s")
logger = logging.getLogger("migrate_db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_db = os.getenv("AIEXAM_ISOLATED_DB")
if not _env_db and os.getenv("DATABASE_URL"):
    _url = os.getenv("DATABASE_URL", "")
    if _url.startswith("sqlite:///"):
        _env_db = _url[len("sqlite:///"):]
DB_PATH = os.path.abspath(_env_db) if _env_db else os.path.join(BASE_DIR, "cheating_system.db")

NEW_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(100) PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL DEFAULT 'cam1',
    source_label VARCHAR(100) DEFAULT 'Camera 1',
    source_type VARCHAR(50) DEFAULT 'browser_ws',
    session_id VARCHAR(100),
    track_id INTEGER,
    violation_type VARCHAR(50) NOT NULL,
    confidence REAL NOT NULL,
    level VARCHAR(20) NOT NULL DEFAULT 'red',
    detected_at TIMESTAMP NOT NULL,
    clip_started_at TIMESTAMP,
    clip_ended_at TIMESTAMP,
    video_path VARCHAR(500),
    snapshot_path VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    proctor_notes TEXT,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_incidents_id ON incidents (id);
CREATE INDEX IF NOT EXISTS ix_incidents_source_id ON incidents (source_id);
CREATE INDEX IF NOT EXISTS ix_incidents_session_id ON incidents (session_id);
CREATE INDEX IF NOT EXISTS ix_incidents_track_id ON incidents (track_id);
CREATE INDEX IF NOT EXISTS ix_incidents_detected_at ON incidents (detected_at);
"""


def verify_backup(backup_path: str, original_size: int) -> bool:
    """Verify backup file integrity: existence, non-empty, matches size, and opens cleanly."""
    if not os.path.exists(backup_path):
        logger.error(f"Backup file does not exist: {backup_path}")
        return False

    backup_size = os.path.getsize(backup_path)
    if backup_size != original_size:
        logger.error(f"Backup size mismatch: original={original_size}, backup={backup_size}")
        return False

    try:
        test_conn = sqlite3.connect(backup_path)
        cur = test_conn.cursor()
        cur.execute("PRAGMA quick_check;")
        res = cur.fetchone()
        test_conn.close()
        if res and res[0] == "ok":
            return True
        logger.error(f"Backup integrity check returned: {res}")
        return False
    except Exception as e:
        logger.error(f"Failed to open backup database: {e}")
        return False


def create_verified_backup(target_db_path: str) -> Optional[str]:
    """Create a unique timestamped backup and verify its integrity before modifying database."""
    if not os.path.exists(target_db_path):
        return None

    orig_size = os.path.getsize(target_db_path)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    db_dir = os.path.dirname(target_db_path)
    backup_filename = f"cheating_system_backup_{ts}_{unique_suffix}.db"
    backup_path = os.path.join(db_dir, backup_filename)

    shutil.copy2(target_db_path, backup_path)
    logger.info(f"Created backup file: {backup_path}")

    if not verify_backup(backup_path, orig_size):
        raise RuntimeError(f"Backup verification failed for {backup_path}! Aborting migration to protect data.")

    logger.info(f"Backup verified successfully ({orig_size} bytes, SQLite integrity OK).")
    return backup_path


def migrate_database(db_path: str = DB_PATH) -> Tuple[bool, str]:
    """
    Execute transaction-safe database migration.
    Returns (success: bool, message: str).
    """
    logger.info(f"Starting database migration for: {db_path}")

    if not os.path.exists(db_path):
        logger.info(f"Database {db_path} does not exist. Initializing fresh schema...")
        conn = sqlite3.connect(db_path)
        try:
            conn.executescript(NEW_SCHEMA_SQL)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.commit()
            logger.info("Initialized fresh database with WAL mode.")
            return True, "Fresh database initialized"
        finally:
            conn.close()

    # Step 1: Create verified timestamped backup
    backup_path = None
    try:
        backup_path = create_verified_backup(db_path)
    except Exception as e:
        logger.error(f"Aborting migration: backup creation failed: {e}")
        return False, f"Backup creation failed: {e}"

    # Step 2: Inspect existing database
    conn = sqlite3.connect(db_path)
    conn.isolation_level = None  # Manual transaction management
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Existing tables in database: {tables}")

        old_incidents = []
        is_already_migrated = False

        if "incidents" in tables:
            cursor.execute("PRAGMA table_info(incidents);")
            columns = [info[1] for info in cursor.fetchall()]
            logger.info(f"Existing columns in incidents table: {columns}")

            has_legacy = "student_id" in columns or "room_code" in columns or "source_id" not in columns
            if not has_legacy:
                is_already_migrated = True
                logger.info("Database already conforms to modern identity-free schema. Preserving all records.")
            else:
                logger.info("Detected legacy incidents table. Extracting records for migration...")
                cursor.execute("SELECT * FROM incidents;")
                rows = cursor.fetchall()
                col_map = {col: i for i, col in enumerate(columns)}

                for row in rows:
                    inc_id = row[col_map["id"]]
                    source = row[col_map["room_code"]] if "room_code" in col_map else "webcam_local"
                    vtype = row[col_map["violation_type"]] if "violation_type" in col_map else "PHONE"
                    conf_val = float(row[col_map["confidence"]]) if "confidence" in col_map else 90.0
                    lvl = row[col_map["level"]] if "level" in col_map else "red"
                    vpath = row[col_map["video_path"]] if "video_path" in col_map else None
                    spath = row[col_map["snapshot_path"]] if "snapshot_path" in col_map else None
                    stat = row[col_map["status"]] if "status" in col_map else "pending"
                    notes = row[col_map["proctor_notes"]] if "proctor_notes" in col_map else None
                    dt_val = row[col_map["full_datetime"]] if "full_datetime" in col_map else datetime.now(timezone.utc).isoformat()
                    cr_val = row[col_map["created_at"]] if "created_at" in col_map else datetime.now(timezone.utc).isoformat()

                    old_incidents.append((
                        inc_id, source, None, vtype, conf_val, lvl,
                        dt_val, None, None, vpath, spath, stat, notes, cr_val
                    ))

        # Step 3: Execute migration in an atomic transaction
        cursor.execute("BEGIN IMMEDIATE TRANSACTION;")
        try:
            # Drop legacy out-of-scope tables
            cursor.execute("DROP TABLE IF EXISTS students;")
            cursor.execute("DROP TABLE IF EXISTS protocol_reports;")
            cursor.execute("DROP TABLE IF EXISTS rooms;")

            if not is_already_migrated:
                cursor.execute("DROP TABLE IF EXISTS incidents;")
                for stmt in NEW_SCHEMA_SQL.strip().split(";"):
                    clean_stmt = stmt.strip()
                    if clean_stmt:
                        cursor.execute(clean_stmt + ";")

                if old_incidents:
                    cursor.executemany(
                        """
                        INSERT INTO incidents (
                            id, source_id, track_id, violation_type, confidence, level,
                            detected_at, clip_started_at, clip_ended_at, video_path,
                            snapshot_path, status, proctor_notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        old_incidents
                    )
                    logger.info(f"Migrated {len(old_incidents)} legacy records into clean schema.")
            else:
                # Add any missing Sprint 3.2 Dual-Camera columns idempotently
                cursor.execute("PRAGMA table_info(incidents);")
                current_cols = [row[1] for row in cursor.fetchall()]

                if "source_label" not in current_cols:
                    cursor.execute("ALTER TABLE incidents ADD COLUMN source_label VARCHAR(100) DEFAULT 'Camera 1';")
                    cursor.execute("UPDATE incidents SET source_label = 'Camera 1' WHERE source_label IS NULL;")
                    logger.info("Added 'source_label' column to incidents table.")

                if "source_type" not in current_cols:
                    cursor.execute("ALTER TABLE incidents ADD COLUMN source_type VARCHAR(50) DEFAULT 'browser_ws';")
                    cursor.execute("UPDATE incidents SET source_type = 'browser_ws' WHERE source_type IS NULL;")
                    logger.info("Added 'source_type' column to incidents table.")

                if "session_id" not in current_cols:
                    cursor.execute("ALTER TABLE incidents ADD COLUMN session_id VARCHAR(100);")
                    logger.info("Added 'session_id' column to incidents table.")

                # Ensure indexes exist without dropping existing data
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_id ON incidents (id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_source_id ON incidents (source_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_session_id ON incidents (session_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_track_id ON incidents (track_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_detected_at ON incidents (detected_at);")

            cursor.execute("COMMIT;")
        except Exception as tx_err:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            raise tx_err

        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        logger.info("Database schema migration completed successfully with WAL mode.")

        # Step 4: Audit and migrate confidence scores
        audit_success, audit_stats = audit_and_migrate_confidence(db_path, backup_first=False)
        if not audit_success:
            raise RuntimeError(f"Confidence migration failed: {audit_stats.get('error')}")

        return True, f"Migration completed successfully. Stats: {audit_stats}"

    except Exception as e:
        logger.error(f"Migration failed: {e}. Initiating restore from backup...", exc_info=True)
        try:
            conn.close()
        except Exception:
            pass

        # Step 5: Restore database from verified backup if failure occurred
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            logger.info(f"Restored database to original state from: {backup_path}")

        return False, f"Migration failed: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def audit_and_migrate_confidence(db_path: str = DB_PATH, backup_first: bool = True) -> Tuple[bool, dict]:
    """
    Audit and migrate confidence scores in SQLite database:
    - [0.0, 1.0]: kept untouched (already canonical probability).
    - (1.0, 100.0]: normalized to [0.0, 1.0] via normalize_confidence(value).
    - invalid (<0, >100, NaN, Inf, non-numeric, NULL): moved to `incidents_quarantine` table with reason.
      NOT clamped to 0 or 1. Quarantined records are safely purged from `incidents`.
    - runs in atomic transaction with rollback on failure.
    - creates verified backup first if backup_first=True.
    Returns: (success: bool, stats: dict).
    """
    try:
        from confidence import normalize_confidence, InvalidConfidenceError
    except ImportError:
        from backend.confidence import normalize_confidence, InvalidConfidenceError

    if not os.path.exists(db_path):
        return False, {"error": f"Database does not exist: {db_path}"}

    backup_path = None
    if backup_first:
        try:
            backup_path = create_verified_backup(db_path)
        except Exception as e:
            logger.error(f"Aborting confidence audit: backup creation failed: {e}")
            return False, {"error": f"Backup creation failed: {e}"}

    conn = sqlite3.connect(db_path)
    conn.isolation_level = None  # Manual transaction management
    cursor = conn.cursor()

    stats = {
        "total_audited": 0,
        "untouched_canonical": 0,
        "normalized_legacy": 0,
        "quarantined_invalid": 0,
        "backup_path": backup_path,
    }

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidents';")
        if not cursor.fetchone():
            conn.close()
            return True, stats

        # Ensure quarantine table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents_quarantine (
            id VARCHAR(100) PRIMARY KEY,
            source_id VARCHAR(100),
            source_label VARCHAR(100),
            source_type VARCHAR(50),
            session_id VARCHAR(100),
            track_id INTEGER,
            violation_type VARCHAR(50),
            raw_confidence TEXT,
            quarantine_reason TEXT,
            quarantined_at TIMESTAMP,
            level VARCHAR(20),
            detected_at TIMESTAMP,
            clip_started_at TIMESTAMP,
            clip_ended_at TIMESTAMP,
            video_path VARCHAR(500),
            snapshot_path VARCHAR(500),
            status VARCHAR(20),
            proctor_notes TEXT,
            created_at TIMESTAMP
        );
        """)

        cursor.execute("PRAGMA table_info(incidents);")
        inc_cols = [r[1] for r in cursor.fetchall()]
        col_indices = {c: idx for idx, c in enumerate(inc_cols)}

        cursor.execute("SELECT * FROM incidents;")
        rows = cursor.fetchall()
        stats["total_audited"] = len(rows)

        updates = []
        quarantines = []

        now_iso = datetime.now(timezone.utc).isoformat()

        for row in rows:
            inc_id = row[col_indices["id"]]
            raw_conf = row[col_indices["confidence"]]

            try:
                norm_conf = normalize_confidence(raw_conf)
                # Check if normalization actually changed the value
                if abs(float(raw_conf) - norm_conf) > 1e-6:
                    updates.append((norm_conf, inc_id))
                    stats["normalized_legacy"] += 1
                else:
                    stats["untouched_canonical"] += 1
            except (InvalidConfidenceError, Exception) as err:
                quarantine_entry = (
                    inc_id,
                    row[col_indices["source_id"]] if "source_id" in col_indices else None,
                    row[col_indices["source_label"]] if "source_label" in col_indices else None,
                    row[col_indices["source_type"]] if "source_type" in col_indices else None,
                    row[col_indices["session_id"]] if "session_id" in col_indices else None,
                    row[col_indices["track_id"]] if "track_id" in col_indices else None,
                    row[col_indices["violation_type"]] if "violation_type" in col_indices else None,
                    str(raw_conf),
                    str(err),
                    now_iso,
                    row[col_indices["level"]] if "level" in col_indices else None,
                    row[col_indices["detected_at"]] if "detected_at" in col_indices else None,
                    row[col_indices["clip_started_at"]] if "clip_started_at" in col_indices else None,
                    row[col_indices["clip_ended_at"]] if "clip_ended_at" in col_indices else None,
                    row[col_indices["video_path"]] if "video_path" in col_indices else None,
                    row[col_indices["snapshot_path"]] if "snapshot_path" in col_indices else None,
                    row[col_indices["status"]] if "status" in col_indices else None,
                    row[col_indices["proctor_notes"]] if "proctor_notes" in col_indices else None,
                    row[col_indices["created_at"]] if "created_at" in col_indices else None,
                )
                quarantines.append((quarantine_entry, inc_id))
                stats["quarantined_invalid"] += 1

        # Atomic transaction execution
        cursor.execute("BEGIN IMMEDIATE TRANSACTION;")
        try:
            # Apply normalizations
            if updates:
                cursor.executemany("UPDATE incidents SET confidence = ? WHERE id = ?;", updates)

            # Move invalid records to quarantine and delete from main incidents table
            for q_row, inc_id in quarantines:
                cursor.execute("""
                INSERT OR REPLACE INTO incidents_quarantine (
                    id, source_id, source_label, source_type, session_id, track_id,
                    violation_type, raw_confidence, quarantine_reason, quarantined_at,
                    level, detected_at, clip_started_at, clip_ended_at, video_path,
                    snapshot_path, status, proctor_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, q_row)
                cursor.execute("DELETE FROM incidents WHERE id = ?;", (inc_id,))

            cursor.execute("COMMIT;")
            logger.info(
                f"[CONFIDENCE_MIGRATION] Done: {stats['total_audited']} total, "
                f"{stats['untouched_canonical']} untouched, {stats['normalized_legacy']} normalized, "
                f"{stats['quarantined_invalid']} quarantined."
            )
            return True, stats
        except Exception as tx_err:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            raise tx_err

    except Exception as e:
        logger.error(f"[CONFIDENCE_MIGRATION] Failed: {e}", exc_info=True)
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            logger.info(f"Restored database from backup {backup_path}")
        stats["error"] = str(e)
        return False, stats
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    success, msg = migrate_database()
    if not success:
        sys.exit(1)
    print(f"Result: {msg}")
