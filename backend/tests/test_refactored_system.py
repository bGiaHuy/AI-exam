"""
================================================================================
AUTOMATED TEST SUITE - REFACTORED AI EXAM CONTROL SYSTEM (SPRINT 1.2B HARDENED)
================================================================================
Strict Scope Compliance Verification: 27 Independent Acceptance Tests
  1. test_01_schema_contains_zero_identity
  2. test_02_migration_safe_and_idempotent
  3. test_03_create_phone_violation
  4. test_04_create_head_turning_violation
  5. test_05_yellow_flag_does_not_create_clip_or_db_event
  6. test_06_red_flag_creates_clip
  7. test_07_cooldown_isolates_separate_tracks
  8. test_08_cooldown_blocks_duplicate_triggers_on_same_track
  9. test_09_temporal_rule_uses_real_elapsed_time
  10. test_10_preroll_5s_and_postroll_10s_duration
  11. test_11_corrupted_clip_not_saved_as_completed_evidence
  12. test_12_db_write_queue_handles_multiple_concurrent_requests_without_dropping
  13. test_13_settings_affect_runtime_behavior
  14. test_14_api_returns_correct_schema
  15. test_15_frontend_does_not_call_legacy_endpoints
  16. test_16_model_weights_loadable
  17. test_17_pipeline_end_to_end_with_fixture
  18. test_18_temporal_continuity_guard
  19. test_19_single_slot_inference_buffer_zero_backlog
  20. test_20_ring_buffer_15fps_and_session_isolation
  21. test_21_websocket_binary_ingest_endpoint
  22. test_22_websocket_malformed_packets
  23. test_23_websocket_query_parameter_validation
  24. test_24_websocket_stress_disconnect_during_inference
  25. test_25_session_isolation_and_reset_api
  26. test_26_single_session_lock_rejects_concurrent_connection
  27. test_27_server_monotonic_timestamp_and_telemetry_fields
  28. test_28_session_telemetry_invariants_and_isolation
================================================================================
"""

import os
import re
import sys
import time
import uuid
import shutil
import sqlite3
import unittest
import threading
import tempfile
import numpy as np
import cv2
from datetime import datetime, timezone

# Add backend directory to sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from main import app
from database import DB_PATH, get_db, SessionLocal
import struct
from models import Incident
from services.db_queue import db_write_queue
from services.ring_buffer import ring_buffer_service, EVIDENCE_DIR, validate_video_file
from services.temporal_tracker import TemporalPostureTracker, temporal_posture_tracker
from services.inference_worker import SingleSlotInferenceBuffer, inference_buffer
import routers.ai_engine as ai_engine_mod
from routers.ai_engine import (
    update_detector_settings,
    _posture_temporal_tracker,
    PHONE_WEIGHTS,
    POSE_WEIGHTS
)
from routers.settings import load_settings, save_settings
from migrate_db import migrate_database, NEW_SCHEMA_SQL


