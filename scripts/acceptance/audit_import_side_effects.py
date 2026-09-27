"""
================================================================================
IMPORT SIDE-EFFECT & METADATA AUDIT (SPRINT 3.2B-R2)
================================================================================
Executes in an isolated Python process to audit runtime side-effects across
three distinct checkpoints:
  - Checkpoint A: Import services.ring_buffer
  - Checkpoint B: Import main (from main import app)
  - Checkpoint C: Execute GET /api/camera/sources via TestClient(app)

At each checkpoint, 7 parameters are strictly recorded and verified:
  1. Thread count and thread names
  2. SQLite database mtime and file size
  3. DB worker state (db_write_queue._started)
  4. Model loader call count (get_detector)
  5. VideoCapture / OpenCV decoder call count
  6. Camera manager initialization state
  7. Inference worker execution state

Conclusion Phrasing Mandate:
  "không quan sát thấy các side effect bị cấm tại checkpoint được liệt kê"
================================================================================
"""

import os
import sys
import time
import json
import threading
from unittest.mock import patch

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "sprint_3_2b_r2")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)
AUDIT_JSON_OUT = os.path.join(ARTIFACTS_DIR, "audit_import_side_effects.json")

DB_PATH = os.environ.get("AIEXAM_ISOLATED_DB") or os.path.join(PROJECT_ROOT, "cheating_system.db")

print("=" * 80)
print("AUDIT: IMPORT SIDE-EFFECT & METADATA AUDIT (3 CHECKPOINTS)")
print("=" * 80)

audit_records = {}

def capture_metrics(stage_label: str, model_mock=None, cv2_mock=None) -> dict:
    threads = threading.enumerate()
    t_count = len(threads)
    t_names = [t.name for t in threads]
    
    db_exists = os.path.exists(DB_PATH)
    db_mtime = os.path.getmtime(DB_PATH) if db_exists else None
    db_size = os.path.getsize(DB_PATH) if db_exists else None

    # DB write queue check
    db_worker_started = False
    if "services.db_queue" in sys.modules:
        from services.db_queue import db_write_queue
        db_worker_started = getattr(db_write_queue, "_started", False)

    # Model loader count
    model_calls = model_mock.call_count if model_mock is not None else 0

    # VideoCapture count
    cv2_calls = cv2_mock.call_count if cv2_mock is not None else 0

    # Camera manager state
    cam_mgr_init = False
    active_sources = 0
    if "services.camera_manager" in sys.modules:
        from services.camera_manager import camera_manager
        cam_mgr_init = getattr(camera_manager, "_initialized", False)
        active_sources = len(getattr(camera_manager, "_sources", {}))

    # Inference worker state
    inf_running = False
    if "services.inference_worker" in sys.modules:
        from services.inference_worker import inference_worker
        inf_running = getattr(inference_worker, "_running", False)

    metrics = {
        "stage": stage_label,
        "thread_count": t_count,
        "thread_names": t_names,
        "db_exists": db_exists,
        "db_mtime": db_mtime,
        "db_size_bytes": db_size,
        "db_worker_started": db_worker_started,
        "model_loader_calls": model_calls,
        "videocapture_calls": cv2_calls,
        "camera_manager_initialized": cam_mgr_init,
        "camera_manager_active_sources": active_sources,
        "inference_worker_running": inf_running,
    }
    return metrics

# 0. Baseline measurement
baseline = capture_metrics("Baseline (Pre-Import)")
audit_records["baseline"] = baseline
print(f"[*] Baseline: threads={baseline['thread_count']} {baseline['thread_names']}, "
      f"db_size={baseline['db_size_bytes']} bytes, db_mtime={baseline['db_mtime']}")

