"""
================================================================================
CONFIDENCE MIGRATION AUDIT (READ-ONLY AUDIT FOR SPRINT 3.2B-R2)
================================================================================
Performs strict read-only audit of the production SQLite database and verified
migration backup:
1. Verifies SHA-256 and size of backup and current SQLite files.
2. Runs PRAGMA integrity_check on both databases.
3. Audits all incident records for canonical confidence invariants:
   - 100% of stored confidence values must be in [0.0, 1.0].
   - 0 legacy values in (1.0, 100.0].
   - 0 invalid values (< 0.0, > 100.0, NaN, NULL).
4. Tests idempotency on an isolated temporary copy:
   - Re-running migration logic must modify exactly 0 records.
5. Emits confidence_migration_audit.json into artifacts directory.
6. Zero write operations against real cheating_system.db or backup.
================================================================================
"""

import os
import sys
import math
import json
import shutil
import sqlite3
import hashlib
import tempfile

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from confidence import normalize_confidence

ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
AUDIT_JSON_OUT = os.path.join(ARTIFACTS_DIR, "confidence_migration_audit.json")

BACKUP_DB = os.path.join(PROJECT_ROOT, "cheating_system_backup_20260916_004041_0d9a80.db")
CURRENT_DB = os.getenv("AIEXAM_ISOLATED_DB") or os.path.join(PROJECT_ROOT, "cheating_system.db")

print("=" * 80)
print("READ-ONLY DATABASE CONFIDENCE MIGRATION AUDIT (SPRINT 3.2B-R2)")
print("=" * 80)

def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

# 1. Verify existence of backup and current database
assert os.path.exists(BACKUP_DB), f"Verified backup not found at {BACKUP_DB}"
assert os.path.exists(CURRENT_DB), f"Current database not found at {CURRENT_DB}"

backup_size = os.path.getsize(BACKUP_DB)
backup_sha256 = compute_sha256(BACKUP_DB)

current_size = os.path.getsize(CURRENT_DB)
current_sha256 = compute_sha256(CURRENT_DB)

print(f"[*] Verified Backup DB: {os.path.basename(BACKUP_DB)}")
print(f"    - Size:   {backup_size:,} bytes")
print(f"    - SHA256: {backup_sha256}")

print(f"[*] Current SQLite DB:  {os.path.basename(CURRENT_DB)}")
print(f"    - Size:   {current_size:,} bytes")
print(f"    - SHA256: {current_sha256}")

# 2. PRAGMA integrity check (Read-Only URI mode)
def check_db_integrity(db_path: str) -> str:
    uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        rows = cursor.fetchall()
        if len(rows) == 1 and rows[0][0] == "ok":
            return "ok"
        return "; ".join(r[0] for r in rows)
    finally:
        conn.close()

backup_integrity = check_db_integrity(BACKUP_DB)
current_integrity = check_db_integrity(CURRENT_DB)

print(f"\n[*] Integrity check:")
print(f"    - Backup DB integrity:  {backup_integrity}")
print(f"    - Current DB integrity: {current_integrity}")
assert backup_integrity == "ok", f"Backup DB integrity check failed: {backup_integrity}"
assert current_integrity == "ok", f"Current DB integrity check failed: {current_integrity}"

# 3. Read-only audit of records in current DB
uri_ro = f"file:{os.path.abspath(CURRENT_DB)}?mode=ro"
conn_ro = sqlite3.connect(uri_ro, uri=True)
conn_ro.row_factory = sqlite3.Row
cursor_ro = conn_ro.cursor()

cursor_ro.execute("SELECT id, confidence, violation_type, level, detected_at FROM incidents ORDER BY id ASC")
incident_rows = cursor_ro.fetchall()
total_incidents = len(incident_rows)

canonical_records = []
legacy_records = []
invalid_records = []

conf_values = []

for r in incident_rows:
    c_val = r["confidence"]
    if c_val is None:
        invalid_records.append({"id": r["id"], "value": None, "reason": "NULL"})
        continue
    try:
        val_f = float(c_val)
    except (ValueError, TypeError):
        invalid_records.append({"id": r["id"], "value": c_val, "reason": "non_numeric"})
        continue

    if math.isnan(val_f) or math.isinf(val_f):
        invalid_records.append({"id": r["id"], "value": str(val_f), "reason": "nan_or_inf"})
    elif 0.0 <= val_f <= 1.0:
        canonical_records.append({"id": r["id"], "value": val_f})
        conf_values.append(val_f)
    elif 1.0 < val_f <= 100.0:
        legacy_records.append({"id": r["id"], "value": val_f})
    else:
        invalid_records.append({"id": r["id"], "value": val_f, "reason": "out_of_range"})

