"""
================================================================================
SQLITE ONLINE BACKUP ISOLATED SNAPSHOT CREATOR (SPRINT 3.2B-R2)
================================================================================
Creates an isolated acceptance database copy using SQLite Online Backup API:
- Connects to main cheating_system.db in read-only URI mode: file:...?mode=ro
- Holds read-only sharing handle on Windows to prevent any timestamp or file mutation
- Performs atomic online backup: src.backup(dst) (Zero os.utime, zero mutation)
- Verifies PRAGMA integrity_check == 'ok' on the isolated snapshot
- Configures WAL mode on the isolated snapshot
- Exits 0 on success, 1 on any failure
================================================================================
"""

import os
import sys
import argparse
import hashlib
import sqlite3
import json
from datetime import datetime, timezone

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
MAIN_DB_PATH = os.path.join(PROJECT_ROOT, "cheating_system.db")


def get_file_info(fpath: str) -> dict:
    if not os.path.exists(fpath):
        return {"exists": False, "size": 0, "mtime_ns": 0, "atime_ns": 0, "sha256": None}
    st = os.stat(fpath)
    h = hashlib.sha256()
    with open(fpath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return {
        "exists": True,
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "atime_ns": st.st_atime_ns,
        "sha256": h.hexdigest()
    }


def main():
    parser = argparse.ArgumentParser(description="Create isolated SQLite snapshot via Online Backup API.")
    parser.add_argument("--run-id", default=os.environ.get("ACCEPTANCE_RUN_ID", "default_run"),
                        help="Run ID for acceptance directory naming")
    parser.add_argument("--output-db", default=None,
                        help="Explicit destination path for isolated DB (optional)")
    args = parser.parse_args()

    print("=" * 80)
    print("CREATING ISOLATED SQLITE SNAPSHOT VIA ONLINE BACKUP API")
    print("=" * 80)

    if not os.path.exists(MAIN_DB_PATH):
        print(f"[FATAL] Source database does not exist at {MAIN_DB_PATH}")
        sys.exit(1)

    # Determine destination path
    if args.output_db:
        dest_db_path = os.path.abspath(args.output_db)
    else:
        dest_dir = os.path.join(PROJECT_ROOT, "data", "isolated_acceptance", args.run_id)
        os.makedirs(dest_dir, exist_ok=True)
        dest_db_path = os.path.join(dest_dir, "isolated_acceptance.db")

    print(f"[*] Source Database:      {MAIN_DB_PATH}")
    print(f"[*] Destination Database: {dest_db_path}")

    # Guard: destination cannot be source
    if os.path.abspath(MAIN_DB_PATH).lower() == os.path.abspath(dest_db_path).lower():
        print("[FATAL] Destination database path cannot be identical to source production DB!")
        sys.exit(1)

    # Remove existing dest if present
    if os.path.exists(dest_db_path):
        os.remove(dest_db_path)
    if os.path.exists(dest_db_path + "-wal"):
        os.remove(dest_db_path + "-wal")
    if os.path.exists(dest_db_path + "-shm"):
        os.remove(dest_db_path + "-shm")

    # Record baseline state of main db files before connection
    related_files = [
        MAIN_DB_PATH,
        MAIN_DB_PATH + "-wal",
        MAIN_DB_PATH + "-shm"
    ]
    baseline_stats = {f: get_file_info(f) for f in related_files}

    for f, info in baseline_stats.items():
        if info["exists"]:
            print(f"[BASELINE] {os.path.basename(f):<24} Size: {info['size']:>8} B, SHA256: {info['sha256'][:16]}...")
        else:
            print(f"[BASELINE] {os.path.basename(f):<24} (Does not exist)")

    # Execute SQLite Online Backup API
    print("[*] Executing sqlite3.Connection.backup() via read-only URI...")
    shm_path = MAIN_DB_PATH + "-shm"
    h_shm = None

    # On Windows, if -shm exists, hold a GENERIC_READ / FILE_SHARE_READ handle during backup.
    # This prevents SQLite from opening -shm with GENERIC_WRITE, causing SQLite to use its
    # built-in read-only fallback so Windows NTFS does not alter LastWriteTime.
    # Zero attributes are modified, zero bytes are written, zero os.utime is used.
    if sys.platform == "win32" and os.path.exists(shm_path):
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 1
        OPEN_EXISTING = 3
        FILE_ATTRIBUTE_NORMAL = 0x80
        h_shm = kernel32.CreateFileW(
            os.path.abspath(shm_path),
            GENERIC_READ,
            FILE_SHARE_READ,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None
        )
        if h_shm == -1 or h_shm == 0xFFFFFFFFFFFFFFFF:
            h_shm = None

    src_uri = f"file:{MAIN_DB_PATH}?mode=ro"
    src_conn = sqlite3.connect(src_uri, uri=True)
    dst_conn = sqlite3.connect(dest_db_path)

    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()
        if h_shm is not None:
            kernel32.CloseHandle(h_shm)

    # Verify source files remain bit-for-bit and timestamp identical (strictly read-only, NO utime)
    for f, info in baseline_stats.items():
        curr_info = get_file_info(f)
        if info["exists"] != curr_info["exists"]:
            print(f"[FATAL] Existence changed for {f}!")
            sys.exit(1)
        if info["exists"]:
            if info["size"] != curr_info["size"]:
                print(f"[FATAL] Size changed for {f}: {info['size']} != {curr_info['size']}")
                sys.exit(1)
            if info["mtime_ns"] != curr_info["mtime_ns"]:
                print(f"[FATAL] Mtime changed for {f}: diff = {curr_info['mtime_ns'] - info['mtime_ns']} ns")
                sys.exit(1)
            if info["sha256"] != curr_info["sha256"]:
                print(f"[FATAL] SHA-256 changed for {f}!")
                sys.exit(1)

    print("[OK] Source production DB files confirmed bit-for-bit and timestamp identical.")

    # Validate destination database
    print("[*] Verifying integrity of isolated snapshot...")
    val_conn = sqlite3.connect(dest_db_path)
    try:
        cursor = val_conn.cursor()
        integrity_res = cursor.execute("PRAGMA integrity_check;").fetchone()
        if not integrity_res or integrity_res[0] != "ok":
            print(f"[FATAL] Isolated database integrity check failed: {integrity_res}")
            sys.exit(1)

        rec_count = cursor.execute("SELECT COUNT(*) FROM incidents;").fetchone()[0]
        print(f"[OK] PRAGMA integrity_check: {integrity_res[0]} | Incidents count: {rec_count}")

        # Set WAL mode on destination isolated DB
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()
    finally:
        val_conn.close()

    dest_sha = get_file_info(dest_db_path)["sha256"]
    print(f"[OK] Isolated snapshot ready: {dest_db_path}")
    print(f"[*] Snapshot SHA-256:         {dest_sha}")

    # Write snapshot_meta.json alongside isolated_acceptance.db
    meta_path = os.path.join(os.path.dirname(dest_db_path), "snapshot_meta.json")
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump({
            "run_id": args.run_id,
            "production_snapshot_initial_count": rec_count,
            "isolated_initial_count": rec_count,
            "dest_db_path": dest_db_path,
            "dest_sha256": dest_sha
        }, mf, indent=2)
    print(f"[OK] Snapshot metadata written: {meta_path}")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
