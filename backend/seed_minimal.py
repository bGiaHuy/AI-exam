"""
================================================================================
MINIMAL DATABASE INITIALIZATION & SAMPLE INCIDENT SEED SCRIPT
================================================================================
Initializes `cheating_system.db` with WAL mode and populates sample anonymous
incidents for testing UI feeds.
Zero examinee identity.
================================================================================
"""

import os
import sys
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import engine, Base, SessionLocal, DB_PATH
from models import Incident


def seed_minimal():
    print(f"[INIT] Initializing database at: {DB_PATH}")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        session.query(Incident).delete()
        session.commit()

        inc1 = Incident(
            id="inc_sample_phone",
            source_id="webcam_local",
            track_id=2,
            violation_type="PHONE",
            confidence=94.5,
            level="red",
            detected_at=datetime.now(timezone.utc),
            clip_started_at=datetime.now(timezone.utc),
            clip_ended_at=datetime.now(timezone.utc),
            video_path="/evidence/inc_sample_phone.mp4",
            snapshot_path="/evidence/inc_sample_phone_snap.jpg",
            status="pending",
            proctor_notes="Phát hiện điện thoại thông minh gần tay thí sinh [Track 2]."
        )

        inc2 = Incident(
            id="inc_sample_posture",
            source_id="webcam_local",
            track_id=5,
            violation_type="HEAD_TURNING",
            confidence=88.0,
            level="red",
            detected_at=datetime.now(timezone.utc),
            clip_started_at=datetime.now(timezone.utc),
            clip_ended_at=datetime.now(timezone.utc),
            video_path="/evidence/inc_sample_posture.mp4",
            snapshot_path="/evidence/inc_sample_posture_snap.jpg",
            status="confirmed",
            proctor_notes="Thí sinh quay đầu lệch hướng bài làm liên tục quá 1.25s [Track 5]."
        )

        session.add_all([inc1, inc2])
        session.commit()
        print("[OK] Sample anonymous incidents seeded successfully.")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Failed to seed database: {e}")
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    if "--dev-only" not in sys.argv:
        print("[BLOCKED] seed_minimal.py is restricted to development environments and will clear the incidents table.")
        print("To confirm manual execution in development, run with flag: python backend/seed_minimal.py --dev-only")
        sys.exit(1)
    seed_minimal()