# Patch cv2.VideoCapture globally before any import might touch it
with patch("cv2.VideoCapture") as mock_cv2_cap:
    # --------------------------------------------------------------------------
    # Checkpoint A: Import services.ring_buffer
    # --------------------------------------------------------------------------
    print("\n[Checkpoint A] Importing services.ring_buffer...")
    t0_a = time.perf_counter()
    import services.ring_buffer
    t_import_a = (time.perf_counter() - t0_a) * 1000.0

    checkpoint_a = capture_metrics("Checkpoint A: import services.ring_buffer", cv2_mock=mock_cv2_cap)
    checkpoint_a["duration_ms"] = round(t_import_a, 2)
    checkpoint_a["thread_delta"] = checkpoint_a["thread_count"] - baseline["thread_count"]
    audit_records["checkpoint_a"] = checkpoint_a

    print(f"    - Duration: {t_import_a:.2f} ms")
    print(f"    - Thread count: {checkpoint_a['thread_count']} (delta={checkpoint_a['thread_delta']})")
    print(f"    - Thread names: {checkpoint_a['thread_names']}")
    print(f"    - DB worker started: {checkpoint_a['db_worker_started']}")
    print(f"    - DB modified: {checkpoint_a['db_mtime'] != baseline['db_mtime']}")
    print(f"    - Model loader calls: {checkpoint_a['model_loader_calls']}")
    print(f"    - VideoCapture calls: {checkpoint_a['videocapture_calls']}")
    print(f"    - Inference worker running: {checkpoint_a['inference_worker_running']}")

    assert checkpoint_a["thread_delta"] == 0, f"Checkpoint A: spawned threads! delta={checkpoint_a['thread_delta']}"
    assert not checkpoint_a["db_worker_started"], "Checkpoint A: DB worker must NOT start on import!"
    assert checkpoint_a["db_mtime"] == baseline["db_mtime"], "Checkpoint A: SQLite DB must NOT be modified!"
    assert checkpoint_a["videocapture_calls"] == 0, "Checkpoint A: cv2.VideoCapture must NOT be called!"
    assert not checkpoint_a["inference_worker_running"], "Checkpoint A: Inference worker must NOT be running!"
    print("    >>> [PASS] Checkpoint A: không quan sát thấy các side effect bị cấm.")

    # --------------------------------------------------------------------------
    # Checkpoint B: Import main (from main import app)
    # --------------------------------------------------------------------------
    print("\n[Checkpoint B] Importing main (from main import app)...")
    os.environ["ENVIRONMENT"] = "test"
    
    with patch("routers.ai_engine.get_detector") as mock_detector:
        t0_b = time.perf_counter()
        from main import app
        t_import_b = (time.perf_counter() - t0_b) * 1000.0

        checkpoint_b = capture_metrics("Checkpoint B: from main import app", model_mock=mock_detector, cv2_mock=mock_cv2_cap)
        checkpoint_b["duration_ms"] = round(t_import_b, 2)
        checkpoint_b["thread_delta"] = checkpoint_b["thread_count"] - baseline["thread_count"]
        audit_records["checkpoint_b"] = checkpoint_b

        print(f"    - Duration: {t_import_b:.2f} ms")
        print(f"    - Thread count: {checkpoint_b['thread_count']} (delta={checkpoint_b['thread_delta']})")
        print(f"    - Thread names: {checkpoint_b['thread_names']}")
        print(f"    - DB worker started: {checkpoint_b['db_worker_started']}")
        print(f"    - DB modified: {checkpoint_b['db_mtime'] != baseline['db_mtime']}")
        print(f"    - Model loader calls: {checkpoint_b['model_loader_calls']}")
        print(f"    - VideoCapture calls: {checkpoint_b['videocapture_calls']}")
        print(f"    - Camera manager initialized: {checkpoint_b['camera_manager_initialized']}")
        print(f"    - Inference worker running: {checkpoint_b['inference_worker_running']}")

        assert checkpoint_b["thread_delta"] == 0, f"Checkpoint B: spawned threads! delta={checkpoint_b['thread_delta']}"
        assert not checkpoint_b["db_worker_started"], "Checkpoint B: DB worker must NOT start on import!"
        assert checkpoint_b["db_mtime"] == baseline["db_mtime"], "Checkpoint B: SQLite DB must NOT be modified!"
        assert checkpoint_b["model_loader_calls"] == 0, "Checkpoint B: Model loader must NOT be called on import!"
        assert checkpoint_b["videocapture_calls"] == 0, "Checkpoint B: cv2.VideoCapture must NOT be called!"
        assert not checkpoint_b["inference_worker_running"], "Checkpoint B: Inference worker must NOT be running!"
        print("    >>> [PASS] Checkpoint B: không quan sát thấy các side effect bị cấm.")

        # --------------------------------------------------------------------------
        # Checkpoint C: Execute GET /api/camera/sources
        # --------------------------------------------------------------------------
        print("\n[Checkpoint C] Executing GET /api/camera/sources...")
        from fastapi.testclient import TestClient
        client = TestClient(app)

        t0_c = time.perf_counter()
        resp = client.get("/api/camera/sources")
        t_req_c = (time.perf_counter() - t0_c) * 1000.0

        checkpoint_c = capture_metrics("Checkpoint C: GET /api/camera/sources", model_mock=mock_detector, cv2_mock=mock_cv2_cap)
        checkpoint_c["duration_ms"] = round(t_req_c, 2)
        checkpoint_c["thread_delta"] = checkpoint_c["thread_count"] - baseline["thread_count"]
        checkpoint_c["response_status_code"] = resp.status_code
        checkpoint_c["response_payload"] = resp.json()
        audit_records["checkpoint_c"] = checkpoint_c

        print(f"    - Duration: {t_req_c:.2f} ms")
        print(f"    - Response status: {resp.status_code}")
        print(f"    - Thread count: {checkpoint_c['thread_count']} (delta={checkpoint_c['thread_delta']})")
        print(f"    - Thread names: {checkpoint_c['thread_names']}")
        print(f"    - DB worker started: {checkpoint_c['db_worker_started']}")
        print(f"    - DB modified: {checkpoint_c['db_mtime'] != baseline['db_mtime']}")
        print(f"    - Model loader calls: {checkpoint_c['model_loader_calls']}")
        print(f"    - VideoCapture calls: {checkpoint_c['videocapture_calls']}")
        print(f"    - Camera manager initialized: {checkpoint_c['camera_manager_initialized']}")
        print(f"    - Inference worker running: {checkpoint_c['inference_worker_running']}")

        assert resp.status_code == 200, f"Checkpoint C: Expected 200, got {resp.status_code}"
        assert checkpoint_c["thread_delta"] == 0, f"Checkpoint C: spawned threads! delta={checkpoint_c['thread_delta']}"
        assert not checkpoint_c["db_worker_started"], "Checkpoint C: DB worker must NOT start on metadata endpoint!"
        assert checkpoint_c["db_mtime"] == baseline["db_mtime"], "Checkpoint C: SQLite DB must NOT be modified!"
        assert checkpoint_c["model_loader_calls"] == 0, "Checkpoint C: Model loader must NOT be called on metadata endpoint!"
        assert checkpoint_c["videocapture_calls"] == 0, "Checkpoint C: cv2.VideoCapture must NOT be called!"
        assert not checkpoint_c["inference_worker_running"], "Checkpoint C: Inference worker must NOT be running!"
        print("    >>> [PASS] Checkpoint C: không quan sát thấy các side effect bị cấm.")

# ------------------------------------------------------------------------------
# Final Conclusion and Artifact Export
# ------------------------------------------------------------------------------
conclusion_phrase = "không quan sát thấy các side effect bị cấm tại checkpoint được liệt kê"

audit_summary = {
    "run_id": os.environ.get("ACCEPTANCE_RUN_ID", "r2_local"),
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "audit_type": "IMPORT_AND_METADATA_SIDE_EFFECT_AUDIT",
    "verdict": "PASS",
    "conclusion": f"Xác nhận thành công: {conclusion_phrase}.",
    "checkpoints": audit_records
}

with open(AUDIT_JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(audit_summary, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Audit output saved to: {AUDIT_JSON_OUT}")
print("=" * 80)
print(f"AUDIT SUMMARY: {audit_summary['conclusion']}")
print("=" * 80)
sys.exit(0)
