"""
================================================================================
SQLAlchemy 2.0 DATA MODELS - AI EXAM CONTROL
================================================================================
Defines single core entity:
  - Incident: Real-time vision violation flag (PHONE, HEAD_TURNING), level,
              temporary track_id, source_id, UTC timestamps, and evidence media paths.
Purely anonymous physical device and posture detection with attached evidence clips.
================================================================================
"""

import sys
import os
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text
)

# Support relative or absolute module imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from database import Base


class Incident(Base):
    """
    Represents an automated vision detection incident with attached evidence clip.
    Strictly anonymous: tracks physical devices and heuristic postures only.
    """
    __tablename__ = "incidents"
    __table_args__ = {'extend_existing': True}

    # Primary identifier: inc_{timestamp}_{uuid}
    id = Column(String(100), primary_key=True, index=True)

    # Physical video/camera source identifier (e.g. 'webcam_local', 'cam_01', 'demo_video')
    source_id = Column(String(100), nullable=False, default="webcam_local", index=True)

    # Temporary tracker ID assigned by ByteTrack across sequential frames (nullable)
    track_id = Column(Integer, nullable=True, index=True)

    # Violation contract: only 'PHONE' or 'HEAD_TURNING'
    violation_type = Column(String(50), nullable=False)

    # Confidence score (float 0.0 - 100.0)
    # - For PHONE: YOLO model detection confidence
    # - For HEAD_TURNING: Heuristic posture anomaly score
    confidence = Column(Float, nullable=False, default=90.0)

    # Severity level: 'yellow' (suspicious warning) or 'red' (confirmed flag)
    level = Column(String(20), nullable=False, default="red")

    # Timezone-aware UTC timestamps
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    clip_started_at = Column(DateTime(timezone=True), nullable=True)
    clip_ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relative static media paths served at /evidence
    video_path = Column(String(500), nullable=True)
    snapshot_path = Column(String(500), nullable=True)

    # Review status by operator: 'pending', 'confirmed', 'dismissed'
    status = Column(String(20), nullable=False, default="pending")

    # Operator review notes / automated system telemetry notes
    proctor_notes = Column(Text, nullable=True)

    # System record creation timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
