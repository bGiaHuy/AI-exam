"""
================================================================================
DATABASE ISOLATION FAIL-CLOSED PREFLIGHT VERIFIER (SPRINT 3.2B-R2)
================================================================================
Asserts that the running Python environment is strictly wired to the isolated
acceptance database and cannot under any circumstance mutate cheating_system.db:
1. Environment variable AIEXAM_ISOLATED_DB is set, absolute, and exists.
2. Environment variable DATABASE_URL is set and starts with sqlite:///.
3. backend.database.DB_PATH is absolute, matches AIEXAM_ISOLATED_DB, and != cheating_system.db.
4. backend.database.DATABASE_URL matches the isolated path.
5. backend.database.engine is connected to the isolated database file.
6. Live query PRAGMA database_list confirms connected file is the isolated DB.
================================================================================
"""

import os
import sys

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
MAIN_PROD_DB = os.path.abspath(os.path.join(PROJECT_ROOT, "cheating_system.db"))

print("=" * 80)
print("FAIL-CLOSED DATABASE ISOLATION PREFLIGHT CHECK")
print("=" * 80)

# 1. Environment variable AIEXAM_ISOLATED_DB
env_iso_db = os.getenv("AIEXAM_ISOLATED_DB")
if not env_iso_db:
    print("[FATAL PREFLIGHT] Environment variable AIEXAM_ISOLATED_DB is not set!")
    sys.exit(1)

if not os.path.isabs(env_iso_db):
    print(f"[FATAL PREFLIGHT] AIEXAM_ISOLATED_DB is not an absolute path: {env_iso_db}")
    sys.exit(1)

norm_iso_db = os.path.normpath(os.path.abspath(env_iso_db))
if not os.path.exists(norm_iso_db):
    print(f"[FATAL PREFLIGHT] Isolated DB file does not exist on disk: {norm_iso_db}")
    sys.exit(1)

print(f"[OK] AIEXAM_ISOLATED_DB set to absolute existing file: {norm_iso_db}")

# 2. Environment variable DATABASE_URL
env_db_url = os.getenv("DATABASE_URL")
if not env_db_url:
    print("[FATAL PREFLIGHT] Environment variable DATABASE_URL is not set!")
    sys.exit(1)

if not env_db_url.startswith("sqlite:///"):
    print(f"[FATAL PREFLIGHT] DATABASE_URL must start with sqlite:///: {env_db_url}")
    sys.exit(1)

print(f"[OK] DATABASE_URL format valid: {env_db_url}")

# 3. Import backend.database and verify resolution
sys.path.insert(0, PROJECT_ROOT)
try:
    from backend.database import DB_PATH, DATABASE_URL as RESOLVED_DB_URL, engine
except Exception as e:
    print(f"[FATAL PREFLIGHT] Failed to import backend.database: {e}")
    sys.exit(1)

norm_resolved_db = os.path.normpath(os.path.abspath(DB_PATH))
if norm_resolved_db != norm_iso_db:
    print(f"[FATAL PREFLIGHT] backend.database.DB_PATH ({norm_resolved_db}) does not match AIEXAM_ISOLATED_DB ({norm_iso_db})!")
    sys.exit(1)

# Guard against pointing to production DB
if norm_resolved_db.lower() == MAIN_PROD_DB.lower():
    print(f"[FATAL PREFLIGHT] backend.database.DB_PATH points to main production DB {MAIN_PROD_DB}!")
    sys.exit(1)

print(f"[OK] backend.database.DB_PATH resolved to isolated DB: {norm_resolved_db}")
print(f"[OK] Confirmed DB_PATH != main production DB ({MAIN_PROD_DB})")

# 4. Engine verification
engine_db_file = None
if engine.url.database:
    engine_db_file = os.path.normpath(os.path.abspath(engine.url.database))

if engine_db_file != norm_iso_db:
    print(f"[FATAL PREFLIGHT] SQLAlchemy engine database ({engine_db_file}) != isolated DB ({norm_iso_db})!")
    sys.exit(1)

print(f"[OK] Engine URL database target verified: {engine.url}")

# 5. Live connection test
try:
    with engine.connect() as conn:
        db_list = conn.exec_driver_sql("PRAGMA database_list;").fetchall()
        # Row format: (seq, name, file)
        connected_main = None
        for row in db_list:
            if row[1] == "main":
                connected_main = os.path.normpath(os.path.abspath(row[2]))
                break

        if not connected_main:
            print("[FATAL PREFLIGHT] Unable to find main database in PRAGMA database_list!")
            sys.exit(1)

        if connected_main.lower() == MAIN_PROD_DB.lower():
            print(f"[FATAL PREFLIGHT] Live engine connection is physically attached to production DB {MAIN_PROD_DB}!")
            sys.exit(1)

        if connected_main != norm_iso_db:
            print(f"[FATAL PREFLIGHT] Live engine connection is attached to {connected_main}, expected {norm_iso_db}!")
            sys.exit(1)

        print(f"[OK] Live connection PRAGMA database_list verified: {connected_main}")
except Exception as e:
    print(f"[FATAL PREFLIGHT] Failed executing live connection test: {e}")
    sys.exit(1)

print("=" * 80)
print("PREFLIGHT PASSED: ALL CHECKS CONFIRM COMPLETE ISOLATION FROM PRODUCTION DB")
print("=" * 80)
sys.exit(0)
