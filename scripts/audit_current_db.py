import os
import hashlib
import sqlite3
from datetime import datetime

def file_hash(path):
    if not os.path.exists(path):
        return None, 0
    h = hashlib.sha256()
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest(), size

db_file = "cheating_system.db"
wal_file = "cheating_system.db-wal"
shm_file = "cheating_system.db-shm"

h_db, s_db = file_hash(db_file)
h_wal, s_wal = file_hash(wal_file)
h_shm, s_shm = file_hash(shm_file)

print(f"=== CURRENT DATABASE STATUS ===")
print(f"DB:  size={s_db}, sha256={h_db}")
print(f"WAL: size={s_wal}, sha256={h_wal}")
print(f"SHM: size={s_shm}, sha256={h_shm}")

conn = sqlite3.connect(db_file)
c = conn.cursor()
c.execute("SELECT count(*) FROM incidents")
total_incidents = c.fetchone()[0]
print(f"Total incidents: {total_incidents}")

c.execute("SELECT min(created_at), max(created_at), min(detected_at), max(detected_at) FROM incidents")
row = c.fetchone()
print(f"Time range of incidents: min_created={row[0]}, max_created={row[1]}, min_det={row[2]}, max_det={row[3]}")

# Check latest 5 records
c.execute("SELECT id, violation_type, confidence, detected_at, created_at, status FROM incidents ORDER BY rowid DESC LIMIT 5")
print("\nLatest 5 records:")
for r in c.fetchall():
    print(" ", r)

conn.close()
