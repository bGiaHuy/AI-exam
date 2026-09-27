"""
================================================================================
UNIFIED CAMERA SOURCE ABSTRACTION - AI EXAM CONTROL
================================================================================
Sprint 3.2 Dual-Camera Architecture:
- Defines CameraStatus and CameraSource abstraction.
- Supports BrowserWebSocketSource, UsbCameraSource, RtspCameraSource, SyntheticCameraSource.
- Dedicated RingBuffer and Single-Slot Inference Buffer per camera source.
- Strict credential redaction: rtsp://***:***@host:port/path.
- Bounded exponential backoff reconnection for network streams.
================================================================================
"""

import os
import re
import sys
import time
import math
import logging
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, Tuple, Callable
from datetime import datetime, timezone

import cv2
import numpy as np

# Resolve backend directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.ring_buffer import VideoRingBuffer

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("camera_source")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CameraStatus(str, Enum):
    CONNECTING = "CONNECTING"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    RECONNECTING = "RECONNECTING"
    OFFLINE = "OFFLINE"
    STOPPED = "STOPPED"


_SENSITIVE_QUERY_KEYS = {"token", "key", "password", "pwd", "secret", "auth", "pass", "apikey"}


def redact_url(url: Optional[str]) -> str:
    """
    Strips credentials and sensitive tokens from RTSP/HTTP URLs for secure logging and telemetry.
    Case-insensitive matching for: token, TOKEN, apiKey, APIKEY, password, secret, auth, pwd, pass.
    Handles RFC-compliant URLs and embedded URLs in exception strings.
    """
    if not url:
        return ""
    text = str(url)

    # 1. Standalone URL parsing with urllib.parse
    try:
        parsed = urllib.parse.urlsplit(text)
        if parsed.scheme in ("rtsp", "rtsps", "http", "https") and parsed.netloc:
            netloc = parsed.netloc
            if "@" in netloc:
                userinfo, hostport = netloc.rsplit("@", 1)
                redacted_netloc = f"***:***@{hostport}"
            else:
                redacted_netloc = netloc

            query = parsed.query
            if query:
                q_pairs = urllib.parse.parse_qsl(query, keep_blank_values=True)
                redacted_pairs = []
                for k, v in q_pairs:
                    if k.lower() in _SENSITIVE_QUERY_KEYS:
                        redacted_pairs.append((k, "***"))
                    else:
                        redacted_pairs.append((k, v))
                query = urllib.parse.urlencode(redacted_pairs)

            redacted_parsed = parsed._replace(netloc=redacted_netloc, query=query)
            text = urllib.parse.urlunsplit(redacted_parsed)
    except Exception:
        pass

    # 2. String/exception message fallback (e.g. OpenCV / FFmpeg error messages)
    redacted = re.sub(r"://([^:@\s\"\'\)\],]+):([^@\s\"\'\)\],]+)@", r"://***:***@", text)
    redacted = re.sub(
        r"([?&](?:token|key|password|pwd|secret|auth|pass|apikey)=)([^&\s\"\'\)\],]+)",
        r"\1***",
        redacted,
        flags=re.IGNORECASE
    )
    return redacted


