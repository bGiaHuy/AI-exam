"""
================================================================================
CAMERA MANAGER & LIFECYCLE SERVICE - AI EXAM CONTROL
================================================================================
Sprint 3.2 Dual-Camera Architecture:
- Coordinates camera sources according to CAMERA_MODE (SINGLE_CAMERA / DUAL_CAMERA).
- Loads configuration from environment variables without exposing credentials.
- Manages independent acquisition, ring buffers, and fair scheduling.
- Provides dynamic runtime switching between single and dual camera modes.
- Never leaks RTSP URLs, passwords, or IP addresses in public telemetry or API responses.
================================================================================
"""

import os
import sys
import logging
import threading
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("camera_manager")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.camera_source import (
    BaseCameraSource,
    BrowserWebSocketSource,
    UsbCameraSource,
    RtspCameraSource,
    SyntheticCameraSource,
    CameraStatus,
    redact_url
)
from services.fair_scheduler import fair_inference_scheduler


class CameraManager:
    """
    Manages active camera sources and runtime mode (SINGLE_CAMERA vs DUAL_CAMERA).
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._mode: str = "SINGLE_CAMERA"
        self._sources: Dict[str, BaseCameraSource] = {}
        self._initialized = False
        self._ring_buffer_settings: Dict[str, float] = {}

    def initialize(self):
        """Initializes sources from environment variables."""
        with self._lock:
            if self._initialized:
                return

            # Read .env from project root if present (skip in test environment to preserve synthetic test fixtures)
            if os.getenv("ENVIRONMENT", "").lower() != "test":
                env_file = os.path.join(os.path.dirname(BACKEND_DIR), ".env")
                if os.path.isfile(env_file):
                    try:
                        with open(env_file, "r", encoding="utf-8") as ef:
                            for line in ef:
                                line = line.strip()
                                if not line or line.startswith("#") or "=" not in line:
                                    continue
                                k, v = line.split("=", 1)
                                k, v = k.strip(), v.strip().strip("'\"")
                                if k and k not in os.environ:
                                    os.environ[k] = v
                    except Exception as ex:
                        logger.warning(f"[CAMERA_MANAGER] Failed reading .env file: {ex}")

            demo_ro = os.getenv("DEMO_READ_ONLY", "false").strip().lower() in ("true", "1", "yes")
            raw_mode = os.getenv("CAMERA_MODE", "single").strip().lower()
            if demo_ro:
                self._mode = "DUAL_CAMERA"
                logger.info("[CAMERA_MANAGER] DEMO_READ_ONLY active: Forcing DUAL_CAMERA mode.")
            elif raw_mode in ("triple", "triple_camera", "3"):
                self._mode = "TRIPLE_CAMERA"
            elif raw_mode in ("dual", "dual_camera", "2"):
                self._mode = "DUAL_CAMERA"
            else:
                self._mode = "SINGLE_CAMERA"

            cam1_type = os.getenv("CAMERA_1_TYPE", "browser_ws").strip().lower()
            cam1_label = os.getenv("CAMERA_1_LABEL", "Camera 1 (Góc trước)").strip()
            cam1_url = os.getenv("CAMERA_1_URL", "").strip()
            if not cam1_url:
                cam1_url = os.getenv("CAMERA_1_DEVICE_INDEX", "") or os.getenv("CAMERA_1_RTSP_URL", "").strip()

            cam2_type = os.getenv("CAMERA_2_TYPE", "browser_ws").strip().lower()
            cam2_label = os.getenv("CAMERA_2_LABEL", "Camera 2 (Góc bên)").strip()
            cam2_url = os.getenv("CAMERA_2_URL", "").strip()
            if not cam2_url:
                cam2_url = os.getenv("CAMERA_2_DEVICE_INDEX", "") or os.getenv("CAMERA_2_RTSP_URL", "").strip()

            cam3_type = os.getenv("CAMERA_3_TYPE", "usb").strip().lower()
            cam3_label = os.getenv("CAMERA_3_LABEL", "Camera 3 (Toàn cảnh)").strip()
            cam3_url = os.getenv("CAMERA_3_URL", "").strip()
            if not cam3_url:
                cam3_url = os.getenv("CAMERA_3_DEVICE_INDEX", "2") or os.getenv("CAMERA_3_RTSP_URL", "").strip()

            logger.info(f"[CAMERA_MANAGER] Initializing in {self._mode} mode.")

            from routers.settings import load_settings
            from services.ring_buffer import ring_buffer_service
            cfg = load_settings()
            self.update_ring_buffer_settings(cfg.pre_roll_seconds, cfg.post_roll_seconds, cfg.cooldown_seconds)
            ring_buffer_service.update_settings(**self._ring_buffer_settings)

            # Create Camera 1
            source1 = self._create_source("cam1", cam1_label, cam1_type, cam1_url)
            self._sources["cam1"] = source1
            source1.start()

            # Create Camera 2
            source2 = self._create_source("cam2", cam2_label, cam2_type, cam2_url)
            self._sources["cam2"] = source2
            if self._mode in ("DUAL_CAMERA", "TRIPLE_CAMERA"):
                source2.start()

            # Create Camera 3
            source3 = self._create_source("cam3", cam3_label, cam3_type, cam3_url)
            self._sources["cam3"] = source3
            if self._mode == "TRIPLE_CAMERA":
                source3.start()

            # Configure fair scheduler
            self._update_scheduler_sources()
            fair_inference_scheduler.start()
            self._initialized = True

    def _create_source(self, source_id: str, label: str, source_type: str, url: str) -> BaseCameraSource:
        """Factory creating appropriate camera source."""
        if source_type == "rtsp" and url:
            logger.info(f"[CAMERA_MANAGER] Created RTSP source {source_id} ({label}): {redact_url(url)}")
            source = RtspCameraSource(source_id=source_id, source_label=label, rtsp_url=url)
        elif source_type == "usb":
            device_idx = 0
            if url and url.isdigit():
                device_idx = int(url)
            logger.info(f"[CAMERA_MANAGER] Created USB source {source_id} ({label}) on index {device_idx}")
            source = UsbCameraSource(source_id=source_id, source_label=label, device_index=device_idx)
        elif source_type == "synthetic":
            logger.info(f"[CAMERA_MANAGER] Created Synthetic test source {source_id} ({label})")
            source = SyntheticCameraSource(source_id=source_id, source_label=label)
        else:
            # Default to BrowserWebSocketSource
            logger.info(f"[CAMERA_MANAGER] Created Browser WebSocket source {source_id} ({label})")
            source = BrowserWebSocketSource(source_id=source_id, source_label=label)
        source.ring_buffer.update_settings(**self._ring_buffer_settings)
        return source

    def update_ring_buffer_settings(self, pre_roll_seconds: float, post_roll_seconds: float, cooldown_seconds: float):
        """Apply settings to existing sources and retain them for later sources."""
        with self._lock:
            self._ring_buffer_settings = dict(pre_roll_seconds=pre_roll_seconds,
                                             post_roll_seconds=post_roll_seconds,
                                             cooldown_seconds=cooldown_seconds)
            for source in self._sources.values():
                source.ring_buffer.update_settings(**self._ring_buffer_settings)
            logger.info("[CAMERA_MANAGER] Applied recording settings to %s sources: %s",
                        len(self._sources), self._ring_buffer_settings)

    def _update_scheduler_sources(self):
        """Updates fair scheduler with currently active sources."""
        active = []
        if "cam1" in self._sources:
            active.append(self._sources["cam1"])
        if self._mode in ("DUAL_CAMERA", "TRIPLE_CAMERA") and "cam2" in self._sources:
            active.append(self._sources["cam2"])
        if self._mode == "TRIPLE_CAMERA" and "cam3" in self._sources:
            active.append(self._sources["cam3"])
        fair_inference_scheduler.set_sources(active)

    @property
    def mode(self) -> str:
        with self._lock:
            return self._mode

    def set_mode(self, new_mode: str) -> str:
        """Switch between SINGLE_CAMERA, DUAL_CAMERA, and TRIPLE_CAMERA cleanly."""
        with self._lock:
            if os.getenv("DEMO_READ_ONLY", "false").strip().lower() in ("true", "1", "yes"):
                logger.warning("[CAMERA_MANAGER] Rejected set_mode: DEMO_READ_ONLY is active.")
                return self._mode

            m_up = new_mode.strip().upper()
            if m_up in ("TRIPLE", "TRIPLE_CAMERA", "3"):
                norm = "TRIPLE_CAMERA"
            elif m_up in ("DUAL", "DUAL_CAMERA", "2"):
                norm = "DUAL_CAMERA"
            else:
                norm = "SINGLE_CAMERA"

            if norm == self._mode:
                return self._mode

            logger.info(f"[CAMERA_MANAGER] Switching mode from {self._mode} to {norm}")
            self._mode = norm

            if self._mode == "TRIPLE_CAMERA":
                if "cam3" not in self._sources:
                    cam3_type = os.getenv("CAMERA_3_TYPE", "usb" if os.getenv("ENVIRONMENT", "").lower() != "test" else "browser_ws").strip().lower()
                    cam3_label = os.getenv("CAMERA_3_LABEL", "Camera 3 (Toàn cảnh)").strip()
                    cam3_url = os.getenv("CAMERA_3_URL", "").strip() or os.getenv("CAMERA_3_DEVICE_INDEX", "2")
                    self._sources["cam3"] = self._create_source("cam3", cam3_label, cam3_type, cam3_url)
                if "cam2" in self._sources:
                    self._sources["cam2"].start()
                if "cam3" in self._sources:
                    self._sources["cam3"].start()
            elif self._mode == "DUAL_CAMERA":
                if "cam2" in self._sources:
                    self._sources["cam2"].start()
                if "cam3" in self._sources:
                    self._sources["cam3"].stop()
            else:
                if "cam2" in self._sources:
                    self._sources["cam2"].stop()
                if "cam3" in self._sources:
                    self._sources["cam3"].stop()

            self._update_scheduler_sources()
            return self._mode

    def get_source(self, source_id: str) -> Optional[BaseCameraSource]:
        with self._lock:
            # Backward compatibility: 'webcam_local' maps to 'cam1'
            if source_id in ("webcam_local", "default", "legacy_single"):
                source_id = "cam1"
            if source_id == "cam3" and "cam3" not in self._sources:
                cam3_type = os.getenv("CAMERA_3_TYPE", "usb" if os.getenv("ENVIRONMENT", "").lower() != "test" else "browser_ws").strip().lower()
                cam3_label = os.getenv("CAMERA_3_LABEL", "Camera 3 (Toàn cảnh)").strip()
                cam3_url = os.getenv("CAMERA_3_URL", "").strip() or os.getenv("CAMERA_3_DEVICE_INDEX", "2")
                self._sources["cam3"] = self._create_source("cam3", cam3_label, cam3_type, cam3_url)
            return self._sources.get(source_id)

    def register_custom_source(self, source: BaseCameraSource):
        """Allows injecting test/synthetic sources for automated testing."""
        with self._lock:
            source.ring_buffer.update_settings(**self._ring_buffer_settings)
            self._sources[source.source_id] = source
            source.start()
            self._update_scheduler_sources()

    def get_all_active_sources(self) -> List[BaseCameraSource]:
        with self._lock:
            if self._mode == "TRIPLE_CAMERA":
                return [s for s in self._sources.values() if s.status != CameraStatus.STOPPED]
            elif self._mode == "DUAL_CAMERA":
                res = []
                for cid in ("cam1", "cam2"):
                    s = self._sources.get(cid)
                    if s and s.status != CameraStatus.STOPPED:
                        res.append(s)
                # Include any dynamically injected sources not stopped
                for k, s in self._sources.items():
                    if k not in ("cam1", "cam2", "cam3") and s.status != CameraStatus.STOPPED:
                        res.append(s)
                return res
            return [self._sources["cam1"]] if "cam1" in self._sources else []

    def get_system_status(self) -> Dict[str, Any]:
        """Returns safe telemetry & camera status without credentials."""
        with self._lock:
            active_sources = self.get_all_active_sources()
            cameras = [s.get_telemetry() for s in active_sources]
            total_online = sum(1 for c in cameras if c["status"] == CameraStatus.ONLINE.value)
            return {
                "mode": self._mode,
                "cameras": cameras,
                "total_online": total_online,
                "scheduler_inference_fps": fair_inference_scheduler.last_inference_fps,
                "scheduler_latency_ms": fair_inference_scheduler.last_inference_latency_ms,
                "demo_read_only": os.getenv("DEMO_READ_ONLY", "false").strip().lower() in ("true", "1", "yes")
            }

    def reset_session(self, session_id: Optional[str] = None):
        with self._lock:
            for s in self._sources.values():
                if session_id is None or session_id == "all" or s.session_id == session_id:
                    s.reset_session()
                    logger.info("[CAMERA_MANAGER] Reset source=%s session=%s", s.source_id, session_id)

    def begin_session(self, source_id: str, session_id: str):
        """Switch only the source that owns the new browser connection."""
        with self._lock:
            source = self.get_source(source_id)
            if source is None:
                source = self._create_source(source_id, f"Camera {source_id}", "browser_ws", "")
                self.register_custom_source(source)
            source.reset_session(session_id)
            logger.info("[CAMERA_MANAGER] Begin source=%s session=%s", source_id, session_id)

    def shutdown(self):
        with self._lock:
            fair_inference_scheduler.stop()
            for s in self._sources.values():
                s.stop()
            logger.info("[CAMERA_MANAGER] Cleaned up all camera sources and stopped scheduler.")


# Global camera manager singleton
camera_manager = CameraManager()