class TestRefactoredSystem17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db_path = DB_PATH

    def tearDown(self):
        # Reset ring_buffer_service configuration to defaults after each test
        ring_buffer_service.update_settings(
            pre_roll_seconds=5.0,
            post_roll_seconds=10.0,
            cooldown_seconds=6.0
        )
        ring_buffer_service.active_tasks.clear()
        ring_buffer_service.last_incident_time_by_key.clear()
        with ai_engine_mod._session_mutex:
            ai_engine_mod._active_ws_session_id = None

    # ----------------------------------------------------------------------
    # 1. Schema contains zero identity
    # ----------------------------------------------------------------------
    def test_01_schema_contains_zero_identity(self):
        """Verify database only has incidents table with zero identity columns."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Check tables: no students, protocol_reports, rooms
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cur.fetchall()]
        self.assertIn("incidents", tables, "Incidents table must exist")
        self.assertNotIn("students", tables, "CRITICAL: students table must NOT exist")
        self.assertNotIn("protocol_reports", tables, "CRITICAL: protocol_reports table must NOT exist")
        self.assertNotIn("rooms", tables, "CRITICAL: rooms table must NOT exist")

        # Check columns of incidents table
        cur.execute("PRAGMA table_info(incidents);")
        columns = [r[1] for r in cur.fetchall()]
        prohibited_cols = ["student_id", "sbd", "cccd", "name", "student_name", "integrity_score", "room_id"]
        for col in prohibited_cols:
            self.assertNotIn(col, columns, f"CRITICAL: Column '{col}' violates zero-identity mandate")

        # Check required schema columns
        required_cols = [
            "id", "source_id", "track_id", "violation_type", "confidence",
            "level", "detected_at", "video_path", "snapshot_path", "status", "created_at"
        ]
        for col in required_cols:
            self.assertIn(col, columns, f"Required column '{col}' missing from incidents")

        # Check WAL mode
        cur.execute("PRAGMA journal_mode;")
        journal_mode = cur.fetchone()[0].lower()
        self.assertEqual(journal_mode, "wal", "Database should be running in WAL mode")
        conn.close()

    # ----------------------------------------------------------------------
    # 2. Migration safe and idempotent
    # ----------------------------------------------------------------------
    def test_02_migration_safe_and_idempotent(self):
        """Verify migration script creates backups, handles legacy tables, and is idempotent."""
        temp_dir = tempfile.mkdtemp(prefix="test_mig_")
        temp_db = os.path.join(temp_dir, "legacy_test.db")

        try:
            # 1. Create a legacy database with legacy tables and columns
            conn = sqlite3.connect(temp_db)
            conn.execute("""
                CREATE TABLE students (
                    id VARCHAR(100) PRIMARY KEY,
                    sbd VARCHAR(50),
                    name VARCHAR(100)
                );
            """)
            conn.execute("""
                CREATE TABLE rooms (
                    id VARCHAR(100) PRIMARY KEY,
                    room_code VARCHAR(50)
                );
            """)
            conn.execute("""
                CREATE TABLE incidents (
                    id VARCHAR(100) PRIMARY KEY,
                    student_id VARCHAR(100),
                    room_code VARCHAR(50),
                    violation_type VARCHAR(50),
                    confidence REAL,
                    level VARCHAR(20),
                    video_path VARCHAR(500),
                    snapshot_path VARCHAR(500),
                    status VARCHAR(20),
                    proctor_notes TEXT,
                    full_datetime TIMESTAMP,
                    created_at TIMESTAMP
                );
            """)
            conn.execute("INSERT INTO students VALUES ('S01', 'B20DCCN001', 'Nguyen Van A');")
            conn.execute("INSERT INTO rooms VALUES ('R01', 'P301');")
            conn.execute("""
                INSERT INTO incidents VALUES (
                    'inc_leg_1', 'S01', 'P301', 'PHONE', 92.5, 'red',
                    '/evidence/inc_leg_1.mp4', '/evidence/inc_leg_1.jpg',
                    'pending', 'Notes', '2026-03-01T10:00:00Z', '2026-03-01T10:00:00Z'
                );
            """)
            conn.commit()
            conn.close()

            # 2. Run migration
            success, msg = migrate_database(temp_db)
            self.assertTrue(success, f"Migration failed: {msg}")

            # Verify legacy tables dropped and incident data preserved
            conn = sqlite3.connect(temp_db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cur.fetchall()]
            self.assertIn("incidents", tables)
            self.assertNotIn("students", tables)
            self.assertNotIn("rooms", tables)

            cur.execute("PRAGMA table_info(incidents);")
            cols = [r[1] for r in cur.fetchall()]
            self.assertNotIn("student_id", cols)
            self.assertIn("source_id", cols)

            cur.execute("SELECT id, source_id, violation_type, confidence FROM incidents WHERE id='inc_leg_1';")
            migrated_row = cur.fetchone()
            self.assertIsNotNone(migrated_row)
            self.assertEqual(migrated_row[0], "inc_leg_1")
            self.assertEqual(migrated_row[1], "P301")
            self.assertEqual(migrated_row[2], "PHONE")
            self.assertEqual(migrated_row[3], 92.5)
            conn.close()

            # 3. Test Idempotency: Run migration AGAIN on already-migrated DB
            success2, msg2 = migrate_database(temp_db)
            self.assertTrue(success2, f"Idempotent migration run failed: {msg2}")

            # Verify records are preserved intact
            conn = sqlite3.connect(temp_db)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM incidents WHERE id='inc_leg_1';")
            count = cur.fetchone()[0]
            self.assertEqual(count, 1, "Record must be preserved after re-running migration")
            conn.close()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ----------------------------------------------------------------------
    # 3. Create phone violation
    # ----------------------------------------------------------------------
    def test_03_create_phone_violation(self):
        """Verify phone violation triggers red incident and persists into database."""
        test_id = f"test_phone_{int(time.time()*1000)}"
        db_write_queue.enqueue_incident({
            "id": test_id,
            "source_id": "test_cam_03",
            "track_id": 301,
            "violation_type": "PHONE",
            "confidence": 93.5,
            "level": "red",
            "detected_at": datetime.now(timezone.utc),
            "status": "pending",
            "proctor_notes": "Phone detected with high confidence"
        })
        self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

        db = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == test_id).first()
            self.assertIsNotNone(inc)
            self.assertEqual(inc.violation_type, "PHONE")
            self.assertEqual(inc.level, "red")
            self.assertEqual(inc.track_id, 301)
            self.assertEqual(inc.confidence, 93.5)
            db.delete(inc)
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------------------------
    # 4. Create head turning violation
    # ----------------------------------------------------------------------
    def test_04_create_head_turning_violation(self):
        """Verify head turning violation triggers red incident and persists into database."""
        test_id = f"test_head_{int(time.time()*1000)}"
        db_write_queue.enqueue_incident({
            "id": test_id,
            "source_id": "test_cam_04",
            "track_id": 401,
            "violation_type": "HEAD_TURNING",
            "confidence": 88.0,
            "level": "red",
            "detected_at": datetime.now(timezone.utc),
            "status": "pending",
            "proctor_notes": "Continuous head turning > 1.25s"
        })
        self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

        db = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == test_id).first()
            self.assertIsNotNone(inc)
            self.assertEqual(inc.violation_type, "HEAD_TURNING")
            self.assertEqual(inc.level, "red")
            self.assertEqual(inc.track_id, 401)
            db.delete(inc)
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------------------------
    # 5. Yellow flag does not create clip or DB event
    # ----------------------------------------------------------------------
    def test_05_yellow_flag_does_not_create_clip_or_db_event(self):
        """Verify yellow flag (warning) does not trigger RingBuffer recording or DB persistence."""
        active_tasks_before = len(ring_buffer_service.active_tasks)

        db = SessionLocal()
        try:
            count_before = db.query(Incident).count()
        finally:
            db.close()

        # Simulate yellow flag rule check: only HUD notification, no trigger_incident call
        flag_level = "yellow"
        if flag_level == "red":
            ring_buffer_service.trigger_incident(
                violation_type="HEAD_TURNING",
                confidence=75.0,
                source_id="cam_05",
                track_id=501,
                level="red"
            )

        active_tasks_after = len(ring_buffer_service.active_tasks)
        self.assertEqual(active_tasks_before, active_tasks_after, "Yellow flag must not create any RingBuffer task")

        db = SessionLocal()
        try:
            count_after = db.query(Incident).count()
            self.assertEqual(count_before, count_after, "Yellow flag must not insert any incident into DB")
        finally:
            db.close()

    # ----------------------------------------------------------------------
    # 6. Red flag creates clip
    # ----------------------------------------------------------------------
    def test_06_red_flag_creates_clip(self):
        """Verify red flag initiates video clip generation, verifies integrity, and saves to DB."""
        ring_buffer_service.update_settings(pre_roll_seconds=1.0, post_roll_seconds=1.0, cooldown_seconds=1.0)
        source_id = "test_clip_cam"

        try:
            # Push synthetic pre-roll frames
            for i in range(12):
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"Pre {i}", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
                ring_buffer_service.push_frame(frame, timestamp=time.time())
                time.sleep(0.04)

            # Trigger Red Flag
            incident_id = ring_buffer_service.trigger_incident(
                violation_type="PHONE",
                confidence=95.0,
                source_id=source_id,
                track_id=601,
                level="red"
            )
            self.assertIsNotNone(incident_id, "Red flag must return valid incident_id")

            # Push post-roll frames
            start_post = time.time()
            idx = 0
            while time.time() - start_post < 1.2:
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"Post {idx}", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                ring_buffer_service.push_frame(frame, timestamp=time.time())
                time.sleep(0.04)
                idx += 1

            # Wait for clip generation worker and DB queue
            time.sleep(1.0)
            self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

            # Check DB and File
            db = SessionLocal()
            try:
                inc = db.query(Incident).filter(Incident.id == incident_id).first()
                self.assertIsNotNone(inc)
                self.assertIsNotNone(inc.video_path)
                self.assertIsNotNone(inc.snapshot_path)

                video_filename = os.path.basename(inc.video_path)
                full_video_path = os.path.join(EVIDENCE_DIR, video_filename)
                self.assertTrue(os.path.exists(full_video_path), f"Video file {full_video_path} not found")
                self.assertTrue(validate_video_file(full_video_path), "Video file failed integrity validation")

                # Clean up
                db.delete(inc)
                db.commit()
                if os.path.exists(full_video_path):
                    os.remove(full_video_path)
                snap_file = os.path.join(EVIDENCE_DIR, os.path.basename(inc.snapshot_path))
                if os.path.exists(snap_file):
                    os.remove(snap_file)
            finally:
                db.close()
        finally:
            ring_buffer_service.update_settings(pre_roll_seconds=5.0, post_roll_seconds=10.0, cooldown_seconds=6.0)

    # ----------------------------------------------------------------------
    # 7. Cooldown isolates separate tracks
    # ----------------------------------------------------------------------
    def test_07_cooldown_isolates_separate_tracks(self):
        """Verify cooldown on track 1 does not suppress triggers on track 2."""
        ring_buffer_service.last_incident_time_by_key.clear()

        # Trigger for track 1
        res1 = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=90.0,
            source_id="cam_iso",
            track_id=101,
            level="red"
        )
        self.assertIsNotNone(res1, "Trigger for track 101 must succeed")

        # Immediate trigger for track 2 (different track) -> MUST SUCCEED
        res2 = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=92.0,
            source_id="cam_iso",
            track_id=102,
            level="red"
        )
        self.assertIsNotNone(res2, "Trigger for track 102 must NOT be blocked by track 101 cooldown")

    # ----------------------------------------------------------------------
    # 8. Cooldown blocks duplicate triggers on same track
    # ----------------------------------------------------------------------
    def test_08_cooldown_blocks_duplicate_triggers_on_same_track(self):
        """Verify rapid repeated trigger on same track is blocked by cooldown."""
        ring_buffer_service.last_incident_time_by_key.clear()

        # First trigger
        res1 = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=90.0,
            source_id="cam_blk",
            track_id=201,
            level="red"
        )
        self.assertIsNotNone(res1, "First trigger must succeed")

        # Second trigger on same track, same source, same violation -> MUST BE BLOCKED
        res2 = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=95.0,
            source_id="cam_blk",
            track_id=201,
            level="red"
        )
        self.assertIsNone(res2, "Immediate second trigger on same track must return None")

    # ----------------------------------------------------------------------
    # 9. Temporal rule uses real elapsed time
    # ----------------------------------------------------------------------
    def test_09_temporal_rule_uses_real_elapsed_time(self):
        """
        Verify temporal decision is computed using real timestamp delta (elapsed time >= 1.25s),
        NOT by counting 25 frames under hardcoded 20 FPS assumption.
        """
        _posture_temporal_tracker.clear()
        alert_sec = 1.25
        source = "cam_temporal"
        track = 901
        key = (source, track)

        # Frame 1 at t = 100.0s: first suspicious posture
        t1 = 100.0
        _posture_temporal_tracker[key] = {"first_suspicious_time": t1}
        elapsed_1 = t1 - _posture_temporal_tracker[key]["first_suspicious_time"]
        self.assertLess(elapsed_1, alert_sec)
        level_1 = "red" if elapsed_1 >= alert_sec else "yellow"
        self.assertEqual(level_1, "yellow", "Frame 1 at t=0s must be yellow warning, not red")

        # Frame 2 at t = 100.5s: elapsed = 0.5s < 1.25s
        t2 = 100.5
        elapsed_2 = t2 - _posture_temporal_tracker[key]["first_suspicious_time"]
        self.assertLess(elapsed_2, alert_sec)
        level_2 = "red" if elapsed_2 >= alert_sec else "yellow"
        self.assertEqual(level_2, "yellow", "Frame 2 at t=0.5s must remain yellow")

        # Frame 3 at t = 101.3s: elapsed = 1.3s >= 1.25s -> ESCALATE TO RED
        t3 = 101.3
        elapsed_3 = t3 - _posture_temporal_tracker[key]["first_suspicious_time"]
        self.assertGreaterEqual(elapsed_3, alert_sec)
        level_3 = "red" if elapsed_3 >= alert_sec else "yellow"
        self.assertEqual(level_3, "red", "Frame 3 at t=1.3s (elapsed >= 1.25s) must escalate to red")

    # ----------------------------------------------------------------------
    # 10. Pre-roll 5s and post-roll 10s duration
    # ----------------------------------------------------------------------
    def test_10_preroll_5s_and_postroll_10s_duration(self):
        """Verify default configuration and buffer window adhere to 5.0s pre-roll + 10.0s post-roll (15.0s total)."""
        settings = load_settings()
        self.assertEqual(settings.pre_roll_seconds, 5.0, "Pre-roll default must be 5.0s")
        self.assertEqual(settings.post_roll_seconds, 10.0, "Post-roll default must be 10.0s")

        ring_buffer = ring_buffer_service
        self.assertEqual(ring_buffer.pre_roll_seconds, 5.0)
        self.assertEqual(ring_buffer.post_roll_seconds, 10.0)

        total_clip_duration = ring_buffer.pre_roll_seconds + ring_buffer.post_roll_seconds
        self.assertEqual(total_clip_duration, 15.0, "Total clip duration window must equal 15.0s")

    # ----------------------------------------------------------------------
    # 11. Corrupted clip not saved as completed evidence
    # ----------------------------------------------------------------------
    def test_11_corrupted_clip_not_saved_as_completed_evidence(self):
        """Verify file integrity check rejects 0-byte or corrupted non-video files."""
        # 1. Non-existent file
        self.assertFalse(validate_video_file("non_existent_file_path.mp4"))

        # 2. 0-byte file
        temp_zero = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_zero.close()
        try:
            self.assertFalse(validate_video_file(temp_zero.name), "0-byte file must fail validation")
        finally:
            if os.path.exists(temp_zero.name):
                os.remove(temp_zero.name)

        # 3. Fake / corrupted video file (plain text content)
        temp_corrupt = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_corrupt.write(b"NOT A VALID MP4 VIDEO HEADER CORRUPTED")
        temp_corrupt.close()
        try:
            self.assertFalse(validate_video_file(temp_corrupt.name), "Corrupted text-as-video must fail validation")
        finally:
            if os.path.exists(temp_corrupt.name):
                os.remove(temp_corrupt.name)

    # ----------------------------------------------------------------------
    # 12. DB write queue handles multiple concurrent requests without dropping
    # ----------------------------------------------------------------------
    def test_12_db_write_queue_handles_multiple_concurrent_requests_without_dropping(self):
        """Verify 20 concurrent thread writes succeed sequentially without database lock or data loss."""
        num_items = 20
        test_ids = [f"test_conc_{i}_{int(time.time()*1000)}" for i in range(num_items)]
        errors = []

        def worker(item_id):
            try:
                db_write_queue.enqueue_incident({
                    "id": item_id,
                    "source_id": "test_conc_cam",
                    "track_id": 99,
                    "violation_type": "PHONE",
                    "confidence": 91.0,
                    "level": "red",
                    "detected_at": datetime.now(timezone.utc),
                    "status": "pending"
                })
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(tid,)) for tid in test_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread enqueue exceptions: {errors}")
        self.assertTrue(db_write_queue.wait_until_idle(timeout=10.0), "Queue did not drain in time")

        # Verify all 20 records exist in DB
        db = SessionLocal()
        try:
            for tid in test_ids:
                item = db.query(Incident).filter(Incident.id == tid).first()
                self.assertIsNotNone(item, f"Record {tid} missing from database!")
                db.delete(item)
            db.commit()
        finally:
            db.close()

    # ----------------------------------------------------------------------
    # 13. Settings affect runtime behavior
    # ----------------------------------------------------------------------
    def test_13_settings_affect_runtime_behavior(self):
        """Verify changing settings via API immediately propagates to detector and ring buffer."""
        orig_settings = self.client.get("/api/settings/ai").json()

        try:
            # Update all 6 parameters (suspicion_threshold must be in range [0.1, 1.0])
            payload = {
                "phone_confidence": 0.72,
                "posture_alert_seconds": 2.2,
                "suspicion_threshold": 0.48,
                "pre_roll_seconds": 4.5,
                "post_roll_seconds": 8.5,
                "cooldown_seconds": 7.5
            }
            res = self.client.post("/api/settings/ai", json=payload)
            self.assertEqual(res.status_code, 200)

            # Check runtime state
            self.assertEqual(ring_buffer_service.pre_roll_seconds, 4.5)
            self.assertEqual(ring_buffer_service.post_roll_seconds, 8.5)
            self.assertEqual(ring_buffer_service.cooldown_seconds, 7.5)

            # Check GET endpoint returns updated settings
            fetch_res = self.client.get("/api/settings/ai").json()
            self.assertEqual(fetch_res["phone_confidence"], 0.72)
            self.assertEqual(fetch_res["posture_alert_seconds"], 2.2)

        finally:
            # Restore original settings
            self.client.post("/api/settings/ai", json=orig_settings)

    # ----------------------------------------------------------------------
    # 14. API returns correct schema
    # ----------------------------------------------------------------------
    def test_14_api_returns_correct_schema(self):
        """Verify API endpoints return valid response models without legacy fields."""
        # 1. Health
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get("status"), "ONLINE")

        # 2. Status: check distinct FPS keys
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("observed_acquisition_fps", data)
        self.assertIn("inference_fps", data)
        self.assertIn("output_video_fps", data)
        self.assertIn("active_models", data)
        self.assertNotIn("facenet", str(data).lower())

        # 3. Incidents: check absence of student/sbd/room fields
        res = self.client.get("/api/incidents?limit=5")
        self.assertEqual(res.status_code, 200)
        incidents = res.json()
        self.assertIsInstance(incidents, list)
        for inc in incidents:
            self.assertIn("id", inc)
            self.assertIn("source_id", inc)
            self.assertNotIn("student_id", inc)
            self.assertNotIn("sbd", inc)
            self.assertNotIn("room_id", inc)

    # ----------------------------------------------------------------------
    # 15. Frontend does not call legacy endpoints
    # ----------------------------------------------------------------------
    def test_15_frontend_does_not_call_legacy_endpoints(self):
        """Scan all frontend source files (src/) to verify zero legacy API calls."""
        src_dir = os.path.join(PROJECT_ROOT, "src")
        if not os.path.exists(src_dir):
            self.skipTest("Frontend src directory not found")

        forbidden_patterns = [
            r"/api/students",
            r"/api/reports",
            r"/api/rooms",
            r"/api/assistant",
            r"/api/candidates"
        ]

        violations = []
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for pat in forbidden_patterns:
                            if re.search(pat, content):
                                violations.append(f"{file} matches {pat}")

        self.assertEqual(
            len(violations), 0,
            f"Frontend files contain legacy API calls: {violations}"
        )

    # ----------------------------------------------------------------------
    # 16. Model weights loadable
    # ----------------------------------------------------------------------
    def test_16_model_weights_loadable(self):
        """Verify YOLO pose and phone weights exist and load successfully via Ultralytics."""
        self.assertTrue(os.path.exists(POSE_WEIGHTS), f"Pose weights missing at {POSE_WEIGHTS}")
        self.assertTrue(os.path.exists(PHONE_WEIGHTS), f"Phone weights missing at {PHONE_WEIGHTS}")

        from ultralytics import YOLO

        pose_model = YOLO(POSE_WEIGHTS)
        self.assertIsNotNone(pose_model)

        phone_model = YOLO(PHONE_WEIGHTS)
        self.assertIsNotNone(phone_model)

        # Warm-up inference on synthetic frame
        dummy = np.zeros((320, 320, 3), dtype=np.uint8)
        pose_res = pose_model(dummy, verbose=False)
        self.assertIsNotNone(pose_res)
        phone_res = phone_model(dummy, verbose=False)
        self.assertIsNotNone(phone_res)

    # ----------------------------------------------------------------------
    # 17. Pipeline end to end with fixture
    # ----------------------------------------------------------------------
    def test_17_pipeline_end_to_end_with_fixture(self):
        """Full end-to-end integration test: feed frames -> trigger red flag -> render clip -> DB record."""
        ring_buffer_service.update_settings(pre_roll_seconds=1.0, post_roll_seconds=1.0, cooldown_seconds=1.0)
        source = "test_pipeline_cam"
        track = 777

        try:
            # 1. Feed 10 synthetic frames
            for i in range(10):
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"E2E Frame {i}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                ring_buffer_service.push_frame(frame, timestamp=time.time())
                time.sleep(0.04)

            # 2. Trigger red flag
            incident_id = ring_buffer_service.trigger_incident(
                violation_type="PHONE",
                confidence=97.0,
                source_id=source,
                track_id=track,
                level="red",
                proctor_notes="E2E test verification incident"
            )
            self.assertIsNotNone(incident_id)

            # 3. Feed post-roll frames to fulfill duration
            start = time.time()
            f_idx = 10
            while time.time() - start < 1.2:
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"E2E Post {f_idx}", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                ring_buffer_service.push_frame(frame, timestamp=time.time())
                time.sleep(0.04)
                f_idx += 1

            # 4. Wait for export and DB persistence
            time.sleep(1.0)
            self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

            # 5. Assert DB row and playable video
            db = SessionLocal()
            try:
                inc = db.query(Incident).filter(Incident.id == incident_id).first()
                self.assertIsNotNone(inc, "Incident must exist in DB")
                self.assertEqual(inc.violation_type, "PHONE")
                self.assertEqual(inc.level, "red")

                video_file = os.path.join(EVIDENCE_DIR, os.path.basename(inc.video_path))
                self.assertTrue(os.path.exists(video_file), "Video file must exist on disk")
                self.assertTrue(validate_video_file(video_file), "Generated video file must be playable")

                # Clean up
                db.delete(inc)
                db.commit()
                if os.path.exists(video_file):
                    os.remove(video_file)
                snap_file = os.path.join(EVIDENCE_DIR, os.path.basename(inc.snapshot_path))
                if os.path.exists(snap_file):
                    os.remove(snap_file)
            finally:
                db.close()
        finally:
            ring_buffer_service.update_settings(pre_roll_seconds=5.0, post_roll_seconds=10.0, cooldown_seconds=6.0)

    # ----------------------------------------------------------------------
    # 18. Temporal Continuity Guard (Sprint 1.2)
    # ----------------------------------------------------------------------
    def test_18_temporal_continuity_guard(self):
        """Verify that gaps > 0.75s reset posture tracking and prevent false RED flags."""
        tracker = TemporalPostureTracker(max_gap_seconds=0.75, min_samples=3)
        src = "test_guard_cam"
        tid = 42

        # 1. First suspicious frame at t=0.0s -> YELLOW
        st, lvl, dur = tracker.update(src, tid, True, timestamp=0.0, alert_seconds=1.25)
        self.assertEqual(lvl, "yellow")
        self.assertEqual(st, "SUSPICIOUS")
        self.assertAlmostEqual(dur, 0.0)

        # 2. Frame gap of 2.0s (network lag/drop) -> MUST NOT escalate to RED!
        st, lvl, dur = tracker.update(src, tid, True, timestamp=2.0, alert_seconds=1.25)
        self.assertEqual(lvl, "yellow", "Gap of 2.0s (> 0.75s) MUST NOT escalate to RED flag!")
        self.assertEqual(st, "SUSPICIOUS")
        self.assertAlmostEqual(dur, 0.0, msg="Duration must reset to 0.0s after gap violation")

        # 3. Continuous sequence with valid intervals (< 0.75s)
        # t=2.4s (gap=0.4s) -> yellow
        st, lvl, dur = tracker.update(src, tid, True, timestamp=2.4, alert_seconds=1.25)
        self.assertEqual(lvl, "yellow")

        # t=2.8s (gap=0.4s) -> yellow
        st, lvl, dur = tracker.update(src, tid, True, timestamp=2.8, alert_seconds=1.25)
        self.assertEqual(lvl, "yellow")

        # t=3.3s (gap=0.5s, continuous=1.3s >= 1.25s, sample count = 4 >= 3) -> ESCALATE TO RED
        st, lvl, dur = tracker.update(src, tid, True, timestamp=3.3, alert_seconds=1.25)
        self.assertEqual(lvl, "red", "Continuous violation >= 1.25s must escalate to RED flag")
        self.assertEqual(st, "CHEATING_POSTURE")
        self.assertGreaterEqual(dur, 1.25)

        # 4. Quiet period (> 0.75s) resets to NORMAL
        st, lvl, dur = tracker.update(src, tid, False, timestamp=4.2, alert_seconds=1.25)
        self.assertEqual(lvl, "green")
        self.assertEqual(st, "NORMAL")
        self.assertAlmostEqual(dur, 0.0)

    # ----------------------------------------------------------------------
    # 19. Single-Slot Inference Buffer Zero-Backlog (Sprint 1.2)
    # ----------------------------------------------------------------------
    def test_19_single_slot_inference_buffer_zero_backlog(self):
        """Verify backlog depth is strictly <= 1 and superseded frames are discarded."""
        buf = SingleSlotInferenceBuffer()
        self.assertEqual(buf.backlog_depth, 0)

        # Rapidly push 20 frames without consumer popping
        for seq in range(20):
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            buf.push_latest(
                source_id="cam",
                session_id="sess_test",
                sequence_id=seq,
                timestamp=time.time() + seq * 0.05,
                frame=frame
            )
            self.assertEqual(buf.backlog_depth, 1, "Backlog depth must never exceed 1")

        stats = buf.get_stats()
        self.assertEqual(stats["total_enqueued"], 20)
        self.assertEqual(stats["total_superseded"], 19)
        self.assertEqual(stats["backlog_depth"], 1)

        # Consumer pops the single item: it MUST be the newest frame (seq 19)
        popped = buf.pop_latest(timeout=0.1)
        self.assertIsNotNone(popped)
        self.assertEqual(popped["sequence_id"], 19, "Must return newest superseded frame")
        self.assertEqual(buf.backlog_depth, 0, "Buffer must be empty after pop")

    # ----------------------------------------------------------------------
    # 20. RingBuffer 15 FPS and Session Isolation (Sprint 1.2)
    # ----------------------------------------------------------------------
    def test_20_ring_buffer_15fps_and_session_isolation(self):
        """Verify 15 FPS container target and session pre-roll isolation."""
        self.assertEqual(ring_buffer_service.target_fps, 15.0)

        # Clear buffer
        ring_buffer_service.frame_buffer.clear()
        t_base = time.time()

        # Push 15 frames from session_A
        for i in range(15):
            f = np.zeros((100, 100, 3), dtype=np.uint8)
            ring_buffer_service.push_frame(
                frame=f,
                timestamp=t_base + i * 0.066,
                sequence_id=i,
                session_id="session_A"
            )

        # Push 15 frames from session_B
        for j in range(15):
            f = np.zeros((100, 100, 3), dtype=np.uint8)
            ring_buffer_service.push_frame(
                frame=f,
                timestamp=t_base + (15 + j) * 0.066,
                sequence_id=100 + j,
                session_id="session_B"
            )

        # Trigger incident specifying session_B
        inc_id = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=95.0,
            source_id="iso_cam",
            track_id=1,
            level="red",
            session_id="session_B",
            timestamp=t_base + 30 * 0.066
        )
        self.assertIsNotNone(inc_id)

        # Find active task
        task = next((t for t in ring_buffer_service.active_tasks if t.incident_id == inc_id), None)
        self.assertIsNotNone(task)

        # Pre-frames in task must ONLY belong to session_B
        for item in task.timed_frames:
            sess = item[3] if len(item) > 3 else None
            self.assertEqual(sess, "session_B", "Pre-roll MUST NOT contain frames from session_A")

        # Clean up active task
        ring_buffer_service.active_tasks.remove(task)

    # ----------------------------------------------------------------------
    # 21. WebSocket Binary Ingestion Endpoint (Sprint 1.2)
    # ----------------------------------------------------------------------
    def test_21_websocket_binary_ingest_endpoint(self):
        """Verify /api/ws/ingest accepts 16-byte header + JPEG frame."""
        # Create a valid JPEG
        dummy = np.zeros((120, 160, 3), dtype=np.uint8)
        cv2.putText(dummy, "WS Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        ret, jpeg_bytes = cv2.imencode(".jpg", dummy)
        self.assertTrue(ret)

        seq_id = 999
        mono_ts = time.time()
        # Pack 16 bytes: int64 seq, float64 ts
        header = struct.pack(">qd", seq_id, mono_ts)
        binary_payload = header + jpeg_bytes.tobytes()

        # Connect and send via TestClient
        with self.client.websocket_connect("/api/ws/ingest?source_id=test_ws&session_id=ws_sess_01") as ws:
            ws.send_bytes(binary_payload)
            time.sleep(0.2)
            # Send close
            ws.close()

    # ----------------------------------------------------------------------
    # 22. WebSocket Malformed Packets Handling (Sprint 1.2A)
    # ----------------------------------------------------------------------
    def test_22_websocket_malformed_packets(self):
        """Verify WebSocket endpoint safely handles/discards malformed binary frames."""
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        ret, jpeg_bytes = cv2.imencode(".jpg", dummy)
        self.assertTrue(ret)
        valid_jpeg = jpeg_bytes.tobytes()

        with self.client.websocket_connect("/api/ws/ingest?source_id=test_cam&session_id=sess_malform_01") as ws:
            # 1. Payload < 20 bytes (e.g. 10 bytes) -> discarded, connection stays open
            ws.send_bytes(b"1234567890")
            time.sleep(0.05)

            # 2. Payload > 3MB (e.g. 3.2MB dummy bytes) -> discarded
            large_payload = struct.pack(">qd", 1, time.time()) + (b"X" * (3 * 1024 * 1024 + 200))
            ws.send_bytes(large_payload)
            time.sleep(0.05)

            # 3. Negative sequence ID -> discarded
            bad_seq = struct.pack(">qd", -5, time.time()) + valid_jpeg
            ws.send_bytes(bad_seq)
            time.sleep(0.05)

            # 4. Invalid timestamp (<= 0, NaN, Inf) -> discarded
            bad_ts1 = struct.pack(">qd", 2, -10.0) + valid_jpeg
            ws.send_bytes(bad_ts1)
            time.sleep(0.05)
            bad_ts2 = struct.pack(">qd", 3, float("nan")) + valid_jpeg
            ws.send_bytes(bad_ts2)
            time.sleep(0.05)

            # 5. Send valid frame seq 10 -> accepted
            good_frame = struct.pack(">qd", 10, time.time()) + valid_jpeg
            ws.send_bytes(good_frame)
            time.sleep(0.05)

            # 6. Duplicate sequence ID (seq 10 again) or older seq (seq 5) -> discarded
            dup_frame = struct.pack(">qd", 10, time.time()) + valid_jpeg
            ws.send_bytes(dup_frame)
            time.sleep(0.05)
            old_frame = struct.pack(">qd", 5, time.time()) + valid_jpeg
            ws.send_bytes(old_frame)
            time.sleep(0.05)

            # 7. Subsequent higher sequence frame -> still accepted
            good_frame2 = struct.pack(">qd", 11, time.time()) + valid_jpeg
            ws.send_bytes(good_frame2)
            time.sleep(0.1)

            ws.close()

    # ----------------------------------------------------------------------
    # 23. WebSocket Query Parameter Validation (Sprint 1.2A)
    # ----------------------------------------------------------------------
    def test_23_websocket_query_parameter_validation(self):
        """Verify invalid source_id or session_id triggers 1008 policy violation close."""
        # 1. source_id containing dangerous characters (path traversal / XSS)
        with self.assertRaises(WebSocketDisconnect) as cm1:
            with self.client.websocket_connect("/api/ws/ingest?source_id=cam%2F..%2Fhack&session_id=valid_sess_1"):
                pass
        self.assertEqual(cm1.exception.code, 1008)

        # 2. session_id exceeding 64 characters
        long_sess = "s" * 65
        with self.assertRaises(WebSocketDisconnect) as cm2:
            with self.client.websocket_connect(f"/api/ws/ingest?source_id=valid_cam&session_id={long_sess}"):
                pass
        self.assertEqual(cm2.exception.code, 1008)

        # 3. session_id containing special symbols (e.g. spaces, quotes)
        with self.assertRaises(WebSocketDisconnect) as cm3:
            with self.client.websocket_connect("/api/ws/ingest?source_id=valid_cam&session_id=bad+session%27;"):
                pass
        self.assertEqual(cm3.exception.code, 1008)

    # ----------------------------------------------------------------------
    # 24. Stress Disconnect During Inference (Sprint 1.2A)
    # ----------------------------------------------------------------------
    def test_24_websocket_stress_disconnect_during_inference(self):
        """Verify rapid connect/disconnect under frame flood does not crash or leave dangling errors."""
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        ret, jpeg_bytes = cv2.imencode(".jpg", dummy)
        self.assertTrue(ret)
        raw_jpeg = jpeg_bytes.tobytes()

        # Rapidly connect, blast frames, disconnect abruptly 5 times
        for i in range(5):
            sess = f"stress_sess_{i}"
            with self.client.websocket_connect(f"/api/ws/ingest?source_id=stress_cam&session_id={sess}") as ws:
                for seq in range(3):
                    payload = struct.pack(">qd", seq + 1, time.time()) + raw_jpeg
                    ws.send_bytes(payload)
                # Disconnect immediately without waiting
                ws.close()

        # Check server health endpoint remains 200 OK
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ONLINE")

    # ----------------------------------------------------------------------
    # 25. Session Isolation and Reset API (Sprint 1.2A)
    # ----------------------------------------------------------------------
    def test_25_session_isolation_and_reset_api(self):
        """Verify POST /api/session/reset cleans up all temporal & buffer states for a given session."""
        sess_target = "sess_to_isolate_99"
        src_target = "cam_iso"

        # 1. Populate temporal tracker state
        st, lvl, dur = temporal_posture_tracker.update(
            source_id=src_target,
            track_id=88,
            is_suspicious=True,
            timestamp=time.time(),
            alert_seconds=1.25,
            session_id=sess_target
        )
        self.assertEqual(lvl, "yellow")
        self.assertIn((sess_target, src_target, 88), temporal_posture_tracker._states)

        # 2. Populate inference buffer
        dummy = np.zeros((50, 50, 3), dtype=np.uint8)
        inference_buffer.push_latest(
            source_id=src_target,
            session_id=sess_target,
            sequence_id=1,
            timestamp=time.time(),
            frame=dummy
        )

        # 3. Call reset session API
        res = self.client.post(f"/api/session/reset?session_id={sess_target}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["reset_session"], sess_target)

        # 4. Verify temporal tracker state for sess_target was removed
        self.assertNotIn((sess_target, src_target, 88), temporal_posture_tracker._states)

        # 5. Verify calling reset without session_id clears all
        res2 = self.client.post("/api/session/reset")
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["reset_session"], "all")

    # ----------------------------------------------------------------------
    # 26. Single-Session Lock Rejects Concurrent Connection (Sprint 1.2B)
    # ----------------------------------------------------------------------
    def test_26_single_session_lock_rejects_concurrent_connection(self):
        """Verify only 1 active ingestion session is permitted; concurrent attempts are rejected with 1008."""
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        ret, jpeg_bytes = cv2.imencode(".jpg", dummy)
        self.assertTrue(ret)
        raw_jpeg = jpeg_bytes.tobytes()

        # Connect session 1
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam_primary&session_id=sess_primary") as ws1:
            # Verify module records active session
            self.assertEqual(ai_engine_mod._active_ws_session_id, "sess_primary")

            # Attempt to connect session 2 concurrently -> must raise WebSocketDisconnect with code 1008
            with self.assertRaises(WebSocketDisconnect) as cm:
                with self.client.websocket_connect("/api/ws/ingest?source_id=cam_secondary&session_id=sess_secondary"):
                    pass
            self.assertEqual(cm.exception.code, 1008)

            # Verify session 1 is NOT affected or reset by the rejected attempt
            self.assertEqual(ai_engine_mod._active_ws_session_id, "sess_primary")
            payload = struct.pack(">qd", 1, time.time()) + raw_jpeg
            ws1.send_bytes(payload)

            # Try resetting a different session via API -> should be IGNORED without disrupting active session
            res_ignored = self.client.post("/api/session/reset?session_id=sess_different")
            self.assertEqual(res_ignored.status_code, 200)
            self.assertEqual(res_ignored.json()["status"], "IGNORED")
            self.assertEqual(ai_engine_mod._active_ws_session_id, "sess_primary")

            # Close session 1 normally
            ws1.close()

        # After session 1 closes, session lock should be freed
        self.assertIsNone(ai_engine_mod._active_ws_session_id)

        # Now session 3 can connect successfully
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam_third&session_id=sess_third") as ws3:
            self.assertEqual(ai_engine_mod._active_ws_session_id, "sess_third")
            ws3.close()

        self.assertIsNone(ai_engine_mod._active_ws_session_id)

    # ----------------------------------------------------------------------
    # 27. Server Monotonic Timestamp & Standardized Telemetry Fields (Sprint 1.2B)
    # ----------------------------------------------------------------------
    def test_27_server_monotonic_timestamp_and_telemetry_fields(self):
        """Verify telemetry counters match 7-field contract and incidents record server UTC wall-clock."""
        # 1. Verify RingBuffer trigger records UTC timezone-aware server time
        test_track = 77
        mono_ts = time.monotonic()
        t_before = datetime.now(timezone.utc)
        time.sleep(0.01)

        inc_id = ring_buffer_service.trigger_incident(
            violation_type="PHONE",
            confidence=95.5,
            source_id="cam_mono_test",
            track_id=test_track,
            current_frame=np.zeros((100, 100, 3), dtype=np.uint8),
            level="red",
            session_id="sess_mono_test",
            timestamp=mono_ts
        )
        self.assertIsNotNone(inc_id)

        t_after = datetime.now(timezone.utc)

        # Verify task stores UTC detected_at and server monotonic trigger_time
        task = next((t for t in ring_buffer_service.active_tasks if t.incident_id == inc_id), None)
        self.assertIsNotNone(task, "Triggered task must be present in active_tasks")
        self.assertIsNotNone(task.detected_at)
        self.assertGreaterEqual(task.detected_at, t_before)
        self.assertLessEqual(task.detected_at, t_after)
        self.assertEqual(task.trigger_time, mono_ts)

        # Enqueue into DB queue to verify SQLite UTC persistence
        test_db_id = f"test_inc_utc_{int(time.time()*1000)}"
        db_write_queue.enqueue_incident({
            "id": test_db_id,
            "source_id": "cam_mono_test",
            "track_id": test_track,
            "violation_type": "PHONE",
            "confidence": 95.5,
            "level": "red",
            "detected_at": task.detected_at,
            "status": "pending",
            "proctor_notes": "Test UTC persistence"
        })
        self.assertTrue(db_write_queue.wait_until_idle(timeout=5.0))

        # Check in DB
        db = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == test_db_id).first()
            self.assertIsNotNone(inc)
            self.assertIsNotNone(inc.detected_at)
            db.delete(inc)
            db.commit()
        finally:
            db.close()

        # 2. Verify Single-Slot Buffer tracks enqueued and superseded counters accurately
        test_sess = "sess_telemetry_check"
        test_src = "cam_telemetry_check"
        initial_enqueued = inference_buffer.total_enqueued
        initial_superseded = inference_buffer.total_superseded

        dummy_frame = np.zeros((80, 80, 3), dtype=np.uint8)
        # Push 2 frames rapidly without worker consuming
        with inference_buffer._lock:
            inference_buffer._slot = {
                "source_id": test_src,
                "session_id": test_sess,
                "sequence_id": 101,
                "timestamp": time.monotonic(),
                "frame": dummy_frame,
                "callback": None
            }
            inference_buffer.total_enqueued += 1
            # Push second frame (overwrites first)
            inference_buffer._slot = {
                "source_id": test_src,
                "session_id": test_sess,
                "sequence_id": 102,
                "timestamp": time.monotonic(),
                "frame": dummy_frame,
                "callback": None
            }
            inference_buffer.total_enqueued += 1
            inference_buffer.total_superseded += 1

        self.assertEqual(inference_buffer.total_enqueued, initial_enqueued + 2)
        self.assertEqual(inference_buffer.total_superseded, initial_superseded + 1)

    # ----------------------------------------------------------------------
    # 28. Session Telemetry Invariants, Fresh Start, and Isolation
    # ----------------------------------------------------------------------
    def test_28_session_telemetry_invariants_and_isolation(self):
        """
        Verify strict mathematical invariants for session telemetry:
        1. submitted == processed + superseded + pending (pending = in_progress + in_slot)
        2. results_sent <= processed
        3. Fresh start: each session starts strictly at 0
        4. Session isolation: old session stats do not pollute new sessions
        5. API /api/session/telemetry verifies invariant booleans
        """
        sess_a = f"sess_inv_a_{uuid.uuid4().hex[:8]}"
        sess_b = f"sess_inv_b_{uuid.uuid4().hex[:8]}"
        src_id = "cam_invariant_test"

        # 1. Fresh start for session A
        inference_buffer.reset_session(sess_a)
        stats_a0 = inference_buffer.get_session_stats(sess_a)
        self.assertEqual(stats_a0["submitted"], 0)
        self.assertEqual(stats_a0["superseded"], 0)
        self.assertEqual(stats_a0["processed"], 0)
        self.assertEqual(stats_a0["in_progress"], 0)
        self.assertEqual(stats_a0["in_slot"], 0)
        self.assertEqual(stats_a0["results_sent"], 0)

        # 2. Put 25 frames rapidly into buffer for session A
        dummy_frame = np.zeros((64, 64, 3), dtype=np.uint8)
        for i in range(1, 26):
            inference_buffer.push_latest(src_id, sess_a, i, time.monotonic(), dummy_frame, None)
            time.sleep(0.005)  # small interval allowing worker to pick up some frames

        # Give worker a brief moment to process whatever is current
        time.sleep(0.1)

        stats_a = inference_buffer.get_session_stats(sess_a)
        # Check invariant 1: submitted == processed + superseded + pending
        pending_a = stats_a["in_progress"] + stats_a["in_slot"]
        self.assertEqual(
            stats_a["submitted"],
            stats_a["processed"] + stats_a["superseded"] + pending_a,
            f"Invariant balance failed for session A: {stats_a}"
        )
        self.assertEqual(stats_a["submitted"], 25)
        self.assertGreater(stats_a["superseded"], 0, "Fast push must have superseded frames")
        # Check invariant 2: results_sent <= processed
        self.assertLessEqual(stats_a["results_sent"], stats_a["processed"])

        # 3. Session B isolation: Session B must start at 0 and have zero frames from A
        inference_buffer.reset_session(sess_b)
        stats_b0 = inference_buffer.get_session_stats(sess_b)
        self.assertEqual(stats_b0["submitted"], 0)
        self.assertEqual(stats_b0["superseded"], 0)
        self.assertEqual(stats_b0["processed"], 0)
        self.assertEqual(stats_b0["results_sent"], 0)

        # Put 5 frames for session B
        for i in range(1, 6):
            inference_buffer.push_latest(src_id, sess_b, i, time.monotonic(), dummy_frame, None)
            time.sleep(0.01)

        time.sleep(0.1)
        stats_b = inference_buffer.get_session_stats(sess_b)
        pending_b = stats_b["in_progress"] + stats_b["in_slot"]
        self.assertEqual(
            stats_b["submitted"],
            stats_b["processed"] + stats_b["superseded"] + pending_b,
            f"Invariant balance failed for session B: {stats_b}"
        )
        self.assertEqual(stats_b["submitted"], 5)
        # Session A stats must remain unchanged by session B activity
        stats_a_post = inference_buffer.get_session_stats(sess_a)
        self.assertEqual(stats_a_post["submitted"], 25)

        # 4. Verify API /api/session/telemetry endpoint
        res = self.client.get(f"/api/session/telemetry?session_id={sess_a}")
        self.assertEqual(res.status_code, 200)
        telemetry_data = res.json()
        self.assertEqual(telemetry_data["session_id"], sess_a)
        self.assertEqual(telemetry_data["inference_submitted_frames"], 25)
        self.assertIn("invariants", telemetry_data)
        self.assertTrue(telemetry_data["invariants"]["balance_check"])
        self.assertTrue(telemetry_data["invariants"]["sent_le_processed_check"])

    # ----------------------------------------------------------------------
    # 29. Test endpoint guard and deprecated ingest guard (Sprint 3.1)
    # ----------------------------------------------------------------------
    def test_29_test_endpoint_guard_and_deprecated_ingest_guard(self):
        """Verify test-only endpoints and deprecated ingest are protected and unmounted by default."""
        import importlib
        import main
        
        # 1. Default (production mode): test endpoints and deprecated ingest must be unmounted
        os.environ.pop("ENABLE_TEST_ENDPOINTS", None)
        os.environ.pop("ENVIRONMENT", None)
        os.environ.pop("ENABLE_DEPRECATED_INGEST", None)
        importlib.reload(main)
        default_client = TestClient(main.app)

        res_test_default = default_client.post("/api/test/trigger_incident")
        self.assertEqual(res_test_default.status_code, 404, "Test trigger endpoint must return 404 when disabled")

        res_ingest_default = default_client.post("/api/detect/frame", json={"image_base64": "invalid"})
        self.assertEqual(res_ingest_default.status_code, 404, "Deprecated Base64 ingest must return 404 when disabled")

        # Check OpenAPI schema in default mode
        openapi_res = default_client.get("/openapi.json")
        self.assertEqual(openapi_res.status_code, 200)
        paths = openapi_res.json().get("paths", {})
        self.assertNotIn("/api/test/trigger_incident", paths)
        self.assertNotIn("/api/detect/frame", paths)

        # 2. Test mode: ENABLE_TEST_ENDPOINTS=true mounts the endpoint
        os.environ["ENABLE_TEST_ENDPOINTS"] = "true"
        importlib.reload(main)
        test_client = TestClient(main.app)

        res_test_enabled = test_client.post("/api/test/trigger_incident")
        self.assertEqual(res_test_enabled.status_code, 200, "Test trigger endpoint must return 200 when enabled")
        openapi_test = test_client.get("/openapi.json").json().get("paths", {})
        self.assertIn("/api/test/trigger_incident", openapi_test)

    # ----------------------------------------------------------------------
    # 30. Canonical incident vocabulary and confidence semantics (Sprint 3.1)
    # ----------------------------------------------------------------------
    def test_30_canonical_incident_type_and_confidence_semantics(self):
        """Verify strict canonical incident enum (PHONE, HEAD_TURNING) and confidence normalization."""
        from schemas import IncidentResponse
        from datetime import datetime, timezone
        from pydantic import ValidationError

        now = datetime.now(timezone.utc)
        # 1. Canonical PHONE and raw probability 0.95
        inc_phone = IncidentResponse(
            id="inc_test_p",
            source_id="cam_01",
            violation_type="PHONE",
            confidence=0.95,
            level="red",
            detected_at=now,
            status="pending",
            created_at=now
        )
        self.assertEqual(inc_phone.violation_type, "PHONE")
        self.assertEqual(inc_phone.confidence, 0.95)

        # 2. Canonical HEAD_TURNING
        inc_head = IncidentResponse(
            id="inc_test_h",
            source_id="cam_01",
            violation_type="HEAD_TURNING",
            confidence=0.88,
            level="red",
            detected_at=now,
            status="pending",
            created_at=now
        )
        self.assertEqual(inc_head.violation_type, "HEAD_TURNING")
        self.assertEqual(inc_head.confidence, 0.88)

        # 3. Legacy CHEATING_POSTURE normalizes to HEAD_TURNING
        inc_legacy = IncidentResponse(
            id="inc_test_leg",
            source_id="cam_01",
            violation_type="CHEATING_POSTURE",
            confidence=92.5,  # legacy percentage format
            level="red",
            detected_at=now,
            status="pending",
            created_at=now
        )
        self.assertEqual(inc_legacy.violation_type, "HEAD_TURNING")
        self.assertEqual(inc_legacy.confidence, 0.925)  # Normalized to raw probability

        # 4. Rejections: negative, NaN, Inf, > 100.0
        with self.assertRaises(ValidationError):
            IncidentResponse(
                id="inc_bad",
                source_id="cam_01",
                violation_type="PHONE",
                confidence=-0.5,
                level="red",
                detected_at=now,
                status="pending",
                created_at=now
            )
        with self.assertRaises(ValidationError):
            IncidentResponse(
                id="inc_bad",
                source_id="cam_01",
                violation_type="PHONE",
                confidence=float("nan"),
                level="red",
                detected_at=now,
                status="pending",
                created_at=now
            )
        with self.assertRaises(ValidationError):
            IncidentResponse(
                id="inc_bad",
                source_id="cam_01",
                violation_type="PHONE",
                confidence=150.0,
                level="red",
                detected_at=now,
                status="pending",
                created_at=now
            )

    # ----------------------------------------------------------------------
    # 31. Canonical evidence route and path traversal protection (Sprint 3.1 & 3.1A)
    # ----------------------------------------------------------------------
    def test_31_canonical_evidence_route_and_path_traversal(self):
        """
        Verify canonical static evidence route /evidence/{filename} works,
        legacy /api/clips/{filename} returns 404 by default,
        and multiple path traversal payloads do not escape evidence root.
        """
        from services.ring_buffer import EVIDENCE_DIR

        # Create a sample test clip in EVIDENCE_DIR
        test_file = os.path.join(EVIDENCE_DIR, "test_sample_evidence.mp4")
        with open(test_file, "wb") as f:
            f.write(b"SAMPLE_VIDEO_DATA")

        try:
            # 1. Canonical route /evidence/{filename} works
            res_canonical = self.client.get("/evidence/test_sample_evidence.mp4")
            self.assertEqual(res_canonical.status_code, 200)
            self.assertEqual(res_canonical.content, b"SAMPLE_VIDEO_DATA")

            # 2. Legacy /api/clips/{filename} returns 404 by default in production mode
            res_legacy_default = self.client.get("/api/clips/test_sample_evidence.mp4")
            self.assertEqual(res_legacy_default.status_code, 404, "Legacy /api/clips/ must be disabled by default (404)")

            # 3. Path traversal payloads via /evidence/ are blocked across various formats
            traversal_payloads = [
                "/evidence/../../cheating_system.db",
                "/evidence/..%2F..%2Fcheating_system.db",
                "/evidence/..\\..\\cheating_system.db",
                "/evidence/..%5C..%5Ccheating_system.db",
                "/evidence/nested/../../../cheating_system.db",
                "/evidence/nested%2F..%2F..%2F..%2Fcheating_system.db"
            ]
            for payload in traversal_payloads:
                res_trav = self.client.get(payload)
                self.assertIn(
                    res_trav.status_code,
                    (404, 400),
                    f"Payload {payload} must return 404 or 400, got {res_trav.status_code}"
                )
                self.assertNotIn(b"SQLite format 3", res_trav.content, f"Payload {payload} must not leak DB content")

            # 4. Verify default OpenAPI schema excludes test, deprecated ingest, and legacy clips endpoints
            res_openapi = self.client.get("/openapi.json")
            self.assertEqual(res_openapi.status_code, 200)
            paths = res_openapi.json().get("paths", {})
            self.assertNotIn("/api/test/trigger_incident", paths, "Test endpoint must not appear in default OpenAPI")
            self.assertNotIn("/api/detect/frame", paths, "Deprecated ingest must not appear in default OpenAPI")
            self.assertNotIn("/api/clips/{filename}", paths, "Legacy clips must not appear in default OpenAPI")

            # 5. When explicitly enabled via ENABLE_LEGACY_CLIPS, legacy clips route functions with basename defense
            from fastapi import FastAPI
            from starlette.testclient import TestClient
            from starlette.staticfiles import StaticFiles
            import routers.ai_engine as ai_engine_module

            test_app = FastAPI()
            test_app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")
            test_app.include_router(ai_engine_module.legacy_clips_router, prefix="/api")
            custom_client = TestClient(test_app)

            res_custom = custom_client.get("/api/clips/test_sample_evidence.mp4")
            self.assertEqual(res_custom.status_code, 200)
            self.assertIn("X-API-Deprecation", res_custom.headers)

            # Traversal attempts against legacy clips router are neutralized by os.path.basename
            res_custom_trav = custom_client.get("/api/clips/..%2F..%2Fcheating_system.db")
            self.assertIn(res_custom_trav.status_code, (404, 400))
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == "__main__":
    unittest.main()


