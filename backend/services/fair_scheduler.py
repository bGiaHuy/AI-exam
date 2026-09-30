"""
================================================================================
FAIR MULTI-CAMERA INFERENCE SCHEDULER - AI EXAM CONTROL
================================================================================
Sprint 3.2 Dual-Camera Architecture:
- Coordinates single shared model instance across multiple camera sources.
- Alternates round-robin between active cameras to prevent starvation.
- Per-source single-slot zero-backlog buffer (pending depth <= 1).
- Per-source temporal tracker isolation.
- Per-source ring buffer evidence triggering.
- Full telemetry tracking per source.
================================================================================
"""

import os
import sys
import time
import logging
import threading
from typing import List, Dict, Any, Optional, Callable, Tuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("fair_scheduler")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.camera_source import BaseCameraSource
from services.temporal_tracker import temporal_posture_tracker


class FairInferenceScheduler:
    """
    Fair round-robin scheduler serving multiple camera sources with a
    single shared AI detector instance.
    """

    def __init__(self):
        self._sources: List[BaseCameraSource] = []
        self._sources_lock = threading.RLock()
        self._last_served_idx: int = -1
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._detector = None

        # FPS metrics
        self.last_inference_fps = 0.0
        self.last_inference_latency_ms = 0.0
        self._fps_window: List[float] = []

    def set_sources(self, sources: List[BaseCameraSource]):
        """Register the list of active camera sources."""
        with self._sources_lock:
            self._sources = list(sources)
            self._last_served_idx = -1
            logger.info(f"[FAIR_SCHEDULER] Configured {len(self._sources)} sources: {[s.source_id for s in self._sources]}")

    def add_source(self, source: BaseCameraSource):
        with self._sources_lock:
            if source not in self._sources:
                self._sources.append(source)
                logger.info(f"[FAIR_SCHEDULER] Added source {source.source_id}")

    def remove_source(self, source_id: str):
        with self._sources_lock:
            self._sources = [s for s in self._sources if s.source_id != source_id]
            logger.info(f"[FAIR_SCHEDULER] Removed source {source_id}")

    def _get_detector(self):
        if self._detector is None:
            try:
                from routers.ai_engine import get_detector
                self._detector = get_detector()
            except Exception as e:
                logger.warning(f"[FAIR_SCHEDULER] Cannot load detector: {e}")
        return self._detector

    def set_detector(self, detector_instance):
        """Allows injecting mock or shared detector for unit testing."""
        self._detector = detector_instance

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="FairInferenceSchedulerThread",
            daemon=True
        )
        self._thread.start()
        logger.info("[FAIR_SCHEDULER] Started Fair Multi-Camera Inference Scheduler thread.")

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("[FAIR_SCHEDULER] Stopped Fair Multi-Camera Inference Scheduler thread.")

    def _pick_next_frame(self) -> Optional[Tuple[BaseCameraSource, Dict[str, Any]]]:
        """
        Fair round-robin selection among active camera sources.
        Returns (source, item) or None if all source slots are empty.
        """
        with self._sources_lock:
            num_sources = len(self._sources)
            if num_sources == 0:
                return None

            # Check each source in round-robin sequence starting from last_served + 1
            for i in range(num_sources):
                candidate_idx = (self._last_served_idx + 1 + i) % num_sources
                candidate_source = self._sources[candidate_idx]
                item = candidate_source.inference_slot.pop()
                if item is not None:
                    self._last_served_idx = candidate_idx
                    return candidate_source, item

        return None

    def _scheduler_loop(self):
        while not self._stop_event.is_set():
            picked = self._pick_next_frame()
            if picked is None:
                time.sleep(0.005)  # 5ms idle sleep if no camera has a pending frame
                continue

            source, item = picked
            source_id = source.source_id
            session_id = item["session_id"]
            sequence_id = item["sequence_id"]
            frame_ts = item["timestamp"]
            frame = item["frame"]
            callback = item.get("callback")

            t_start = time.monotonic()
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

                        # 1. Phone violation
                        if status_code == "CHEATING_PHONE":
                            has_phone = True
                            has_red = True
                            red_violation_type = "PHONE"
                            red_confidence = max(red_confidence, score * 100.0 if score <= 1.0 else score)
                            red_track_id = tid
                            detections.append({
                                "id": f"det_phone_{source_id}_{tid}_{sequence_id}",
                                "label": "PHONE_DETECTED",
                                "label_vi": f"Điện thoại (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else score, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "red",
                                "track_id": tid,
                                "source_id": source_id
                            })
                            continue

                        # 2. Posture violation (strictly isolated temporal tracking per source_id)
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
                            red_confidence = max(red_confidence, score * 100.0 if score <= 1.0 else score)
                            red_track_id = tid
                            detections.append({
                                "id": f"det_head_{source_id}_{tid}_{sequence_id}",
                                "label": "HEAD_TURNING",
                                "label_vi": f"Quay đầu {turn_deg:.0f}° ({elapsed_continuous:.1f}s) (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else score, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "red",
                                "track_id": tid,
                                "source_id": source_id
                            })
                        elif posture_level == "yellow":
                            has_yellow = True
                            detections.append({
                                "id": f"det_head_warn_{source_id}_{tid}_{sequence_id}",
                                "label": "SUSPICIOUS_POSTURE",
                                "label_vi": f"Nghi vấn quay đầu {turn_deg:.0f}° ({elapsed_continuous:.1f}s) (Track {tid})",
                                "confidence": round(score * 100.0 if score <= 1.0 else score, 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "yellow",
                                "track_id": tid,
                                "source_id": source_id
                            })
                        else:
                            detections.append({
                                "id": f"det_norm_{source_id}_{tid}_{sequence_id}",
                                "label": "NORMAL",
                                "label_vi": f"Bình thường [Track {tid}]",
                                "confidence": round(float(min(98.0, max(80.0, (1.0 - score) * 100.0))), 1),
                                "bbox": [round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
                                "level": "green",
                                "track_id": tid,
                                "source_id": source_id
                            })

                except Exception as err:
                    logger.warning(f"[FAIR_SCHEDULER:{source_id}] Inference error on frame {sequence_id}: {err}", exc_info=True)

            # Trigger evidence recording on this camera's OWN RingBuffer
            incident_id: Optional[str] = None
            if has_red:
                incident_id = source.ring_buffer.trigger_incident(
                    source_id=source_id,
                    track_id=red_track_id,
                    violation_type=red_violation_type,
                    confidence=red_confidence,
                    level="red",
                    peak_frame=frame,
                    proctor_notes=f"AI phát hiện {red_violation_type} trên nguồn {source.source_label} ({source_id})",
                    session_id=session_id,
                    # Use the acquisition timeline (WebSocket frames use monotonic time).
                    # Wall-clock fallback would leave post-roll waiting indefinitely.
                    timestamp=frame_ts,
                    source_label=source.source_label,
                    source_type=source.source_type
                )

            # Performance telemetry calculation
            t_end = time.monotonic()
            latency_ms = round((t_end - t_start) * 1000.0, 1)
            self.last_inference_latency_ms = latency_ms

            self._fps_window.append(t_end)
            if len(self._fps_window) > 15:
                self._fps_window.pop(0)
            if len(self._fps_window) >= 2:
                dur = self._fps_window[-1] - self._fps_window[0]
                if dur > 0.001:
                    current_fps = round((len(self._fps_window) - 1) / dur, 2)
                    self.last_inference_fps = current_fps

            # An old inference may complete while this camera reconnects.
            current_level = "red" if has_red else ("yellow" if has_yellow else "normal")
            if not source.record_inference_result(session_id, detections, current_level, self.last_inference_fps):
                continue

            # Build standardized camera result payload
            result_payload: Dict[str, Any] = {
                "type": "detection_result",
                "source_id": source_id,
                "source_label": source.source_label,
                "session_id": session_id,
                "sequence_id": sequence_id,
                "timestamp": frame_ts,
                "latency_ms": latency_ms,
                "inference_fps": self.last_inference_fps,
                "level": "red" if has_red else ("yellow" if has_yellow else "green"),
                "has_cheating": has_red,
                "has_phone": has_phone,
                "incident_id": incident_id,
                "detections": detections,
                "telemetry": source.get_telemetry()
            }

            if callback:
                try:
                    callback(result_payload)
                except Exception as cb_err:
                    logger.debug(f"[FAIR_SCHEDULER:{source_id}] Callback error: {cb_err}")


# Global fair scheduler singleton
fair_inference_scheduler = FairInferenceScheduler()
