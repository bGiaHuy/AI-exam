"""
================================================================================
SINGLE-SLOT ZERO-BACKLOG ASYNC INFERENCE WORKER
================================================================================
Sprint 1.2 Pipeline Decoupling:
- Recording pipeline pushes raw frames into RingBuffer at 15 FPS.
- Inference pipeline consumes frames asynchronously from a Single-Slot Buffer.
- Backlog depth is STRICTLY 0 or 1 at all times.
- Slow AI forward pass NEVER blocks or delays the recording pipeline.
- Superseded frames are replaced immediately, never queued.
- Monotonic timestamp and sequence ID are tracked end-to-end.
================================================================================
"""

import os
import sys
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Tuple, Callable
import numpy as np

logger = logging.getLogger("inference_worker")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Backend path resolution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.temporal_tracker import temporal_posture_tracker
from services.ring_buffer import ring_buffer_service


class SingleSlotInferenceBuffer:
    """
    Thread-safe buffer holding exactly 0 or 1 item for AI inference.
    If a new frame arrives before the previous frame is inferred,
    the old frame is replaced and discarded (superseded).
    Backlog depth is guaranteed to be <= 1.

    Enforces strict mathematical invariants per session:
      submitted = processed + superseded + pending
    where pending = in_progress (0 or 1) + in_slot (0 or 1).
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._slot: Optional[Dict[str, Any]] = None
        self._new_frame_event = threading.Event()
        # session_id -> dict of counters
        self._sessions: Dict[str, Dict[str, int]] = {}

    def _ensure_session_locked(self, session_id: str) -> Dict[str, int]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "submitted": 0,
                "superseded": 0,
                "in_progress": 0,
                "processed": 0,
                "results_sent": 0,
                "detected_objects": 0
            }
        return self._sessions[session_id]

    def reset_session(self, session_id: Optional[str] = None):
        """Discards queued frame for session and resets its counters to zero."""
        with self._lock:
            if session_id is None or session_id == "all":
                self._slot = None
                self._new_frame_event.clear()
                self._sessions.clear()
            else:
                slot_sess = self._slot.get("session_id") if isinstance(self._slot, dict) else (self._slot[1] if (isinstance(self._slot, (tuple, list)) and len(self._slot) > 1) else None)
                if self._slot is not None and slot_sess == session_id:
                    self._slot = None
                    self._new_frame_event.clear()
                self._sessions[session_id] = {
                    "submitted": 0,
                    "superseded": 0,
                    "in_progress": 0,
                    "processed": 0,
                    "results_sent": 0,
                    "detected_objects": 0
                }

    def push_latest(
        self,
        source_id: str,
        session_id: str,
        sequence_id: int,
        timestamp: float,
        frame: np.ndarray,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """Push latest frame. If slot already has an unprocessed frame, supersede it."""
        with self._lock:
            if self._slot is not None:
                old_sess = self._slot["session_id"]
                self._ensure_session_locked(old_sess)["superseded"] += 1

            self._slot = {
                "source_id": source_id,
                "session_id": session_id,
                "sequence_id": sequence_id,
                "timestamp": timestamp,
                "frame": frame,
                "callback": callback,
                "enqueued_at": time.time()
            }
            self._ensure_session_locked(session_id)["submitted"] += 1
            self._new_frame_event.set()

    def pop_latest(self, timeout: float = 0.05) -> Optional[Dict[str, Any]]:
        """Pop the latest frame for inference, clearing the slot."""
        if not self._new_frame_event.wait(timeout=timeout):
            return None

        with self._lock:
            item = self._slot
            self._slot = None
            self._new_frame_event.clear()
            if item is not None:
                sess = item["session_id"]
                self._ensure_session_locked(sess)["in_progress"] += 1
            return item

    def record_processed(self, session_id: str, detected_objects_count: int = 0):
        """Record completion of inference on a frame."""
        with self._lock:
            stats = self._ensure_session_locked(session_id)
            if stats["in_progress"] > 0:
                stats["in_progress"] -= 1
            stats["processed"] += 1
            stats["detected_objects"] += detected_objects_count

    def record_result_sent(self, session_id: str):
        """Record dispatch of an inference result message to client."""
        with self._lock:
            stats = self._ensure_session_locked(session_id)
            stats["results_sent"] += 1

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Return exact, isolated counters and pending state for session_id."""
        with self._lock:
            stats = self._ensure_session_locked(session_id)
            slot_sess = self._slot.get("session_id") if isinstance(self._slot, dict) else (self._slot[1] if (isinstance(self._slot, (tuple, list)) and len(self._slot) > 1) else None)
            in_slot = 1 if (self._slot is not None and slot_sess == session_id) else 0
            pending = stats["in_progress"] + in_slot
            return {
                "session_id": session_id,
                "submitted": stats["submitted"],
                "superseded": stats["superseded"],
                "in_progress": stats["in_progress"],
                "in_slot": in_slot,
                "pending": pending,
                "processed": stats["processed"],
                "results_sent": stats["results_sent"],
                "detected_objects": stats["detected_objects"]
            }

    def has_session(self, session_id: str) -> bool:
        """Check if session_id is tracked in _sessions."""
        with self._lock:
            return session_id in self._sessions

    def clear_session(self, session_id: str):
        """Discards waiting item if it belongs to session_id."""
        self.reset_session(session_id)

    def clear(self):
        """Discards any waiting item in the slot."""
        self.reset_session(None)

    @property
    def backlog_depth(self) -> int:
        """Returns 1 if a frame is waiting in the slot, 0 otherwise."""
        with self._lock:
            return 1 if self._slot is not None else 0

    @property
    def total_enqueued(self) -> int:
        with self._lock:
            return sum(s["submitted"] for s in self._sessions.values())

    @total_enqueued.setter
    def total_enqueued(self, val: int):
        with self._lock:
            s = self._ensure_session_locked("default")
            s["submitted"] = val

    @property
    def total_superseded(self) -> int:
        with self._lock:
            return sum(s["superseded"] for s in self._sessions.values())

    @total_superseded.setter
    def total_superseded(self, val: int):
        with self._lock:
            s = self._ensure_session_locked("default")
            s["superseded"] = val

    @property
    def total_inferred(self) -> int:
        with self._lock:
            return sum(s["processed"] for s in self._sessions.values())

    @total_inferred.setter
    def total_inferred(self, val: int):
        with self._lock:
            s = self._ensure_session_locked("default")
            s["processed"] = val

    def get_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if session_id and session_id in self._sessions:
                s = self._sessions[session_id]
                slot_sess = self._slot.get("session_id") if isinstance(self._slot, dict) else (self._slot[1] if (isinstance(self._slot, (tuple, list)) and len(self._slot) > 1) else None)
                in_slot = 1 if (self._slot is not None and slot_sess == session_id) else 0
                return {
                    "total_enqueued": s["submitted"],
                    "total_superseded": s["superseded"],
                    "total_inferred": s["processed"],
                    "backlog_depth": in_slot
                }
            return {
                "total_enqueued": sum(s["submitted"] for s in self._sessions.values()),
                "total_superseded": sum(s["superseded"] for s in self._sessions.values()),
                "total_inferred": sum(s["processed"] for s in self._sessions.values()),
                "backlog_depth": 1 if self._slot is not None else 0
            }



