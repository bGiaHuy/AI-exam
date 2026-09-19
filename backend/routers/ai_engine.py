"""
================================================================================
AI INFERENCE ENGINE ROUTER - AI EXAM CONTROL
================================================================================
Bridges V7 ExamBehaviorDetector with VideoRingBuffer and SQLite.
- Accepts raw frames via Base64.
- Runs YOLO11m Pose (ByteTrack) and YOLO Phone Detector.
- Triggers RingBuffer clip recording on confirmed violations (PHONE, HEAD_TURNING).
- Broadcasts real-time MJPEG live stream.
- Zero examinee identity handling.
================================================================================
"""

import os
import sys
import time
import base64
import uuid
import struct
import json
import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Generator, Tuple

# Ensure backend directory is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import cv2
import numpy as np
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False
import re
import math
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Incident
from schemas import (
    AIDetectionResult,
    FrameDetectionResponse,
    FrameDetectionRequest,
    SessionResetResponse,
    TestTriggerIncidentResponse,
    SessionTelemetryResponse
)
from services.ring_buffer import ring_buffer_service, EVIDENCE_DIR
from services.temporal_tracker import temporal_posture_tracker
from services.inference_worker import inference_buffer, inference_worker

logger = logging.getLogger("ai_engine")
router = APIRouter(tags=["AI Vision Engine"])
test_router = APIRouter(prefix="/test", tags=["Testing"])
deprecated_router = APIRouter(tags=["Deprecated Ingest"])

# Regex for source_id and session_id validation: alphanumeric, dash, underscore, dot (1..64 chars)
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")

# Strict Single-Session Lock (Sprint 1.2B)
_active_ws_session_id: Optional[str] = None
_session_mutex = threading.Lock()
_latest_session_telemetry: Optional[Dict[str, Any]] = None
_server_session_telemetry_history: Dict[str, Dict[str, Any]] = {}
_live_session_telemetry: Dict[str, Dict[str, Any]] = {}


def reset_ai_session_state(session_id: Optional[str] = None):
    """
    Hardened Session Isolation (Sprint 1.2A/1.2B):
    Resets all ephemeral runtime state for a session to prevent state leakage:
    1. Resets ExamBehaviorDetector (AdaptiveMonitor baseline, EMA keypoint smoothers).
    2. Resets Ultralytics YOLO ByteTracker so track IDs restart cleanly from 1.
    3. Resets TemporalPostureTracker state for the given session.
    4. Discards any waiting frame and resets counters in SingleSlotInferenceBuffer for this session.
    5. Discards any buffered frames and active tasks in RingBuffer for this session.
    """
    global detector
    if detector is not None:
        try:
            detector.reset()
            logger.info("[SESSION_ISOLATION] Reset ExamBehaviorDetector monitor baseline & smoothers.")
        except Exception as e:
            logger.warning(f"[SESSION_ISOLATION] detector.reset() error: {e}")

        try:
            if hasattr(detector, "pose_model") and hasattr(detector.pose_model, "predictor") and detector.pose_model.predictor:
                trackers = getattr(detector.pose_model.predictor, "trackers", [])
                for trk in trackers:
                    if hasattr(trk, "reset"):
                        trk.reset()
                        logger.info("[SESSION_ISOLATION] Reset Ultralytics BYTETracker state.")
        except Exception as e:
            logger.warning(f"[SESSION_ISOLATION] ByteTracker reset error: {e}")

    if session_id:
        temporal_posture_tracker.reset_session(session_id)
        inference_buffer.reset_session(session_id)
        ring_buffer_service.reset_session(session_id)
    else:
        temporal_posture_tracker.clear()
        inference_buffer.reset_session(None)

    logger.info(f"[SESSION_ISOLATION] Successfully completed state isolation for session={session_id}")


@router.post("/session/reset", response_model=SessionResetResponse)
def api_reset_session(session_id: Optional[str] = None):
    """Explicitly reset and isolate AI session state for the active session."""
    global _active_ws_session_id
    with _session_mutex:
        if session_id and _active_ws_session_id and session_id != _active_ws_session_id:
            logger.warning(f"[SESSION_RESET] Reject reset for inactive session '{session_id}'; active is '{_active_ws_session_id}'")
            return SessionResetResponse(
                status="IGNORED",
                reset_session=session_id,
                message=f"Session '{session_id}' is not the currently active session ('{_active_ws_session_id}')"
            )
        target = session_id if session_id else (_active_ws_session_id or "all")
        reset_ai_session_state(target)
        if _active_ws_session_id == target or target == "all":
            _active_ws_session_id = None
        return SessionResetResponse(
            status="SUCCESS",
            reset_session=target,
            message=f"Session {target} state reset successfully"
        )

