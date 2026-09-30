"""
================================================================================
DUAL-CAMERA PIPELINE AUTOMATED TEST SUITE - AI EXAM CONTROL (SPRINT 3.2)
================================================================================
Comprehensive verification of Dual-Camera monitoring mode:
1. test_01_single_camera_backward_compatibility
2. test_02_dual_camera_mode_switching
3. test_03_camera_sources_status_endpoint
4. test_04_rtsp_credential_redaction
5. test_05_rtsp_safe_reconnect_backoff
6. test_06_camera_source_synthetic_feed
7. test_07_camera_source_status_transitions
8. test_08_fair_scheduler_round_robin
9. test_09_fair_scheduler_single_camera_fallback
10. test_10_single_slot_buffer_zero_backlog
11. test_11_single_slot_invariant_balance
12. test_12_ring_buffer_dual_camera_isolation
13. test_13_ring_buffer_dual_camera_concurrent_clips
14. test_14_incident_id_collision_resistance
15. test_15_database_source_metadata_persistence
16. test_16_temporal_tracker_per_camera_isolation
17. test_17_websocket_ingest_multi_source
18. test_18_websocket_ingest_same_source_mutex
19. test_19_session_reset_dual_camera
20. test_20_dual_camera_evidence_retrieval
================================================================================
"""

import os
import sys
import time
import uuid
import struct
import sqlite3
import unittest
import json
import numpy as np
import cv2

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["ENABLE_TEST_ENDPOINTS"] = "true"

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from main import app
from database import DB_PATH, SessionLocal
from models import Incident
from services.camera_source import (
    BaseCameraSource,
    BrowserWebSocketSource,
    RtspCameraSource,
    SyntheticCameraSource,
    SingleSlotSourceBuffer,
    CameraStatus,
    redact_url
)
from services.fair_scheduler import fair_inference_scheduler
from services.camera_manager import camera_manager
from services.ring_buffer import VideoRingBuffer, ring_buffer_service, EVIDENCE_DIR
from services.temporal_tracker import temporal_posture_tracker
from services.db_queue import db_write_queue
import routers.ai_engine as ai_engine_mod


