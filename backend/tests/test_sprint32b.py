"""
================================================================================
SPRINT 3.2B-R1 — Hardened Test Suite (T1–T11)
================================================================================
Tests VideoRingBuffer memory bounds, corrupt frame recovery, DEMO_READ_ONLY
enforcement, model loader isolation, and credential scan.
All tests self-contained: process exits cleanly, no YOLO loaded, no real DB used.
================================================================================
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import numpy as np
import cv2

os.environ["ENVIRONMENT"] = "test"
os.environ["ENABLE_TEST_ENDPOINTS"] = "true"

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.ring_buffer import VideoRingBuffer, VideoClipTask, validate_video_file, EVIDENCE_DIR


def _make_frame(color=(0, 200, 0), sz=(64, 64)) -> np.ndarray:
    return np.full((sz[1], sz[0], 3), color, dtype=np.uint8)


def _encode_jpeg(frame: np.ndarray, quality: int = 80) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    assert ok, "cv2.imencode failed"
    return buf.tobytes()


def _make_jpeg(color=(0, 200, 0), sz=(64, 64), quality: int = 80) -> bytes:
    return _encode_jpeg(_make_frame(color, sz), quality)


# ── T1–T4: VideoRingBuffer Tests ──────────────────────────────────────────────
class T1T4RingBufferTests(unittest.TestCase):

    def _rb(self, max_bytes: int = 10_000_000):
        return VideoRingBuffer(
            max_retention_seconds=20,
            max_frames=350,
            max_bytes=max_bytes
        )

    def test_01_jpeg_storage_push_frame(self):
        """T1: push_frame(jpeg_bytes=...) stores bytes, increments frame & byte counts."""
        rb = self._rb()
        j = _make_jpeg()
        initial_tel = rb.get_telemetry()
        self.assertEqual(initial_tel["ring_buffer_frames"], 0)
        self.assertEqual(initial_tel["ring_buffer_bytes"], 0)

        rb.push_frame(
            jpeg_bytes=j,
            timestamp=time.time(),
            sequence_id=1,
            session_id="s1",
            source_id="cam1"
        )
        tel = rb.get_telemetry()
        self.assertEqual(tel["ring_buffer_frames"], 1, "Frame count must be 1")
        self.assertEqual(tel["ring_buffer_bytes"], len(j), "Byte count must match JPEG size")
        self.assertLess(tel["ring_buffer_bytes"], 12288, "JPEG size must be smaller than raw BGR")

        with rb.lock:
            stored_item = rb.frame_buffer[0]
        stored_payload = stored_item[1]
        self.assertIsInstance(stored_payload, bytes, "Payload must be bytes, not ndarray")

    def test_02_byte_limit_strictly_enforced(self):
        """T2: ring_buffer_bytes <= max_bytes strictly after pushes exceed limit."""
        j = _make_jpeg(sz=(160, 120))
        n = len(j)
        max_b = n * 3
        rb = self._rb(max_bytes=max_b)

        for i in range(10):
            rb.push_frame(
                jpeg_bytes=j,
                timestamp=time.time() + i * 0.1,
                sequence_id=i + 1,
                session_id="s2",
                source_id="cam1"
            )

        tel = rb.get_telemetry()
        self.assertLessEqual(
            tel["ring_buffer_bytes"], max_b,
            f"ring_buffer_bytes ({tel['ring_buffer_bytes']}) must NOT exceed max_bytes ({max_b})"
        )
        self.assertGreater(
            tel["ring_buffer_dropped_by_limit"], 0,
            "dropped_by_limit counter must be > 0 when frames are pruned"
        )
        self.assertLessEqual(tel["ring_buffer_frames"], 3, "Buffer must hold at most 3 frames")

    def test_03_corrupt_jpeg_counter_and_recovery(self):
        """T3: corrupt_frames_skipped increments, clip renders playable video, no crash."""
        rb = self._rb()
        good_f = _make_frame((0, 180, 0), sz=(160, 120))
        good_j = _encode_jpeg(good_f)
        corrupt_j1 = b"\xff\xd8\xff\xe0" + b"\x00" * 20
        corrupt_j2 = b"not_a_valid_jpeg_header"

        t0 = time.time()
        timed_frames = []
        for i in range(8):
            timed_frames.append((t0 + i * 0.1, good_j, i, "sess_c", "cam1", 160, 120))
        timed_frames.append((t0 + 0.8, corrupt_j1, 8, "sess_c", "cam1", 160, 120))
        timed_frames.append((t0 + 0.9, corrupt_j2, 9, "sess_c", "cam1", 160, 120))
        for i in range(10, 18):
            timed_frames.append((t0 + i * 0.1, good_j, i, "sess_c", "cam1", 160, 120))

        task = VideoClipTask(
            incident_id="test_t3_corrupt_inc",
            source_id="cam1",
            track_id=1,
            violation_type="PHONE",
            confidence=95.0,
            level="red",
            pre_frames=timed_frames,
            post_end_time=t0 + 1.8,
            peak_frame=good_f,
            detected_at=datetime.now(timezone.utc),
            target_fps=15.0
        )

        with patch("services.ring_buffer.db_write_queue") as mock_db:
            before_skip = rb.corrupt_frames_skipped
            rb._render_and_persist_clip(task)
            after_skip = rb.corrupt_frames_skipped

            self.assertEqual(
                after_skip - before_skip, 2,
                f"corrupt_frames_skipped must increase by 2, got {after_skip - before_skip}"
            )
            mock_db.enqueue_incident.assert_called_once()

            saved_mp4 = os.path.join(EVIDENCE_DIR, "test_t3_corrupt_inc.mp4")
            self.assertTrue(os.path.exists(saved_mp4), "Video file must be generated")
            self.assertTrue(validate_video_file(saved_mp4), "Generated clip must be playable")

            try:
                os.remove(saved_mp4)
                snap = os.path.join(EVIDENCE_DIR, "test_t3_corrupt_inc_snap.jpg")
                if os.path.exists(snap):
                    os.remove(snap)
            except Exception:
                pass

    def test_04_telemetry_schema_and_types(self):
        """T4: Telemetry fields types, values >= 0, and dynamic updates."""
        rb = self._rb()
        tel = rb.get_telemetry()
        required_int_fields = [
            "ring_buffer_frames",
            "ring_buffer_bytes",
            "ring_buffer_dropped_by_limit",
            "corrupt_frames_skipped",
            "active_tasks"
        ]
        for f in required_int_fields:
            self.assertIn(f, tel, f"Missing telemetry field {f}")
            self.assertIsInstance(tel[f], int, f"{f} must be int")
            self.assertGreaterEqual(tel[f], 0, f"{f} must be >= 0")

        self.assertIn("ring_buffer_oldest_age", tel)
        self.assertIsInstance(tel["ring_buffer_oldest_age"], (int, float))
        self.assertGreaterEqual(tel["ring_buffer_oldest_age"], 0.0)

        self.assertIn("state", tel)
        self.assertIn(tel["state"], ("IDLE", "RECORDING_POST", "SAVING"))

        j = _make_jpeg()
        rb.push_frame(jpeg_bytes=j, timestamp=time.time(), sequence_id=1, session_id="s4", source_id="cam1")
        tel2 = rb.get_telemetry()
        self.assertEqual(tel2["ring_buffer_frames"], 1)
        self.assertEqual(tel2["ring_buffer_bytes"], len(j))


# ── T5–T9: DEMO_READ_ONLY & Metadata Tests ────────────────────────────────────
class T5T9DemoReadOnlyTests(unittest.TestCase):

    def test_05_camera_mode_blocked_in_demo(self):
        """T5: POST /api/camera/mode returns exactly 403 when DEMO_READ_ONLY=true."""
        with patch.dict(os.environ, {"DEMO_READ_ONLY": "true"}):
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            resp = client.post("/api/camera/mode", json={"mode": "SINGLE_CAMERA"})
            self.assertEqual(resp.status_code, 403)

    def test_06_session_reset_blocked_in_demo(self):
        """T6: POST /api/session/reset returns exactly 403 when DEMO_READ_ONLY=true."""
        with patch.dict(os.environ, {"DEMO_READ_ONLY": "true"}):
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            resp = client.post("/api/session/reset")
            self.assertEqual(resp.status_code, 403)

    def test_07_incident_confirm_blocked_in_demo(self):
        """T7: PATCH /api/incidents/{id}/confirm returns exactly 403 when DEMO_READ_ONLY=true."""
        with patch.dict(os.environ, {"DEMO_READ_ONLY": "true"}):
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            resp = client.patch("/api/incidents/fake-incident-id/confirm", json={"status": "confirmed"})
            self.assertEqual(resp.status_code, 403)

    def test_08_settings_ai_blocked_in_demo(self):
        """T8: POST /api/settings/ai returns exactly 403 when DEMO_READ_ONLY=true."""
        with patch.dict(os.environ, {"DEMO_READ_ONLY": "true"}):
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            resp = client.post("/api/settings/ai", json={"head_turning_yellow_threshold": 1.25})
            self.assertEqual(resp.status_code, 403)

    def test_09_camera_sources_returns_200_without_loading_yolo(self):
        """T9: GET /api/camera/sources returns exactly 200 without initializing YOLO."""
        from fastapi.testclient import TestClient
        from main import app

        with patch("routers.ai_engine.get_detector") as mock_get_det:
            client = TestClient(app)
            resp = client.get("/api/camera/sources")
            self.assertEqual(resp.status_code, 200, f"Expected 200, got {resp.status_code}")
            data = resp.json()
            self.assertIn("mode", data)
            self.assertIn("cameras", data)
            self.assertIn("demo_read_only", data)
            mock_get_det.assert_not_called()

    def test_09b_unknown_route_returns_404(self):
        """Unknown routes return 404, not 403 or 200."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.get("/api/nonexistent_route_404")
        self.assertEqual(resp.status_code, 404)

    def test_09c_demo_read_only_false_allows_local_mode(self):
        """When DEMO_READ_ONLY=false, mode endpoint returns 200 for local client."""
        with patch.dict(os.environ, {"DEMO_READ_ONLY": "false"}):
            from fastapi.testclient import TestClient
            from main import app
            client = TestClient(app)
            resp = client.post("/api/camera/mode", json={"mode": "DUAL_CAMERA"})
            self.assertEqual(resp.status_code, 200)