# Resolve model paths: check both model/ and model/weights/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
if MODEL_DIR not in sys.path:
    sys.path.insert(0, MODEL_DIR)


def resolve_model_path(filename: str) -> str:
    """Check model directory first, then model/weights/."""
    direct_path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(direct_path):
        return direct_path
    weights_path = os.path.join(MODEL_DIR, "weights", filename)
    if os.path.exists(weights_path):
        return weights_path
    return direct_path


PHONE_WEIGHTS = resolve_model_path("phone_detector_v5.pt")
POSE_WEIGHTS = resolve_model_path("yolo11m-pose.pt")

detector = None
last_frame_fps = 20.0
latest_processed_frame: Optional[np.ndarray] = None

# Real-time telemetry trackers: distinct acquisition vs inference vs output
_last_frame_timestamp_by_source: Dict[str, float] = {}
_last_observed_fps_by_source: Dict[str, float] = {}

# Per-track temporal tracker for posture: (source_id, track_id) -> state
_posture_temporal_tracker: Dict[Tuple[str, int], Dict[str, Any]] = {}


def update_detector_settings(phone_conf: float, suspicion_threshold: float, alert_seconds: float):
    """Synchronize runtime parameters on active ExamBehaviorDetector."""
    global detector
    if detector is not None:
        detector.phone_conf = phone_conf
        if hasattr(detector, "monitor"):
            detector.monitor.suspicion_threshold = suspicion_threshold
            detector.monitor.alert_seconds = alert_seconds
        logger.info(
            f"[AI_ENGINE] Runtime settings applied: phone_conf={phone_conf}, "
            f"suspicion={suspicion_threshold}, alert_sec={alert_seconds}"
        )


def get_detector():
    global detector
    if detector is None:
        try:
            from exam_analyzer import ExamBehaviorDetector
            from routers.settings import load_settings
            current_cfg = load_settings()
            logger.info(f"[AI ENGINE] Loading models: Pose={POSE_WEIGHTS}, Phone={PHONE_WEIGHTS}")
            detector = ExamBehaviorDetector(
                phone_model_path=PHONE_WEIGHTS,
                pose_model_path=POSE_WEIGHTS,
                phone_conf=current_cfg.phone_confidence,
                suspicion_threshold=current_cfg.suspicion_threshold,
                alert_seconds=current_cfg.posture_alert_seconds
            )
            print(f"[AI ENGINE] Successfully loaded ExamBehaviorDetector with YOLO Pose & Phone weights.", flush=True)
        except Exception as e:
            logger.error(f"[AI ENGINE] WARNING: Không thể tải ExamBehaviorDetector: {e}", exc_info=True)
            detector = None
    return detector


legacy_clips_router = APIRouter(tags=["legacy-clips"])

@legacy_clips_router.get(
    "/clips/{filename}",
    deprecated=True,
    summary="[DEPRECATED] Legacy clip endpoint (Canonical route is static mount /evidence/{filename})"
)
def get_clip_file(filename: str):
    """
    [DEPRECATED]: Phục vụ file video clip bằng chứng cho tính tương thích ngược cũ.
    Mặc định tắt trong chế độ sản xuất (ENABLE_LEGACY_CLIPS=false).
    Canonical route chính thức là /evidence/{filename}.
    Bảo vệ an toàn chống path traversal qua os.path.basename.
    """
    clean_filename = os.path.basename(filename)
    clip_path = os.path.join(EVIDENCE_DIR, clean_filename)
    if not os.path.exists(clip_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy video clip")
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        headers={"X-API-Deprecation": "This endpoint is deprecated. Use /evidence/{filename} instead."}
    )


@router.get("/status")
def get_ai_status(db: Session = Depends(get_db)):
    """
    Kiểm tra trạng thái online của hệ thống AI và CSDL SQLite.
    Báo cáo rõ ràng:
      - inference_fps: Tốc độ xử lý của mô hình AI (1 / thời gian chạy).
      - observed_acquisition_fps: Tốc độ nhận frame thực tế từ client (1 / khoảng cách thời gian giữa 2 frame).
      - output_video_fps: Tốc độ khung hình của video bằng chứng (RingBuffer container).
    """
    if TORCH_AVAILABLE and torch.cuda.is_available():
        device = "CUDA GPU (" + torch.cuda.get_device_name(0) + ")"
    else:
        device = "CPU"
    total_incidents = db.query(Incident).count()

    observed_fps = None
    if _last_observed_fps_by_source:
        observed_fps = round(sum(_last_observed_fps_by_source.values()) / len(_last_observed_fps_by_source), 1)

    return {
        "status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device": device,
        "inference_fps": round(last_frame_fps, 1),
        "observed_acquisition_fps": observed_fps,
        "output_video_fps": ring_buffer_service.target_fps,
        "active_models": {
            "pose_estimator": "yolo11m-pose.pt (COCO 17 Keypoints)",
            "phone_detector": "phone_detector_v5.pt"
        },
        "total_session_incidents": total_incidents,
        "database_connected": True,
        "ring_buffer_state": ring_buffer_service.current_state,
        "inference_queue_stats": inference_buffer.get_stats()
    }