class SingleSlotSourceBuffer:
    """
    Dedicated single-slot inference buffer for a single camera source.
    Backlog depth is strictly 0 or 1. If a new frame arrives before previous
    frame is picked by scheduler, the previous frame is superseded.
    """

    def __init__(self, source_id: str):
        self.source_id = source_id
        self._lock = threading.RLock()
        self._slot: Optional[Dict[str, Any]] = None
        self._in_progress = 0

        # Mathematical telemetry counters
        self.submitted = 0
        self.superseded = 0
        self.processed = 0
        self.results_sent = 0
        self.detected_objects = 0

    def push(
        self,
        frame: np.ndarray,
        timestamp: float,
        sequence_id: int,
        session_id: str,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """Push latest frame. If slot already has an unprocessed frame, supersede it."""
        with self._lock:
            self.submitted += 1
            if self._slot is not None:
                self.superseded += 1
            self._slot = {
                "source_id": self.source_id,
                "frame": frame,
                "timestamp": timestamp,
                "sequence_id": sequence_id,
                "session_id": session_id,
                "callback": callback
            }

    def pop(self) -> Optional[Dict[str, Any]]:
        """Pop the pending frame from slot for inference. Mark in_progress = 1."""
        with self._lock:
            if self._slot is None:
                return None
            item = self._slot
            self._slot = None
            self._in_progress = 1
            return item

    def mark_processed(self, num_objects: int = 0):
        """Mark currently in-progress frame as processed."""
        with self._lock:
            self._in_progress = 0
            self.processed += 1
            self.detected_objects += num_objects

    def reset(self):
        """Reset slot and counters."""
        with self._lock:
            self._slot = None
            self._in_progress = 0
            self.submitted = 0
            self.superseded = 0
            self.processed = 0
            self.results_sent = 0
            self.detected_objects = 0

    @property
    def pending_depth(self) -> int:
        """Returns 0 or 1 (slot occupied or in_progress)."""
        with self._lock:
            return 1 if (self._slot is not None or self._in_progress > 0) else 0

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            slot_depth = 1 if self._slot is not None else 0
            pending = slot_depth + self._in_progress
            return {
                "submitted": self.submitted,
                "superseded": self.superseded,
                "in_progress": self._in_progress,
                "processed": self.processed,
                "pending": pending,
                "results_sent": self.results_sent,
                "detected_objects": self.detected_objects
            }


class BaseCameraSource(ABC):
    """
    Abstract Camera Source with independent recording pipeline,
    single-slot inference buffer, and telemetry metrics.
    """

    def __init__(
        self,
        source_id: str,
        source_label: str,
        source_type: str = "browser_ws",
        target_fps: float = 15.0
    ):
        self.source_id = source_id
        self.source_label = source_label
        self.source_type = source_type
        self.target_fps = target_fps

        self.status = CameraStatus.STOPPED
        self.last_frame_at: Optional[float] = None
        self.last_frame_monotonic: Optional[float] = None
        self.first_frame_monotonic: Optional[float] = None

        self.frames_received = 0
        self.frames_dropped = 0
        self.reconnect_count = 0

        # Acquisition FPS calculation window (last 15 frames)
        self._fps_window: list[float] = []
        self.acquisition_fps = 0.0
        self.inference_fps = 0.0

        # Dedicated RingBuffer for recording independent evidence clips
        self.ring_buffer = VideoRingBuffer(
            pre_roll_seconds=5.0,
            post_roll_seconds=10.0,
            cooldown_seconds=6.0,
            target_fps=target_fps
        )

        # Dedicated Single-Slot Buffer for AI inference
        self.inference_slot = SingleSlotSourceBuffer(source_id)

        # Single-slot latest preview frame (Sprint 3.2B)
        self._latest_preview_jpeg: Optional[bytes] = None
        self._latest_preview_seq: int = -1
        self._latest_preview_ts: float = 0.0
        self._latest_detections: list[Dict[str, Any]] = []
        self._latest_level: str = "normal"
        self._preview_lock = threading.Lock()
        self.preview_frames_produced: int = 0
        self.preview_frames_transmitted: int = 0
        self.preview_frames_superseded: int = 0
        self.preview_bytes_transmitted: int = 0
        self.preview_subscribers: int = 0

        self._lock = threading.RLock()
        self._running = False
        self.session_id: str = f"sess_{int(time.time()*1000)}_{source_id}"

    @abstractmethod
    def start(self):
        """Start acquisition worker thread or initialize listener."""
        pass

    @abstractmethod
    def stop(self):
        """Stop acquisition worker and release capture devices cleanly."""
        pass

    def set_latest_preview(
        self,
        jpeg_bytes: bytes,
        timestamp: float,
        sequence_id: int,
        detections: Optional[list[Dict[str, Any]]] = None,
        level: Optional[str] = None
    ):
        """Stores latest JPEG preview frame in single-slot without queue buildup."""
        with self._preview_lock:
            self.preview_frames_produced += 1
            if self._latest_preview_jpeg is not None and sequence_id > self._latest_preview_seq:
                self.preview_frames_superseded += 1
            self._latest_preview_jpeg = jpeg_bytes
            self._latest_preview_ts = timestamp
            self._latest_preview_seq = sequence_id
            if detections is not None:
                self._latest_detections = list(detections)
            if level is not None:
                self._latest_level = level

    def record_preview_transmitted(self, byte_count: int):
        with self._preview_lock:
            self.preview_frames_transmitted += 1
            self.preview_bytes_transmitted += byte_count

    def add_preview_subscriber(self):
        with self._preview_lock:
            self.preview_subscribers += 1

    def remove_preview_subscriber(self):
        with self._preview_lock:
            self.preview_subscribers = max(0, self.preview_subscribers - 1)

    @property
    def preview_pending_depth(self) -> int:
        with self._preview_lock:
            return 1 if self._latest_preview_jpeg is not None else 0

    def set_latest_detections(self, detections: list[Dict[str, Any]], level: str):
        """Updates latest bounding box overlays for this camera source."""
        with self._preview_lock:
            self._latest_detections = list(detections)
            self._latest_level = level

    def get_latest_preview(self) -> Tuple[int, float, Optional[bytes], list[Dict[str, Any]], str]:
        """Returns (sequence_id, timestamp, latest_jpeg_bytes, latest_detections, latest_level)."""
        with self._preview_lock:
            return (
                self._latest_preview_seq,
                self._latest_preview_ts,
                self._latest_preview_jpeg,
                list(self._latest_detections),
                self._latest_level
            )

    def push_frame(
        self,
        frame: np.ndarray,
        timestamp: Optional[float] = None,
        sequence_id: Optional[int] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """
        Ingest a raw frame:
        1. Updates acquisition FPS and counters.
        2. Compresses to JPEG once for RingBuffer and Preview.
        3. Pushes raw frame into dedicated Single-Slot inference buffer.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return False

        now_ts = timestamp if timestamp is not None else time.time()
        now_mono = time.monotonic()

        with self._lock:
            if not self._running and self.status == CameraStatus.STOPPED:
                return False

            self.frames_received += 1
            seq = sequence_id if sequence_id is not None else self.frames_received
            self.last_frame_at = now_ts
            self.last_frame_monotonic = now_mono

            if self.first_frame_monotonic is None:
                self.first_frame_monotonic = now_mono

            # Windowed acquisition FPS
            self._fps_window.append(now_mono)
            if len(self._fps_window) > 15:
                self._fps_window.pop(0)
            if len(self._fps_window) >= 2:
                dur = self._fps_window[-1] - self._fps_window[0]
                if dur > 0.001:
                    self.acquisition_fps = round((len(self._fps_window) - 1) / dur, 2)

            self.status = CameraStatus.ONLINE

        # 1. Compress once for RingBuffer and Preview
        h, w = frame.shape[:2]
        success, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.ring_buffer.jpeg_quality])
        jpeg_bytes = encoded.tobytes() if success else b""

        # 2. Feed RingBuffer (compressed JPEG representation)
        self.ring_buffer.push_frame(
            frame=None,
            jpeg_bytes=jpeg_bytes,
            frame_shape=(h, w),
            timestamp=now_ts,
            source_id=self.source_id,
            sequence_id=seq,
            session_id=self.session_id
        )

        # 3. Feed single-slot preview
        if jpeg_bytes:
            self.set_latest_preview(jpeg_bytes, now_ts, seq)

        # 4. Push raw frame to Single-Slot Inference Buffer (zero backlog, full resolution)
        self.inference_slot.push(
            frame=frame,
            timestamp=now_ts,
            sequence_id=seq,
            session_id=self.session_id,
            callback=callback
        )
        return True

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns per-camera telemetry without secrets."""
        with self._lock:
            stats = self.inference_slot.get_stats()
            rb_stats = self.ring_buffer.get_telemetry()
            return {
                "source_id": self.source_id,
                "source_label": self.source_label,
                "source_type": self.source_type,
                "status": self.status.value,
                "acquisition_fps": self.acquisition_fps,
                "inference_fps": self.inference_fps,
                "frames_received": self.frames_received,
                "frames_submitted": stats["submitted"],
                "frames_processed": stats["processed"],
                "frames_superseded": stats["superseded"],
                "frames_dropped": self.frames_dropped,
                "pending_depth": self.inference_slot.pending_depth,
                "reconnect_count": self.reconnect_count,
                "last_frame_at": datetime.fromtimestamp(self.last_frame_at, timezone.utc).isoformat() if self.last_frame_at else None,
                "session_id": self.session_id,
                "ring_buffer_frames": rb_stats["ring_buffer_frames"],
                "ring_buffer_bytes": rb_stats["ring_buffer_bytes"],
                "ring_buffer_oldest_age": rb_stats["ring_buffer_oldest_age"],
                "ring_buffer_dropped_by_limit": rb_stats["ring_buffer_dropped_by_limit"],
                "corrupt_frames_skipped": rb_stats["corrupt_frames_skipped"]
            }

    def reset_session(self, new_session_id: Optional[str] = None):
        """Reset state and counters for a new session."""
        with self._lock:
            self.session_id = new_session_id or f"sess_{int(time.time()*1000)}_{self.source_id}"
            self.frames_received = 0
            self.frames_dropped = 0
            self.acquisition_fps = 0.0
            self.inference_fps = 0.0
            self._fps_window.clear()
            self.first_frame_monotonic = None
            self.last_frame_monotonic = None
            self.last_frame_at = None
            self.ring_buffer.reset_session(self.session_id)
            self.inference_slot.reset()
        with self._preview_lock:
            self._latest_preview_jpeg = None
            self._latest_preview_seq = -1
            self._latest_preview_ts = 0.0
            self._latest_detections.clear()
            self._latest_level = "normal"


class BrowserWebSocketSource(BaseCameraSource):
    """Camera source fed via Browser WebSocket Ingestion."""

    def __init__(self, source_id: str, source_label: str = "Webcam Trình Duyệt"):
        super().__init__(source_id, source_label, source_type="browser_ws")

    def start(self):
        with self._lock:
            self._running = True
            self.status = CameraStatus.CONNECTING
            logger.info(f"[CAMERA_SOURCE:{self.source_id}] Browser WebSocket Source ready.")

    def stop(self):
        with self._lock:
            self._running = False
            self.status = CameraStatus.STOPPED
            logger.info(f"[CAMERA_SOURCE:{self.source_id}] Browser WebSocket Source stopped.")


class UsbCameraSource(BaseCameraSource):
    """Camera source fed via USB capture device (cv2.VideoCapture)."""

    def __init__(self, source_id: str, source_label: str = "USB Camera", device_index: int = 0):
        super().__init__(source_id, source_label, source_type="usb")
        self.device_index = device_index
        self._thread: Optional[threading.Thread] = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self.status = CameraStatus.CONNECTING
            self._thread = threading.Thread(target=self._capture_loop, daemon=True, name=f"usb_{self.source_id}")
            self._thread.start()
            logger.info(f"[CAMERA_SOURCE:{self.source_id}] USB Camera starting on index {self.device_index}")

    def stop(self):
        with self._lock:
            self._running = False
            self.status = CameraStatus.STOPPED
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info(f"[CAMERA_SOURCE:{self.source_id}] USB Camera stopped.")

    def _capture_loop(self):
        cap = None
        backoff = 1.0
        while self._running:
            try:
                if sys.platform == "win32":
                    cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(self.device_index)

                if not cap.isOpened():
                    self.status = CameraStatus.RECONNECTING
                    self.reconnect_count += 1
                    time.sleep(backoff)
                    backoff = min(backoff * 2.0, 15.0)
                    continue

                try:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                except Exception:
                    pass

                self.status = CameraStatus.ONLINE
                backoff = 1.0
                while self._running:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        self.status = CameraStatus.DEGRADED
                        self.frames_dropped += 1
                        time.sleep(0.1)
                        break
                    self.push_frame(frame)
                    time.sleep(1.0 / self.target_fps)
            except Exception as err:
                logger.warning(f"[CAMERA_SOURCE:{self.source_id}] USB capture error: {err}")
                self.status = CameraStatus.RECONNECTING
                self.reconnect_count += 1
                time.sleep(backoff)
                backoff = min(backoff * 2.0, 15.0)
            finally:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass


class RtspCameraSource(BaseCameraSource):
    """
    RTSP IP Camera Source (e.g. TP-Link Tapo TC70/TC71).
    - Credential redaction in all logs.
    - Bounded exponential backoff reconnection: 1s, 2s, 4s ... max 15s.
    - Stale-frame timeout detection (5s).
    - Fault-isolated: failure does not impact other camera sources.
    """

    def __init__(
        self,
        source_id: str,
        source_label: str = "Tapo RTSP Camera",
        rtsp_url: str = "",
        target_fps: float = 15.0,
        frame_timeout_sec: float = 5.0
    ):
        super().__init__(source_id, source_label, source_type="rtsp", target_fps=target_fps)
        self.rtsp_url = rtsp_url
        self.frame_timeout_sec = frame_timeout_sec
        self._thread: Optional[threading.Thread] = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self.status = CameraStatus.CONNECTING
            self._thread = threading.Thread(target=self._rtsp_loop, daemon=True, name=f"rtsp_{self.source_id}")
            self._thread.start()
            logger.info(f"[CAMERA_SOURCE:{self.source_id}] RTSP Source starting on {redact_url(self.rtsp_url)}")

    def stop(self):
        with self._lock:
            self._running = False
            self.status = CameraStatus.STOPPED
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info(f"[CAMERA_SOURCE:{self.source_id}] RTSP Source stopped.")

    def _calculate_backoff(self, attempt: int) -> float:
        """Bounded exponential backoff: 1s, 2s, 4s... capped at 15s."""
        return min(1.0 * (2.0 ** max(0, attempt - 1)), 15.0)

    def _rtsp_loop(self):
        cap = None
        backoff = 1.0
        while self._running:
            redacted = redact_url(self.rtsp_url)
            try:
                self.status = CameraStatus.CONNECTING
                logger.info(f"[CAMERA_SOURCE:{self.source_id}] Connecting to RTSP: {redacted}")

                # Configure OpenCV VideoCapture with environment-safe options
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|analyzeduration;1000000|max_delay;500000"
                cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not cap.isOpened():
                    logger.warning(f"[CAMERA_SOURCE:{self.source_id}] Failed to open RTSP {redacted}. Retrying in {backoff}s...")
                    self.status = CameraStatus.RECONNECTING
                    self.reconnect_count += 1
                    time.sleep(backoff)
                    backoff = min(backoff * 2.0, 15.0)
                    continue

                self.status = CameraStatus.ONLINE
                backoff = 1.0
                last_successful_read = time.monotonic()

                while self._running:
                    ret, frame = cap.read()
                    now = time.monotonic()

                    if not ret or frame is None:
                        if now - last_successful_read > self.frame_timeout_sec:
                            logger.warning(f"[CAMERA_SOURCE:{self.source_id}] RTSP frame timeout ({self.frame_timeout_sec}s). Reconnecting...")
                            break
                        self.frames_dropped += 1
                        time.sleep(0.05)
                        continue

                    last_successful_read = now
                    self.push_frame(frame)
                    time.sleep(1.0 / self.target_fps)

                # Reconnect trigger
                self.status = CameraStatus.RECONNECTING
                self.reconnect_count += 1
                time.sleep(backoff)
                backoff = min(backoff * 2.0, 15.0)

            except Exception as err:
                logger.warning(f"[CAMERA_SOURCE:{self.source_id}] RTSP error ({redacted}): {err}")
                self.status = CameraStatus.RECONNECTING
                self.reconnect_count += 1
                time.sleep(backoff)
                backoff = min(backoff * 2.0, 15.0)
            finally:
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass


class SyntheticCameraSource(BaseCameraSource):
    """
    Deterministic Synthetic Camera Source for Automated Tests & Benchmarks.
    Generates video frames with embedded source_id, timestamp, and test patterns.
    Requires no hardware cameras or external network connections.
    """

    def __init__(
        self,
        source_id: str,
        source_label: str = "Synthetic Test Camera",
        target_fps: float = 15.0,
        generate_anomalies: bool = False
    ):
        super().__init__(source_id, source_label, source_type="synthetic", target_fps=target_fps)
        self.generate_anomalies = generate_anomalies
        self._thread: Optional[threading.Thread] = None

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self.status = CameraStatus.ONLINE
            self._thread = threading.Thread(target=self._generator_loop, daemon=True, name=f"synth_{self.source_id}")
            self._thread.start()
            logger.info(f"[CAMERA_SOURCE:{self.source_id}] Synthetic Camera started at {self.target_fps} FPS.")

    def stop(self):
        with self._lock:
            self._running = False
            self.status = CameraStatus.STOPPED
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info(f"[CAMERA_SOURCE:{self.source_id}] Synthetic Camera stopped.")

    def _generator_loop(self):
        frame_idx = 0
        while self._running:
            t_start = time.monotonic()
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Draw background grid & metadata
            cv2.putText(frame, f"SOURCE: {self.source_id}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"LABEL: {self.source_label}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            cv2.putText(frame, f"FRAME: {frame_idx}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Draw simulated student desk / test bounding box
            color = (0, 0, 255) if (self.generate_anomalies and frame_idx % 30 >= 15) else (255, 255, 0)
            cv2.rectangle(frame, (180, 140), (460, 420), color, 2)

            self.push_frame(frame, timestamp=time.time(), sequence_id=frame_idx)
            frame_idx += 1

            elapsed = time.monotonic() - t_start
            sleep_time = max(0.001, (1.0 / self.target_fps) - elapsed)
            time.sleep(sleep_time)
