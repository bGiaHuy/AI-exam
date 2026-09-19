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
        trigger_time: float = 0.0
    ):
        self.incident_id = incident_id
        self.source_id = source_id
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


class VideoRingBuffer:
    """
    Time-based circular frame buffer with automated pre/post incident clip stitching.
    """
    def __init__(
        self,
        pre_roll_seconds: float = 5.0,
        post_roll_seconds: float = 10.0,
        cooldown_seconds: float = 6.0,
        target_fps: float = 15.0
    ):
        self.pre_roll_seconds = pre_roll_seconds
        self.post_roll_seconds = post_roll_seconds
        self.cooldown_seconds = cooldown_seconds
        self.target_fps = target_fps

        # Buffer storing (timestamp: float, frame: np.ndarray, sequence_id, session_id)
        self.frame_buffer: deque = deque()
        self.active_tasks: List[VideoClipTask] = []
        self.lock = threading.Lock()

        # Cooldown dictionary keyed by (source_id, track_id, violation_type)
        self.last_incident_time_by_key: Dict[Tuple[str, str, str], float] = {}
        self.last_completed_clip_metrics: Dict[str, Any] = {}

    def update_settings(
        self,
        pre_roll_seconds: Optional[float] = None,
        post_roll_seconds: Optional[float] = None,
        cooldown_seconds: Optional[float] = None
    ):
        with self.lock:
            if pre_roll_seconds is not None:
                self.pre_roll_seconds = pre_roll_seconds
            if post_roll_seconds is not None:
                self.post_roll_seconds = post_roll_seconds
            if cooldown_seconds is not None:
                self.cooldown_seconds = cooldown_seconds
            logger.info(
                f"[RING_BUFFER] Updated config: pre={self.pre_roll_seconds}s, "
                f"post={self.post_roll_seconds}s, cooldown={self.cooldown_seconds}s"
            )

    def reset_session(self, session_id: str):
        """Clear all buffered frames, active tasks, and cooldowns for a specific session."""
        with self.lock:
            to_del_cd = [k for k in self.last_incident_time_by_key if k[0] == session_id]
            for k in to_del_cd:
                del self.last_incident_time_by_key[k]

            self.active_tasks = [t for t in self.active_tasks if t.session_id != session_id]
            self.frame_buffer = deque(
                [item for item in self.frame_buffer if len(item) <= 3 or item[3] != session_id],
                maxlen=self.frame_buffer.maxlen
            )
            logger.info(f"[RING_BUFFER] Cleared session buffer, tasks, and cooldown for session={session_id}")

    @property
    def current_state(self) -> str:
        with self.lock:
            if any(t.state == "SAVING" for t in self.active_tasks):
                return "SAVING"
            if any(t.state == "RECORDING_POST" for t in self.active_tasks):
                return "RECORDING_POST"
            return "IDLE"

    def push_frame(
        self,
        frame: np.ndarray,
        timestamp: Optional[float] = None,
        sequence_id: Optional[int] = None,
        session_id: Optional[str] = None
    ):
        """
        Push a raw frame into the circular buffer with exact timestamp.
        Automatically advances active post-recording tasks without blocking.
        """
        if frame is None or frame.size == 0:
            return

        now = timestamp if timestamp is not None else time.time()

        with self.lock:
            # 1. Maintain time-based rolling buffer: (timestamp, frame, sequence_id, session_id)
            self.frame_buffer.append((now, frame.copy(), sequence_id, session_id))

            # Prune frames older than (now - pre_roll_seconds * 2) to manage memory
            retention_cutoff = now - max(self.pre_roll_seconds * 2.0, 20.0)
            while self.frame_buffer and self.frame_buffer[0][0] < retention_cutoff:
                self.frame_buffer.popleft()

            # 2. Advance active post-recording tasks
            completed_tasks: List[VideoClipTask] = []
            for task in self.active_tasks:
                if task.state == "RECORDING_POST":
                    # If task has a session_id, ignore post-frames from a different session
                    if task.session_id is not None and session_id is not None and task.session_id != session_id:
                        continue
                    task.timed_frames.append((now, frame.copy(), sequence_id, session_id))

                    # Check if post-roll duration has completed
                    if now >= task.post_end_time:
                        task.state = "SAVING"
                        completed_tasks.append(task)

            # 3. Hand off completed tasks to background thread
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
        timestamp: Optional[float] = None
    ) -> Optional[str]:
        """
        Trigger an automated evidence clip recording.
        Cooldown key is multi-target: (session_id, source_id, track_id, violation_type).
        """
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
            incident_id = f"inc_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            detected_at = datetime.now(timezone.utc)

            logger.info(
                f"[AI_ENGINE] Incident triggered: {violation_type} [Track {track_key}] "
                f"(score: {confidence:.2f}) -> Capturing pre/post clip ({self.pre_roll_seconds}s / {self.post_roll_seconds}s)..."
            )

            # Extract pre-roll frames based on timestamp: [trigger_time - pre_roll_seconds, trigger_time]
            cutoff_time = trigger_time - self.pre_roll_seconds
            pre_frames = []
            for item in self.frame_buffer:
                t = item[0]
                f = item[1]
                seq = item[2] if len(item) > 2 else None
                sess = item[3] if len(item) > 3 else None
                if t >= cutoff_time:
                    # Do not mix buffers across sessions if session_id is specified
                    if session_id is not None and sess is not None and sess != session_id:
                        continue
                    pre_frames.append((t, f.copy(), seq, sess))

            task = VideoClipTask(
                incident_id=incident_id,
                source_id=source_id,
                track_id=track_id,
                violation_type=violation_type,
                confidence=confidence,
                level=level,
                pre_frames=pre_frames,
                post_end_time=trigger_time + self.post_roll_seconds,
                peak_frame=current_frame.copy() if (isinstance(current_frame, np.ndarray) and current_frame.size > 0) else None,
                detected_at=detected_at,
                target_fps=self.target_fps,
                proctor_notes=proctor_notes,
                session_id=session_id,
                trigger_time=trigger_time
            )
            self.active_tasks.append(task)
            return incident_id

    def _render_and_persist_clip(self, task: VideoClipTask):
        """
        Background Worker:
        1. Resamples frames along exact real-world time grid for 1.0x natural playback speed.
        2. Encodes MP4 using avc1 (fallback mp4v).
        3. Saves peak snapshot JPEG.
        4. Verifies file integrity (size > 0, valid OpenCV stream).
        5. Enqueues verified incident into DBWriteQueue.
        """
        try:
            if not task.timed_frames:
                logger.warning(f"[RING_BUFFER] Task {task.incident_id} has no frames, canceling export.")
                return

            video_filename = f"{task.incident_id}.mp4"
            snap_filename = f"{task.incident_id}_snap.jpg"
            video_path = os.path.join(EVIDENCE_DIR, video_filename)
            snap_path = os.path.join(EVIDENCE_DIR, snap_filename)

            # 2. Time boundaries using server monotonic timeline and server UTC wall-clock
            from datetime import timedelta
            t_start = task.timed_frames[0][0]
            t_end = task.timed_frames[-1][0]
            duration_real = max(0.1, t_end - t_start)
            
            pre_dur = max(0.0, (task.trigger_time or t_end) - t_start)
            clip_started_at = task.detected_at - timedelta(seconds=pre_dur)
            clip_ended_at = clip_started_at + timedelta(seconds=duration_real)

            # 1. Save Peak Snapshot Thumbnail
            if task.peak_frame is not None and task.peak_frame.size > 0:
                cv2.imwrite(snap_path, task.peak_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            elif task.timed_frames:
                mid_frame = task.timed_frames[len(task.timed_frames) // 2][1]
                cv2.imwrite(snap_path, mid_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

            h, w = task.timed_frames[0][1].shape[:2]
            target_fps = max(1.0, task.target_fps)

            # 3. Real-time Resampling along uniform time grid
            total_output_frames = max(1, int(round(duration_real * target_fps)))
            time_grid = np.linspace(t_start, t_end, total_output_frames)

            # Build timestamps array for nearest neighbor frame matching
            frame_times = np.array([tf[0] for tf in task.timed_frames])
            frame_images = [tf[1] for tf in task.timed_frames]

            # 4. Open VideoWriter (try avc1 first, fallback mp4v)
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

            # 5. Write resampled frames & compute duplicate metrics
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

            raw_seq_ids = [tf[2] for tf in task.timed_frames if len(tf) > 2 and tf[2] is not None]
            if raw_seq_ids:
                transport_unique = len(set(raw_seq_ids))
                transport_duplicate_ratio = max(0.0, 1.0 - (transport_unique / max(1, len(raw_seq_ids))))
            else:
                transport_duplicate_ratio = 0.0

            task.metrics = {
                "duration_real": duration_real,
                "total_output_frames": total_output_frames,
                "total_raw_frames": len(task.timed_frames),
                "unique_source_frames": unique_source_in_clip,
                "transport_duplicate_ratio": transport_duplicate_ratio,
                "output_repeated_frame_ratio": output_repeated_frame_ratio,
                "target_fps": target_fps
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
            proctor_notes = task.proctor_notes or (
                f"Phát hiện {task.violation_type} ({track_str}) với điểm tin cậy {task.confidence:.1f}%. "
                f"Clip bằng chứng trích xuất tự động ({duration_real:.1f}s thực tế, "
                f"{unique_source_in_clip} frames nguồn duy nhất)."
            )

            db_write_queue.enqueue_incident({
                "id": task.incident_id,
                "source_id": task.source_id,
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


# Global singleton instance
ring_buffer_service = VideoRingBuffer(
    pre_roll_seconds=5.0,
    post_roll_seconds=10.0,
    cooldown_seconds=6.0,
    target_fps=15.0
)