def generate_mjpeg_stream() -> Generator[bytes, None, None]:
    """
    Generator phát luồng video MJPEG multipart frames.
    """
    global latest_processed_frame
    while True:
        frame = latest_processed_frame
        if frame is None:
            # Standby blank frame with timestamp
            frame = np.zeros((360, 640, 3), dtype=np.uint8)
            now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            cv2.putText(
                frame,
                f"EXAM AI STREAM STANDBY - {now_str}",
                (40, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (100, 200, 100),
                2
            )

        success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if success:
            frame_bytes = buffer.tobytes()
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.05)  # ~20 FPS


@router.websocket("/ws/ingest")
async def websocket_ingest(
    websocket: WebSocket,
    source_id: str = "webcam_local",
    session_id: Optional[str] = None
):
    """
    Primary High-Density Binary Ingestion Pipeline (Sprint 1.2A Hardened):
    - Strict validation of source_id and session_id.
    - Strict packet validation: minimum 20 bytes (16B header + 4B JPEG), max 3MB.
    - Sequence integrity: reject negative seq_id, detect duplicates, out-of-order, gaps.
    - Timestamp sanity: reject non-finite (NaN, inf) or <= 0 timestamps.
    - Thread-safe result handoff with client disconnect detection.
    - Full session isolation: clean reset on connect and disconnect.
    """
    # 1. Validate query parameters
    if not source_id or not ID_PATTERN.match(source_id):
        logger.warning(f"[WS_INGEST] Rejected invalid source_id: '{source_id}'")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid source_id (must match ^[a-zA-Z0-9_\\-\\.]{1,64}$)")
        return

    active_session_id = session_id or f"sess_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
    if not ID_PATTERN.match(active_session_id):
        logger.warning(f"[WS_INGEST] Rejected invalid session_id: '{active_session_id}'")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session_id (must match ^[a-zA-Z0-9_\\-\\.]{1,64}$)")
        return

    # 2. Strict Single-Session Lock (Sprint 1.2B)
    is_current_session_owner = False
    with _session_mutex:
        global _active_ws_session_id
        if _active_ws_session_id is not None:
            logger.warning(f"[WS_INGEST] Rejected concurrent session '{active_session_id}': Active session is '{_active_ws_session_id}'")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Another ingestion session is currently active")
            return
        _active_ws_session_id = active_session_id
        is_current_session_owner = True

    await websocket.accept()
    loop = asyncio.get_running_loop()
    is_session_active = True
    reset_ai_session_state(active_session_id)
    logger.info(f"[WS_INGEST] Client connected: source={source_id}, session={active_session_id}")

    server_packets_received = 0
    server_frames_decoded = 0
    first_server_mono: Optional[float] = None
    last_server_mono: Optional[float] = None
    arrival_intervals_sec: List[float] = []
    gaps_gt_100ms = 0
    gaps_gt_250ms = 0

    def on_inference_result(payload: Dict[str, Any]):
        if not is_session_active or loop.is_closed():
            return
        if payload.get("session_id") != active_session_id:
            return
        try:
            stats = inference_buffer.get_session_stats(active_session_id)
            inference_buffer.record_result_sent(active_session_id)
            stats["results_sent"] += 1

            payload["server_packets_received"] = server_packets_received
            payload["server_frames_decoded"] = server_frames_decoded
            payload["server_received_frames"] = server_frames_decoded
            payload["inference_submitted_frames"] = stats["submitted"]
            payload["inference_superseded_frames"] = stats["superseded"]
            payload["inference_processed_frames"] = stats["processed"]
            payload["processed_inference_frames"] = stats["processed"]
            payload["inference_pending_frames"] = stats["pending"]
            payload["pending_inference_frames"] = stats["pending"]
            payload["result_messages_sent"] = stats["results_sent"]
            payload["detection_results_sent"] = stats["results_sent"]
            payload["detected_objects"] = stats["detected_objects"]
            payload["first_decoded_monotonic"] = first_server_mono
            payload["last_decoded_monotonic"] = last_server_mono

            if first_server_mono is not None and last_server_mono is not None and server_frames_decoded > 1:
                dur_mono = last_server_mono - first_server_mono
                if dur_mono > 0.001:
                    payload["effective_acquisition_fps"] = round((server_frames_decoded - 1) / dur_mono, 2)

            msg_str = json.dumps(payload)
            async def _safe_send():
                try:
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_text(msg_str)
                except Exception:
                    pass
            asyncio.run_coroutine_threadsafe(_safe_send(), loop)
        except Exception as err:
            logger.debug(f"[WS_INGEST] Failed to dispatch inference result: {err}")

    last_seq_id = -1
    t_last_frame = time.time()

    try:
        while True:
            data = await websocket.receive_bytes()
            server_packets_received += 1

            # Packet size guard: minimum 20 bytes (16B header + >=4B JPEG), max 3MB
            if len(data) < 20:
                logger.warning(f"[WS_INGEST] Dropped undersized payload: len={len(data)} < 20 bytes")
                continue
            if len(data) > 3 * 1024 * 1024:
                logger.warning(f"[WS_INGEST] Dropped oversized payload: len={len(data)} > 3MB")
                continue

            # Strict 16-byte header extraction
            try:
                seq_id, mono_ts = struct.unpack(">qd", data[:16])
            except Exception as unpack_err:
                logger.warning(f"[WS_INGEST] Failed to unpack 16-byte header: {unpack_err}")
                continue

            # Reject negative sequence ID
            if seq_id < 0:
                logger.warning(f"[WS_INGEST] Rejected negative sequence_id: {seq_id}")
                continue

            # Reject invalid timestamp
            if math.isnan(mono_ts) or math.isinf(mono_ts) or mono_ts <= 0:
                logger.warning(f"[WS_INGEST] Rejected invalid timestamp: {mono_ts}")
                continue

            # Sequence duplicate and ordering check
            if last_seq_id >= 0:
                if seq_id <= last_seq_id:
                    logger.warning(f"[WS_INGEST] Duplicate or out-of-order sequence: seq={seq_id} <= last={last_seq_id}")
                    continue
                elif seq_id > last_seq_id + 1:
                    gap = seq_id - last_seq_id - 1
                    logger.info(f"[WS_INGEST] Transport frame gap detected: missed {gap} frame(s) between {last_seq_id} and {seq_id}")
            last_seq_id = seq_id

            jpeg_bytes = data[16:]
            # Validate JPEG SOI marker
            if len(jpeg_bytes) < 4 or jpeg_bytes[:2] != b'\xff\xd8':
                logger.warning("[WS_INGEST] Malformed JPEG payload (invalid SOI marker)")
                continue

            # Decode JPEG
            frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None or frame.size == 0:
                logger.warning("[WS_INGEST] cv2.imdecode returned empty frame")
                continue

            # Telemetry tracking & Server-side monotonic clock
            server_frames_decoded += 1
            server_received_monotonic = time.monotonic()

            if first_server_mono is None:
                first_server_mono = server_received_monotonic
            else:
                dt_arr = server_received_monotonic - last_server_mono
                arrival_intervals_sec.append(dt_arr)
                if dt_arr > 0.100:
                    gaps_gt_100ms += 1
                if dt_arr > 0.250:
                    gaps_gt_250ms += 1
            last_server_mono = server_received_monotonic

            now = time.time()
            dt = now - t_last_frame
            t_last_frame = now
            if dt > 0.001:
                _last_observed_fps_by_source[source_id] = round(1.0 / dt, 1)

            global latest_processed_frame
            latest_processed_frame = frame

            # Keep live telemetry record updated for target_session
            _live_session_telemetry[active_session_id] = {
                "session_id": active_session_id,
                "source_id": source_id,
                "server_packets_received": server_packets_received,
                "server_frames_decoded": server_frames_decoded,
                "first_decoded_monotonic": first_server_mono,
                "last_decoded_monotonic": last_server_mono,
                "arrival_intervals_sec": arrival_intervals_sec,
                "gaps_gt_100ms": gaps_gt_100ms,
                "gaps_gt_250ms": gaps_gt_250ms,
            }

            # 🔴 PIPELINE 1: RECORDING (RingBuffer) - Immediate non-blocking push using server monotonic clock
            ring_buffer_service.push_frame(
                frame=frame,
                timestamp=server_received_monotonic,
                sequence_id=seq_id,
                session_id=active_session_id
            )

            # 🟡 PIPELINE 2: INFERENCE (Single-Slot Zero-Backlog Buffer) using server monotonic clock
            inference_buffer.push_latest(
                source_id=source_id,
                session_id=active_session_id,
                sequence_id=seq_id,
                timestamp=server_received_monotonic,
                frame=frame,
                callback=on_inference_result
            )

    except WebSocketDisconnect:
        logger.info(f"[WS_INGEST] Client disconnected normally: source={source_id}, session={active_session_id}")
    except Exception as e:
        logger.warning(f"[WS_INGEST] WebSocket session ended with exception: {e}")
    finally:
        if is_current_session_owner:
            is_session_active = False

            # Compile session telemetry summary with full invariant verification
            global _latest_session_telemetry
            dur_mono = (last_server_mono - first_server_mono) if (first_server_mono and last_server_mono) else 0.0
            eff_fps = round((server_frames_decoded - 1) / dur_mono, 2) if (dur_mono > 0.001 and server_frames_decoded > 1) else 0.0
            intervals_ms = [d * 1000.0 for d in arrival_intervals_sec]
            p50 = 0.0
            p95 = 0.0
            max_int = 0.0
            if intervals_ms:
                sorted_int = sorted(intervals_ms)
                p50 = round(sorted_int[int(len(sorted_int) * 0.50)], 1)
                p95 = round(sorted_int[min(len(sorted_int) - 1, int(len(sorted_int) * 0.95))], 1)
                max_int = round(sorted_int[-1], 1)

            final_stats = inference_buffer.get_session_stats(active_session_id)
            inv_i4 = (server_frames_decoded <= server_packets_received)
            inv_i5 = (final_stats["submitted"] <= server_frames_decoded)
            inv_i6 = (final_stats["processed"] + final_stats["superseded"] + final_stats["pending"] == final_stats["submitted"])
            inv_i7 = (final_stats["results_sent"] <= final_stats["processed"])

            fps_calc = {
                "formula": "(server_frames_decoded - 1) / (last_decoded_monotonic - first_decoded_monotonic)",
                "server_frames_decoded": server_frames_decoded,
                "numerator": max(0, server_frames_decoded - 1),
                "first_decoded_monotonic": first_server_mono,
                "last_decoded_monotonic": last_server_mono,
                "duration_seconds": round(dur_mono, 4),
                "effective_fps": eff_fps
            }

            _latest_session_telemetry = {
                "session_id": active_session_id,
                "source_id": source_id,
                "server_packets_received": server_packets_received,
                "server_frames_decoded": server_frames_decoded,
                "server_received_frames": server_frames_decoded,
                "duration_seconds": round(dur_mono, 2),
                "effective_acquisition_fps": eff_fps,
                "first_decoded_monotonic": first_server_mono,
                "last_decoded_monotonic": last_server_mono,
                "fps_calculation": fps_calc,
                "interval_p50_ms": p50,
                "interval_p95_ms": p95,
                "interval_max_ms": max_int,
                "gaps_gt_100ms": gaps_gt_100ms,
                "gaps_gt_250ms": gaps_gt_250ms,
                "inference_submitted_frames": final_stats["submitted"],
                "inference_superseded_frames": final_stats["superseded"],
                "inference_processed_frames": final_stats["processed"],
                "processed_inference_frames": final_stats["processed"],
                "inference_pending_frames": final_stats["pending"],
                "pending_inference_frames": final_stats["pending"],
                "result_messages_sent": final_stats["results_sent"],
                "detection_results_sent": final_stats["results_sent"],
                "detected_objects": final_stats["detected_objects"],
                "invariants": {
                    "inv_i4_server_frames_decoded_le_packets_received": inv_i4,
                    "inv_i5_inference_submitted_le_frames_decoded": inv_i5,
                    "inv_i6_balance_processed_superseded_pending_eq_submitted": inv_i6,
                    "inv_i7_result_messages_sent_le_processed": inv_i7,
                    "balance": inv_i6,
                    "balance_check": inv_i6,
                    "submitted_le_received": inv_i5,
                    "submitted_le_received_check": inv_i5,
                    "sent_le_processed_check": inv_i7,
                    "results_sent_le_processed": inv_i7
                }
            }
            _server_session_telemetry_history[active_session_id] = _latest_session_telemetry
            logger.info(f"[WS_INGEST] Session Telemetry Summary: {_latest_session_telemetry}")

            with _session_mutex:
                if _active_ws_session_id == active_session_id:
                    _active_ws_session_id = None
            reset_ai_session_state(active_session_id)
            logger.info(f"[WS_INGEST] Cleaned up active session resources: session={active_session_id}")