class InferenceWorker:
    """
    Dedicated background worker thread running AI models on the latest frame.
    Decoupled from frame acquisition.
    """

    def __init__(self, buffer: SingleSlotInferenceBuffer):
        self.buffer = buffer
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.last_inference_fps = 0.0
        self.last_inference_latency_ms = 0.0
        self._detector = None

    def _get_detector(self):
        if self._detector is None:
            try:
                from routers.ai_engine import get_detector
                self._detector = get_detector()
            except Exception as e:
                logger.warning(f"[INFERENCE_WORKER] Cannot load detector: {e}")
        return self._detector

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="AIInferenceWorkerThread",
            daemon=True
        )
        self._thread.start()
        logger.info("[INFERENCE_WORKER] Started decoupled zero-backlog AI inference worker thread.")

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("[INFERENCE_WORKER] Stopped AI inference worker thread.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            item = self.buffer.pop_latest(timeout=0.05)
            if item is None:
                continue

            source_id = item["source_id"]
            session_id = item["session_id"]
            sequence_id = item["sequence_id"]
            frame_ts = item["timestamp"]
            frame = item["frame"]
            callback = item.get("callback")

            t_start = time.time()
            detector = self._get_detector()

            detections: List[Dict[str, Any]] = []
            has_phone = False
            has_red = False
            has_yellow = False
            red_violation_type = "PHONE"
            red_confidence = 90.0
            red_track_id = 0

            if detector is not None and frame is not None and frame.size > 0:
                try:
                    # Run detector
                    annotated_frame, alerts = detector.process_frame(frame, fps=15.0, draw=True)
                    h, w = frame.shape[:2]

                    for alert in (alerts or []):
                        box = alert.get("box")
                        tid = alert.get("track_id", 0)
                        status_code = alert.get("status_code", "NORMAL")
                        score = float(alert.get("score", 0.0))
                        turn_deg = float(alert.get("turn_deg", 0.0))

                        if not box or len(box) < 4:
                            continue

                        x1, y1, x2, y2 = box
                        left_pct = max(0.0, min(100.0, (x1 / w) * 100.0))
                        top_pct = max(0.0, min(100.0, (y1 / h) * 100.0))
                        w_pct = max(1.0, min(100.0 - left_pct, ((x2 - x1) / w) * 100.0))
                        h_pct = max(1.0, min(100.0 - top_pct, ((y2 - y1) / h) * 100.0))

                        # 1. Phone detection
                        if status_code == "CHEATING_PHONE":
                            has_phone = True
                            has_red = True
                            red_violation_type = "PHONE"
                            red_confidence = max(red_confidence, score * 100.0 if score <= 1.0 else score)
                            red_track_id = tid
                            detections.append({
                                "id": f"det_phone_{tid}_{sequence_id}",
                                "label": "PHONE_DETECTED",
                                "label_vi": f"Điện thoại (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else score, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "red",
                                "track_id": tid
                            })
                            continue

                        # 2. Posture detection with Temporal Gap Guard
                        is_suspicious_posture = (status_code in ("CHEATING_POSTURE", "SUSPICIOUS"))
                        alert_sec = getattr(getattr(detector, "monitor", None), "alert_seconds", 1.25)

                        posture_status, posture_level, elapsed_continuous = temporal_posture_tracker.update(
                            source_id=source_id,
                            track_id=tid,
                            is_suspicious=is_suspicious_posture,
                            timestamp=frame_ts,
                            alert_seconds=alert_sec,
                            session_id=session_id
                        )

                        if posture_level == "red":
                            has_red = True
                            red_violation_type = "HEAD_TURNING"
                            red_confidence = max(red_confidence, score * 100.0 if score <= 1.0 else 88.0)
                            red_track_id = tid
                            detections.append({
                                "id": f"det_head_{tid}_{sequence_id}",
                                "label": "CHEATING_POSTURE",
                                "label_vi": f"Quay đầu {int(turn_deg)}° ({elapsed_continuous:.1f}s) (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else 88.0, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "red",
                                "track_id": tid
                            })
                        elif posture_level == "yellow":
                            has_yellow = True
                            detections.append({
                                "id": f"det_susp_{tid}_{sequence_id}",
                                "label": "SUSPICIOUS_POSTURE",
                                "label_vi": f"Nghi vấn quay đầu {int(turn_deg)}° (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else 70.0, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "yellow",
                                "track_id": tid
                            })
                        else:
                            detections.append({
                                "id": f"det_norm_{tid}_{sequence_id}",
                                "label": "NORMAL",
                                "label_vi": f"Bình thường (Track {tid})",
                                "confidence": round((1.0 - score) * 100.0 if score <= 1.0 else 90.0, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "green",
                                "track_id": tid
                            })

                except Exception as ai_err:
                    logger.error(f"[INFERENCE_WORKER] AI execution failed on frame {sequence_id}: {ai_err}", exc_info=True)

            # Record frame processed on session
            self.buffer.record_processed(session_id, len(detections))

            t_elapsed = time.time() - t_start
            self.last_inference_latency_ms = round(t_elapsed * 1000.0, 1)
            if t_elapsed > 0:
                self.last_inference_fps = round(1.0 / t_elapsed, 1)

            # Trigger RingBuffer ONLY if RED flag confirmed
            incident_id = None
            if has_red:
                incident_id = ring_buffer_service.trigger_incident(
                    violation_type=red_violation_type,
                    confidence=red_confidence,
                    source_id=source_id,
                    track_id=red_track_id,
                    current_frame=frame,
                    level="red",
                    session_id=session_id,
                    timestamp=frame_ts
                )

            # Dispatch result payload
            level = "red" if has_red else ("yellow" if has_yellow else "green")
            payload = {
                "type": "detection_result",
                "source_id": source_id,
                "session_id": session_id,
                "sequence_id": sequence_id,
                "timestamp": frame_ts,
                "latency_ms": self.last_inference_latency_ms,
                "inference_fps": self.last_inference_fps,
                "level": level,
                "has_cheating": has_red,
                "has_phone": has_phone,
                "incident_id": incident_id,
                "detections": detections
            }

            if callback is not None:
                try:
                    callback(payload)
                except Exception as cb_err:
                    logger.debug(f"[INFERENCE_WORKER] Callback error: {cb_err}")


# Global single-slot buffer and worker instances
inference_buffer = SingleSlotInferenceBuffer()
inference_worker = InferenceWorker(inference_buffer)
inference_worker.start()
