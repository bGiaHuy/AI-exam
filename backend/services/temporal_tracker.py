"""
================================================================================
TEMPORAL POSTURE TRACKER WITH CONTINUITY & GAP GUARD
================================================================================
Sprint 1.2 Strict Enforcement:
- A head-turning violation MUST NOT escalate to RED flag merely because two
  suspicious frames are separated by >= 1.25s.
- There must be continuous observation:
    1. Interval between consecutive suspicious frames <= max_gap_seconds (default 0.75s).
    2. Minimum number of suspicious detections in the sequence (default min_samples = 3).
    3. If frame stream has a gap > max_gap_seconds, the suspicious sequence RESETS.
- Monotonic or real timestamp support.
================================================================================
"""

import logging
import threading
from typing import Dict, Tuple, Any, Optional

logger = logging.getLogger("temporal_tracker")


class TemporalPostureTracker:
    """
    Tracks suspicious head-turning per (source_id, track_id) with continuity verification.
    """

    def __init__(self, max_gap_seconds: float = 0.75, min_samples: int = 3):
        self.max_gap_seconds = max_gap_seconds
        self.min_samples = min_samples
        # Key: (session_id, source_id, track_id) -> state dict
        self._states: Dict[Tuple[str, str, int], Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def update(
        self,
        source_id: str,
        track_id: int,
        is_suspicious: bool,
        timestamp: float,
        alert_seconds: float = 1.25,
        session_id: Optional[str] = None
    ) -> Tuple[str, str, float]:
        """
        Process an observation for (session_id, source_id, track_id).

        Returns:
            (status_code, level, elapsed_continuous_seconds)
            status_code: 'NORMAL' | 'SUSPICIOUS' | 'CHEATING_POSTURE'
            level: 'green' | 'yellow' | 'red'
        """
        sess = session_id or "default"
        key = (sess, source_id, track_id)

        with self._lock:
            if not is_suspicious:
                # Normal posture -> immediately clear suspicious sequence
                if key in self._states:
                    logger.debug(f"[TEMPORAL] Track {track_id} in session {sess} resumed normal posture, resetting tracker.")
                    del self._states[key]
                return "NORMAL", "green", 0.0

            now = float(timestamp)
            state = self._states.get(key)

            if state is None:
                # First suspicious observation in sequence
                self._states[key] = {
                    "first_time": now,
                    "last_time": now,
                    "count": 1
                }
                return "SUSPICIOUS", "yellow", 0.0

            # Check gap between consecutive suspicious detections
            gap = now - state["last_time"]
            if gap > self.max_gap_seconds:
                # Continuity broken: gap is too large! Reset sequence starting from this frame
                logger.info(
                    f"[TEMPORAL] Gap {gap:.2f}s > {self.max_gap_seconds}s for Track {track_id} (sess={sess}). "
                    f"Resetting suspicious sequence."
                )
                self._states[key] = {
                    "first_time": now,
                    "last_time": now,
                    "count": 1
                }
                return "SUSPICIOUS", "yellow", 0.0

            # Continuous sequence: update last_time and increment count
            state["last_time"] = now
            state["count"] += 1
            continuous_elapsed = now - state["first_time"]

            # Escalation to RED only if BOTH elapsed >= alert_seconds AND count >= min_samples
            if continuous_elapsed >= alert_seconds and state["count"] >= self.min_samples:
                return "CHEATING_POSTURE", "red", continuous_elapsed
            else:
                return "SUSPICIOUS", "yellow", continuous_elapsed

    def get_state(self, source_id: str, track_id: int, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        sess = session_id or "default"
        with self._lock:
            state = self._states.get((sess, source_id, track_id))
            return dict(state) if state else None

    def reset_session(self, session_id: str):
        """Clear all states for a specific session."""
        with self._lock:
            to_del = [k for k in self._states if k[0] == session_id]
            for k in to_del:
                del self._states[k]
            if to_del:
                logger.info(f"[TEMPORAL] Reset {len(to_del)} track state(s) for session={session_id}")

    def clear(self):
        with self._lock:
            self._states.clear()


# Global singleton
temporal_posture_tracker = TemporalPostureTracker(max_gap_seconds=0.75, min_samples=3)