@router.get("/stream")
def mjpeg_video_stream():
    """
    Endpoint phát luồng video MJPEG thời gian thực (/api/stream).
    Cho phép thẻ <img> trên frontend xem trực tiếp camera AI stream.
    """
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@deprecated_router.post(
    "/detect/frame",
    response_model=FrameDetectionResponse,
    deprecated=True,
    summary="[DEPRECATED] Single Frame Base64 Ingestion (Use WebSocket /ws/ingest for 15 FPS pipeline)"
)
def detect_frame(payload: FrameDetectionRequest):
    """
    [DEPRECATED in Sprint 1.2]: Thay thế bằng WebSocket Binary Ingestion (/api/ws/ingest)
    để đạt chuẩn 15 FPS ghi bằng chứng độc lập với tốc độ suy luận AI.
    Endpoint HTTP POST này giữ lại duy nhất cho tương thích ngược nếu cần.
    """
    global last_frame_fps, latest_processed_frame
    start_time = time.time()

    # 1. Decode Base64 image
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Không thể decode frame từ chuỗi Base64")
    except Exception as e:
        return FrameDetectionResponse(
            success=False,
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            detections=[],
            has_cheating=False,
            has_phone=False,
            total_detections=0,
            error=str(e)
        )

    h, w = frame.shape[:2]
    source_id = payload.source_id or "webcam_local"
    frame_timestamp = payload.timestamp if payload.timestamp is not None else start_time

    # 2. Measure real inter-frame acquisition interval
    observed_acq_fps = None
    last_t = _last_frame_timestamp_by_source.get(source_id)
    if last_t is not None and frame_timestamp > last_t:
        delta_t = frame_timestamp - last_t
        if delta_t > 0.001:
            observed_acq_fps = round(1.0 / delta_t, 2)
            _last_observed_fps_by_source[source_id] = observed_acq_fps
    _last_frame_timestamp_by_source[source_id] = frame_timestamp

    # 3. Feed raw frame into RingBuffer with verified frame timestamp
    ring_buffer_service.push_frame(frame, timestamp=frame_timestamp)

    det_engine = get_detector()
    if det_engine is None:
        latest_processed_frame = frame
        return FrameDetectionResponse(
            success=False,
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            detections=[],
            has_cheating=False,
            has_phone=False,
            total_detections=0,
            error="Model chưa được nạp",
            observed_acquisition_fps=observed_acq_fps,
            inference_fps=None
        )

    # 4. Process frame with ExamBehaviorDetector
    effective_fps = max(1, int(round(observed_acq_fps or 20.0)))
    try:
        annotated_frame, alerts = det_engine.process_frame(frame, fps=effective_fps, draw=True)
        latest_processed_frame = annotated_frame if annotated_frame is not None else frame
    except Exception as e:
        logger.error(f"[AI_ENGINE] Lỗi suy luận: {e}", exc_info=True)
        latest_processed_frame = frame
        return FrameDetectionResponse(
            success=False,
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S"),
            detections=[],
            has_cheating=False,
            has_phone=False,
            total_detections=0,
            error=f"Lỗi suy luận: {str(e)}",
            observed_acquisition_fps=observed_acq_fps,
            inference_fps=None
        )

    inf_elapsed = time.time() - start_time
    inference_fps = round(1.0 / inf_elapsed, 2) if inf_elapsed > 0 else 30.0
    last_frame_fps = inference_fps

    # 5. Format Bounding Boxes & Apply Real-Time Temporal Rule with Continuity Guard
    from routers.settings import load_settings
    current_cfg = load_settings()
    suspicion_threshold = current_cfg.suspicion_threshold
    posture_alert_seconds = current_cfg.posture_alert_seconds

    detections: List[AIDetectionResult] = []
    has_cheating = False
    has_phone = False
    red_alerts_to_trigger = []

    for alert in alerts:
        box = alert.get("box")
        tid = alert.get("track_id")
        raw_status = alert.get("status_code", "NORMAL")
        score = alert.get("score", 0.0)
        turn_deg = alert.get("turn_deg", 0.0)

        if not box or len(box) < 4:
            continue

        x1, y1, x2, y2 = box
        left_pct = max(0.0, min(100.0, (x1 / w) * 100.0))
        top_pct = max(0.0, min(100.0, (y1 / h) * 100.0))
        w_pct = max(1.0, min(100.0 - left_pct, ((x2 - x1) / w) * 100.0))
        h_pct = max(1.0, min(100.0 - top_pct, ((y2 - y1) / h) * 100.0))

        if w_pct > 75.0 and h_pct > 75.0:
            continue

        if raw_status == "CHEATING_PHONE":
            has_phone = True
            has_cheating = True
            level = "red"
            label = "PHONE"
            label_vi = f"Điện thoại [Track {tid}]"
            conf = round(float(min(99.0, max(85.0, score * 100.0))), 1)
            red_alerts_to_trigger.append(("PHONE", conf, tid))
        else:
            # Posture temporal analysis with Continuity Guard
            is_instant_suspicious = (score >= suspicion_threshold) or (raw_status in ("SUSPICIOUS", "CHEATING_POSTURE"))
            posture_status, posture_level, elapsed_duration = temporal_posture_tracker.update(
                source_id=source_id,
                track_id=tid if tid is not None else 0,
                is_suspicious=is_instant_suspicious,
                timestamp=frame_timestamp,
                alert_seconds=posture_alert_seconds
            )

            if posture_level == "red":
                has_cheating = True
                level = "red"
                label = "HEAD_TURNING"
                label_vi = f"Quay đầu {elapsed_duration:.1f}s >= {posture_alert_seconds:.1f}s [Track {tid}]"
                conf = round(float(min(98.0, max(80.0, score * 100.0))), 1)
                red_alerts_to_trigger.append(("HEAD_TURNING", conf, tid))
            elif posture_level == "yellow":
                level = "yellow"
                label = "HEAD_TURNING"
                label_vi = f"Nghi vấn quay đầu {int(turn_deg)}° ({elapsed_duration:.1f}s/{posture_alert_seconds:.1f}s) [Track {tid}]"
                conf = round(float(min(90.0, max(60.0, score * 100.0))), 1)
            else:
                level = "green"
                label = "NORMAL"
                label_vi = f"Bình thường [Track {tid}]"
                conf = round(float(min(98.0, max(80.0, (1.0 - score) * 100.0))), 1)

        detections.append(AIDetectionResult(
            id=f"det_{tid}_{int(frame_timestamp*1000)}",
            label=label,
            label_vi=label_vi,
            confidence=conf,
            bbox=[round(left_pct, 2), round(top_pct, 2), round(w_pct, 2), round(h_pct, 2)],
            level=level,
            raw_coords=[int(x1), int(y1), int(x2), int(y2)],
            track_id=tid
        ))

    # 6. Trigger VideoRingBuffer clip recording ONLY on confirmed RED violations
    new_incident = None
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

    if red_alerts_to_trigger:
        vtype, conf_val, p_tid = red_alerts_to_trigger[0]

        # Trigger RingBuffer with multi-target cooldown (source_id, track_id, violation_type)
        inc_id = ring_buffer_service.trigger_incident(
            violation_type=vtype,
            confidence=conf_val,
            source_id=source_id,
            track_id=p_tid,
            current_frame=frame,
            level="red"
        )

        if inc_id:
            new_incident = {
                "id": inc_id,
                "source_id": source_id,
                "track_id": p_tid,
                "timestamp": now_str,
                "violation_type": vtype,
                "confidence": conf_val,
                "level": "red",
                "video_path": f"/evidence/{inc_id}.mp4",
                "snapshot_path": f"/evidence/{inc_id}_snap.jpg"
            }

    return FrameDetectionResponse(
        success=True,
        timestamp=now_str,
        detections=detections,
        has_cheating=has_cheating,
        has_phone=has_phone,
        new_incident=new_incident,
        total_detections=len(detections)
    )


