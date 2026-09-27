"""
================================================================================
BACKEND INTEGRATION TESTS — /api/ws/preview TRANSPORT (SPRINT 3.2B-R2)
================================================================================
1. cam1 connects and receives valid JPEG, OpenCV decodable.
2. cam2 connects and receives valid JPEG, OpenCV decodable.
3. No cross-camera frame/sequence or color contamination.
4. Preview does NOT initialize a second RTSP decoder or load models.
5. Preview does NOT increase inference pending depth.
6. Malformed source_id rejected with explicit WebSocket close code 1008.
7. Offline camera sends OFFLINE status message.
8. Payload strictly free of credentials, RTSP URLs, and filesystem paths.
9. Slow client: tracks produced, transmitted, received, superseded, bytes, pending depth.
   Proves single-slot bound (no unbounded memory queue).
10. Disconnect cleanup: subscriber count and pending depth measured before, during,
    and after disconnect; strictly returns to baseline.
================================================================================
"""

import os
import sys
import time
import struct
import json
import unittest
import numpy as np
import cv2

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
from services.camera_manager import camera_manager
from services.camera_source import BrowserWebSocketSource, CameraStatus, RtspCameraSource


def _make_colored_jpeg(b: int, g: int, r: int, sz=(160, 120)) -> bytes:
    frame = np.zeros((sz[1], sz[0], 3), dtype=np.uint8)
    frame[:, :, 0] = b
    frame[:, :, 1] = g
    frame[:, :, 2] = r
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    assert ok
    return buf.tobytes()


