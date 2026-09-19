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
from fastapi import APIRouter
from schemas import AISettingsSchema
from services.ring_buffer import ring_buffer_service

logger = logging.getLogger("settings_router")
router = APIRouter(prefix="/settings", tags=["AI Settings"])

SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "ai_settings.json")


def load_settings() -> AISettingsSchema:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AISettingsSchema(**data)
        except Exception as e:
            logger.warning(f"Could not parse {SETTINGS_FILE}: {e}")
    return AISettingsSchema(
        phone_confidence=0.35,
        posture_alert_seconds=1.25,
        suspicion_threshold=0.50,
        pre_roll_seconds=5.0,
        post_roll_seconds=10.0,
        cooldown_seconds=6.0
    )


def save_settings(settings: AISettingsSchema):
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
    # Synchronize RingBuffer
    ring_buffer_service.update_settings(
        pre_roll_seconds=settings.pre_roll_seconds,
        post_roll_seconds=settings.post_roll_seconds,
        cooldown_seconds=settings.cooldown_seconds
    )
    # Synchronize runtime AI Detector
    try:
        from routers.ai_engine import update_detector_settings
        update_detector_settings(
            phone_conf=settings.phone_confidence,
            suspicion_threshold=settings.suspicion_threshold,
            alert_seconds=settings.posture_alert_seconds
        )
    except Exception as e:
        logger.warning(f"Could not update AI detector runtime settings: {e}")


@router.get("/ai", response_model=AISettingsSchema)
def get_ai_settings():
    """
    Lấy cấu hình độ nhạy AI và tham số ghi video bằng chứng.
    """
    return load_settings()


@router.post("/ai", response_model=AISettingsSchema)
def update_ai_settings(payload: AISettingsSchema):
    """
    Cập nhật cấu hình độ nhạy AI và đồng bộ hóa ngay lập tức vào RingBuffer.
    """
    save_settings(payload)
    return payload
