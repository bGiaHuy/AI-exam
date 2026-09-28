"""Regression: red alerts must export clips on the acquisition clock."""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.camera_source import BrowserWebSocketSource
from services.fair_scheduler import FairInferenceScheduler
from services.ring_buffer import validate_video_file
from services.temporal_tracker import TemporalPostureTracker


class SchedulerEvidenceClockTest(unittest.TestCase):
    def test_red_head_turn_exports_on_both_acquisition_clocks(self):
        for start in (100.0, 1_800_000_000.0):
            with self.subTest(start=start), tempfile.TemporaryDirectory() as evidence_dir:
                source = BrowserWebSocketSource("clock_test")
                source.start()
                source.ring_buffer.update_settings(
                    pre_roll_seconds=1.0, post_roll_seconds=1.0, cooldown_seconds=6.0
                )
                scheduler = FairInferenceScheduler()
                scheduler.set_sources([source])
                frame = np.full((64, 64, 3), 100, dtype=np.uint8)
                detector = Mock()
                detector.monitor = SimpleNamespace(alert_seconds=1.25)
                detector.process_frame.return_value = (frame, [{
                    "box": [5, 5, 45, 55], "track_id": 7,
                    "status_code": "SUSPICIOUS", "score": 0.9, "turn_deg": 45,
                }])
                scheduler.set_detector(detector)
                results = []

                def receive(result):
                    results.append(result)
                    scheduler._stop_event.set()

                with patch("services.fair_scheduler.temporal_posture_tracker", TemporalPostureTracker()), \
                     patch("services.ring_buffer.EVIDENCE_DIR", evidence_dir), \
                     patch("services.ring_buffer.db_write_queue") as db_queue:
                    try:
                        for index in range(4):
                            source.push_frame(frame, timestamp=start + index * 0.5,
                                              sequence_id=index, callback=receive)
                            scheduler._stop_event.clear()
                            scheduler._scheduler_loop()
                        self.assertTrue(all(r["incident_id"] is None for r in results[:3]))
                        self.assertEqual(results[-1]["level"], "red")
                        incident_id = results[-1]["incident_id"]
                        self.assertIsNotNone(incident_id)
                        task = source.ring_buffer.tasks_by_id[incident_id]
                        self.assertEqual(task.trigger_time, start + 1.5)
                        self.assertEqual(task.post_end_time, start + 2.5)
                        self.assertGreater(len(task.timed_frames), 0)
                        for index in range(4, 6):
                            source.push_frame(frame, timestamp=start + index * 0.5,
                                              sequence_id=index)
                        self.assertTrue(task.completion_event.wait(10), "Clip never finished post-roll")
                        self.assertTrue(validate_video_file(task.output_video_path))
                        db_queue.enqueue_incident.assert_called_once()
                        payload = db_queue.enqueue_incident.call_args.args[0]
                        self.assertEqual(payload["violation_type"], "HEAD_TURNING")
                        self.assertEqual(payload["level"], "red")
                        self.assertEqual(payload["source_id"], source.source_id)
                    finally:
                        source.stop()


if __name__ == "__main__":
    unittest.main()
