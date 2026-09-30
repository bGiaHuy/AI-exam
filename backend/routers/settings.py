"""
================================================================================
SETTINGS ROUTER - AI EXAM CONTROL
================================================================================
Synchronized AI detection & RingBuffer operational parameters.
Single source of truth between Backend and Frontend.
================================================================================
"""

import os
import json
import logging
import tempfile
import threading
from fastapi import APIRouter, Depends
from schemas import AISettingsSchema
from services.ring_buffer import ring_buffer_service
from routers.ai_engine import verify_write_allowed

logger = logging.getLogger("settings_router")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
router = APIRouter(prefix="/settings", tags=["AI Settings"])

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "ai_settings.json")
_settings_lock = threading.Lock()


def load_settings() -> AISettingsSchema:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AISettingsSchema(**data)
        except Exception as e:
            logger.warning(f"Could not parse {SETTINGS_FILE}: {e}")
    return AISettingsSchema(
        phone_confidence=0.55,
        posture_alert_seconds=1.25,
        suspicion_threshold=0.50,
        pre_roll_seconds=5.0,
        post_roll_seconds=10.0,
        cooldown_seconds=6.0
    )


def save_settings(settings: AISettingsSchema):
    with _settings_lock:
        _save_settings_locked(settings)


def _save_settings_locked(settings: AISettingsSchema):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=SETTINGS_DIR,
                                         suffix=".tmp", delete=False) as f:
            temporary_path = f.name
            json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
        os.replace(temporary_path, SETTINGS_FILE)
    except Exception:
        logger.exception("[SETTINGS] Failed to persist AI settings")
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise
    # Synchronize RingBuffer
    ring_buffer_service.update_settings(
        pre_roll_seconds=settings.pre_roll_seconds,
        post_roll_seconds=settings.post_roll_seconds,
        cooldown_seconds=settings.cooldown_seconds
    )
    from services.camera_manager import camera_manager
    camera_manager.update_ring_buffer_settings(settings.pre_roll_seconds, settings.post_roll_seconds,
                                               settings.cooldown_seconds)
    # Synchronize runtime AI Detector
    try:
        from routers.ai_engine import update_detector_settings
        update_detector_settings(
            phone_conf=settings.phone_confidence,
            suspicion_threshold=settings.suspicion_threshold,
            alert_seconds=settings.posture_alert_seconds
        )
    except Exception:
        logger.exception("[SETTINGS] Could not update AI detector runtime settings")
        raise


@router.get("/ai", response_model=AISettingsSchema)
def get_ai_settings():
    """
    Lấy cấu hình độ nhạy AI và tham số ghi video bằng chứng.
    """
    return load_settings()


@router.post("/ai", response_model=AISettingsSchema, dependencies=[Depends(verify_write_allowed)])
def update_ai_settings(payload: AISettingsSchema):
    """
    Cập nhật cấu hình độ nhạy AI và đồng bộ hóa ngay lập tức vào RingBuffer.
    """
    logger.info("[SETTINGS] Updating AI settings: %s", payload.model_dump())
    save_settings(payload)
    return payload