@test_router.post("/trigger_incident", response_model=TestTriggerIncidentResponse)
def trigger_test_incident(
    violation_type: str = "PHONE",
    confidence: float = 0.95,
    source_id: str = "webcam_local"
):
    """
    Endpoint kích hoạt thử nghiệm sự cố vi phạm (phục vụ Browser E2E & Validation).
    Chỉ được mount khi ENABLE_TEST_ENDPOINTS=true hoặc ENVIRONMENT=test.
    Tự động gắn vào session WebSocket đang hoạt động để RingBuffer xuất clip từ frame client thực tế.
    """
    with _session_mutex:
        active_sess = _active_ws_session_id

    # Canonical violation type and confidence normalization
    vtype_norm = "HEAD_TURNING" if violation_type.upper() in ("HEAD_TURNING", "CHEATING_POSTURE") else "PHONE"
    conf_norm = confidence if confidence <= 1.0 else confidence / 100.0

    inc_id = ring_buffer_service.trigger_incident(
        violation_type=vtype_norm,
        confidence=conf_norm,
        source_id=source_id,
        track_id=101,
        current_frame=latest_processed_frame,
        level="red",
        session_id=active_sess,
        timestamp=time.monotonic()
    )
    return TestTriggerIncidentResponse(
        status="SUCCESS" if inc_id else "COOLDOWN_ACTIVE",
        incident_id=inc_id,
        session_id=active_sess
    )


