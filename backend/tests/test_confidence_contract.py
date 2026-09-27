"""
Unit and Integration Tests for Canonical Confidence Contract (Sprint 3.2B-R2)
Validates:
1. normalize_confidence canonical contract:
   - [0.0, 1.0] -> untouched
   - (1.0, 100.0] -> / 100.0
   - invalid (<0, >100, NaN, Inf, bool, None, string, etc.) -> InvalidConfidenceError (NO clamping)
2. DBWriteQueue worker behavior:
   - Invalid confidence triggers rollback, 0 DB insertions, incremented failed_writes_count,
     and structured entry in dead_letter_queue.
   - Valid confidence persisted canonically in [0.0, 1.0].
3. Transactional database migration on temporary SQLite DB:
   - Untouched canonical values, normalized legacy percentages, and quarantined invalid rows.
"""

import os
import sys
import math
import uuid
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from confidence import normalize_confidence, InvalidConfidenceError
from migrate_db import audit_and_migrate_confidence, NEW_SCHEMA_SQL


class TestConfidenceContract(unittest.TestCase):
    """Test suite for normalize_confidence contract."""

    def test_canonical_probabilities_untouched(self):
        """Values in [0.0, 1.0] must remain untouched."""
        test_cases = [
            (0.0, 0.0),
            (0, 0.0),
            (0.0001, 0.0001),
            (0.5, 0.5),
            (0.92, 0.92),
            (0.965, 0.965),
            (0.9999, 0.9999),
            (1.0, 1.0),
            (1, 1.0),
            ("0.0", 0.0),
            ("0.965", 0.965),
            ("1.0", 1.0),
        ]
        for inp, expected in test_cases:
            with self.subTest(inp=inp):
                res = normalize_confidence(inp)
                self.assertIsInstance(res, float)
                self.assertAlmostEqual(res, expected, places=6)

    def test_legacy_percentages_divided_by_100(self):
        """Values in (1.0, 100.0] must be divided by 100.0."""
        test_cases = [
            (1.0001, 0.010001),
            (2.0, 0.02),
            (2, 0.02),
            (50.0, 0.5),
            (88.0, 0.88),
            (92.0, 0.92),
            (94.5, 0.945),
            (95.0, 0.95),
            (96.5, 0.965),
            (100.0, 1.0),
            (100, 1.0),
            ("96.5", 0.965),
            ("100", 1.0),
        ]
        for inp, expected in test_cases:
            with self.subTest(inp=inp):
                res = normalize_confidence(inp)
                self.assertIsInstance(res, float)
                self.assertAlmostEqual(res, expected, places=6)

    def test_rejections_no_clamping(self):
        """Invalid values must raise InvalidConfidenceError without clamping."""
        invalid_inputs = [
            -0.0001,
            -0.5,
            -1.0,
            -100.0,
            100.0001,
            101.0,
            999.0,
            float("nan"),
            float("inf"),
            float("-inf"),
            None,
            True,   # bool must be rejected even though isinstance(True, int) is True
            False,  # bool must be rejected
            "not_a_number",
            "96.5%",
            "",
            [],
            {},
        ]
        for inp in invalid_inputs:
            with self.subTest(inp=inp):
                with self.assertRaises(InvalidConfidenceError):
                    normalize_confidence(inp)


class TestDBWriteQueueConfidenceIntegration(unittest.TestCase):
    """Test DBWriteQueue behavior with valid and invalid confidence scores."""

    def setUp(self):
        # Use a temporary SQLite database for DBWriteQueue tests
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Initialize schema
        conn = sqlite3.connect(self.db_path)
        conn.executescript(NEW_SCHEMA_SQL)
        conn.commit()
        conn.close()

        # Patch SessionLocal to target this test db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(f"sqlite:///{self.db_path}")
        self.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_db_queue_rejects_invalid_confidence_and_records_dead_letter(self):
        """Worker must rollback, not insert incident, and log to dead_letter_queue."""
        from services.db_queue import DBWriteQueue
        import unittest.mock as mock

        queue = DBWriteQueue()
        # Mock SessionLocal inside worker loop to point to our test DB
        with mock.patch("database.SessionLocal", self.TestSessionLocal):
            queue.start()

            # 1. Enqueue an invalid task (negative confidence)
            invalid_id = f"test_invalid_{uuid.uuid4().hex[:6]}"
            queue.enqueue_incident({
                "id": invalid_id,
                "violation_type": "PHONE",
                "confidence": -0.5,
                "level": "red",
                "source_id": "cam1",
            })

            # Wait for queue to process
            queue.wait_until_idle(timeout=3.0)

            # Assert database has ZERO records
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM incidents WHERE id = ?", (invalid_id,))
            count = c.fetchone()[0]
            conn.close()

            self.assertEqual(count, 0, "Invalid incident must NOT be persisted to database")

            # Assert metrics and dead letter queue
            metrics = queue.get_metrics()
            self.assertGreaterEqual(metrics["failed_writes"], 1)
            self.assertGreaterEqual(metrics["dead_letter_count"], 1)

            dead_letters = queue.get_dead_letter_queue()
            matching = [dl for dl in dead_letters if dl["task_id"] == invalid_id]
            self.assertEqual(len(matching), 1)
            self.assertIn("Confidence cannot be negative", matching[0]["error"])

            # 2. Enqueue another invalid task (> 100.0)
            invalid_id_2 = f"test_invalid_{uuid.uuid4().hex[:6]}"
            queue.enqueue_incident({
                "id": invalid_id_2,
                "violation_type": "HEAD_TURNING",
                "confidence": 150.0,
                "level": "yellow",
                "source_id": "cam2",
            })
            queue.wait_until_idle(timeout=3.0)

            metrics = queue.get_metrics()
            self.assertGreaterEqual(metrics["failed_writes"], 2)

            # 3. Enqueue a valid task with legacy percentage (96.5) -> should normalize to 0.965
            valid_id = f"test_valid_{uuid.uuid4().hex[:6]}"
            queue.enqueue_incident({
                "id": valid_id,
                "violation_type": "PHONE",
                "confidence": 96.5,
                "level": "red",
                "source_id": "cam1",
            })
            queue.wait_until_idle(timeout=3.0)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT id, confidence FROM incidents WHERE id = ?", (valid_id,))
            row = c.fetchone()
            conn.close()

            self.assertIsNotNone(row)
            self.assertAlmostEqual(row[1], 0.965, places=4)

            queue.shutdown()


