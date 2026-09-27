import sqlite3
import json

conn = sqlite3.connect('cheating_system.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for t in tables:
    tname = t[0]
    cursor.execute(f"PRAGMA table_info({tname})")
    cols = cursor.fetchall()
    print(f"\nTable {tname}:")
    col_names = [c[1] for c in cols]
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
    cursor.execute(f"SELECT count(*) FROM {tname}")
    cnt = cursor.fetchone()[0]
    print(f"  Total rows: {cnt}")
    cursor.execute(f"SELECT * FROM {tname} ORDER BY rowid DESC LIMIT 3")
    rows = cursor.fetchall()
    for r in rows:
        row_dict = dict(zip(col_names, r))
        print("  Sample row:", json.dumps(row_dict, default=str, ensure_ascii=False))

conn.close()