conn_ro.close()

print(f"\n[*] Incident Records Breakdown (Current DB):")
print(f"    - Total incidents:          {total_incidents}")
print(f"    - Canonical in [0.0, 1.0]:  {len(canonical_records)} ({len(canonical_records)/total_incidents*100:.1f}%)")
print(f"    - Legacy in (1.0, 100.0]:   {len(legacy_records)}")
print(f"    - Invalid / Corrupted:      {len(invalid_records)}")

if conf_values:
    min_conf = min(conf_values)
    max_conf = max(conf_values)
    mean_conf = sum(conf_values) / len(conf_values)
    print(f"    - Confidence Range:         [{min_conf:.4f}, {max_conf:.4f}]")
    print(f"    - Confidence Mean:          {mean_conf:.4f}")
else:
    min_conf, max_conf, mean_conf = 0.0, 0.0, 0.0

assert len(invalid_records) == 0, f"Found {len(invalid_records)} invalid confidence records!"
assert len(legacy_records) == 0, f"Found {len(legacy_records)} legacy confidence records that need normalization!"
assert len(canonical_records) == total_incidents, "Not all incident records have canonical [0.0, 1.0] confidence!"

# 4. Idempotency test on isolated temporary copy
print(f"\n[*] Testing Migration Idempotency on Isolated Temp Copy...")
with tempfile.TemporaryDirectory() as tmp_dir:
    temp_db = os.path.join(tmp_dir, "test_copy.db")
    shutil.copyfile(CURRENT_DB, temp_db)
    temp_sha_before = compute_sha256(temp_db)

    # Simulate migration loop on the copy
    t_conn = sqlite3.connect(temp_db)
    t_cursor = t_conn.cursor()
    t_cursor.execute("SELECT id, confidence FROM incidents")
    temp_rows = t_cursor.fetchall()
    
    modified_count = 0
    for rid, conf in temp_rows:
        canonical = normalize_confidence(conf)
        if abs(canonical - conf) > 1e-7:
            modified_count += 1
            t_cursor.execute("UPDATE incidents SET confidence = ? WHERE id = ?", (canonical, rid))
    t_conn.commit()
    t_conn.close()

    print(f"    - Records inspected: {len(temp_rows)}")
    print(f"    - Records modified by idempotent re-normalization: {modified_count}")
    assert modified_count == 0, f"Idempotency violation! Re-running normalization modified {modified_count} records."
    print("    >>> [PASS] Migration is 100% idempotent; 0 records altered.")

# 5. Backup vs Current comparison
# Read backup count
conn_bak = sqlite3.connect(f"file:{os.path.abspath(BACKUP_DB)}?mode=ro", uri=True)
c_bak = conn_bak.cursor()
c_bak.execute("SELECT count(*) FROM incidents")
backup_incidents_count = c_bak.fetchone()[0]
conn_bak.close()

audit_result = {
    "run_id": os.environ.get("ACCEPTANCE_RUN_ID", "r2_local"),
    "audit_type": "CONFIDENCE_DATABASE_MIGRATION_AUDIT",
    "verdict": "PASS",
    "backup_file": {
        "filename": os.path.basename(BACKUP_DB),
        "size_bytes": backup_size,
        "sha256": backup_sha256,
        "integrity": backup_integrity,
        "incident_count": backup_incidents_count
    },
    "current_db": {
        "filename": os.path.basename(CURRENT_DB),
        "size_bytes": current_size,
        "sha256": current_sha256,
        "integrity": current_integrity,
        "total_incidents": total_incidents,
        "canonical_count": len(canonical_records),
        "legacy_count": len(legacy_records),
        "invalid_count": len(invalid_records),
        "confidence_min": round(min_conf, 4),
        "confidence_max": round(max_conf, 4),
        "confidence_mean": round(mean_conf, 4)
    },
    "idempotency_check": {
        "records_inspected": total_incidents,
        "records_modified": 0,
        "status": "PASS"
    },
    "conclusion": "Toàn bộ dữ liệu độ tin cậy trong SQLite đã được chuẩn hóa canonical trong khoảng [0, 1], đạt kiểm tra toàn vẹn và bất biến."
}

with open(AUDIT_JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(audit_result, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Confidence migration audit manifest saved to: {AUDIT_JSON_OUT}")
print("=" * 80)
print(f"MIGRATION AUDIT VERDICT: PASS | Canonical Records: {len(canonical_records)}/{total_incidents}")
print("=" * 80)
sys.exit(0)