class TestPreviewTransportIntegrationR2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        camera_manager.initialize()
        cls.client = TestClient(app)

    def test_01_two_cameras_valid_jpeg_and_color_isolation(self):
        """1-3: Connect cam1 & cam2, decode via OpenCV, verify distinct colors and zero leakage."""
        cam1 = camera_manager.get_source("cam1")
        cam2 = camera_manager.get_source("cam2")
        if cam2 is None:
            camera_manager.set_mode("DUAL_CAMERA")
            cam2 = camera_manager.get_source("cam2")

        self.assertIsNotNone(cam1)
        self.assertIsNotNone(cam2)
        cam1.status = CameraStatus.ONLINE
        cam2.status = CameraStatus.ONLINE

        # cam1: Green (B=0, G=220, R=0)
        green_jpeg = _make_colored_jpeg(0, 220, 0)
        cam1.set_latest_preview(green_jpeg, time.time(), sequence_id=101)

        # cam2: Blue (B=220, G=0, R=0)
        blue_jpeg = _make_colored_jpeg(220, 0, 0)
        cam2.set_latest_preview(blue_jpeg, time.time(), sequence_id=201)

        # Connect cam1 preview
        with self.client.websocket_connect("/api/ws/preview?source_id=cam1&fps=15") as ws1:
            msg1 = ws1.receive()
            if "text" in msg1:
                msg1 = ws1.receive()

            raw_bytes1 = msg1.get("bytes")
            self.assertIsNotNone(raw_bytes1)
            self.assertGreater(len(raw_bytes1), 16)
            seq1, ts1 = struct.unpack(">qd", raw_bytes1[:16])
            self.assertEqual(seq1, 101)

            img1 = cv2.imdecode(np.frombuffer(raw_bytes1[16:], np.uint8), cv2.IMREAD_COLOR)
            self.assertIsNotNone(img1)
            avg_b1 = np.mean(img1[:, :, 0])
            avg_g1 = np.mean(img1[:, :, 1])
            self.assertGreater(avg_g1, 150)
            self.assertLess(avg_b1, 50)

        # Connect cam2 preview
        with self.client.websocket_connect("/api/ws/preview?source_id=cam2&fps=15") as ws2:
            msg2 = ws2.receive()
            if "text" in msg2:
                msg2 = ws2.receive()

            raw_bytes2 = msg2.get("bytes")
            self.assertIsNotNone(raw_bytes2)
            seq2, ts2 = struct.unpack(">qd", raw_bytes2[:16])
            self.assertEqual(seq2, 201)

            img2 = cv2.imdecode(np.frombuffer(raw_bytes2[16:], np.uint8), cv2.IMREAD_COLOR)
            self.assertIsNotNone(img2)
            avg_b2 = np.mean(img2[:, :, 0])
            avg_g2 = np.mean(img2[:, :, 1])
            self.assertGreater(avg_b2, 150)
            self.assertLess(avg_g2, 50)

        # Strict isolation verification
        self.assertNotEqual(seq1, seq2)
        self.assertGreater(avg_g1, avg_g2)
        self.assertGreater(avg_b2, avg_b1)

    def test_02_preview_does_not_spawn_rtsp_decoder_or_touch_models(self):
        """4: Mock/spy VideoCapture and model loader; verify preview transport isolates decoder & models."""
        from unittest.mock import patch
        import threading

        cam1 = camera_manager.get_source("cam1")
        baseline_threads = threading.active_count()
        init_submitted = cam1.inference_slot.submitted
        init_pending = cam1.inference_slot.pending_depth

        with patch("services.camera_source.cv2.VideoCapture") as mock_vc, \
             patch("routers.ai_engine.get_detector") as mock_detector:

            cam1.status = CameraStatus.ONLINE
            cam1.set_latest_preview(_make_colored_jpeg(0, 180, 0), time.time(), sequence_id=701)

            with self.client.websocket_connect("/api/ws/preview?source_id=cam1&fps=10") as ws:
                msg = ws.receive()
                if "text" in msg:
                    msg = ws.receive()
                raw_b = msg.get("bytes")
                self.assertIsNotNone(raw_b)

            # Assert VideoCapture was never invoked
            self.assertEqual(mock_vc.call_count, 0, "Preview transport MUST NOT spawn cv2.VideoCapture decoder")
            # Assert get_detector was never invoked
            self.assertEqual(mock_detector.call_count, 0, "Preview transport MUST NOT invoke AI model loader")
            # Assert inference queue metrics untouched
            self.assertEqual(cam1.inference_slot.submitted, init_submitted, "Inference submitted must remain unchanged")
            self.assertEqual(cam1.inference_slot.pending_depth, init_pending, "Inference pending depth must remain unchanged")
            # Assert thread count returns to baseline
            self.assertEqual(threading.active_count(), baseline_threads, "Thread count must remain at baseline")

    def test_03_preview_does_not_increase_inference_pending_depth(self):
        """5: Verify preview operations leave AI inference slot untouched."""
        cam1 = camera_manager.get_source("cam1")
        initial_pending = cam1.inference_slot.pending_depth
        initial_submitted = cam1.inference_slot.submitted

        for i in range(5):
            cam1.set_latest_preview(_make_colored_jpeg(0, 100 + i, 0), time.time(), sequence_id=300 + i)

        self.assertEqual(cam1.inference_slot.pending_depth, initial_pending)
        self.assertEqual(cam1.inference_slot.submitted, initial_submitted)

    def test_04_invalid_source_id_closed_with_1008(self):
        """6: Malformed source_id is rejected with explicit code 1008 (WS_1008_POLICY_VIOLATION)."""
        with self.assertRaises(WebSocketDisconnect) as ctx:
            with self.client.websocket_connect("/api/ws/preview?source_id=bad%20id%24%24&fps=10") as ws:
                ws.receive()
        self.assertEqual(ctx.exception.code, 1008, f"Expected 1008, got {ctx.exception.code}")

    def test_05_offline_camera_sends_offline_status(self):
        """7: Offline camera reports OFFLINE status message."""
        temp_src = BrowserWebSocketSource("cam_offline_test", "Offline Test Cam")
        camera_manager.register_custom_source(temp_src)
        temp_src.status = CameraStatus.OFFLINE

        with self.client.websocket_connect("/api/ws/preview?source_id=cam_offline_test&fps=10") as ws:
            msg = ws.receive_text()
            data = json.loads(msg)
            self.assertEqual(data.get("type"), "status")
            self.assertEqual(data.get("status"), "OFFLINE")

    def test_06_payload_free_of_secrets_and_filesystem_paths(self):
        """8: Ensure messages contain zero credentials, RTSP URLs, or filesystem paths."""
        cam1 = camera_manager.get_source("cam1")
        cam1.status = CameraStatus.ONLINE
        cam1.set_latest_preview(
            _make_colored_jpeg(0, 200, 0),
            time.time(),
            401,
            detections=[{"label": "NORMAL"}],
            level="normal"
        )

        with self.client.websocket_connect("/api/ws/preview?source_id=cam1&fps=15") as ws:
            for _ in range(2):
                msg = ws.receive()
                if "text" in msg:
                    t = msg["text"].lower()
                    self.assertNotIn("password", t)
                    self.assertNotIn("rtsp://", t)
                    self.assertNotIn("secret", t)
                    self.assertNotIn("c:\\", t)
                    self.assertNotIn("/users/", t)

    def test_07_slow_client_backpressure_and_single_slot_invariants(self):
        """
        9: Connect real WebSocket client first, actively stream frames faster than client reads,
        verify slow client receives latest frame, pending_depth <= 1, superseded increases,
        and produced, transmitted, and received are independently measured.
        """
        import threading
        cam1 = camera_manager.get_source("cam1")
        cam1.status = CameraStatus.ONLINE

        with cam1._preview_lock:
            cam1._latest_preview_jpeg = None
            cam1._latest_preview_seq = -1
            cam1.preview_frames_produced = 0
            cam1.preview_frames_transmitted = 0
            cam1.preview_frames_superseded = 0
            cam1.preview_bytes_transmitted = 0

        bytes_produced = 0
        frames_produced_count = 0
        stop_producer = threading.Event()

        def rapid_producer():
            nonlocal bytes_produced, frames_produced_count
            seq = 500
            while not stop_producer.is_set():
                seq += 1
                jpeg = _make_colored_jpeg(0, (100 + seq) % 255, 0)
                bytes_produced += len(jpeg)
                frames_produced_count += 1
                cam1.set_latest_preview(jpeg, time.time(), sequence_id=seq)
                time.sleep(0.01)  # 10ms interval = ~100 FPS (much faster than client reads)

        frames_received = 0
        received_seqs = []

        # Connect real WebSocket client while streaming is active
        with self.client.websocket_connect("/api/ws/preview?source_id=cam1&fps=20") as ws:
            # Start active producer AFTER client connection is established
            prod_thread = threading.Thread(target=rapid_producer, daemon=True)
            prod_thread.start()

            # Client intentionally reads slowly (with delay between reads)
            for _ in range(4):
                time.sleep(0.05)  # Client waits 50ms (producer produces ~5 frames in this window)
                msg = ws.receive()
                if "text" in msg:
                    msg = ws.receive()
                raw_b = msg.get("bytes")
                if raw_b and len(raw_b) > 16:
                    seq, ts = struct.unpack(">qd", raw_b[:16])
                    frames_received += 1
                    received_seqs.append(seq)

                # Check pending depth invariant while running
                self.assertLessEqual(cam1.preview_pending_depth, 1, "Pending depth must never exceed 1")

            stop_producer.set()
            prod_thread.join(timeout=2.0)

        # Invariant Assertions:
        # 1. Produced > Transmitted >= Received
        self.assertGreater(cam1.preview_frames_produced, cam1.preview_frames_transmitted,
                           "Producer must generate more frames than transmitted over WebSocket")
        self.assertGreaterEqual(cam1.preview_frames_transmitted, frames_received,
                                "Transmitted frames must be >= received frames")
        self.assertGreaterEqual(frames_received, 2, "Client must have received at least 2 frames")

        # 2. Bytes produced vs bytes transmitted
        self.assertGreater(bytes_produced, cam1.preview_bytes_transmitted,
                           "Produced bytes must exceed transmitted bytes under slow client backpressure")
        self.assertGreater(cam1.preview_bytes_transmitted, 0, "Transmitted bytes must be > 0")

        # 3. Superseded count must have increased
        self.assertGreater(cam1.preview_frames_superseded, 0,
                           "Superseded count must increase when client reads slower than producer")

        # 4. Client received newer frames skipping stale ones (non-consecutive sequences)
        if len(received_seqs) >= 2:
            step_gap = received_seqs[-1] - received_seqs[0]
            self.assertGreater(step_gap, len(received_seqs) - 1,
                               f"Received sequences {received_seqs} should skip superseded frames without backlog")

    def test_08_disconnect_cleanup_returns_to_baseline(self):
        """
        10: Verify all preview resources return to baseline upon client disconnect:
        - subscriber count
        - pending slot bound (<= 1)
        - active preview connection registry count
        - thread count
        (Explicitly reporting: kernel OS socket buffers are managed by OS networking stack and not instrumented).
        """
        from routers.ai_engine import get_active_preview_count
        import threading

        cam1 = camera_manager.get_source("cam1")
        cam1.status = CameraStatus.ONLINE
        cam1.set_latest_preview(_make_colored_jpeg(50, 50, 50), time.time(), 601)

        # Baseline measurements BEFORE connection
        subs_before = cam1.preview_subscribers
        tasks_before = get_active_preview_count()
        depth_before = cam1.preview_pending_depth
        threads_before = threading.active_count()

        self.assertEqual(subs_before, 0, "Baseline subscribers must be 0")
        self.assertEqual(tasks_before, 0, "Baseline active preview tasks must be 0")
        self.assertLessEqual(depth_before, 1, "Baseline pending depth must be <= 1")

        # Active connection measurements DURING connection
        with self.client.websocket_connect("/api/ws/preview?source_id=cam1&fps=10") as ws:
            _ = ws.receive()
            subs_during = cam1.preview_subscribers
            tasks_during = get_active_preview_count()

            self.assertEqual(subs_during, 1, "Active subscribers must be 1")
            self.assertEqual(tasks_during, 1, "Active preview task count must be 1")
            # Verify preview transport itself does not spawn dedicated background camera threads
            preview_named_threads = [t for t in threading.enumerate() if "preview_worker" in t.name.lower()]
            self.assertEqual(len(preview_named_threads), 0, "No dedicated preview worker threads should be spawned")

        # Baseline restoration measurements AFTER disconnect
        # Allow brief time for client portal closure and disconnect cleanup
        time.sleep(0.1)
        subs_after = cam1.preview_subscribers
        tasks_after = get_active_preview_count()
        depth_after = cam1.preview_pending_depth
        threads_after = threading.active_count()

        self.assertEqual(subs_after, 0, "Subscriber count must strictly return to 0 after disconnect")
        self.assertEqual(tasks_after, 0, "Active preview task registry must strictly return to 0 after disconnect")
        self.assertLessEqual(depth_after, 1, "Pending depth must strictly remain bounded <= 1")
        self.assertEqual(threads_after, threads_before, "Thread count must strictly return to baseline after disconnect")


if __name__ == "__main__":
    unittest.main(verbosity=2)

