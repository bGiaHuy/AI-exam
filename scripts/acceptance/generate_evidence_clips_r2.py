"""
================================================================================
DUAL-CAMERA EVIDENCE CLIP GENERATION & METADATA AUDIT (SPRINT 3.2B-R2)
================================================================================
Comprehensive verification of Pre-Roll (~5s), Event Trigger, and Post-Roll (~10s)
for dual independent cameras (Cam1: Green isolated, Cam2: Blue isolated).

Embeds optical markers and 16-bit binary sequence encodings into frames:
- PRE-ROLL: distinctive color patch, phase='PRE', sequence 1..N
- TRIGGER EVENT: white high-contrast patch, phase='EVENT', sequence N+1
- POST-ROLL: distinctive color patch, phase='POST', sequence N+2..M

Decodes generated MP4 files frame-by-frame via OpenCV to independently verify:
- Exact pre-roll frame count and duration (~5.0s +- 0.5s)
- Trigger point event frame occurrence
- Exact post-roll frame count and duration (~10.0s +- 0.5s)
- Total clip duration (~15.0s +- 0.5s)
- First and last decoded sequence and timestamps
- Color signature isolation (zero cross-camera contamination)
- Cryptographic SHA-256 hash
- SQLite database persistence and schema matching (source_id, violation_type,
  confidence, video_path).
================================================================================
"""

import os
import sys
import time
import json
import hashlib
import sqlite3
import numpy as np
import cv2

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.camera_source import BrowserWebSocketSource, CameraStatus
from services.ring_buffer import VideoRingBuffer, EVIDENCE_DIR, validate_video_file
from services.db_queue import db_write_queue

_env_db = os.getenv("AIEXAM_ISOLATED_DB")
if not _env_db and os.getenv("DATABASE_URL"):
    _url = os.getenv("DATABASE_URL", "")
    if _url.startswith("sqlite:///"):
        _env_db = _url[len("sqlite:///"):]
DB_PATH = os.path.abspath(_env_db) if _env_db else os.path.join(PROJECT_ROOT, "cheating_system.db")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")
EVIDENCE_OUT_DIR = os.path.join(ARTIFACTS_DIR, "evidence")
os.makedirs(EVIDENCE_OUT_DIR, exist_ok=True)

print("=" * 80)
print("EVIDENCE CLIP GENERATION & PRE/POST-ROLL AUDIT (SPRINT 3.2B-R2)")
print("=" * 80)

# Start DB write queue explicitly
db_write_queue.start()