# ── T10–T11: Secret Redaction & Marker Scan ──────────────────────────────────
class T10T11SecretScanTests(unittest.TestCase):

    def test_10_redact_url_all_variants(self):
        """T10: redact_url() redacts all listed secret query key variants (case-insensitive)."""
        from services.camera_source import redact_url
        secret_keys = [
            "token", "TOKEN", "apiKey", "password", "Password",
            "secret", "auth", "key", "pass"
        ]
        marker = "CONFIDENTIAL_MARKER_98765"
        for k in secret_keys:
            url = f"rtsp://cam.local:554/live?stream=0&{k}={marker}"
            redacted = redact_url(url)
            self.assertNotIn(
                marker, redacted,
                f"Secret value not redacted for key='{k}': got '{redacted}'"
            )
            self.assertIn(
                k.lower(), redacted.lower(),
                f"Key '{k}' should still be preserved in URL structure"
            )

    def test_11_secret_marker_scan_source_files(self):
        """T11: Scan source files for banned plaintext credential markers."""
        BANNED_PATTERNS = [
            "password=secret",
            "password=admin",
            "token=abc",
            "apikey=",
            "supersecret",
            "confidential_marker_98765"
        ]
        SCAN_EXTENSIONS = (".py", ".ts", ".tsx")
        SCAN_ROOTS = [
            os.path.join(BACKEND_DIR, "routers"),
            os.path.join(BACKEND_DIR, "services"),
            os.path.join(PROJECT_ROOT, "src", "services"),
        ]
        EXEMPT_FILENAMES = {"test_sprint32b.py", "camera_source.py"}

        violations = []
        for root in SCAN_ROOTS:
            if not os.path.isdir(root):
                continue
            for dirpath, _, files in os.walk(root):
                for fname in files:
                    if not fname.endswith(SCAN_EXTENSIONS):
                        continue
                    if fname in EXEMPT_FILENAMES:
                        continue
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, encoding="utf-8", errors="ignore") as fh:
                            content_lower = fh.read().lower()
                        for pat in BANNED_PATTERNS:
                            if pat in content_lower:
                                violations.append(
                                    f"{os.path.relpath(fpath, PROJECT_ROOT)}: contains '{pat}'"
                                )
                    except OSError:
                        pass

        self.assertEqual(violations, [], "Secret scan found violations:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