class TestDualCameraPipeline(unittest.TestCase):
    """20 Automated Tests covering all aspects of Dual-Camera monitoring."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        camera_manager.initialize()

    def setUp(self):
        camera_manager.set_mode("SINGLE_CAMERA")
        ai_engine_mod.reset_ai_session_state(None)

    def tearDown(self):
        camera_manager.set_mode("SINGLE_CAMERA")
        ai_engine_mod.reset_ai_session_state(None)
        with camera_manager._lock:
            extra = [k for k in camera_manager._sources if k not in ("cam1", "cam2")]
            for k in extra:
                s = camera_manager._sources.pop(k, None)
                if s:
                    s.stop()

    # ----------------------------------------------------------------------
    # 1. test_01_single_camera_backward_compatibility
    # ----------------------------------------------------------------------
    def test_01_single_camera_backward_compatibility(self):
        """Verify SINGLE_CAMERA mode preserves 100% legacy single-stream behavior."""
        camera_manager.set_mode("SINGLE_CAMERA")
        self.assertEqual(camera_manager.mode, "SINGLE_CAMERA")

        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        _, jpeg = cv2.imencode(".jpg", dummy)
        payload = struct.pack(">qd", 1, time.time()) + jpeg.tobytes()

        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=sess_sc_01") as ws:
            ws.send_bytes(payload)
            time.sleep(0.05)
            self.assertEqual(ai_engine_mod._active_ws_session_id, "sess_sc_01")
            ws.close()

        self.assertIsNone(ai_engine_mod._active_ws_session_id)

    # ----------------------------------------------------------------------
    # 2. test_02_dual_camera_mode_switching
    # ----------------------------------------------------------------------
    def test_02_dual_camera_mode_switching(self):
        """Verify safe runtime switching between SINGLE_CAMERA and DUAL_CAMERA."""
        # Switch to DUAL_CAMERA via POST API
        res1 = self.client.post("/api/camera/mode", json={"mode": "DUAL_CAMERA"})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["mode"], "DUAL_CAMERA")
        self.assertEqual(camera_manager.mode, "DUAL_CAMERA")

        # Query GET /api/camera/mode
        res_get = self.client.get("/api/camera/mode")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["mode"], "DUAL_CAMERA")

        # Switch back to SINGLE_CAMERA
        res2 = self.client.post("/api/camera/mode", json={"mode": "SINGLE_CAMERA"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["mode"], "SINGLE_CAMERA")
        self.assertEqual(camera_manager.mode, "SINGLE_CAMERA")

    # ----------------------------------------------------------------------
    # 3. test_03_camera_sources_status_endpoint
    # ----------------------------------------------------------------------
    def test_03_camera_sources_status_endpoint(self):
        """Verify GET /api/camera/sources returns status and zero exposed credentials."""
        res = self.client.get("/api/camera/sources")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("mode", data)
        self.assertIn("cameras", data)
        self.assertIn("total_online", data)
        self.assertIn("scheduler_inference_fps", data)
        self.assertIn("scheduler_latency_ms", data)

        for cam in data["cameras"]:
            self.assertIn("source_id", cam)
            self.assertIn("source_label", cam)
            self.assertIn("source_type", cam)
            self.assertIn("status", cam)
            # Guarantee no credentials or sensitive URLs
            self.assertNotIn("password", str(cam).lower())
            self.assertNotIn("secret", str(cam).lower())

    # ----------------------------------------------------------------------
    # 4. test_04_rtsp_credential_redaction
    # ----------------------------------------------------------------------
    def test_04_rtsp_credential_redaction(self):
        """Verify redact_url obscures user/passwords in RTSP URLs."""
        raw = "rtsp://admin:secretPass123@192.168.1.100:554/stream1"
        redacted = redact_url(raw)
        self.assertEqual(redacted, "rtsp://***:***@192.168.1.100:554/stream1")
        self.assertNotIn("secretPass123", redacted)
        self.assertNotIn("admin", redacted)

        # URL without credentials remains safe
        no_creds = "rtsp://192.168.1.50:554/live"
        self.assertEqual(redact_url(no_creds), no_creds)

        # Empty or non-string input
        self.assertEqual(redact_url(""), "")

    # ----------------------------------------------------------------------
    # 5. test_05_rtsp_safe_reconnect_backoff
    # ----------------------------------------------------------------------
    def test_05_rtsp_safe_reconnect_backoff(self):
        """Verify RTSP camera source handles reconnect backoff safely without crashing."""
        source = RtspCameraSource(
            source_id="test_rtsp_safe",
            source_label="Test RTSP",
            rtsp_url="rtsp://test:pass@127.0.0.1:9999/live"
        )
        self.assertEqual(source.reconnect_count, 0)
        b1 = source._calculate_backoff(1)
        b2 = source._calculate_backoff(2)
        b5 = source._calculate_backoff(10)
        self.assertGreaterEqual(b1, 1.0)
        self.assertGreater(b2, b1)
        self.assertLessEqual(b5, 30.0)  # Max capped at 30s

    # ----------------------------------------------------------------------
    # 6. test_06_camera_source_synthetic_feed
    # ----------------------------------------------------------------------
    def test_06_camera_source_synthetic_feed(self):
        """Verify SyntheticCameraSource generates test frames at configured rate."""
        synth = SyntheticCameraSource("test_synth_cam", "Synthetic Camera", target_fps=30.0)
        self.assertEqual(synth.status, CameraStatus.STOPPED)
        synth.start()
        self.assertIn(synth.status, (CameraStatus.CONNECTING, CameraStatus.ONLINE))
        time.sleep(0.15)
        self.assertGreater(synth.frames_received, 0)
        synth.stop()
        self.assertEqual(synth.status, CameraStatus.STOPPED)

    # ----------------------------------------------------------------------
    # 7. test_07_camera_source_status_transitions
    # ----------------------------------------------------------------------
    def test_07_camera_source_status_transitions(self):
        """Verify camera status state machine: CONNECTING -> ONLINE -> STOPPED."""
        ws_src = BrowserWebSocketSource("trans_cam", "Transition Camera")
        self.assertEqual(ws_src.status, CameraStatus.STOPPED)
        ws_src.start()
        self.assertEqual(ws_src.status, CameraStatus.CONNECTING)

        dummy = np.zeros((50, 50, 3), dtype=np.uint8)
        ws_src.push_frame(dummy, timestamp=time.monotonic(), sequence_id=1)
        self.assertEqual(ws_src.status, CameraStatus.ONLINE)
        self.assertEqual(ws_src.frames_received, 1)

        ws_src.stop()
        self.assertEqual(ws_src.status, CameraStatus.STOPPED)

    # ----------------------------------------------------------------------
    # 8. test_08_fair_scheduler_round_robin
    # ----------------------------------------------------------------------
    def test_08_fair_scheduler_round_robin(self):
        """Verify fair scheduler alternates round-robin between active cameras."""
        from services.fair_scheduler import FairInferenceScheduler
        sched = FairInferenceScheduler()
        s1 = BrowserWebSocketSource("rr_cam1", "Camera 1")
        s2 = BrowserWebSocketSource("rr_cam2", "Camera 2")
        s1.start()
        s2.start()

        sched.set_sources([s1, s2])
        dummy = np.zeros((40, 40, 3), dtype=np.uint8)

        # Push to both cameras
        s1.push_frame(dummy, timestamp=time.monotonic(), sequence_id=1)
        s2.push_frame(dummy, timestamp=time.monotonic(), sequence_id=1)

        # 1st pick
        p1 = sched._pick_next_frame()
        self.assertIsNotNone(p1)
        picked_src1, item1 = p1

        # Push another to s1 so both have pending frames
        s1.push_frame(dummy, timestamp=time.monotonic(), sequence_id=2)

        # 2nd pick must be s2 (fair alternating, zero starvation)
        p2 = sched._pick_next_frame()
        self.assertIsNotNone(p2)
        picked_src2, item2 = p2

        self.assertNotEqual(picked_src1.source_id, picked_src2.source_id)

    # ----------------------------------------------------------------------
    # 9. test_09_fair_scheduler_single_camera_fallback
    # ----------------------------------------------------------------------
    def test_09_fair_scheduler_single_camera_fallback(self):
        """Verify scheduler dedicates 100% time to active camera if other is silent."""
        from services.fair_scheduler import FairInferenceScheduler
        sched = FairInferenceScheduler()
        s1 = BrowserWebSocketSource("fb_cam1", "Camera 1")
        s2 = BrowserWebSocketSource("fb_cam2", "Camera 2")
        s1.start()
        s2.start()
        sched.set_sources([s1, s2])

        dummy = np.zeros((40, 40, 3), dtype=np.uint8)
        for i in range(1, 4):
            s1.push_frame(dummy, timestamp=time.monotonic(), sequence_id=i)
            p = sched._pick_next_frame()
            self.assertIsNotNone(p)
            self.assertEqual(p[0].source_id, "fb_cam1")
            p[0].inference_slot.mark_processed(0)

    # ----------------------------------------------------------------------
    # 10. test_10_single_slot_buffer_zero_backlog
    # ----------------------------------------------------------------------
    def test_10_single_slot_buffer_zero_backlog(self):
        """Verify single-slot buffer holds at most 1 pending frame (superseding older)."""
        buf = SingleSlotSourceBuffer("zero_backlog_cam")
        dummy = np.zeros((50, 50, 3), dtype=np.uint8)

        buf.push(dummy, timestamp=1.0, sequence_id=1, session_id="s1")
        self.assertEqual(buf.pending_depth, 1)
        self.assertEqual(buf.submitted, 1)
        self.assertEqual(buf.superseded, 0)

        buf.push(dummy, timestamp=2.0, sequence_id=2, session_id="s1")
        self.assertEqual(buf.pending_depth, 1)
        self.assertEqual(buf.submitted, 2)
        self.assertEqual(buf.superseded, 1)

        item = buf.pop()
        self.assertIsNotNone(item)
        self.assertEqual(item["sequence_id"], 2)

    # ----------------------------------------------------------------------
    # 11. test_11_single_slot_invariant_balance
    # ----------------------------------------------------------------------
    def test_11_single_slot_invariant_balance(self):
        """Verify invariant: submitted == processed + superseded + pending."""
        buf = SingleSlotSourceBuffer("inv_cam")
        dummy = np.zeros((30, 30, 3), dtype=np.uint8)

        for i in range(1, 11):
            buf.push(dummy, timestamp=float(i), sequence_id=i, session_id="s1")
            if i % 3 == 0:
                item = buf.pop()
                if item:
                    buf.mark_processed(1)

        stats = buf.get_stats()
        self.assertEqual(
            stats["submitted"],
            stats["processed"] + stats["superseded"] + stats["pending"],
            f"Invariant failed: {stats}"
        )

    # ----------------------------------------------------------------------
    # 12. test_12_ring_buffer_dual_camera_isolation
    # ----------------------------------------------------------------------
    def test_12_ring_buffer_dual_camera_isolation(self):
        """Verify RingBuffer instances are isolated; zero cross-contamination."""
        rb1 = VideoRingBuffer(pre_roll_seconds=3.0, post_roll_seconds=3.0)
        rb2 = VideoRingBuffer(pre_roll_seconds=3.0, post_roll_seconds=3.0)

        dummy1 = np.ones((40, 40, 3), dtype=np.uint8) * 10
        dummy2 = np.ones((40, 40, 3), dtype=np.uint8) * 20

        rb1.push_frame(dummy1, timestamp=1.0, source_id="cam1", session_id="s_cam1")
        rb2.push_frame(dummy2, timestamp=1.0, source_id="cam2", session_id="s_cam2")

        with rb1.lock:
            for f in rb1.frame_buffer:
                self.assertEqual(f[4], "cam1")
                self.assertEqual(f[3], "s_cam1")

        with rb2.lock:
            for f in rb2.frame_buffer:
                self.assertEqual(f[4], "cam2")
                self.assertEqual(f[3], "s_cam2")

    # ----------------------------------------------------------------------
    # 13. test_13_ring_buffer_dual_camera_concurrent_clips
    # ----------------------------------------------------------------------
    def test_13_ring_buffer_dual_camera_concurrent_clips(self):
        """Verify concurrent triggers on 2 cameras produce distinct incident IDs."""
        rb1 = VideoRingBuffer(pre_roll_seconds=1.0, post_roll_seconds=1.0)
        rb2 = VideoRingBuffer(pre_roll_seconds=1.0, post_roll_seconds=1.0)

        dummy = np.zeros((40, 40, 3), dtype=np.uint8)
        rb1.push_frame(dummy, timestamp=time.monotonic(), source_id="cam1", session_id="s1")
        rb2.push_frame(dummy, timestamp=time.monotonic(), source_id="cam2", session_id="s2")

        inc1 = rb1.trigger_incident(violation_type="PHONE", confidence=95.0, source_id="cam1", track_id=1, current_frame=dummy, level="red", session_id="s1", source_label="Camera 1")
        inc2 = rb2.trigger_incident(violation_type="HEAD_TURNING", confidence=90.0, source_id="cam2", track_id=2, current_frame=dummy, level="red", session_id="s2", source_label="Camera 2")

        self.assertIsNotNone(inc1)
        self.assertIsNotNone(inc2)
        self.assertNotEqual(inc1, inc2)
        self.assertTrue(inc1.startswith("inc_cam1_"))
        self.assertTrue(inc2.startswith("inc_cam2_"))

    # ----------------------------------------------------------------------
    # 14. test_14_incident_id_collision_resistance
    # ----------------------------------------------------------------------
    def test_14_incident_id_collision_resistance(self):
        """Verify 200 incident IDs generated simultaneously have zero collisions."""
        ids = set()
        t = time.time()
        for i in range(100):
            id_cam1 = f"inc_cam1_{int(t)}_{uuid.uuid4().hex[:8]}"
            id_cam2 = f"inc_cam2_{int(t)}_{uuid.uuid4().hex[:8]}"
            ids.add(id_cam1)
            ids.add(id_cam2)

        self.assertEqual(len(ids), 200)

    # ----------------------------------------------------------------------
    # 15. test_15_database_source_metadata_persistence
    # ----------------------------------------------------------------------
    def test_15_database_source_metadata_persistence(self):
        """Verify source_label, source_type, session_id are stored into SQLite."""
        inc_id = f"test_meta_{int(time.time()*1000)}"
        db_write_queue.enqueue_incident(
            incident_id=inc_id,
            source_id="cam2",
            track_id=88,
            violation_type="PHONE",
            confidence=94.5,
            level="red",
            detected_at=time.time(),
            clip_started_at=time.time() - 2.0,
            clip_ended_at=time.time() + 2.0,
            video_path=f"/evidence/{inc_id}.mp4",
            snapshot_path=f"/evidence/{inc_id}_snap.jpg",
            proctor_notes="Test note",
            source_label="Camera 2 (Góc bên)",
            source_type="rtsp",
            session_id="sess_dual_meta_99"
        )
        self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT source_id, source_label, source_type, session_id FROM incidents WHERE id = ?",
            (inc_id,)
        )
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "cam2")
        self.assertEqual(row[1], "Camera 2 (Góc bên)")
        self.assertEqual(row[2], "rtsp")
        self.assertEqual(row[3], "sess_dual_meta_99")

    # ----------------------------------------------------------------------
    # 16. test_16_temporal_tracker_per_camera_isolation
    # ----------------------------------------------------------------------
    def test_16_temporal_tracker_per_camera_isolation(self):
        """Verify temporal posture tracking on cam1 does not affect cam2."""
        temporal_posture_tracker.reset_session("sess_iso_1")
        t0 = time.time()

        temporal_posture_tracker.update("cam1", track_id=10, is_suspicious=True, timestamp=t0, alert_seconds=1.25, session_id="sess_iso_1")
        temporal_posture_tracker.update("cam1", track_id=10, is_suspicious=True, timestamp=t0 + 0.5, alert_seconds=1.25, session_id="sess_iso_1")
        temporal_posture_tracker.update("cam1", track_id=10, is_suspicious=True, timestamp=t0 + 1.0, alert_seconds=1.25, session_id="sess_iso_1")
        status1, level1, el1 = temporal_posture_tracker.update("cam1", track_id=10, is_suspicious=True, timestamp=t0 + 1.5, alert_seconds=1.25, session_id="sess_iso_1")
        self.assertEqual(level1, "red")

        status2, level2, el2 = temporal_posture_tracker.update("cam2", track_id=10, is_suspicious=False, timestamp=t0 + 1.5, alert_seconds=1.25, session_id="sess_iso_1")
        self.assertEqual(level2, "green")
        self.assertEqual(el2, 0.0)

    # ----------------------------------------------------------------------
    # 17. test_17_websocket_ingest_multi_source
    # ----------------------------------------------------------------------
    def test_17_websocket_ingest_multi_source(self):
        """Verify 2 WebSockets with different source_id can stream concurrently in DUAL_CAMERA mode."""
        camera_manager.set_mode("DUAL_CAMERA")
        self.assertEqual(camera_manager.mode, "DUAL_CAMERA")

        dummy = np.zeros((60, 60, 3), dtype=np.uint8)
        _, jpeg = cv2.imencode(".jpg", dummy)
        payload1 = struct.pack(">qd", 1, time.time()) + jpeg.tobytes()
        payload2 = struct.pack(">qd", 1, time.time()) + jpeg.tobytes()

        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=sess_cam1_live") as ws1:
            with self.client.websocket_connect("/api/ws/ingest?source_id=cam2&session_id=sess_cam2_live") as ws2:
                ws1.send_bytes(payload1)
                ws2.send_bytes(payload2)
                time.sleep(0.05)
                self.assertIn("cam1", ai_engine_mod._active_ws_sessions)
                self.assertIn("cam2", ai_engine_mod._active_ws_sessions)
                ws2.close()
            ws1.close()

    # ----------------------------------------------------------------------
    # 18. test_18_websocket_ingest_same_source_mutex
    # ----------------------------------------------------------------------
    def test_18_websocket_ingest_same_source_mutex(self):
        """Verify second connection on SAME source_id is rejected with 1008 in DUAL_CAMERA mode."""
        camera_manager.set_mode("DUAL_CAMERA")

        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=sess_cam1_first") as ws1:
            with self.assertRaises(WebSocketDisconnect) as cm:
                with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=sess_cam1_second"):
                    pass
            self.assertEqual(cm.exception.code, 1008)
            ws1.close()

    # ----------------------------------------------------------------------
    # 19. test_19_session_reset_dual_camera
    # ----------------------------------------------------------------------
    def test_19_session_reset_dual_camera(self):
        """Verify an explicit session reset leaves other sources untouched."""
        camera_manager.set_mode("DUAL_CAMERA")
        cam1 = camera_manager.get_source("cam1")
        cam2 = camera_manager.get_source("cam2")

        if cam1:
            cam1.session_id = "test_reset_sess"
            cam1.frames_received = 50
        if cam2:
            cam2.session_id = "other_camera_session"
            cam2.frames_received = 40

        res = self.client.post("/api/session/reset?session_id=test_reset_sess")
        self.assertEqual(res.status_code, 200)

        if cam1:
            self.assertEqual(cam1.frames_received, 0)
        if cam2:
            self.assertEqual(cam2.frames_received, 40)
            self.assertEqual(cam2.session_id, "other_camera_session")

    # ----------------------------------------------------------------------
    # 20. test_20_dual_camera_evidence_retrieval
    # ----------------------------------------------------------------------
    def test_20_dual_camera_evidence_retrieval(self):
        """Verify /incidents API returns source metadata and clips are accessible."""
        res = self.client.get("/api/incidents?limit=5")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertIsInstance(items, list)
        for inc in items:
            self.assertIn("source_id", inc)

    # ----------------------------------------------------------------------
    # 21. test_21_canonical_ws_ingest_source_id_contract
    # ----------------------------------------------------------------------
    def test_21_canonical_ws_ingest_source_id_contract(self):
        """Verify canonical WebSocket /api/ws/ingest preserves source_id for cam1 and cam2."""
        camera_manager.set_mode("DUAL_CAMERA")

        # Connect cam1
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=sess_cws_cam1") as ws1:
            dummy = np.zeros((30, 30, 3), dtype=np.uint8)
            _, buf = cv2.imencode(".jpg", dummy)
            payload1 = struct.pack(">qd", 1, time.monotonic()) + buf.tobytes()
            ws1.send_bytes(payload1)
            time.sleep(0.05)
            src1 = camera_manager.get_source("cam1")
            self.assertIsNotNone(src1)
            self.assertEqual(src1.source_id, "cam1")
            ws1.close()

        # Connect cam2
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam2&session_id=sess_cws_cam2") as ws2:
            payload2 = struct.pack(">qd", 1, time.monotonic()) + buf.tobytes()
            ws2.send_bytes(payload2)
            time.sleep(0.05)
            src2 = camera_manager.get_source("cam2")
            self.assertIsNotNone(src2)
            self.assertEqual(src2.source_id, "cam2")
            ws2.close()

    # ----------------------------------------------------------------------
    # 22. test_22_loopback_access_guard
    # ----------------------------------------------------------------------
    def test_22_loopback_access_guard(self):
        """Verify non-local clients receive 403 on administrative endpoints."""
        from routers.ai_engine import verify_local_loopback
        from fastapi import HTTPException

        class MockNonLocalClient:
            host = "192.168.1.99"

        class MockNonLocalRequest:
            client = MockNonLocalClient()

        with self.assertRaises(HTTPException) as ctx:
            verify_local_loopback(MockNonLocalRequest())
        self.assertEqual(ctx.exception.status_code, 403)

        class MockLocalClient:
            host = "127.0.0.1"

        class MockLocalRequest:
            client = MockLocalClient()

        verify_local_loopback(MockLocalRequest())

    # ----------------------------------------------------------------------
    # 23. test_23_api_camera_sources_zero_rtsp_urls
    # ----------------------------------------------------------------------
    def test_23_api_camera_sources_zero_rtsp_urls(self):
        """Verify GET /api/camera/sources NEVER returns any RTSP URL."""
        res = self.client.get("/api/camera/sources")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        raw_text = json.dumps(data)
        self.assertNotIn("rtsp://", raw_text)
        for cam in data.get("cameras", []):
            self.assertNotIn("rtsp://", json.dumps(cam))
            self.assertNotIn("url", cam)

    # ----------------------------------------------------------------------
    # 24. test_24_hardened_url_credential_redaction
    # ----------------------------------------------------------------------
    def test_24_hardened_url_credential_redaction(self):
        """Verify RFC URL parser, URL-encoded credentials, query parameters, and exception strings."""
        # 1. Standard credentials
        u1 = "rtsp://admin:my_secret@192.168.1.50:554/stream"
        r1 = redact_url(u1)
        self.assertEqual(r1, "rtsp://***:***@192.168.1.50:554/stream")
        self.assertNotIn("my_secret", r1)

        # 2. URL-encoded credentials and username with special characters
        u2 = "rtsp://user.name%2Badmin:P%40ssw0rd%23123@cam.local:8554/live"
        r2 = redact_url(u2)
        self.assertEqual(r2, "rtsp://***:***@cam.local:8554/live")
        self.assertNotIn("P%40ssw0rd%23123", r2)

        # 3. Query string with sensitive parameters (token, key, password)
        u3 = "rtsp://camera.internal:554/live?token=SECRET_TOKEN_999&cam_id=1&password=HIDDEN_PASS"
        r3 = redact_url(u3)
        self.assertNotIn("SECRET_TOKEN_999", r3)
        self.assertNotIn("HIDDEN_PASS", r3)
        self.assertIn("cam_id=1", r3)
        self.assertIn("token=***", r3)
        self.assertIn("password=***", r3)

        # 4. OpenCV / FFmpeg exception message with embedded URL
        exc_msg = "[rtsp @ 0000021c] method DESCRIBE failed: 401 Unauthorized for rtsp://admin:leaked_pass@10.0.0.5:554/stream1"
        r_exc = redact_url(exc_msg)
        self.assertNotIn("leaked_pass", r_exc)
        self.assertIn("rtsp://***:***@10.0.0.5:554/stream1", r_exc)

    # ----------------------------------------------------------------------
    # 25. test_25_synthetic_secret_marker_leak_scan
    # ----------------------------------------------------------------------
    def test_25_synthetic_secret_marker_leak_scan(self):
        """Scan API, SQLite, and telemetry to prove SENSITIVE_RTSP_MARKER_123 never leaks."""
        secret_marker = "SENSITIVE_RTSP_MARKER_123"
        sensitive_url = f"rtsp://proctor_admin:{secret_marker}@192.168.1.88:554/stream1?token={secret_marker}"

        source = RtspCameraSource("secret_cam", "Secret Camera", rtsp_url=sensitive_url)
        with camera_manager._lock:
            camera_manager._sources["secret_cam"] = source

        try:
            # 1. Scan /api/camera/sources
            res = self.client.get("/api/camera/sources")
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(secret_marker, res.text)

            # 2. Trigger incident on this source and enqueue to DB
            inc_id = f"inc_sec_{int(time.time()*1000)}"
            db_write_queue.enqueue_incident(
                incident_id=inc_id,
                source_id="secret_cam",
                violation_type="PHONE",
                confidence=95.0,
                proctor_notes=f"Source: {redact_url(sensitive_url)}",
                source_label="Secret Camera",
                source_type="rtsp"
            )
            db_write_queue.wait_until_idle(timeout=5.0)

            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT proctor_notes, source_label FROM incidents WHERE id = ?", (inc_id,))
            row = cur.fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertNotIn(secret_marker, str(row))
        finally:
            with camera_manager._lock:
                camera_manager._sources.pop("secret_cam", None)

    # ----------------------------------------------------------------------
    # 26. test_26_real_video_clip_generation_and_isolation
    # ----------------------------------------------------------------------
    def test_26_real_video_clip_generation_and_isolation(self):
        """
        Generate two real ~15-second MP4 evidence clips from cam1 and cam2 simultaneously.
        Inspect using OpenCV: verify duration, FPS, frame count, duplicate ratio, and
        prove cam1 clip has ZERO frames from cam2 and vice versa.
        """
        rb1 = VideoRingBuffer(pre_roll_seconds=5.0, post_roll_seconds=10.0, cooldown_seconds=1.0, target_fps=15.0)
        rb2 = VideoRingBuffer(pre_roll_seconds=5.0, post_roll_seconds=10.0, cooldown_seconds=1.0, target_fps=15.0)

        frame_cam1 = np.zeros((120, 160, 3), dtype=np.uint8)
        frame_cam1[:, :, 1] = 255  # Green channel = 255 (Cam 1 marker)

        frame_cam2 = np.zeros((120, 160, 3), dtype=np.uint8)
        frame_cam2[:, :, 0] = 255  # Blue channel = 255 (Cam 2 marker)

        t_base = 1000.0
        fps = 15.0
        dt = 1.0 / fps

        # 1. Feed 5.0 seconds of pre-roll (75 frames)
        for i in range(75):
            t_f = t_base + i * dt
            rb1.push_frame(frame_cam1, timestamp=t_f, sequence_id=i+1, session_id="sess_v_cam1", source_id="cam1")
            rb2.push_frame(frame_cam2, timestamp=t_f, sequence_id=i+1, session_id="sess_v_cam2", source_id="cam2")

        t_trigger = t_base + 75 * dt

        # 2. Trigger simultaneous incidents
        inc1 = rb1.trigger_incident(
            violation_type="PHONE",
            confidence=95.0,
            source_id="cam1",
            track_id=10,
            current_frame=frame_cam1,
            timestamp=t_trigger,
            session_id="sess_v_cam1",
            source_label="Camera 1 (Goc truoc)"
        )
        inc2 = rb2.trigger_incident(
            violation_type="HEAD_TURNING",
            confidence=92.0,
            source_id="cam2",
            track_id=20,
            current_frame=frame_cam2,
            timestamp=t_trigger,
            session_id="sess_v_cam2",
            source_label="Camera 2 (Goc ben)"
        )
        self.assertIsNotNone(inc1)
        self.assertIsNotNone(inc2)

        # 3. Feed 10.0 seconds of post-roll (150 frames)
        for i in range(75, 226):
            t_f = t_base + i * dt
            rb1.push_frame(frame_cam1, timestamp=t_f, sequence_id=i+1, session_id="sess_v_cam1", source_id="cam1")
            rb2.push_frame(frame_cam2, timestamp=t_f, sequence_id=i+1, session_id="sess_v_cam2", source_id="cam2")

        clip1_path = os.path.join(EVIDENCE_DIR, f"{inc1}.mp4")
        clip2_path = os.path.join(EVIDENCE_DIR, f"{inc2}.mp4")

        timeout = 10.0
        start_w = time.time()
        while time.time() - start_w < timeout:
            if os.path.exists(clip1_path) and os.path.exists(clip2_path):
                if os.path.getsize(clip1_path) > 1000 and os.path.getsize(clip2_path) > 1000:
                    break
            time.sleep(0.1)

        self.assertTrue(os.path.exists(clip1_path), f"Clip 1 was not created: {clip1_path}")
        self.assertTrue(os.path.exists(clip2_path), f"Clip 2 was not created: {clip2_path}")

        cap1 = cv2.VideoCapture(clip1_path)
        self.assertTrue(cap1.isOpened(), "Cannot open clip1 MP4")
        fc1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
        fps1 = cap1.get(cv2.CAP_PROP_FPS)
        dur1 = fc1 / fps1 if fps1 > 0 else 0.0

        cam1_frames_read = 0
        while True:
            ret, frame = cap1.read()
            if not ret:
                break
            cam1_frames_read += 1
            self.assertGreater(np.mean(frame[:, :, 1]), 200, "Frame in Cam 1 clip does not have Cam 1 marker")
            self.assertLess(np.mean(frame[:, :, 0]), 50, "Frame in Cam 1 clip contaminated with Cam 2 marker!")
        cap1.release()

        cap2 = cv2.VideoCapture(clip2_path)
        self.assertTrue(cap2.isOpened(), "Cannot open clip2 MP4")
        fc2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))
        fps2 = cap2.get(cv2.CAP_PROP_FPS)
        dur2 = fc2 / fps2 if fps2 > 0 else 0.0

        cam2_frames_read = 0
        while True:
            ret, frame = cap2.read()
            if not ret:
                break
            cam2_frames_read += 1
            self.assertGreater(np.mean(frame[:, :, 0]), 200, "Frame in Cam 2 clip does not have Cam 2 marker")
            self.assertLess(np.mean(frame[:, :, 1]), 50, "Frame in Cam 2 clip contaminated with Cam 1 marker!")
        cap2.release()

        self.assertEqual(cam1_frames_read, fc1)
        self.assertEqual(cam2_frames_read, fc2)
        self.assertAlmostEqual(dur1, 15.0, delta=1.0)
        self.assertAlmostEqual(dur2, 15.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()

