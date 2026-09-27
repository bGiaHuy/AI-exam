import sqlite3
import os

db_path = 'cheating_system.db'
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM incidents")
total_incidents = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM incidents WHERE video_path IS NOT NULL AND video_path != ''")
incidents_with_video_path = c.fetchone()[0]

c.execute("SELECT id, video_path FROM incidents WHERE video_path IS NOT NULL AND video_path != ''")
rows = c.fetchall()

existing_clips = 0
missing_clips = 0
unreadable_clips = 0

for inc_id, vpath in rows:
    # normalize path
    norm = vpath.replace("\\", "/").lstrip("/")
    if norm.startswith("evidence/"):
        target_path = os.path.join("data", norm)
    elif norm.startswith("data/"):
        target_path = norm
    else:
        target_path = os.path.join("data", "evidence", os.path.basename(norm))
    
    if os.path.exists(target_path):
        size = os.path.getsize(target_path)
        if size > 100: # non-empty valid file
            existing_clips += 1
        else:
            unreadable_clips += 1
    else:
        missing_clips += 1

evidence_dir = os.path.join("data", "evidence")
disk_mp4s = [f for f in os.listdir(evidence_dir) if f.endswith(".mp4")] if os.path.exists(evidence_dir) else []
disk_valid = [f for f in disk_mp4s if os.path.getsize(os.path.join(evidence_dir, f)) > 100]

print("=== AUDIT CLIPS RESULTS ===")
print(f"1. Tổng số incident trong DB: {total_incidents}")
print(f"2. Số incident có trường video_path: {incidents_with_video_path}")
print(f"3. Số clip tham chiếu thực sự tồn tại và đọc được (>100 bytes): {existing_clips}")
print(f"4. Số clip tham chiếu bị thiếu trên đĩa: {missing_clips}")
print(f"5. Số clip tham chiếu hỏng/rỗng (<=100 bytes): {unreadable_clips}")
print(f"6. Tổng số tệp .mp4 thực tế trên đĩa (data/evidence/): {len(disk_mp4s)} (trong đó hợp lệ: {len(disk_valid)})")
conn.close()
