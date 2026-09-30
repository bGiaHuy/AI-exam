"""AUD-02..06: isolated SQLite, temporary media and synthetic 64px frames only.

Run this module in a fresh Python process; it never imports backend.main or loads
the user's model. Environment overrides are installed before database imports.
"""

import json
import os
import struct
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

TEST_ROOT = tempfile.TemporaryDirectory(prefix="aiexam-audit-")
os.environ["AIEXAM_ISOLATED_DB"] = str(Path(TEST_ROOT.name) / "audit.db")
os.environ["DATABASE_URL"] = "sqlite:///" + os.environ["AIEXAM_ISOLATED_DB"]
os.environ["ENVIRONMENT"] = "test"
os.environ["DEMO_READ_ONLY"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from database import Base, SessionLocal, engine, get_db
from models import Incident
from routers import ai_engine, incidents, settings
from schemas import AISettingsSchema
from services import evidence_files, ring_buffer
from services.camera_manager import CameraManager
from services.db_queue import db_write_queue
from services.inference_worker import SingleSlotInferenceBuffer
from services.ring_buffer import VideoRingBuffer, validate_video_file

if Path(engine.url.database).resolve() != Path(os.environ["AIEXAM_ISOLATED_DB"]).resolve():
    raise RuntimeError("Audit tests require a fresh process with an isolated SQLite database")
Base.metadata.create_all(engine)


def tearDownModule():
    db_write_queue.wait_until_idle(10)
    db_write_queue.shutdown()
    engine.dispose()
    TEST_ROOT.cleanup()


class AuditRegressionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(db_write_queue.wait_until_idle(10))
        with SessionLocal() as db:
            db.query(Incident).delete()
            db.commit()
        self.temp = tempfile.TemporaryDirectory(dir=TEST_ROOT.name)
        self.root = Path(self.temp.name)
        self.evidence = self.root / "evidence"
        self.evidence.mkdir()
        self.manager = CameraManager()
        self.manager._mode = "DUAL_CAMERA"
        self.rb = VideoRingBuffer()
        self.detector = Mock()
        self.patches = [
            patch.object(ring_buffer, "EVIDENCE_DIR", str(self.evidence)),
            patch.object(incidents, "EVIDENCE_DIR", str(self.evidence)),
            patch.object(ai_engine, "camera_manager", self.manager),
            patch.object(ai_engine, "ring_buffer_service", self.rb),
            patch.object(ai_engine, "inference_buffer", SingleSlotInferenceBuffer()),
            patch.object(ai_engine, "detector", self.detector),
            patch("services.inference_worker.inference_worker.start"),
            patch("services.camera_manager.fair_inference_scheduler.start"),
            patch("services.camera_manager.fair_inference_scheduler.set_sources"),
            patch.object(settings, "SETTINGS_DIR", str(self.root)),
            patch.object(settings, "SETTINGS_FILE", str(self.root / "ai_settings.json")),
        ]
        for item in self.patches:
            item.start()
        ai_engine._active_ws_session_id = None
        ai_engine._active_ws_sessions.clear()
        self.app = FastAPI()
        self.app.include_router(ai_engine.router, prefix="/api")
        self.app.include_router(incidents.router, prefix="/api")
        self.app.include_router(settings.router, prefix="/api")
        self.client = TestClient(self.app)
        self.frame = np.full((64, 64, 3), 120, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", self.frame)
        self.assertTrue(ok)
        self.jpeg = encoded.tobytes()

    def tearDown(self):
        self.assertTrue(db_write_queue.wait_until_idle(10))
        self.client.close()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def wait_for(self, predicate):
        deadline = time.monotonic() + 5
        while not predicate() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(predicate(), "Timed out waiting for the server")

    def send(self, ws, sequence):
        ws.send_bytes(struct.pack(">qd", sequence, time.monotonic()) + self.jpeg)

    def seed_incident(self, incident_id="audit_inc"):
        with SessionLocal() as db:
            db.add(Incident(id=incident_id, source_id="cam1", violation_type="PHONE", confidence=0.95,
                            video_path=f"/evidence/{incident_id}.mp4",
                            snapshot_path=f"/evidence/{incident_id}_snap.jpg"))
            db.commit()
        (self.evidence / f"{incident_id}.mp4").write_bytes(b"synthetic video fixture")
        (self.evidence / f"{incident_id}_snap.jpg").write_bytes(self.jpeg)

    def row_count(self):
        with SessionLocal() as db:
            return db.query(Incident).count()

    def test_disconnect_exports_partial_clip_in_single_dual_and_triple_modes(self):
        for mode in ("SINGLE_CAMERA", "DUAL_CAMERA", "TRIPLE_CAMERA"):
            with self.subTest(mode=mode):
                self.manager._mode = mode
                session = "session_" + mode
                with self.client.websocket_connect(f"/api/ws/ingest?source_id=cam1&session_id={session}") as ws:
                    self.send(ws, 1)
                    source = self.manager.get_source("cam1")
                    buffer = self.rb if mode == "SINGLE_CAMERA" else source.ring_buffer
                    self.wait_for(lambda: len(buffer.frame_buffer) == 1)
                    incident_id = buffer.trigger_incident("PHONE", 0.95, source_id="cam1", session_id=session,
                                                         timestamp=time.monotonic(), current_frame=self.frame)
                    task = buffer.tasks_by_id[incident_id]
                    self.assertFalse(task.completion_event.is_set())
                self.assertTrue(task.completion_event.wait(10))
                self.assertTrue(validate_video_file(task.output_video_path))
                self.assertEqual(task.state, "COMPLETED")
                self.assertTrue(db_write_queue.wait_until_idle(10))
                with SessionLocal() as db:
                    row = db.get(Incident, incident_id)
                    self.assertIsNotNone(row)
                    self.assertIn("post-roll", row.proctor_notes)
                    self.assertEqual(row.session_id, session)
                    self.assertLess((row.clip_ended_at - row.clip_started_at).total_seconds(), 10)
        self.detector.reset.assert_not_called()

    def test_late_inference_after_disconnect_exports_peak_instead_of_hanging(self):
        self.rb.reset_session("ended")
        incident_id = self.rb.trigger_incident("HEAD_TURNING", 0.91, source_id="cam1", session_id="ended",
                                              timestamp=100, current_frame=self.frame)
        task = self.rb.tasks_by_id[incident_id]
        self.assertTrue(task.completion_event.wait(10))
        self.assertTrue(validate_video_file(task.output_video_path))
        self.assertEqual(self.rb.active_tasks, [])

    def test_connect_reset_disconnect_do_not_touch_other_camera(self):
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=first") as first:
            self.send(first, 1)
            source = self.manager.get_source("cam1")
            self.wait_for(lambda: source.frames_received == 1)
            before = (source.session_id, source.frames_received, source.ring_buffer.total_bytes,
                      source.inference_slot.get_stats(), source.get_latest_preview())
            incident_id = source.ring_buffer.trigger_incident("PHONE", 0.95, source_id="cam1", session_id="first",
                                                             timestamp=time.monotonic())
            task = source.ring_buffer.tasks_by_id[incident_id]
            with self.client.websocket_connect("/api/ws/ingest?source_id=cam2&session_id=second") as second:
                self.send(second, 1)
                other = self.manager.get_source("cam2")
                self.wait_for(lambda: other.frames_received == 1)
                response = self.client.post("/api/session/reset?session_id=second")
                self.assertEqual(response.json()["status"], "SUCCESS")
                self.assertEqual(ai_engine._active_ws_sessions["cam2"], "second")
                self.send(second, 2)
                self.wait_for(lambda: other.frames_received == 1)
            after = (source.session_id, source.frames_received, source.ring_buffer.total_bytes,
                     source.inference_slot.get_stats(), source.get_latest_preview())
            self.assertEqual(before, after)
            self.assertEqual(task.state, "RECORDING_POST")
            self.assertIn(task, source.ring_buffer.active_tasks)
            self.assertFalse(source.record_inference_result("old_session", [], "red", 1.0))
            self.assertEqual(source.inference_slot.get_stats(), before[3])
        self.assertTrue(task.completion_event.wait(10))
        self.assertTrue(validate_video_file(task.output_video_path))
        self.detector.reset.assert_not_called()

    def test_duplicate_session_id_on_other_source_is_rejected(self):
        with self.client.websocket_connect("/api/ws/ingest?source_id=cam1&session_id=shared"):
            with self.assertRaises(WebSocketDisconnect) as caught:
                with self.client.websocket_connect("/api/ws/ingest?source_id=cam2&session_id=shared"):
                    pass
            self.assertEqual(caught.exception.code, 1008)

    def test_reset_finishes_old_session_before_switching_id(self):
        self.manager.begin_session("cam1", "old")
        source = self.manager.get_source("cam1")
        source.push_frame(self.frame, timestamp=100)
        incident_id = source.ring_buffer.trigger_incident("PHONE", 0.95, source_id="cam1", session_id="old", timestamp=100)
        source.reset_session("new")
        task = source.ring_buffer.tasks_by_id[incident_id]
        self.assertTrue(task.completion_event.wait(10))
        self.assertTrue(validate_video_file(task.output_video_path))
        self.assertEqual(source.session_id, "new")
        self.assertEqual(len(source.ring_buffer.frame_buffer), 0)

    def test_settings_apply_to_existing_new_and_restarted_sources_and_clip_duration(self):
        from services import camera_manager as manager_module
        cfg = AISettingsSchema(pre_roll_seconds=1, post_roll_seconds=2, cooldown_seconds=3)
        with patch.object(manager_module, "camera_manager", self.manager):
            self.manager.begin_session("cam1", "configured")
            response = self.client.post("/api/settings/ai", json=cfg.model_dump())
            self.assertEqual(response.status_code, 200)
            self.manager.begin_session("cam2", "later")
            for name in ("cam1", "cam2"):
                buffer = self.manager.get_source(name).ring_buffer
                self.assertEqual((buffer.pre_roll_seconds, buffer.post_roll_seconds, buffer.cooldown_seconds), (1, 2, 3))
            source = self.manager.get_source("cam1")
            source.push_frame(self.frame, timestamp=100)
            source.push_frame(self.frame, timestamp=101)
            incident_id = source.ring_buffer.trigger_incident("PHONE", 0.95, source_id="cam1", session_id="configured", timestamp=101)
            self.assertIsNone(source.ring_buffer.trigger_incident("PHONE", 0.95, source_id="cam1", session_id="configured", timestamp=102))
            source.push_frame(self.frame, timestamp=102)
            source.push_frame(self.frame, timestamp=103)
            task = source.ring_buffer.tasks_by_id[incident_id]
            self.assertTrue(task.completion_event.wait(10))
            self.assertAlmostEqual(task.metrics["duration_real"], 3.0)
            self.assertEqual(task.metrics["total_output_frames"], 45)
        restarted = CameraManager()
        with patch.dict(os.environ, {"CAMERA_MODE": "triple", "CAMERA_1_TYPE": "browser_ws",
                                     "CAMERA_2_TYPE": "browser_ws", "CAMERA_3_TYPE": "browser_ws"}):
            restarted.initialize()
        for source in restarted._sources.values():
            self.assertEqual((source.ring_buffer.pre_roll_seconds, source.ring_buffer.post_roll_seconds,
                              source.ring_buffer.cooldown_seconds), (1, 2, 3))

    def test_purge_and_single_delete_restore_files_when_commit_fails(self):
        self.seed_incident()
        original = {p.name: p.read_bytes() for p in self.evidence.iterdir()}
        for route in ("/api/incidents/videos/purge-all", "/api/incidents/audit_inc"):
            with self.subTest(route=route):
                def failing_db():
                    with SessionLocal() as db:
                        with patch.object(db, "commit", side_effect=RuntimeError("simulated commit failure")):
                            yield db
                self.app.dependency_overrides[get_db] = failing_db
                response = self.client.delete(route)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(self.row_count(), 1)
                self.assertEqual({p.name: p.read_bytes() for p in self.evidence.iterdir()}, original)
        self.app.dependency_overrides.clear()

    def test_purge_restores_already_staged_files_if_later_file_is_locked(self):
        self.seed_incident()
        rename = Path.rename

        def locked(path, target):
            if path.parent.resolve() == self.evidence.resolve() and path.name.endswith("_snap.jpg"):
                raise PermissionError("simulated locked snapshot")
            return rename(path, target)

        with patch.object(Path, "rename", locked):
            response = self.client.delete("/api/incidents/videos/purge-all")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.row_count(), 1)
        self.assertEqual(len(list(self.evidence.iterdir())), 2)

    def test_cleanup_failure_is_reported_and_retry_clears_private_staging(self):
        self.seed_incident()
        unlink = Path.unlink

        def locked(path, *args, **kwargs):
            if path.suffix == ".mp4" and ".evidence-trash" in path.parts:
                raise PermissionError("simulated cleanup lock")
            return unlink(path, *args, **kwargs)

        with patch.object(Path, "unlink", locked):
            response = self.client.delete("/api/incidents/videos/purge-all")
        result = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(result["success"])
        self.assertEqual(result["failed_files"], ["audit_inc.mp4"])
        self.assertEqual(self.row_count(), 0)
        self.assertEqual(list(self.evidence.iterdir()), [])
        self.assertTrue(list((self.root / ".evidence-trash").rglob("*.mp4")))
        retry = self.client.delete("/api/incidents/videos/purge-all")
        self.assertTrue(retry.json()["success"])
        self.assertEqual(list((self.root / ".evidence-trash").iterdir()), [])

    def test_successful_purge_removes_rows_and_orphan_media_only(self):
        self.seed_incident()
        (self.evidence / "orphan.mp4").write_bytes(b"orphan fixture")
        (self.evidence / "keep.txt").write_text("keep", encoding="utf-8")
        response = self.client.delete("/api/incidents/videos/purge-all")
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["deleted_records_count"], 1)
        self.assertEqual(response.json()["deleted_files_count"], 3)
        self.assertEqual(self.row_count(), 0)
        self.assertEqual([p.name for p in self.evidence.iterdir()], ["keep.txt"])

    def test_single_delete_does_not_remove_other_incident_evidence(self):
        self.seed_incident("first")
        self.seed_incident("second")
        response = self.client.delete("/api/incidents/first")
        self.assertTrue(response.json()["success"])
        self.assertEqual(self.row_count(), 1)
        self.assertEqual(sorted(p.name for p in self.evidence.iterdir()), ["second.mp4", "second_snap.jpg"])

    def test_interrupted_staging_is_restored_before_a_later_delete_attempt(self):
        self.seed_incident()
        operation = self.root / ".evidence-trash" / "interrupted"
        operation.mkdir(parents=True)
        (operation / "manifest.json").write_text(json.dumps({"incident_ids": ["audit_inc"]}), encoding="utf-8")
        (self.evidence / "audit_inc.mp4").rename(operation / "audit_inc.mp4")
        # A different/missing ID causes no new deletion, but recovery must restore the live record's media.
        response = self.client.delete("/api/incidents/absent")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.row_count(), 1)
        self.assertEqual((self.evidence / "audit_inc.mp4").read_bytes(), b"synthetic video fixture")
        self.assertFalse(operation.exists())

    def test_busy_db_queue_cannot_delete_unpublished_evidence(self):
        self.seed_incident()
        with patch.object(evidence_files.db_write_queue, "wait_until_idle", return_value=False):
            response = self.client.delete("/api/incidents/videos/purge-all")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.row_count(), 1)
        self.assertEqual(len(list(self.evidence.iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