@router.get("/session/telemetry", response_model=SessionTelemetryResponse)
def get_session_telemetry(session_id: Optional[str] = None):
    """
    Endpoint truy xuất báo cáo telemetry và kiểm tra các bất biến (invariants) của phiên gần nhất/đang chạy.
    """
    global _latest_session_telemetry
    target_session = session_id
    if target_session is None:
        with _session_mutex:
            target_session = _active_ws_session_id
        if target_session is None and _latest_session_telemetry is not None:
            target_session = _latest_session_telemetry.get("session_id")

    # 1. Historical completed session lookup
    if target_session and target_session in _server_session_telemetry_history:
        return _server_session_telemetry_history[target_session]

    # 2. Live active session lookup
    if target_session and (inference_buffer.has_session(target_session) or target_session in _live_session_telemetry):
        live_info = _live_session_telemetry.get(target_session, {})
        packets_recv = live_info.get("server_packets_received", 0)
        frames_dec = live_info.get("server_frames_decoded", 0)
        first_mono = live_info.get("first_decoded_monotonic")
        last_mono = live_info.get("last_decoded_monotonic")
        intervals_sec = live_info.get("arrival_intervals_sec", [])
        gaps_100 = live_info.get("gaps_gt_100ms", 0)
        gaps_250 = live_info.get("gaps_gt_250ms", 0)
        source_id = live_info.get("source_id", "live_session")

        stats = inference_buffer.get_session_stats(target_session)
        # Fallback if frames were submitted directly in tests without websocket
        if frames_dec == 0 and stats["submitted"] > 0:
            frames_dec = stats["submitted"]
            packets_recv = max(packets_recv, frames_dec)

        dur_mono = (last_mono - first_mono) if (first_mono and last_mono) else 0.0
        eff_fps = round((frames_dec - 1) / dur_mono, 2) if (dur_mono > 0.001 and frames_dec > 1) else 0.0

        intervals_ms = [d * 1000.0 for d in intervals_sec]
        p50 = 0.0
        p95 = 0.0
        max_int = 0.0
        if intervals_ms:
            sorted_int = sorted(intervals_ms)
            p50 = round(sorted_int[int(len(sorted_int) * 0.50)], 1)
            p95 = round(sorted_int[min(len(sorted_int) - 1, int(len(sorted_int) * 0.95))], 1)
            max_int = round(sorted_int[-1], 1)

        inv_i4 = (frames_dec <= packets_recv)
        inv_i5 = (stats["submitted"] <= frames_dec)
        inv_i6 = (stats["processed"] + stats["superseded"] + stats["pending"] == stats["submitted"])
        inv_i7 = (stats["results_sent"] <= stats["processed"])

        fps_calc = {
            "formula": "(server_frames_decoded - 1) / (last_decoded_monotonic - first_decoded_monotonic)",
            "server_frames_decoded": frames_dec,
            "numerator": max(0, frames_dec - 1),
            "first_decoded_monotonic": first_mono,
            "last_decoded_monotonic": last_mono,
            "duration_seconds": round(dur_mono, 4),
            "effective_fps": eff_fps
        }

        return {
            "session_id": target_session,
            "source_id": source_id,
            "server_packets_received": packets_recv,
            "server_frames_decoded": frames_dec,
            "server_received_frames": frames_dec,
            "duration_seconds": round(dur_mono, 2),
            "effective_acquisition_fps": eff_fps,
            "first_decoded_monotonic": first_mono,
            "last_decoded_monotonic": last_mono,
            "fps_calculation": fps_calc,
            "interval_p50_ms": p50,
            "interval_p95_ms": p95,
            "interval_max_ms": max_int,
            "gaps_gt_100ms": gaps_100,
            "gaps_gt_250ms": gaps_250,
            "inference_submitted_frames": stats["submitted"],
            "inference_superseded_frames": stats["superseded"],
            "inference_processed_frames": stats["processed"],
            "processed_inference_frames": stats["processed"],
            "inference_pending_frames": stats["pending"],
            "pending_inference_frames": stats["pending"],
            "result_messages_sent": stats["results_sent"],
            "detection_results_sent": stats["results_sent"],
            "detected_objects": stats["detected_objects"],
            "invariants": {
                "inv_i4_server_frames_decoded_le_packets_received": inv_i4,
                "inv_i5_inference_submitted_le_frames_decoded": inv_i5,
                "inv_i6_balance_processed_superseded_pending_eq_submitted": inv_i6,
                "inv_i7_result_messages_sent_le_processed": inv_i7,
                "balance": inv_i6,
                "balance_check": inv_i6,
                "submitted_le_received": inv_i5,
                "submitted_le_received_check": inv_i5,
                "sent_le_processed_check": inv_i7,
                "results_sent_le_processed": inv_i7
            }
        }

    # 3. Fallback to latest session telemetry
    if _latest_session_telemetry is not None:
        if session_id is None or _latest_session_telemetry.get("session_id") == session_id:
            return _latest_session_telemetry

    raise HTTPException(status_code=404, detail="No session telemetry recorded yet for requested session")



