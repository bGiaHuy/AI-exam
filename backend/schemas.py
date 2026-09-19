"""
================================================================================
PYDANTIC V2 SCHEMAS - AI EXAM CONTROL
================================================================================
Strict validation models for vision violations, incidents, and AI settings.
Zero identity fields (no examinee personal information).
================================================================================
"""

import math
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. INCIDENT SCHEMAS
# ==============================================================================
class IncidentResponse(BaseModel):
    id: str
    source_id: str
    track_id: Optional[int] = None
    violation_type: Literal["PHONE", "HEAD_TURNING"]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Độ tin cậy chuẩn hóa (raw probability 0.0 - 1.0)")
    level: Literal["yellow", "red"]
    detected_at: datetime
    clip_started_at: Optional[datetime] = None
    clip_ended_at: Optional[datetime] = None
    video_path: Optional[str] = None
    snapshot_path: Optional[str] = None
    status: Literal["pending", "confirmed", "dismissed"]
    proctor_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("violation_type", mode="before")
    @classmethod
    def normalize_violation_type(cls, v: Any) -> str:
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in ("CHEATING_POSTURE", "HEAD_TURN", "TURNING_HEAD"):
                return "HEAD_TURNING"
            return v_upper
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v: Any) -> float:
        if v is None:
            return 0.0
        val = float(v)
        if math.isnan(val) or math.isinf(val):
            raise ValueError("Confidence cannot be NaN or Infinite")
        if val < 0.0:
            raise ValueError("Confidence cannot be negative")
        # Legacy database records may store percentage e.g. 93.5 or 88.0.
        # Canonical representation in API is raw probability 0.0 - 1.0.
        if val > 1.0:
            if val <= 100.0:
                return round(val / 100.0, 4)
            raise ValueError("Confidence cannot exceed 1.0 (or 100.0%)")
        return round(val, 4)


class IncidentConfirmRequest(BaseModel):
    status: Literal["confirmed", "dismissed", "pending"] = Field("confirmed", description="Trạng thái xác nhận của giám thị")
    notes: Optional[str] = Field(None, description="Ghi chú nghiệp vụ của giám thị")


# ==============================================================================
# 2. AI SETTINGS SCHEMA
# ==============================================================================
class AISettingsSchema(BaseModel):
    phone_confidence: float = Field(0.35, ge=0.1, le=1.0, description="Ngưỡng tin cậy phát hiện điện thoại (raw probability 0.1 - 1.0)")
    posture_alert_seconds: float = Field(1.25, ge=0.5, le=5.0, description="Thời gian duy trì quay đầu để kích hoạt cờ Đỏ (giây)")
    suspicion_threshold: float = Field(0.50, ge=0.1, le=1.0, description="Ngưỡng điểm nghi vấn tư thế chuẩn hóa kích hoạt cờ Vàng (không thứ nguyên [0.0 - 1.0])")
    pre_roll_seconds: float = Field(5.0, ge=1.0, le=10.0, description="Thời lượng video trước thời điểm vi phạm (giây)")
    post_roll_seconds: float = Field(10.0, ge=1.0, le=20.0, description="Thời lượng video sau thời điểm vi phạm (giây)")
    cooldown_seconds: float = Field(6.0, ge=1.0, le=30.0, description="Thời gian giãn cách chống tạo clip trùng (giây)")



# ==============================================================================
# 3. AI DETECTION & INFERENCE SCHEMAS
# ==============================================================================
class AIDetectionResult(BaseModel):
    id: str
    label: str
    label_vi: str
    confidence: float
    bbox: List[float]  # [left%, top%, width%, height%]
    level: Literal["red", "yellow", "green"]
    raw_coords: Optional[List[int]] = None
    track_id: Optional[int] = None


class FrameDetectionRequest(BaseModel):
    image_base64: str
    source_id: Optional[str] = "webcam_local"
    draw_boxes: Optional[bool] = True
    timestamp: Optional[float] = Field(None, description="Unix timestamp of the frame in seconds")


class FrameDetectionResponse(BaseModel):
    success: bool = True
    timestamp: str
    detections: List[AIDetectionResult]
    has_cheating: bool
    has_phone: bool
    new_incident: Optional[Dict[str, Any]] = None
    total_detections: int
    error: Optional[str] = None
    observed_acquisition_fps: Optional[float] = Field(None, description="Tốc độ nhận frame thực tế từ client (1/interval)")
    inference_fps: Optional[float] = Field(None, description="Tốc độ tính toán suy luận thuần túy (1/thời gian chạy)")


class SessionResetResponse(BaseModel):
    status: str = Field("SUCCESS", description="Trạng thái reset session")
    reset_session: str = Field(..., description="Session ID đã được reset hoặc 'all'")
    message: str = Field(..., description="Thông báo kết quả")


class TestTriggerIncidentResponse(BaseModel):
    status: str = Field("SUCCESS", description="Trạng thái kích hoạt thử nghiệm")
    incident_id: Optional[str] = Field(None, description="ID sự cố vi phạm nếu tạo thành công")
    session_id: Optional[str] = Field(None, description="Session ID hiện tại được gắn sự cố")


class SessionTelemetryResponse(BaseModel):
    session_id: str
    source_id: str
    server_packets_received: int = Field(0, description="Tổng số gói nhị phân WebSocket máy chủ nhận được")
    server_frames_decoded: int = Field(0, description="Tổng số frame giải mã JPEG thành công")
    server_received_frames: int = Field(0, description="Alias cho server_frames_decoded")
    duration_seconds: float = Field(0.0, description="Thời lượng từ frame đầu tới frame cuối (giây)")
    effective_acquisition_fps: float = Field(0.0, description="FPS toàn phiên: (decoded - 1) / (last - first)")
    first_decoded_monotonic: Optional[float] = Field(None, description="Timestamp monotonic của frame giải mã đầu tiên")
    last_decoded_monotonic: Optional[float] = Field(None, description="Timestamp monotonic của frame giải mã cuối cùng")
    fps_calculation: Optional[Dict[str, Any]] = Field(None, description="Chi tiết công thức và thay số tính FPS")
    interval_p50_ms: float = 0.0
    interval_p95_ms: float = 0.0
    interval_max_ms: float = 0.0
    gaps_gt_100ms: int = 0
    gaps_gt_250ms: int = 0
    inference_submitted_frames: int = Field(0, description="Số frame nạp vào buffer suy luận")
    inference_superseded_frames: int = Field(0, description="Số frame bị thay thế trước khi worker xử lý")
    inference_processed_frames: int = Field(0, description="Số frame worker đã xử lý xong")
    processed_inference_frames: int = Field(0, description="Alias cho inference_processed_frames")
    inference_pending_frames: int = Field(0, description="Số frame đang trong khe chờ/xử lý")
    pending_inference_frames: int = Field(0, description="Alias cho inference_pending_frames")
    result_messages_sent: int = Field(0, description="Số bản tin kết quả gửi đi")
    detection_results_sent: int = Field(0, description="Alias cho result_messages_sent")
    detected_objects: int = 0
    invariants: Dict[str, bool]