class TestDatabaseConfidenceMigration(unittest.TestCase):
    """Test audit_and_migrate_confidence transactional migration and quarantining on temp SQLite DB."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Populate temporary database with test records
        conn = sqlite3.connect(self.db_path)
        conn.executescript(NEW_SCHEMA_SQL)

        # Insert test incidents:
        # 1. Canonical [0, 1]: 0.92 (should stay 0.92)
        # 2. Legacy (1, 100]: 96.5 (should become 0.965)
        # 3. Legacy (1, 100]: 92.0 (should become 0.92)
        # 4. Legacy (1, 100]: 100.0 (should become 1.0)
        # 5. Invalid: -0.5 (must be quarantined, purged from incidents)
        # 6. Invalid: 150.0 (must be quarantined, purged from incidents)
        test_rows = [
            ("inc_canon_1", "cam1", "Camera 1", "browser_ws", "sess1", 1, "PHONE", 0.92, "red", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
            ("inc_legacy_1", "cam1", "Camera 1", "browser_ws", "sess1", 1, "PHONE", 96.5, "red", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
            ("inc_legacy_2", "cam2", "Camera 2", "browser_ws", "sess1", 2, "HEAD_TURNING", 92.0, "yellow", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
            ("inc_legacy_3", "cam1", "Camera 1", "browser_ws", "sess1", 3, "PHONE", 100.0, "red", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
            ("inc_invalid_neg", "cam1", "Camera 1", "browser_ws", "sess1", 4, "PHONE", -0.5, "red", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
            ("inc_invalid_high", "cam2", "Camera 2", "browser_ws", "sess1", 5, "PHONE", 150.0, "red", "2026-09-15T00:00:00Z", "2026-09-15T00:00:00Z"),
        ]
        conn.executemany("""
            INSERT INTO incidents (
                id, source_id, source_label, source_type, session_id, track_id,
                violation_type, confidence, level, detected_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, test_rows)
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_audit_and_migrate_confidence_invariants(self):
        """Verify transactional migration preserves canonicals, normalizes legacy, and quarantines invalid."""
        success, stats = audit_and_migrate_confidence(self.db_path, backup_first=False)
        self.assertTrue(success, f"Migration failed: {stats}")

        self.assertEqual(stats["total_audited"], 6)
        self.assertEqual(stats["untouched_canonical"], 1)
        self.assertEqual(stats["normalized_legacy"], 3)
        self.assertEqual(stats["quarantined_invalid"], 2)

        # Inspect resulting SQLite database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check incidents table
        c.execute("SELECT id, confidence FROM incidents ORDER BY id;")
        incidents = dict(c.fetchall())

        self.assertEqual(len(incidents), 4, "Only 4 valid incidents must remain in main table")
        self.assertAlmostEqual(incidents["inc_canon_1"], 0.92, places=4)
        self.assertAlmostEqual(incidents["inc_legacy_1"], 0.965, places=4)
        self.assertAlmostEqual(incidents["inc_legacy_2"], 0.92, places=4)
        self.assertAlmostEqual(incidents["inc_legacy_3"], 1.0, places=4)

        # Check quarantine table
        c.execute("SELECT id, raw_confidence, quarantine_reason FROM incidents_quarantine ORDER BY id;")
        quarantined = {r[0]: (r[1], r[2]) for r in c.fetchall()}

        self.assertEqual(len(quarantined), 2, "2 invalid records must be in quarantine table")
        self.assertIn("inc_invalid_neg", quarantined)
        self.assertIn("Confidence cannot be negative", quarantined["inc_invalid_neg"][1])

        self.assertIn("inc_invalid_high", quarantined)
        self.assertIn("cannot exceed 100.0", quarantined["inc_invalid_high"][1])

        conn.close()


if __name__ == "__main__":
    unittest.main()
