"""
================================================================================
TIME-BASED VIDEO RING BUFFER & EVIDENCE RECORDER
================================================================================
Enterprise Real-Time Architecture:
- Circular deque buffer storing (timestamp: float, frame: np.ndarray)
- Time-based pre-roll & post-roll window extraction (seconds, not frame counts)
- Real-time video resampling: ensures exported MP4 plays at exact 1.0x real-world speed
- Strict file integrity verification (size > 0, readable by OpenCV)
- Multi-target cooldown key: (source_id, track_id, violation_type)
- Thread-safe DB persistence via sequential DBWriteQueue
================================================================================
"""

import os
import re
import sys
import time
import uuid
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

import cv2
import numpy as np

logger = logging.getLogger("ring_buffer")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Backend path resolution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

BASE_DIR = os.path.dirname(BACKEND_DIR)
EVIDENCE_DIR = os.path.join(BASE_DIR, "data", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

from services.db_queue import db_write_queue


def validate_video_file(video_path: str) -> bool:
    """Verify video file exists, is non-empty, and can be opened/read by OpenCV."""
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        return False
    try:
        test_cap = cv2.VideoCapture(video_path)
        if not test_cap.isOpened():
            test_cap.release()
            return False
        ret, _ = test_cap.read()
        test_cap.release()
        return bool(ret)
    except Exception:
        return False


class VideoClipTask:
    """Represents an active clip extraction job gathered from the RingBuffer."""
    def __init__(
        self,
        incident_id: str,
        source_id: str,
        track_id: Optional[int],
        violation_type: str,
        confidence: float,
        level: str,
        pre_frames: List[Tuple[float, np.ndarray]],
        post_end_time: float,
        peak_frame: Optional[np.ndarray] = None,
        detected_at: Optional[datetime] = None,
        target_fps: float = 15.0,
        proctor_notes: Optional[str] = None,
        session_id: Optional[str] = None,
        trigger_time: float = 0.0,
        source_label: Optional[str] = None,
        source_type: Optional[str] = None
    ):
        self.incident_id = incident_id
        self.source_id = source_id
        self.source_label = source_label or "Camera 1"
        self.source_type = source_type or "browser_ws"
        self.track_id = track_id
        self.violation_type = violation_type
        self.confidence = confidence
        self.level = level
        # List of (timestamp, frame, sequence_id, session_id)
        self.timed_frames: List[Any] = list(pre_frames)
        self.post_end_time = post_end_time
        self.peak_frame = peak_frame
        self.detected_at = detected_at or datetime.now(timezone.utc)
        self.target_fps = target_fps
        self.proctor_notes = proctor_notes
        self.session_id = session_id
        self.trigger_time = trigger_time
        self.state: str = "RECORDING_POST"
        self.metrics: Dict[str, Any] = {}
        self.completion_event = threading.Event()
        self.output_video_path: Optional[str] = None


class VideoRingBuffer:
    """
    Time-based, memory-bounded circular frame buffer with automated pre/post incident clip stitching.
    - Stores compressed JPEG frames to strictly bound RAM usage.
    - Enforces simultaneous bounds: max_retention_seconds, max_frames, and max_bytes.
    - Safely skips corrupted frames during clip export.
    """
    def __init__(
        self,
        pre_roll_seconds: float = 5.0,
        post_roll_seconds: float = 10.0,
        cooldown_seconds: float = 6.0,
        target_fps: float = 15.0,
        jpeg_quality: int = 85,
        max_bytes: int = 60 * 1024 * 1024,
        max_frames: int = 350,
        max_retention_seconds: float = 20.0
    ):
        self.pre_roll_seconds = pre_roll_seconds
        self.post_roll_seconds = post_roll_seconds
        self.cooldown_seconds = cooldown_seconds
        self.target_fps = target_fps
        self.jpeg_quality = int(os.getenv("RING_BUFFER_JPEG_QUALITY", str(jpeg_quality)))
        self.max_bytes = int(os.getenv("RING_BUFFER_MAX_BYTES", str(max_bytes)))
        self.max_frames = int(os.getenv("RING_BUFFER_MAX_FRAMES", str(max_frames)))
        self.max_retention_seconds = float(os.getenv("RING_BUFFER_MAX_RETENTION_SEC", str(max_retention_seconds)))

        # Buffer storing (timestamp: float, payload: bytes | np.ndarray, sequence_id, session_id, source_id, width, height)
        self.frame_buffer: deque = deque()
        self.active_tasks: List[VideoClipTask] = []
        self.tasks_by_id: Dict[str, VideoClipTask] = {}
        self.lock = threading.RLock()

        # Telemetry metrics
        self.total_bytes: int = 0
        self.dropped_by_limit: int = 0
        self.corrupt_frames_skipped: int = 0

        # Cooldown dictionary keyed by (session_id, source_id, track_id, violation_type)
        self.last_incident_time_by_key: Dict[Tuple[str, str, str, str], float] = {}
        self.last_completed_clip_metrics: Dict[str, Any] = {}

    def update_settings(
        self,
        pre_roll_seconds: Optional[float] = None,
        post_roll_seconds: Optional[float] = None,
        cooldown_seconds: Optional[float] = None,
        max_bytes: Optional[int] = None,
        max_frames: Optional[int] = None
    ):
        with self.lock:
            if pre_roll_seconds is not None:
                self.pre_roll_seconds = pre_roll_seconds
            if post_roll_seconds is not None:
                self.post_roll_seconds = post_roll_seconds
            if cooldown_seconds is not None:
                self.cooldown_seconds = cooldown_seconds
            if max_bytes is not None:
                self.max_bytes = max_bytes
            if max_frames is not None:
                self.max_frames = max_frames
            logger.info(
                f"[RING_BUFFER] Updated config: pre={self.pre_roll_seconds}s, "
                f"post={self.post_roll_seconds}s, cooldown={self.cooldown_seconds}s, "
                f"max_bytes={self.max_bytes}, max_frames={self.max_frames}"
            )

    def reset_session(self, session_id: str):
        """Clear all buffered frames, active tasks, and cooldowns for a specific session."""
        with self.lock:
            to_del_cd = [k for k in self.last_incident_time_by_key if k[0] == session_id]
            for k in to_del_cd:
                del self.last_incident_time_by_key[k]

            self.active_tasks = [t for t in self.active_tasks if t.session_id != session_id]
            new_buffer = deque()
            new_bytes = 0
            for item in self.frame_buffer:
                sess = item[3] if len(item) > 3 else None
                if sess != session_id:
                    new_buffer.append(item)
                    new_bytes += len(item[1]) if isinstance(item[1], bytes) else getattr(item[1], "nbytes", 0)
            self.frame_buffer = new_buffer
            self.total_bytes = new_bytes
            logger.info(f"[RING_BUFFER] Cleared session buffer, tasks, and cooldown for session={session_id}")

    def _current_state_locked(self) -> str:
        if any(t.state == "SAVING" for t in self.active_tasks):
            return "SAVING"
        if any(t.state == "RECORDING_POST" for t in self.active_tasks):
            return "RECORDING_POST"
        return "IDLE"

    @property
    def current_state(self) -> str:
        with self.lock:
            return self._current_state_locked()

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns accurate RingBuffer telemetry metrics."""
        with self.lock:
            now = time.time()
            oldest_age = (now - self.frame_buffer[0][0]) if self.frame_buffer else 0.0
            return {
                "ring_buffer_frames": len(self.frame_buffer),
                "ring_buffer_bytes": self.total_bytes,
                "ring_buffer_oldest_age": round(max(0.0, oldest_age), 2),
                "ring_buffer_dropped_by_limit": self.dropped_by_limit,
                "corrupt_frames_skipped": self.corrupt_frames_skipped,
                "active_tasks": len(self.active_tasks),
                "state": self._current_state_locked()
            }

    def push_frame(
        self,
        frame: Optional[np.ndarray] = None,
        timestamp: Optional[float] = None,
        sequence_id: Optional[int] = None,
        session_id: Optional[str] = None,
        source_id: Optional[str] = None,
        jpeg_bytes: Optional[bytes] = None,
        frame_shape: Optional[Tuple[int, int]] = None
    ):
        """
        Push a frame into the circular buffer with exact timestamp.
        Stores compressed JPEG bytes to bound memory usage.
        Prunes by max_retention_seconds, max_frames, and max_bytes.
        """
        now = timestamp if timestamp is not None else time.time()

        # Extract dimensions and JPEG bytes
        w, h = 640, 480
        if jpeg_bytes is None:
            if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
                return
            h, w = frame.shape[:2]
            success, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
            if not success:
                return
            payload: Any = encoded.tobytes()
        else:
            payload = jpeg_bytes
            if frame_shape:
                h, w = frame_shape
            elif frame is not None and isinstance(frame, np.ndarray) and frame.size > 0:
                h, w = frame.shape[:2]

        byte_size = len(payload) if isinstance(payload, bytes) else getattr(payload, "nbytes", 0)

        with self.lock:
            # 1. Maintain time-based rolling buffer: (timestamp, payload, sequence_id, session_id, source_id, width, height)
            self.frame_buffer.append((now, payload, sequence_id, session_id, source_id, w, h))
            self.total_bytes += byte_size

            # 2. Prune frames older than max_retention_seconds
            retention_cutoff = now - max(self.pre_roll_seconds * 2.0, self.max_retention_seconds)
            while self.frame_buffer and self.frame_buffer[0][0] < retention_cutoff:
                popped = self.frame_buffer.popleft()
                p_size = len(popped[1]) if isinstance(popped[1], bytes) else getattr(popped[1], "nbytes", 0)
                self.total_bytes = max(0, self.total_bytes - p_size)

            # 3. Prune if exceeding max_frames
            while len(self.frame_buffer) > self.max_frames:
                popped = self.frame_buffer.popleft()
                p_size = len(popped[1]) if isinstance(popped[1], bytes) else getattr(popped[1], "nbytes", 0)
                self.total_bytes = max(0, self.total_bytes - p_size)
                self.dropped_by_limit += 1

            # 4. Prune if exceeding max_bytes
            while self.total_bytes > self.max_bytes and self.frame_buffer:
                popped = self.frame_buffer.popleft()
                p_size = len(popped[1]) if isinstance(popped[1], bytes) else getattr(popped[1], "nbytes", 0)
                self.total_bytes = max(0, self.total_bytes - p_size)
                self.dropped_by_limit += 1

            # 5. Advance active post-recording tasks
            completed_tasks: List[VideoClipTask] = []
            for task in self.active_tasks:
                if task.state == "RECORDING_POST":
                    if task.session_id is not None and session_id is not None and task.session_id != session_id:
                        continue
                    if task.source_id is not None and source_id is not None and task.source_id != source_id:
                        continue
                    task.timed_frames.append((now, payload, sequence_id, session_id, source_id, w, h))

                    if now >= task.post_end_time:
                        task.state = "SAVING"
                        completed_tasks.append(task)

            # 6. Hand off completed tasks to background thread
            for task in completed_tasks:
                self.active_tasks.remove(task)
                threading.Thread(
                    target=self._render_and_persist_clip,
                    args=(task,),
                    name=f"Worker-{task.incident_id}",
                    daemon=True
                ).start()

    def trigger_incident(
        self,
        violation_type: str,
        confidence: float,
        source_id: str = "webcam_local",
        track_id: Optional[int] = None,
        current_frame: Optional[np.ndarray] = None,
        level: str = "red",
        proctor_notes: Optional[str] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[float] = None,
        source_label: Optional[str] = None,
        source_type: Optional[str] = None,
        peak_frame: Optional[np.ndarray] = None
    ) -> Optional[str]:
        """
        Trigger an automated evidence clip recording.
        Cooldown key is multi-target: (session_id, source_id, track_id, violation_type).
        """
        frame_to_use = current_frame if current_frame is not None else peak_frame
        trigger_time = timestamp if timestamp is not None else time.time()
        track_key = str(track_id) if track_id is not None else "unknown"
        sess_key = session_id or "default"
        cooldown_key = (sess_key, source_id, track_key, violation_type)

        with self.lock:
            # Check multi-target cooldown
            last_time = self.last_incident_time_by_key.get(cooldown_key, 0.0)
            if trigger_time - last_time < self.cooldown_seconds:
                logger.debug(f"[RING_BUFFER] Cooldown active for {cooldown_key} ({trigger_time - last_time:.1f}s < {self.cooldown_seconds}s).")
                return None

            self.last_incident_time_by_key[cooldown_key] = trigger_time
            clean_src = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(source_id))
            incident_id = f"inc_{clean_src}_{int(trigger_time)}_{uuid.uuid4().hex[:6]}"
            detected_at = datetime.now(timezone.utc)

            # Canonical confidence normalization (Sprint 3.2B-R2)
            from confidence import normalize_confidence
            norm_conf = normalize_confidence(confidence)

            logger.info(
                f"[AI_ENGINE] Incident triggered: {violation_type} [Source {source_id}] [Track {track_key}] "
                f"(raw input: {confidence}, canonical: {norm_conf:.4f}) -> Capturing pre/post clip ({self.pre_roll_seconds}s / {self.post_roll_seconds}s)..."
            )

            # Extract pre-roll frames based on timestamp: [trigger_time - pre_roll_seconds, trigger_time]
            cutoff_time = trigger_time - self.pre_roll_seconds
            pre_frames = []
            for item in self.frame_buffer:
                t = item[0]
                f = item[1]
                seq = item[2] if len(item) > 2 else None
                sess = item[3] if len(item) > 3 else None
                src = item[4] if len(item) > 4 else None
                w_f = item[5] if len(item) > 5 else 640
                h_f = item[6] if len(item) > 6 else 480
                if t >= cutoff_time:
                    # Do not mix buffers across sessions if session_id is specified
                    if session_id is not None and sess is not None and sess != session_id:
                        continue
                    if source_id is not None and src is not None and src != source_id:
                        continue
                    pre_frames.append((t, f, seq, sess, src, w_f, h_f))

            task = VideoClipTask(
                incident_id=incident_id,
                source_id=source_id,
                track_id=track_id,
                violation_type=violation_type,
                confidence=norm_conf,
                level=level,
                pre_frames=pre_frames,
                post_end_time=trigger_time + self.post_roll_seconds,
                peak_frame=frame_to_use.copy() if (isinstance(frame_to_use, np.ndarray) and frame_to_use.size > 0) else frame_to_use,
                detected_at=detected_at,
                target_fps=self.target_fps,
                proctor_notes=proctor_notes,
                session_id=session_id,
                trigger_time=trigger_time,
                source_label=source_label,
                source_type=source_type
            )
            self.active_tasks.append(task)
            self.tasks_by_id[incident_id] = task
            return incident_id

    def _render_and_persist_clip(self, task: VideoClipTask):
        """
        Background Worker:
        1. Decodes JPEG frames safely and skips corrupted frames without crashing.
        2. Resamples frames along exact real-world time grid for 1.0x natural playback speed.
        3. Encodes MP4 using avc1 (fallback mp4v).
        4. Saves peak snapshot JPEG.
        5. Verifies file integrity (size > 0, valid OpenCV stream).
        6. Enqueues verified incident into DBWriteQueue.
        """
        try:
            if not task.timed_frames:
                logger.warning(f"[RING_BUFFER] Task {task.incident_id} has no frames, canceling export.")
                return

            video_filename = f"{task.incident_id}.mp4"
            snap_filename = f"{task.incident_id}_snap.jpg"
            video_path = os.path.join(EVIDENCE_DIR, video_filename)
            snap_path = os.path.join(EVIDENCE_DIR, snap_filename)

            # 1. Decode valid frames and skip corrupted frames safely
            valid_decoded: List[Tuple[float, np.ndarray, Any]] = []
            for item in task.timed_frames:
                t_f = item[0]
                payload = item[1]
                seq_f = item[2] if len(item) > 2 else None

                if isinstance(payload, bytes):
                    if len(payload) < 4 or payload[:2] != b'\xff\xd8':
                        self.corrupt_frames_skipped += 1
                        continue
                    try:
                        decoded = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                        if decoded is None or decoded.size == 0:
                            self.corrupt_frames_skipped += 1
                            continue
                        valid_decoded.append((t_f, decoded, seq_f))
                    except Exception:
                        self.corrupt_frames_skipped += 1
                        continue
                elif isinstance(payload, np.ndarray) and payload.size > 0:
                    valid_decoded.append((t_f, payload, seq_f))

            if not valid_decoded:
                logger.warning(f"[RING_BUFFER] Task {task.incident_id} has no valid decodable frames.")
                return

            # 2. Time boundaries using server monotonic timeline and server UTC wall-clock
            from datetime import timedelta
            t_start = valid_decoded[0][0]
            t_end = valid_decoded[-1][0]
            duration_real = max(0.1, t_end - t_start)
            
            pre_dur = max(0.0, (task.trigger_time or t_end) - t_start)
            clip_started_at = task.detected_at - timedelta(seconds=pre_dur)
            clip_ended_at = clip_started_at + timedelta(seconds=duration_real)

            # 3. Save Peak Snapshot Thumbnail
            if task.peak_frame is not None and isinstance(task.peak_frame, np.ndarray) and task.peak_frame.size > 0:
                cv2.imwrite(snap_path, task.peak_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            elif task.peak_frame is not None and isinstance(task.peak_frame, bytes) and len(task.peak_frame) > 0:
                with open(snap_path, "wb") as sf:
                    sf.write(task.peak_frame)
            elif valid_decoded:
                mid_img = valid_decoded[len(valid_decoded) // 2][1]
                cv2.imwrite(snap_path, mid_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

            h, w = valid_decoded[0][1].shape[:2]
            target_fps = max(1.0, task.target_fps)

            # 4. Real-time Resampling along uniform time grid
            total_output_frames = max(1, int(round(duration_real * target_fps)))
            time_grid = np.linspace(t_start, t_end, total_output_frames)

            # Build timestamps array for nearest neighbor frame matching
            frame_times = np.array([vd[0] for vd in valid_decoded])
            frame_images = [vd[1] for vd in valid_decoded]

            # 5. Open VideoWriter (try avc1 first, fallback mp4v)
            out = None
            codecs_to_try = [('avc1', cv2.VideoWriter_fourcc(*'avc1')), ('mp4v', cv2.VideoWriter_fourcc(*'mp4v'))]
            for _, fourcc in codecs_to_try:
                try:
                    writer = cv2.VideoWriter(video_path, fourcc, target_fps, (w, h))
                    if writer is not None and writer.isOpened():
                        out = writer
                        break
                    if writer is not None:
                        writer.release()
                except Exception:
                    pass

            if out is None or not out.isOpened():
                out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), target_fps, (w, h))

            # 6. Write resampled frames & compute duplicate metrics
            chosen_indices = []
            for target_t in time_grid:
                idx = int(np.argmin(np.abs(frame_times - target_t)))
                chosen_indices.append(idx)
                f = frame_images[idx]
                if f.shape[0] != h or f.shape[1] != w:
                    f = cv2.resize(f, (w, h))
                out.write(f)

            out.release()

            # Metrics computation
            repeated_output_count = sum(1 for i in range(1, len(chosen_indices)) if chosen_indices[i] == chosen_indices[i - 1])
            output_repeated_frame_ratio = repeated_output_count / max(1, len(chosen_indices))
            unique_source_in_clip = len(set(chosen_indices))

            raw_seq_ids = [vd[2] for vd in valid_decoded if vd[2] is not None]
            if raw_seq_ids:
                transport_unique = len(set(raw_seq_ids))
                transport_duplicate_ratio = max(0.0, 1.0 - (transport_unique / max(1, len(raw_seq_ids))))
            else:
                transport_duplicate_ratio = 0.0

            task.metrics = {
                "duration_real": duration_real,
                "total_output_frames": total_output_frames,
                "total_raw_frames": len(valid_decoded),
                "unique_source_frames": unique_source_in_clip,
                "transport_duplicate_ratio": transport_duplicate_ratio,
                "output_repeated_frame_ratio": output_repeated_frame_ratio,
                "target_fps": target_fps,
                "corrupt_frames_skipped": self.corrupt_frames_skipped
            }
            with self.lock:
                self.last_completed_clip_metrics = dict(task.metrics)

            # 6. File Integrity Verification (CRITICAL)
            is_valid = validate_video_file(video_path)

            if not is_valid:
                logger.error(f"[RING_BUFFER] File integrity check failed for {video_path}! Discarding corrupted clip.")
                if os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                    except Exception:
                        pass
                return

            logger.info(
                f"[RING_BUFFER] Evidence clip generated successfully: data/evidence/{video_filename} "
                f"({duration_real:.1f}s real-time duration, {total_output_frames} frames @ {target_fps:.1f} FPS, "
                f"unique_source={unique_source_in_clip}, output_repeated_ratio={output_repeated_frame_ratio:.2%}, "
                f"transport_dup_ratio={transport_duplicate_ratio:.2%})"
            )

            # 7. Enqueue verified incident into sequential DBWriteQueue
            track_str = f"Track {task.track_id}" if task.track_id is not None else "Unknown Track"
            display_pct = (task.confidence * 100.0) if task.confidence <= 1.0 else task.confidence
            proctor_notes = task.proctor_notes or (
                f"Phát hiện {task.violation_type} ({track_str}) với điểm tin cậy {display_pct:.1f}%. "
                f"Clip bằng chứng trích xuất tự động ({duration_real:.1f}s thực tế, "
                f"{unique_source_in_clip} frames nguồn duy nhất)."
            )

            task.output_video_path = video_path

            db_write_queue.enqueue_incident({
                "id": task.incident_id,
                "source_id": task.source_id,
                "source_label": getattr(task, "source_label", "Camera 1"),
                "source_type": getattr(task, "source_type", "browser_ws"),
                "session_id": task.session_id,
                "track_id": task.track_id,
                "violation_type": task.violation_type,
                "confidence": task.confidence,
                "level": task.level,
                "detected_at": task.detected_at,
                "clip_started_at": clip_started_at,
                "clip_ended_at": clip_ended_at,
                "video_path": f"/evidence/{video_filename}",
                "snapshot_path": f"/evidence/{snap_filename}",
                "status": "pending",
                "proctor_notes": proctor_notes
            })

        except Exception as e:
            logger.error(f"[RING_BUFFER] Exception rendering clip {task.incident_id}: {e}", exc_info=True)
        finally:
            task.completion_event.set()

    def wait_for_incident_clip(self, incident_id: str, timeout: float = 20.0) -> Optional[Dict[str, Any]]:
        """
        Explicit event synchronization waiting for a clip task to finish rendering to disk.
        Returns task.metrics on success or None if timed out.
        """
        with self.lock:
            task = self.tasks_by_id.get(incident_id)
        if not task:
            return None
        finished = task.completion_event.wait(timeout=timeout)
        if not finished:
            return None
        return task.metrics


# Global singleton instance
ring_buffer_service = VideoRingBuffer(
    pre_roll_seconds=5.0,
    post_roll_seconds=10.0,
    cooldown_seconds=6.0,
    target_fps=15.0
)
