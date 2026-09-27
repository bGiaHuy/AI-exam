"""
================================================================================
UNIT TESTS: TRIPLE CAMERA MONITORING & SCHEDULER (AI EXAM CONTROL)
================================================================================
Verifies:
1. Mode transitions: SINGLE_CAMERA <-> DUAL_CAMERA <-> TRIPLE_CAMERA.
2. Fair round-robin scheduler balances across 3 active sources.
3. Telemetry and active sources report accurate status for 3 cameras.
================================================================================
"""

import os
import sys
import unittest
import numpy as np

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TEST_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.camera_manager import camera_manager
from services.camera_source import SyntheticCameraSource, CameraStatus
from services.fair_scheduler import fair_inference_scheduler, FairInferenceScheduler


class TestTripleCameraPipeline(unittest.TestCase):

    def setUp(self):
        camera_manager.initialize()
        camera_manager.set_mode("SINGLE_CAMERA")

    def tearDown(self):
        camera_manager.set_mode("SINGLE_CAMERA")

    def test_triple_camera_mode_transition(self):
        # 1. Switch to TRIPLE_CAMERA
        camera_manager.set_mode("TRIPLE_CAMERA")
        self.assertEqual(camera_manager.mode, "TRIPLE_CAMERA")
        sources = camera_manager.get_all_active_sources()
        source_ids = [s.source_id for s in sources]
        self.assertIn("cam1", source_ids)
        self.assertIn("cam2", source_ids)
        self.assertIn("cam3", source_ids)

        # 2. Switch down to DUAL_CAMERA
        camera_manager.set_mode("DUAL_CAMERA")
        self.assertEqual(camera_manager.mode, "DUAL_CAMERA")
        sources_dual = camera_manager.get_all_active_sources()
        dual_ids = [s.source_id for s in sources_dual]
        self.assertIn("cam1", dual_ids)
        self.assertIn("cam2", dual_ids)
        self.assertNotIn("cam3", dual_ids)

        # 3. Switch down to SINGLE_CAMERA
        camera_manager.set_mode("SINGLE_CAMERA")
        self.assertEqual(camera_manager.mode, "SINGLE_CAMERA")
        sources_single = camera_manager.get_all_active_sources()
        single_ids = [s.source_id for s in sources_single]
        self.assertIn("cam1", single_ids)
        self.assertNotIn("cam2", single_ids)
        self.assertNotIn("cam3", single_ids)

    def test_triple_camera_fair_round_robin(self):
        s1 = SyntheticCameraSource("test_tri_1", "Cam 1")
        s2 = SyntheticCameraSource("test_tri_2", "Cam 2")
        s3 = SyntheticCameraSource("test_tri_3", "Cam 3")

        s1.status = CameraStatus.ONLINE
        s1._running = True
        s2.status = CameraStatus.ONLINE
        s2._running = True
        s3.status = CameraStatus.ONLINE
        s3._running = True

        scheduler = FairInferenceScheduler()
        scheduler.set_sources([s1, s2, s3])

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.assertTrue(s1.push_frame(frame))
        self.assertTrue(s2.push_frame(frame))
        self.assertTrue(s3.push_frame(frame))

        # Round 1: should pick s1, s2, s3 in fair round-robin order
        picked1 = scheduler._pick_next_frame()
        self.assertIsNotNone(picked1)
        self.assertEqual(picked1[0].source_id, "test_tri_1")

        picked2 = scheduler._pick_next_frame()
        self.assertIsNotNone(picked2)
        self.assertEqual(picked2[0].source_id, "test_tri_2")

        picked3 = scheduler._pick_next_frame()
        self.assertIsNotNone(picked3)
        self.assertEqual(picked3[0].source_id, "test_tri_3")


if __name__ == "__main__":
    unittest.main()
