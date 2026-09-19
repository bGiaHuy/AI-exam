"""
================================================================================
HARDENED TRANSACTION-SAFE DATABASE MIGRATION SCRIPT - AI EXAM CONTROL
================================================================================
Ensures safe migration to minimal identity-free schema with zero risk of data loss.
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
DB_PATH = os.path.join(BASE_DIR, "cheating_system.db")

NEW_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(100) PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL,
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
                # Ensure indexes exist without dropping existing data
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_id ON incidents (id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS ix_incidents_source_id ON incidents (source_id);")
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
        logger.info("Database migration completed successfully with WAL mode.")
        return True, "Migration completed successfully"

    except Exception as e:
        logger.error(f"Migration failed: {e}. Initiating restore from backup...", exc_info=True)
        try:
            conn.close()
        except Exception:
            pass

        # Step 4: Restore database from verified backup if failure occurred
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            logger.info(f"Restored database to original state from: {backup_path}")

        return False, f"Migration failed: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    success, msg = migrate_database()
    if not success:
        sys.exit(1)