# Helper function to create frame with optical marker and binary sequence
def create_marked_frame(camera_id: str, phase: str, seq: int, ts_offset: float, w=640, h=480) -> np.ndarray:
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Base color signature
    if camera_id == "cam1":
        frame[:, :, 1] = 200  # Green base
    else:
        frame[:, :, 0] = 200  # Blue base

    # Corner phase patch (40x40 at [10:50, 10:50])
    if phase == "PRE":
        patch_color = (0, 0, 255) if camera_id == "cam1" else (0, 255, 0)
    elif phase == "EVENT":
        patch_color = (255, 255, 255)  # White for trigger event
    else:  # POST
        patch_color = (255, 0, 0) if camera_id == "cam1" else (0, 0, 255)
    
    frame[10:50, 10:50] = patch_color

    # 16-bit binary sequence bar (16 boxes of 10x10 at y=60..70, x=10+i*10..20+i*10)
    seq_clamped = seq & 0xFFFF
    for i in range(16):
        bit = (seq_clamped >> (15 - i)) & 1
        box_val = 255 if bit else 0
        frame[60:70, 10 + i * 10 : 20 + i * 10] = (box_val, box_val, box_val)

    # Human-readable diagnostic text
    text = f"{camera_id.upper()} {phase} seq={seq} t={ts_offset:.2f}s"
    cv2.putText(frame, text, (180, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return frame


def decode_marker(frame: np.ndarray, camera_id: str):
    # Base color check outside markers
    base_patch = frame[150:350, 150:450]
    avg_b = float(base_patch[:, :, 0].mean())
    avg_g = float(base_patch[:, :, 1].mean())
    avg_r = float(base_patch[:, :, 2].mean())

    # Phase patch
    patch = frame[10:50, 10:50]
    pr, pg, pb = float(patch[:, :, 2].mean()), float(patch[:, :, 1].mean()), float(patch[:, :, 0].mean())

    if pr > 180 and pg > 180 and pb > 180:
        phase = "EVENT"
    elif camera_id == "cam1":
        if pr > 150 and pb < 60:
            phase = "PRE"
        elif pb > 150 and pr < 60:
            phase = "POST"
        else:
            phase = "UNKNOWN"
    else:  # cam2
        if pg > 150 and pb < 60:
            phase = "PRE"
        elif pr > 150 and pg < 60:
            phase = "POST"
        else:
            phase = "UNKNOWN"

    # Decode 16-bit sequence
    seq = 0
    for i in range(16):
        box = frame[60:70, 10 + i * 10 : 20 + i * 10]
        bit = 1 if box.mean() > 128 else 0
        seq = (seq << 1) | bit

    return phase, seq, (avg_b, avg_g, avg_r)


# Setup two camera sources with configured 5.0s pre-roll / 10.0s post-roll
cam1 = BrowserWebSocketSource("cam1", "Camera 1 (Góc trước)")
cam2 = BrowserWebSocketSource("cam2", "Camera 2 (Góc bên)")
cam1.start()
cam2.start()
cam1.status = CameraStatus.ONLINE
cam2.status = CameraStatus.ONLINE

sess1 = f"sess_clip_{int(time.time()*1000)}_cam1"
sess2 = f"sess_clip_{int(time.time()*1000)}_cam2"
cam1.session_id = sess1
cam2.session_id = sess2

fps = 15.0
interval = 1.0 / fps

print("[*] Feeding ~5.2 seconds of PRE-ROLL frames (target 5.0s pre-roll)...")
t0 = time.time()
seq = 0
pre_roll_pushed = 0

while time.time() - t0 < 5.2:
    seq += 1
    pre_roll_pushed += 1
    now = time.time()
    ts_off = now - t0
    f1 = create_marked_frame("cam1", "PRE", seq, ts_off)
    f2 = create_marked_frame("cam2", "PRE", seq, ts_off)
    cam1.push_frame(f1, timestamp=now, sequence_id=seq)
    cam2.push_frame(f2, timestamp=now, sequence_id=seq)
    time.sleep(interval)

print(f"[*] Pre-roll complete ({pre_roll_pushed} frames pushed). Generating TRIGGER EVENT frames...")
event_frames_pushed = 0
trigger_seq = None
trigger_time = None
inc1_id = None
inc2_id = None

for ev_i in range(3):
    seq += 1
    event_frames_pushed += 1
    now = time.time()
    ts_off = now - t0
    f1_event = create_marked_frame("cam1", "EVENT", seq, ts_off)
    f2_event = create_marked_frame("cam2", "EVENT", seq, ts_off)
    cam1.push_frame(f1_event, timestamp=now, sequence_id=seq)
    cam2.push_frame(f2_event, timestamp=now, sequence_id=seq)
    if ev_i == 1:
        trigger_seq = seq
        trigger_time = now
        inc1_id = cam1.ring_buffer.trigger_incident(
            violation_type="PHONE",
            confidence=96.5,
            source_id="cam1",
            track_id=101,
            current_frame=f1_event,
            session_id=sess1,
            source_label="Camera 1 (Góc trước)",
            source_type="browser_ws",
            proctor_notes="Audited Clip Cam1 Pre/Post"
        )
        inc2_id = cam2.ring_buffer.trigger_incident(
            violation_type="HEAD_TURNING",
            confidence=92.0,
            source_id="cam2",
            track_id=202,
            current_frame=f2_event,
            session_id=sess2,
            source_label="Camera 2 (Góc bên)",
            source_type="browser_ws",
            proctor_notes="Audited Clip Cam2 Pre/Post"
        )
    time.sleep(interval)

print(f"    - Trigger Sequence: {trigger_seq} | Timestamp: {trigger_time:.3f}")
print(f"    - Cam1 incident ID: {inc1_id}")
print(f"    - Cam2 incident ID: {inc2_id}")

print("[*] Continuing active streaming for 10.4 seconds POST-ROLL...")
t_post_start = time.time()
post_roll_pushed = 0
while time.time() - t_post_start < 10.4:
    seq += 1
    post_roll_pushed += 1
    now = time.time()
    ts_off = now - t0
    f1 = create_marked_frame("cam1", "POST", seq, ts_off)
    f2 = create_marked_frame("cam2", "POST", seq, ts_off)
    cam1.push_frame(f1, timestamp=now, sequence_id=seq)
    cam2.push_frame(f2, timestamp=now, sequence_id=seq)
    time.sleep(interval)

print(f"[*] Post-roll complete ({post_roll_pushed} frames pushed). Waiting for video encoding completion...")
metrics1 = cam1.ring_buffer.wait_for_incident_clip(inc1_id, timeout=25.0)
metrics2 = cam2.ring_buffer.wait_for_incident_clip(inc2_id, timeout=25.0)

cam1.stop()
cam2.stop()

assert metrics1 is not None, f"Cam1 clip task {inc1_id} timed out!"
assert metrics2 is not None, f"Cam2 clip task {inc2_id} timed out!"

print(f"[OK] Both clip rendering tasks completed!")

mp4_1 = os.path.join(EVIDENCE_DIR, f"{inc1_id}.mp4")
mp4_2 = os.path.join(EVIDENCE_DIR, f"{inc2_id}.mp4")

assert os.path.exists(mp4_1) and validate_video_file(mp4_1), f"Corrupt {mp4_1}"
assert os.path.exists(mp4_2) and validate_video_file(mp4_2), f"Corrupt {mp4_2}"

def file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

hash1 = file_sha256(mp4_1)
hash2 = file_sha256(mp4_2)

# Copy to artifacts evidence directory
dst1 = os.path.join(EVIDENCE_OUT_DIR, f"clip_cam1_{inc1_id}.mp4")
dst2 = os.path.join(EVIDENCE_OUT_DIR, f"clip_cam2_{inc2_id}.mp4")
import shutil
shutil.copy2(mp4_1, dst1)
shutil.copy2(mp4_2, dst2)

# Detailed Frame-by-Frame Video Decoding and Pre/Post-Roll Audit
def audit_clip_frames(filepath: str, camera_id: str):
    cap = cv2.VideoCapture(filepath)
    fps_video = cap.get(cv2.CAP_PROP_FPS) or 15.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    pre_count = 0
    post_count = 0
    event_count = 0
    unknown_count = 0
    decoded_seqs = []
    cross_contamination_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        phase, decoded_seq, (b, g, r) = decode_marker(frame, camera_id)
        decoded_seqs.append(decoded_seq)

        if camera_id == "cam1":
            if b > 60 or g < 140:
                cross_contamination_frames += 1
        else:
            if g > 60 or b < 140:
                cross_contamination_frames += 1

        if phase == "PRE":
            pre_count += 1
        elif phase == "EVENT":
            event_count += 1
        elif phase == "POST":
            post_count += 1
        else:
            unknown_count += 1

    cap.release()

    pre_dur = pre_count / fps_video
    post_dur = post_count / fps_video
    total_dur = len(decoded_seqs) / fps_video

    return {
        "fps": fps_video,
        "total_frames": len(decoded_seqs),
        "pre_count": pre_count,
        "post_count": post_count,
        "event_count": event_count,
        "unknown_count": unknown_count,
        "pre_duration_sec": pre_dur,
        "post_duration_sec": post_dur,
        "total_duration_sec": total_dur,
        "first_seq": decoded_seqs[0] if decoded_seqs else None,
        "last_seq": decoded_seqs[-1] if decoded_seqs else None,
        "cross_contamination_frames": cross_contamination_frames
    }

print("\n[*] Auditing Cam1 MP4 frame-by-frame...")
audit1 = audit_clip_frames(mp4_1, "cam1")
print(f"    - Total Decoded Frames: {audit1['total_frames']}")
print(f"    - Pre-Roll Frames: {audit1['pre_count']} ({audit1['pre_duration_sec']:.2f}s)")
print(f"    - Event Trigger Frames: {audit1['event_count']}")
print(f"    - Post-Roll Frames: {audit1['post_count']} ({audit1['post_duration_sec']:.2f}s)")
print(f"    - Total Duration: {audit1['total_duration_sec']:.2f}s")
print(f"    - First Seq: {audit1['first_seq']}, Last Seq: {audit1['last_seq']}")
print(f"    - Cross-contamination Frames: {audit1['cross_contamination_frames']}")

print("\n[*] Auditing Cam2 MP4 frame-by-frame...")
audit2 = audit_clip_frames(mp4_2, "cam2")
print(f"    - Total Decoded Frames: {audit2['total_frames']}")
print(f"    - Pre-Roll Frames: {audit2['pre_count']} ({audit2['pre_duration_sec']:.2f}s)")
print(f"    - Event Trigger Frames: {audit2['event_count']}")
print(f"    - Post-Roll Frames: {audit2['post_count']} ({audit2['post_duration_sec']:.2f}s)")
print(f"    - Total Duration: {audit2['total_duration_sec']:.2f}s")
print(f"    - First Seq: {audit2['first_seq']}, Last Seq: {audit2['last_seq']}")
print(f"    - Cross-contamination Frames: {audit2['cross_contamination_frames']}")

# Assertions for independent proof
TOLERANCE_SEC = 0.5
assert abs(audit1["pre_duration_sec"] - 5.0) <= TOLERANCE_SEC, f"Cam1 pre-roll {audit1['pre_duration_sec']}s exceeds 5.0s +- {TOLERANCE_SEC}s"
assert abs(audit2["pre_duration_sec"] - 5.0) <= TOLERANCE_SEC, f"Cam2 pre-roll {audit2['pre_duration_sec']}s exceeds 5.0s +- {TOLERANCE_SEC}s"
assert abs(audit1["post_duration_sec"] - 10.0) <= TOLERANCE_SEC, f"Cam1 post-roll {audit1['post_duration_sec']}s exceeds 10.0s +- {TOLERANCE_SEC}s"
assert abs(audit2["post_duration_sec"] - 10.0) <= TOLERANCE_SEC, f"Cam2 post-roll {audit2['post_duration_sec']}s exceeds 10.0s +- {TOLERANCE_SEC}s"
assert abs(audit1["total_duration_sec"] - 15.0) <= TOLERANCE_SEC, f"Cam1 total duration {audit1['total_duration_sec']}s exceeds 15.0s +- {TOLERANCE_SEC}s"
assert abs(audit2["total_duration_sec"] - 15.0) <= TOLERANCE_SEC, f"Cam2 total duration {audit2['total_duration_sec']}s exceeds 15.0s +- {TOLERANCE_SEC}s"
assert audit1["cross_contamination_frames"] == 0, "Cam1 contains cross-contamination frames!"
assert audit2["cross_contamination_frames"] == 0, "Cam2 contains cross-contamination frames!"
assert audit1["event_count"] >= 1, f"Cam1 must contain at least 1 decoded EVENT frame! Got {audit1['event_count']}"
assert audit2["event_count"] >= 1, f"Cam2 must contain at least 1 decoded EVENT frame! Got {audit2['event_count']}"

# Wait for SQLite writer to flush
time.sleep(2.0)

# SQLite Database Verification: Exact Assertion of Persisted Data
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT id, source_id, violation_type, confidence, video_path FROM incidents WHERE id IN (?, ?)", (inc1_id, inc2_id))
rows = c.fetchall()
conn.close()

db_records = {r[0]: {"source_id": r[1], "violation": r[2], "confidence": r[3], "video_path": r[4]} for r in rows}
print(f"\n[*] SQLite Incidents Persisted: {len(db_records)} records found")

assert inc1_id in db_records, f"Cam1 incident {inc1_id} missing from SQLite!"
assert inc2_id in db_records, f"Cam2 incident {inc2_id} missing from SQLite!"

rec1 = db_records[inc1_id]
rec2 = db_records[inc2_id]

# Validate exact match and canonical normalization
assert rec1["source_id"] == "cam1", f"Expected cam1, got {rec1['source_id']}"
assert rec1["violation"] == "PHONE", f"Expected PHONE, got {rec1['violation']}"
assert abs(rec1["confidence"] - 0.965) < 0.001, f"Expected canonical 0.965 in SQLite, got {rec1['confidence']}"
assert os.path.basename(rec1["video_path"]) == f"{inc1_id}.mp4", f"Video path mismatch: {rec1['video_path']}"

assert rec2["source_id"] == "cam2", f"Expected cam2, got {rec2['source_id']}"
assert rec2["violation"] == "HEAD_TURNING", f"Expected HEAD_TURNING, got {rec2['violation']}"
assert abs(rec2["confidence"] - 0.920) < 0.001, f"Expected canonical 0.920 in SQLite, got {rec2['confidence']}"
assert os.path.basename(rec2["video_path"]) == f"{inc2_id}.mp4", f"Video path mismatch: {rec2['video_path']}"

print(f"[OK] SQLite database records verified: legacy input (96.5, 92.0) -> canonical stored ({rec1['confidence']}, {rec2['confidence']})!")

run_id = os.environ.get("ACCEPTANCE_RUN_ID", "r2_local")

# Generate rigorous clips manifest with pre-roll / post-roll breakdown
manifest = {
    "run_id": run_id,
    "generated_at": time.time(),
    "tolerance_applied_sec": TOLERANCE_SEC,
    "incidents": [
        {
            "incident_id": inc1_id,
            "source_id": "cam1",
            "source_label": "Camera 1 (Góc trước)",
            "violation_type": "PHONE",
            "legacy_input_confidence": 96.5,
            "canonical_stored_confidence": rec1["confidence"],
            "ui_display_percent": f"{rec1['confidence'] * 100.0:.1f}%",
            "file_name": os.path.basename(dst1),
            "file_size_bytes": os.path.getsize(dst1),
            "sha256": hash1,
            "trigger_sequence": trigger_seq,
            "trigger_timestamp": trigger_time,
            "first_decoded_sequence": audit1["first_seq"],
            "last_decoded_sequence": audit1["last_seq"],
            "pre_roll_frames": audit1["pre_count"],
            "event_trigger_frames": audit1["event_count"],
            "post_roll_frames": audit1["post_count"],
            "total_decoded_frames": audit1["total_frames"],
            "pre_roll_duration_sec": audit1["pre_duration_sec"],
            "post_roll_duration_sec": audit1["post_duration_sec"],
            "total_duration_sec": audit1["total_duration_sec"],
            "color_signature": "GREEN_ISOLATED",
            "cross_contamination_frames": audit1["cross_contamination_frames"],
            "db_verification": {
                "persisted": True,
                "matched_source_id": True,
                "matched_violation_type": True,
                "matched_canonical_confidence": True,
                "matched_video_path": True,
                "db_video_path": rec1["video_path"]
            }
        },
        {
            "incident_id": inc2_id,
            "source_id": "cam2",
            "source_label": "Camera 2 (Góc bên)",
            "violation_type": "HEAD_TURNING",
            "legacy_input_confidence": 92.0,
            "canonical_stored_confidence": rec2["confidence"],
            "ui_display_percent": f"{rec2['confidence'] * 100.0:.1f}%",
            "file_name": os.path.basename(dst2),
            "file_size_bytes": os.path.getsize(dst2),
            "sha256": hash2,
            "trigger_sequence": trigger_seq,
            "trigger_timestamp": trigger_time,
            "first_decoded_sequence": audit2["first_seq"],
            "last_decoded_sequence": audit2["last_seq"],
            "pre_roll_frames": audit2["pre_count"],
            "event_trigger_frames": audit2["event_count"],
            "post_roll_frames": audit2["post_count"],
            "total_decoded_frames": audit2["total_frames"],
            "pre_roll_duration_sec": audit2["pre_duration_sec"],
            "post_roll_duration_sec": audit2["post_duration_sec"],
            "total_duration_sec": audit2["total_duration_sec"],
            "color_signature": "BLUE_ISOLATED",
            "cross_contamination_frames": audit2["cross_contamination_frames"],
            "db_verification": {
                "persisted": True,
                "matched_source_id": True,
                "matched_violation_type": True,
                "matched_canonical_confidence": True,
                "matched_video_path": True,
                "db_video_path": rec2["video_path"]
            }
        }
    ]
}

manifest_path = os.path.join(ARTIFACTS_DIR, "clips_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as mf:
    json.dump(manifest, mf, indent=2)

print(f"[OK] Manifest saved to: {manifest_path}")
print("=" * 80)
print("ALL EVIDENCE CLIP & PRE/POST-ROLL AUDITS PASSED CLEANLY (EXIT 0)")
print("=" * 80)
sys.exit(0)
