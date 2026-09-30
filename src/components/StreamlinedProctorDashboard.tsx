import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Incident, CameraMode, CameraSourceInfo } from '../types';
import { 
  getIncidents, 
  confirmIncident, 
  deleteIncident,
  purgeAllIncidentVideos,
  resetSessionState,
  getCameraMode,
  setCameraMode as apiSetCameraMode,
  getCameraSources
} from '../services/api';
import { 
  AIDetectionResult, 
  WebSocketIngestClient, 
  WebSocketPreviewClient,
  IngestTelemetry, 
  WebSocketDetectionPayload 
} from '../services/aiModelService';
import { DEMO_CONFIG } from '../config/demoConfig';
import { MOCK_DEMO_INCIDENTS } from '../demo/mockDemoData';

// Reusable Proctoring Components (THPT Chuyên Hoàng Văn Thụ Visual Direction)
import { MonitoringToolbar } from './proctoring/MonitoringToolbar';
import { CameraCard, CameraSourceOption } from './proctoring/CameraCard';
import { IncidentSidebar } from './proctoring/IncidentSidebar';
import { DashboardFooter } from './proctoring/DashboardFooter';

export interface CameraSourceConfig {
  type: 'device' | 'backend' | 'file';
  deviceId?: string;
  backendSourceId?: string;
  label: string;
}

interface StreamlinedDashboardProps {
  onOpenVideoModal: (incident: Incident) => void;
  onConfirmIncident?: (incidentId: string) => void;
  onDismissIncident?: (incidentId: string) => void;
  onDeleteIncident?: (incidentId: string) => Promise<boolean>;
  incidentsRevision?: number;
}

interface LocalVideoViewportProps {
  stream?: MediaStream | null;
  src?: string | null;
  videoRef: React.MutableRefObject<HTMLVideoElement | null>;
  loop?: boolean;
}

const LocalVideoViewport: React.FC<LocalVideoViewportProps> = ({
  stream,
  src,
  videoRef,
  loop = false
}) => {
  const innerRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const el = innerRef.current;
    if (!el) return;
    if (stream) {
      if (el.srcObject !== stream) {
        el.srcObject = stream;
      }
      el.play().catch(() => {});
    } else if (src) {
      if (el.src !== src) {
        el.src = src;
      }
      el.play().catch(() => {});
    }
  }, [stream, src]);

  return (
    <video
      ref={(el) => {
        innerRef.current = el;
        videoRef.current = el;
        if (el) {
          if (stream && el.srcObject !== stream) {
            el.srcObject = stream;
            el.play().catch(() => {});
          } else if (src && el.src !== src) {
            el.src = src;
            el.play().catch(() => {});
          }
        }
      }}
      playsInline
      autoPlay
      loop={loop}
      muted
      className="w-full h-full object-contain"
    />
  );
};

export const StreamlinedProctorDashboard: React.FC<StreamlinedDashboardProps> = ({
  onOpenVideoModal,
  onConfirmIncident,
  onDismissIncident,
  onDeleteIncident,
  incidentsRevision = 0,
}) => {
  // Video Source & Hardware Elements
  const [sourceType, setSourceType] = useState<'webcam' | 'file'>('webcam');
  const [fileVideoUrl, setFileVideoUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const captureInFlightRef = useRef<boolean>(false);

  // Monitoring & Telemetry States
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [showOverlays, setShowOverlays] = useState(true);
  const [fps, setFps] = useState(0);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<IngestTelemetry>({
    capture_frames: 0,
    sent_frames: 0,
    transport_dropped_frames: 0,
    server_received_frames: 0,
    inference_submitted_frames: 0,
    inference_superseded_frames: 0,
    processed_inference_frames: 0,
    pending_inference_frames: 0,
    detection_results_sent: 0,
    detection_results_received: 0,
    detected_objects: 0,
    acquisition_fps: 15,
    effective_acquisition_fps: 0,
    inference_fps: 0,
    latency_ms: 0
  });

  // Detections & Incidents Feed
  const [liveDetections, setLiveDetections] = useState<AIDetectionResult[]>([]);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [isPolling, setIsPolling] = useState(false);
  const [incidentError, setIncidentError] = useState<string | null>(null);
  const [incidentFeedError, setIncidentFeedError] = useState<string | null>(null);
  const incidentRequestRef = useRef(0);
  const incidentMutationRef = useRef(false);
  const [activeIncidentLevel, setActiveIncidentLevel] = useState<'normal' | 'yellow' | 'red'>('normal');

  // Multi-Camera Mode (Sprint 3.2 Dual/Triple Camera) & Read-Only Demo
  const [cameraMode, setCameraModeState] = useState<CameraMode>('TRIPLE_CAMERA');
  const [cameraSources, setCameraSources] = useState<CameraSourceInfo[]>([]);
  const [isDemoReadOnly, setIsDemoReadOnly] = useState<boolean>(false);

  // Available USB/Browser Video Devices
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);

  // Camera Source Selection for each of the 3 cards
  const [cam1Source, setCam1Source] = useState<CameraSourceConfig>({
    type: 'backend',
    backendSourceId: 'cam1',
    label: 'Backend Cam 1'
  });
  const [cam2Source, setCam2Source] = useState<CameraSourceConfig>({
    type: 'backend',
    backendSourceId: 'cam2',
    label: 'Backend Cam 2'
  });
  const [cam3Source, setCam3Source] = useState<CameraSourceConfig>({
    type: 'backend',
    backendSourceId: 'cam3',
    label: 'Backend Cam 3'
  });

  // Camera 1 Video & Stream Refs
  const cam1VideoRef = useRef<HTMLVideoElement>(null);
  const cam1StreamRef = useRef<MediaStream | null>(null);
  const [cam1StreamActive, setCam1StreamActive] = useState<boolean>(false);
  const [cam1PreviewUrl, setCam1PreviewUrl] = useState<string | null>(null);
  const [cam1Status, setCam1Status] = useState<string>('disconnected');
  const [cam1StatusReason, setCam1StatusReason] = useState<string>('');
  const [cam1Detections, setCam1Detections] = useState<AIDetectionResult[]>([]);
  const cam1PreviewClientRef = useRef<WebSocketPreviewClient | null>(null);
  const cam1IngestClientRef = useRef<WebSocketIngestClient | null>(null);

  // Camera 2 Video & Stream Refs
  const cam2VideoRef = useRef<HTMLVideoElement>(null);
  const cam2StreamRef = useRef<MediaStream | null>(null);
  const [cam2StreamActive, setCam2StreamActive] = useState<boolean>(false);
  const [cam2PreviewUrl, setCam2PreviewUrl] = useState<string | null>(null);
  const [cam2Status, setCam2Status] = useState<string>('disconnected');
  const [cam2StatusReason, setCam2StatusReason] = useState<string>('');
  const [cam2Detections, setCam2Detections] = useState<AIDetectionResult[]>([]);
  const cam2PreviewClientRef = useRef<WebSocketPreviewClient | null>(null);
  const cam2IngestClientRef = useRef<WebSocketIngestClient | null>(null);

  // Camera 3 Video & Stream Refs
  const cam3VideoRef = useRef<HTMLVideoElement>(null);
  const cam3StreamRef = useRef<MediaStream | null>(null);
  const [cam3StreamActive, setCam3StreamActive] = useState<boolean>(false);
  const [cam3PreviewUrl, setCam3PreviewUrl] = useState<string | null>(null);
  const [cam3Status, setCam3Status] = useState<string>('disconnected');
  const [cam3StatusReason, setCam3StatusReason] = useState<string>('');
  const [cam3Detections, setCam3Detections] = useState<AIDetectionResult[]>([]);
  const cam3PreviewClientRef = useRef<WebSocketPreviewClient | null>(null);
  const cam3IngestClientRef = useRef<WebSocketIngestClient | null>(null);

  // Active MediaStreams for DOM direct video binding (prevents black screen on webcam)
  const [cam1MediaStream, setCam1MediaStream] = useState<MediaStream | null>(null);
  const [cam2MediaStream, setCam2MediaStream] = useState<MediaStream | null>(null);
  const [cam3MediaStream, setCam3MediaStream] = useState<MediaStream | null>(null);

  // Scan for connected USB/Webcam video devices
  const refreshVideoDevices = useCallback(async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        return [];
      }
      let devs = await navigator.mediaDevices.enumerateDevices();
      let vDevs = devs.filter(d => d.kind === 'videoinput');

      // Request brief permission if device labels are blank
      if (vDevs.length > 0 && !vDevs[0].label) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
          stream.getTracks().forEach(t => t.stop());
          devs = await navigator.mediaDevices.enumerateDevices();
          vDevs = devs.filter(d => d.kind === 'videoinput');
        } catch (permErr) {
          console.warn('[Camera] Chưa được cấp quyền đọc tên thiết bị:', permErr);
        }
      }

      setVideoDevices(vDevs);

      // Only auto-assign USB devices if sources are NOT already backend or file
      setCam1Source(prev => {
        if (prev.type === 'backend' || prev.type === 'file') return prev;
        if (vDevs.length > 0) {
          return { type: 'device', deviceId: vDevs[0].deviceId, label: vDevs[0].label || 'Webcam máy tính' };
        }
        return prev;
      });
      setCam2Source(prev => {
        if (prev.type === 'backend' || prev.type === 'file') return prev;
        if (vDevs.length > 1) {
          return { type: 'device', deviceId: vDevs[1].deviceId, label: vDevs[1].label || 'Camera USB 2' };
        }
        return prev;
      });
      setCam3Source(prev => {
        if (prev.type === 'backend' || prev.type === 'file') return prev;
        if (vDevs.length > 2) {
          return { type: 'device', deviceId: vDevs[2].deviceId, label: vDevs[2].label || 'Camera USB 3' };
        }
        return prev;
      });

      return vDevs;
    } catch (err) {
      console.error('[Camera] Lỗi quét thiết bị:', err);
      return [];
    }
  }, []);

  // Listen for device connect / disconnect events
  useEffect(() => {
    refreshVideoDevices();
    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      navigator.mediaDevices.addEventListener('devicechange', refreshVideoDevices);
      return () => {
        navigator.mediaDevices.removeEventListener('devicechange', refreshVideoDevices);
      };
    }
  }, [refreshVideoDevices]);

  // Initial Sync with Backend Camera Manager
  useEffect(() => {
    getCameraMode().then(mode => setCameraModeState(mode));
    getCameraSources().then(res => {
      if (res && res.cameras) {
        setCameraSources(res.cameras);
        // If backend cameras are ONLINE, inform the source labels
        const c1 = res.cameras.find(c => c.source_id === 'cam1');
        const c2 = res.cameras.find(c => c.source_id === 'cam2');
        const c3 = res.cameras.find(c => c.source_id === 'cam3');
        if (c1 && (c1.status === 'ONLINE' || c1.source_type === 'usb')) {
          setCam1Source(prev => prev.type === 'file' ? prev : { ...prev, type: 'backend', backendSourceId: 'cam1', label: c1.source_label });
        }
        if (c2 && (c2.status === 'ONLINE' || c2.source_type === 'usb')) {
          setCam2Source(prev => prev.type === 'file' ? prev : { ...prev, type: 'backend', backendSourceId: 'cam2', label: c2.source_label });
        }
        if (c3 && (c3.status === 'ONLINE' || c3.source_type === 'usb')) {
          setCam3Source(prev => prev.type === 'file' ? prev : { ...prev, type: 'backend', backendSourceId: 'cam3', label: c3.source_label });
        }
      }
      if (res && typeof res.demo_read_only === 'boolean') {
        setIsDemoReadOnly(res.demo_read_only);
        if (res.demo_read_only) {
          setCameraModeState('DUAL_CAMERA');
        }
      }
    });
  }, []);

  const handleToggleCameraMode = async (targetMode: CameraMode) => {
    if (isDemoReadOnly) return;
    const updated = await apiSetCameraMode(targetMode);
    setCameraModeState(updated);
    const sourcesRes = await getCameraSources();
    if (sourcesRes && sourcesRes.cameras) {
      setCameraSources(sourcesRes.cameras);
    }
  };

  // =========================================================================
  // CAMERA 1 STREAM MANAGEMENT (Browser Device vs Backend Stream)
  // =========================================================================
  useEffect(() => {
    if (cam1Source.type === 'device') {
      let isSubscribed = true;
      const startCam1 = async () => {
        try {
          if (cam1StreamRef.current) {
            cam1StreamRef.current.getTracks().forEach(t => t.stop());
          }
          const constraints: MediaStreamConstraints = {
            video: cam1Source.deviceId
              ? { deviceId: { exact: cam1Source.deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
              : { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
          };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          if (!isSubscribed) {
            stream.getTracks().forEach(t => t.stop());
            return;
          }
          cam1StreamRef.current = stream;
          setCam1MediaStream(stream);
          setCam1StreamActive(true);
          setCam1Status('ONLINE');
          if (cam1VideoRef.current) {
            cam1VideoRef.current.srcObject = stream;
            cam1VideoRef.current.play().catch(() => {});
          }
        } catch (err) {
          console.warn('[Cam1] Lỗi mở browser stream:', err);
          setCam1MediaStream(null);
          setCam1StreamActive(false);
          setCam1Status('OFFLINE');
          setCam1StatusReason('Không thể truy cập camera USB này');
        }
      };
      startCam1();
      return () => {
        isSubscribed = false;
        if (cam1StreamRef.current) {
          cam1StreamRef.current.getTracks().forEach(t => t.stop());
          cam1StreamRef.current = null;
        }
        setCam1MediaStream(null);
        setCam1StreamActive(false);
      };
    } else {
      if (cam1StreamRef.current) {
        cam1StreamRef.current.getTracks().forEach(t => t.stop());
        cam1StreamRef.current = null;
      }
      setCam1MediaStream(null);
      setCam1StreamActive(false);
    }
  }, [cam1Source]);

  useEffect(() => {
    if (cam1Source.type !== 'backend') {
      if (cam1PreviewClientRef.current) {
        cam1PreviewClientRef.current.disconnect();
        cam1PreviewClientRef.current = null;
      }
      setCam1PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }

    const bSourceId = cam1Source.backendSourceId || 'cam1';
    const previewClient = new WebSocketPreviewClient(bSourceId, 10);
    previewClient.onFrame((blobUrl) => {
      setCam1PreviewUrl(blobUrl);
      setCam1Status('ONLINE');
    });
    previewClient.onDetections((detections, level) => {
      if (detections && Array.isArray(detections)) {
        setCam1Detections(detections);
      }
      if (level === 'red') setActiveIncidentLevel('red');
      else if (level === 'yellow' && activeIncidentLevel !== 'red') setActiveIncidentLevel('yellow');
    });
    previewClient.onStatus((status, reason) => {
      setCam1Status(status);
      if (reason) setCam1StatusReason(reason);
    });
    previewClient.connect();
    cam1PreviewClientRef.current = previewClient;

    return () => {
      previewClient.disconnect();
      if (cam1PreviewClientRef.current === previewClient) {
        cam1PreviewClientRef.current = null;
      }
      setCam1PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, [cam1Source]);

  // =========================================================================
  // CAMERA 2 STREAM MANAGEMENT (Browser Device vs Backend Stream)
  // =========================================================================
  useEffect(() => {
    const isCam2ActiveMode = cameraMode === 'DUAL_CAMERA' || cameraMode === 'TRIPLE_CAMERA';
    if (!isCam2ActiveMode) return;

    if (cam2Source.type === 'device') {
      let isSubscribed = true;
      const startCam2 = async () => {
        try {
          if (cam2StreamRef.current) {
            cam2StreamRef.current.getTracks().forEach(t => t.stop());
          }
          const constraints: MediaStreamConstraints = {
            video: cam2Source.deviceId
              ? { deviceId: { exact: cam2Source.deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
              : { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
          };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          if (!isSubscribed) {
            stream.getTracks().forEach(t => t.stop());
            return;
          }
          cam2StreamRef.current = stream;
          setCam2MediaStream(stream);
          setCam2StreamActive(true);
          setCam2Status('ONLINE');
          if (cam2VideoRef.current) {
            cam2VideoRef.current.srcObject = stream;
            cam2VideoRef.current.play().catch(() => {});
          }
        } catch (err) {
          console.warn('[Cam2] Lỗi mở browser stream:', err);
          setCam2MediaStream(null);
          setCam2StreamActive(false);
          setCam2Status('OFFLINE');
          setCam2StatusReason('Không thể truy cập camera USB này');
        }
      };
      startCam2();
      return () => {
        isSubscribed = false;
        if (cam2StreamRef.current) {
          cam2StreamRef.current.getTracks().forEach(t => t.stop());
          cam2StreamRef.current = null;
        }
        setCam2MediaStream(null);
        setCam2StreamActive(false);
      };
    } else {
      if (cam2StreamRef.current) {
        cam2StreamRef.current.getTracks().forEach(t => t.stop());
        cam2StreamRef.current = null;
      }
      setCam2MediaStream(null);
      setCam2StreamActive(false);
    }
  }, [cam2Source, cameraMode]);

  useEffect(() => {
    const isCam2ActiveMode = cameraMode === 'DUAL_CAMERA' || cameraMode === 'TRIPLE_CAMERA';
    if (!isCam2ActiveMode || cam2Source.type !== 'backend') {
      if (cam2PreviewClientRef.current) {
        cam2PreviewClientRef.current.disconnect();
        cam2PreviewClientRef.current = null;
      }
      setCam2PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }

    const bSourceId = cam2Source.backendSourceId || 'cam2';
    const previewClient = new WebSocketPreviewClient(bSourceId, 10);
    previewClient.onFrame((blobUrl) => {
      setCam2PreviewUrl(blobUrl);
      setCam2Status('ONLINE');
    });
    previewClient.onDetections((detections, level) => {
      if (detections && Array.isArray(detections)) {
        setCam2Detections(detections);
      }
      if (level === 'red') setActiveIncidentLevel('red');
      else if (level === 'yellow' && activeIncidentLevel !== 'red') setActiveIncidentLevel('yellow');
    });
    previewClient.onStatus((status, reason) => {
      setCam2Status(status);
      if (reason) setCam2StatusReason(reason);
    });
    previewClient.connect();
    cam2PreviewClientRef.current = previewClient;

    return () => {
      previewClient.disconnect();
      if (cam2PreviewClientRef.current === previewClient) {
        cam2PreviewClientRef.current = null;
      }
      setCam2PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, [cam2Source, cameraMode]);

  // =========================================================================
  // CAMERA 3 STREAM MANAGEMENT (Browser Device vs Backend Stream)
  // =========================================================================
  useEffect(() => {
    if (cameraMode !== 'TRIPLE_CAMERA') return;

    if (cam3Source.type === 'device') {
      let isSubscribed = true;
      const startCam3 = async () => {
        try {
          if (cam3StreamRef.current) {
            cam3StreamRef.current.getTracks().forEach(t => t.stop());
          }
          const constraints: MediaStreamConstraints = {
            video: cam3Source.deviceId
              ? { deviceId: { exact: cam3Source.deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
              : { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
          };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          if (!isSubscribed) {
            stream.getTracks().forEach(t => t.stop());
            return;
          }
          cam3StreamRef.current = stream;
          setCam3MediaStream(stream);
          setCam3StreamActive(true);
          setCam3Status('ONLINE');
          if (cam3VideoRef.current) {
            cam3VideoRef.current.srcObject = stream;
            cam3VideoRef.current.play().catch(() => {});
          }
        } catch (err) {
          console.warn('[Cam3] Lỗi mở browser stream:', err);
          setCam3MediaStream(null);
          setCam3StreamActive(false);
          setCam3Status('OFFLINE');
          setCam3StatusReason('Không thể truy cập camera USB này');
        }
      };
      startCam3();
      return () => {
        isSubscribed = false;
        if (cam3StreamRef.current) {
          cam3StreamRef.current.getTracks().forEach(t => t.stop());
          cam3StreamRef.current = null;
        }
        setCam3MediaStream(null);
        setCam3StreamActive(false);
      };
    } else {
      if (cam3StreamRef.current) {
        cam3StreamRef.current.getTracks().forEach(t => t.stop());
        cam3StreamRef.current = null;
      }
      setCam3MediaStream(null);
      setCam3StreamActive(false);
    }
  }, [cam3Source, cameraMode]);

  useEffect(() => {
    if (cameraMode !== 'TRIPLE_CAMERA' || cam3Source.type !== 'backend') {
      if (cam3PreviewClientRef.current) {
        cam3PreviewClientRef.current.disconnect();
        cam3PreviewClientRef.current = null;
      }
      setCam3PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }

    const bSourceId = cam3Source.backendSourceId || 'cam3';
    const previewClient = new WebSocketPreviewClient(bSourceId, 10);
    previewClient.onFrame((blobUrl) => {
      setCam3PreviewUrl(blobUrl);
      setCam3Status('ONLINE');
    });
    previewClient.onDetections((detections, level) => {
      if (detections && Array.isArray(detections)) {
        setCam3Detections(detections);
      }
      if (level === 'red') setActiveIncidentLevel('red');
      else if (level === 'yellow' && activeIncidentLevel !== 'red') setActiveIncidentLevel('yellow');
    });
    previewClient.onStatus((status, reason) => {
      setCam3Status(status);
      if (reason) setCam3StatusReason(reason);
    });
    previewClient.connect();
    cam3PreviewClientRef.current = previewClient;

    return () => {
      previewClient.disconnect();
      if (cam3PreviewClientRef.current === previewClient) {
        cam3PreviewClientRef.current = null;
      }
      setCam3PreviewUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, [cam3Source, cameraMode]);

  // =========================================================================
  // HIGH-DENSITY WEBSOCKET INGESTION PIPELINE (Browser Ingestion for AI)
  // =========================================================================
  useEffect(() => {
    if (!isMonitoring) {
      if (cam1IngestClientRef.current) {
        const oldSession = cam1IngestClientRef.current.getSessionId();
        cam1IngestClientRef.current.disconnect();
        cam1IngestClientRef.current = null;
        resetSessionState(oldSession).catch(() => {});
      }
      return;
    }

    if (cam1Source.type !== 'device' && cam1Source.type !== 'file') {
      return;
    }

    const sourceId = 'cam1';
    const client = new WebSocketIngestClient(sourceId);
    cam1IngestClientRef.current = client;

    client.connect(
      (payload: WebSocketDetectionPayload) => {
        if (payload.detections) {
          setLiveDetections(payload.detections);
          setCam1Detections(payload.detections);
        }
        if (payload.level === 'red') setActiveIncidentLevel('red');
        else if (payload.level === 'yellow') setActiveIncidentLevel('yellow');
        else setActiveIncidentLevel('normal');
      },
      (t: IngestTelemetry) => {
        setTelemetry({ ...t });
        (window as any).__EXAM_TELEMETRY__ = { ...t };
        if (t.acquisition_fps > 0) setFps(t.acquisition_fps);
      },
      (isConnected: boolean, error?: string) => {
        setWsConnected(isConnected);
        setWsError(error || null);
      }
    );

    // Capture & Stream frames at target 15 FPS (~66ms) from Cam 1
    const intervalMs = 66;
    const frameTimer = setInterval(() => {
      client.recordCaptureAttempt();
      if (captureInFlightRef.current) return;
      const videoEl = cam1VideoRef.current;
      if (!videoEl || videoEl.readyState < 2 || videoEl.paused) return;

      if (!offscreenCanvasRef.current) {
        offscreenCanvasRef.current = document.createElement('canvas');
      }
      const canvas = offscreenCanvasRef.current;
      canvas.width = 640;
      canvas.height = 360;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      captureInFlightRef.current = true;
      ctx.drawImage(videoEl, 0, 0, 640, 360);

      canvas.toBlob(async (blob) => {
        try {
          if (blob) {
            client.recordCaptureEncoded();
            if (client.getIsConnected()) {
              const buffer = await blob.arrayBuffer();
              client.sendFrame(buffer);
            } else {
              client.recordBackpressureDrop();
            }
          }
        } catch (e) {
          // ignore stream buffer errors
        } finally {
          captureInFlightRef.current = false;
        }
      }, 'image/jpeg', 0.8);
    }, intervalMs);

    return () => {
      clearInterval(frameTimer);
      captureInFlightRef.current = false;
      const oldSession = client.getSessionId();
      client.disconnect();
      if (cam1IngestClientRef.current === client) {
        cam1IngestClientRef.current = null;
      }
      resetSessionState(oldSession).catch(() => {});
    };
  }, [isMonitoring, cam1Source]);

  // Polling Incident Feed from SQLite every 2 seconds
  const fetchIncidents = async () => {
    if (incidentMutationRef.current) return;
    if (DEMO_CONFIG.isDemo) {
      if (recentIncidents.length === 0) {
        setRecentIncidents(MOCK_DEMO_INCIDENTS);
      }
      return;
    }
    const requestId = ++incidentRequestRef.current;
    try {
      setIsPolling(true);
      const data = await getIncidents({ limit: 30 });
      if (requestId === incidentRequestRef.current) {
        setRecentIncidents(data);
        setIncidentFeedError(null);
      }
    } catch (err) {
      console.warn('[Dashboard] Lỗi polling sự cố từ SQLite:', err);
      if (requestId === incidentRequestRef.current) setIncidentFeedError('Không thể tải sự cố. Kiểm tra kết nối máy chủ rồi làm mới.');
    } finally {
      if (requestId === incidentRequestRef.current) setIsPolling(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const timer = setInterval(fetchIncidents, 2000);
    return () => {
      clearInterval(timer);
      incidentRequestRef.current += 1;
    };
  }, [incidentsRevision]);

  // File Video Upload Handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (DEMO_CONFIG.isDemo) return;
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setFileVideoUrl(url);
    setSourceType('file');
    setCam1Source({ type: 'file', label: `Demo: ${file.name}` });
    if (cam1VideoRef.current) {
      cam1VideoRef.current.srcObject = null;
      cam1VideoRef.current.src = url;
      cam1VideoRef.current.play().catch(() => {});
    }
  };

  // Operator Action Handlers
  const handleConfirm = async (incId: string) => {
    if (DEMO_CONFIG.isDemo) {
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'confirmed' } : i));
      if (onConfirmIncident) onConfirmIncident(incId);
      return;
    }
    try {
      await confirmIncident(incId, { status: 'confirmed' });
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'confirmed' } : i));
      if (onConfirmIncident) onConfirmIncident(incId);
    } catch (err) {
      console.error('Lỗi xác nhận sự cố:', err);
      setIncidentError('Không thể xác nhận sự cố. Vui lòng thử lại.');
    }
  };

  const handleDismiss = async (incId: string) => {
    if (DEMO_CONFIG.isDemo) {
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'dismissed' } : i));
      if (onDismissIncident) onDismissIncident(incId);
      return;
    }
    try {
      await confirmIncident(incId, { status: 'dismissed' });
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'dismissed' } : i));
      if (onDismissIncident) onDismissIncident(incId);
    } catch (err) {
      console.error('Lỗi bỏ qua sự cố:', err);
      setIncidentError('Không thể bỏ qua sự cố. Vui lòng thử lại.');
    }
  };

  const handleDeleteIncident = async (incId: string) => {
    if (incidentMutationRef.current) return;
    if (DEMO_CONFIG.isDemo) {
      setRecentIncidents(prev => prev.filter(i => i.id !== incId));
      return;
    }
    incidentMutationRef.current = true;
    incidentRequestRef.current += 1;
    try {
      const success = onDeleteIncident ? await onDeleteIncident(incId) : await deleteIncident(incId);
      if (!success) throw new Error('Chưa xóa được sự cố. Vui lòng thử lại.');
      setRecentIncidents(prev => prev.filter(i => i.id !== incId));
      setIncidentError(null);
    } catch (err) {
      console.error('[LiveMonitor] Lỗi xóa sự cố:', err);
      setIncidentError(err instanceof Error ? err.message : 'Lỗi xóa sự cố');
    } finally {
      incidentMutationRef.current = false;
      setIsPolling(false);
    }
  };

  const handlePurgeAllVideos = async () => {
    if (incidentMutationRef.current) return;
    if (DEMO_CONFIG.isDemo) {
      setRecentIncidents([]);
      return;
    }
    incidentMutationRef.current = true;
    incidentRequestRef.current += 1;
    try {
      await purgeAllIncidentVideos();
      setRecentIncidents([]);
      setIncidentError(null);
    } catch (err) {
      console.error('[LiveMonitor] Lỗi dọn sạch toàn bộ video sự cố:', err);
      setIncidentError(err instanceof Error ? err.message : 'Lỗi dọn sạch bằng chứng');
    } finally {
      incidentMutationRef.current = false;
      setIsPolling(false);
    }
  };

  // Build list of selectable sources for each CameraCard
  const getAvailableSources = (camId: 'cam1' | 'cam2' | 'cam3', currentConfig: CameraSourceConfig): CameraSourceOption[] => {
    const options: CameraSourceOption[] = [];

    // 1. Backend Sources (Primary AI engine pipeline)
    const backendCams = [
      { id: 'cam1', name: 'Góc trước (Bàn thi)' },
      { id: 'cam2', name: 'Góc bên (Bao quát)' },
      { id: 'cam3', name: 'Toàn cảnh phòng thi' }
    ];
    backendCams.forEach(b => {
      const isSelected = currentConfig.type === 'backend' && currentConfig.backendSourceId === b.id;
      const matchingBackend = cameraSources.find(c => c.source_id === b.id);
      const displayName = matchingBackend ? matchingBackend.source_label : b.name;
      options.push({
        id: `backend:${b.id}`,
        label: `[AI Máy chủ] ${b.id.toUpperCase()} - ${displayName}`,
        type: 'backend',
        backendSourceId: b.id,
        isCurrent: isSelected
      });
    });

    // 2. Direct Browser Webcams (USB / Integrated)
    videoDevices.forEach((dev, idx) => {
      const isSelected = currentConfig.type === 'device' && currentConfig.deviceId === dev.deviceId;
      const cleanLabel = dev.label ? dev.label.replace(/\s*\([0-9a-fA-F]{4}:[0-9a-fA-F]{4}\)$/, '') : 'Camera USB';
      const labelSuffix = videoDevices.length > 1 ? ` [Cổng #${idx + 1}]` : '';
      options.push({
        id: `device:${dev.deviceId}`,
        label: `[Trình duyệt] ${cleanLabel}${labelSuffix}`,
        type: 'device',
        deviceId: dev.deviceId,
        isCurrent: isSelected
      });
    });

    // 3. Demo File
    options.push({
      id: 'file:demo',
      label: 'Video Demo (.mp4)',
      type: 'file',
      isCurrent: currentConfig.type === 'file'
    });

    return options;
  };

  // Handle user selecting a camera source from the dropdown
  const handleSelectSource = (camId: 'cam1' | 'cam2' | 'cam3', option: CameraSourceOption) => {
    if (option.type === 'device' && option.deviceId) {
      if (camId === 'cam1') setCam1Source({ type: 'device', deviceId: option.deviceId, label: option.label });
      if (camId === 'cam2') setCam2Source({ type: 'device', deviceId: option.deviceId, label: option.label });
      if (camId === 'cam3') setCam3Source({ type: 'device', deviceId: option.deviceId, label: option.label });
    } else if (option.type === 'backend') {
      const bid = option.backendSourceId || camId;
      if (camId === 'cam1') setCam1Source({ type: 'backend', backendSourceId: bid, label: option.label });
      if (camId === 'cam2') setCam2Source({ type: 'backend', backendSourceId: bid, label: option.label });
      if (camId === 'cam3') setCam3Source({ type: 'backend', backendSourceId: bid, label: option.label });
    } else if (option.type === 'file') {
      if (camId === 'cam1') setCam1Source({ type: 'file', label: 'Video Demo' });
      if (camId === 'cam2') setCam2Source({ type: 'file', label: 'Video Demo' });
      if (camId === 'cam3') setCam3Source({ type: 'file', label: 'Video Demo' });
      fileInputRef.current?.click();
    }
  };

  // Online check helper: recognizes 'ONLINE', 'connected', or active frames/stream
  const isOnlineStatus = (status: string, hasVisualContent: boolean) => {
    const s = (status || '').toLowerCase();
    return s === 'online' || s === 'connected' || hasVisualContent;
  };

  const isCam1Online = cam1Source.type === 'backend'
    ? isOnlineStatus(cam1Status, !!cam1PreviewUrl)
    : (isMonitoring && (cam1StreamActive || sourceType === 'file'));

  const isCam2Online = cam2Source.type === 'backend'
    ? isOnlineStatus(cam2Status, !!cam2PreviewUrl)
    : (isMonitoring && cam2StreamActive);

  const isCam3Online = cam3Source.type === 'backend'
    ? isOnlineStatus(cam3Status, !!cam3PreviewUrl)
    : (isMonitoring && cam3StreamActive);

  // Calculate real active violation count (Critical / Red flag)
  const redViolationCount = recentIncidents.filter(
    i => i.level === 'red' && i.status !== 'dismissed'
  ).length;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#F8FBFF] overflow-hidden font-sans select-none">
      {/* ========================================================================= */}
      {/* 1. MONITORING TOOLBAR                                                     */}
      {/* ========================================================================= */}
      <MonitoringToolbar
        acqFps={fps || telemetry.acquisition_fps || 0}
        aiFps={telemetry.inference_fps || 0}
        latencyMs={telemetry.latency_ms || 0}
        violationCount={redViolationCount}
        cameraMode={cameraMode}
        onToggleCameraMode={handleToggleCameraMode}
        isDemoReadOnly={isDemoReadOnly}
        sourceType={sourceType}
        onTriggerDemoUpload={() => {
          if (sourceType === 'webcam') {
            fileInputRef.current?.click();
          } else {
            setSourceType('webcam');
          }
        }}
        showOverlays={showOverlays}
        onToggleOverlays={() => setShowOverlays(!showOverlays)}
      />

      {/* Hidden File Input for Video Testing */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileUpload} 
        accept="video/mp4,video/webm" 
        className="hidden" 
      />

      {/* Offline Warning Banner (Rule 9: Graceful Fallback if WebSocket drops) */}
      {!wsConnected && cam1Source.type !== 'backend' && (
        <div className="px-4 py-1.5 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs flex items-center justify-between font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            MẤT KẾT NỐI WEBSOCKET MÁY CHỦ ({wsError || 'Đang tự động kết nối lại...'})
          </span>
          <span className="text-[10px] text-rose-600 font-semibold">Chế độ Offline-First</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. MAIN DASHBOARD CONTENT AREA: CAMERAS (78%) & SIDEBAR (22%)             */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col lg:flex-row gap-3.5 p-3 sm:p-4 min-h-0 overflow-y-auto lg:overflow-hidden">
        {/* LEFT COLUMN: CAMERA GRID (Occupies ~78% on Desktop) */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className={`grid gap-3.5 flex-1 min-h-0 ${
            cameraMode === 'TRIPLE_CAMERA'
              ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
              : cameraMode === 'DUAL_CAMERA'
              ? 'grid-cols-1 lg:grid-cols-2'
              : 'grid-cols-1'
          }`}>
            {/* Camera 1: Góc Trước (Bàn thi) */}
            <CameraCard
              cameraId="cam1"
              title="Camera 1"
              subtitle="Góc trước (Bàn thi)"
              footerLabel="Camera 1 - Bàn thi"
              room="Phòng thi số 1"
              isOnline={isCam1Online}
              fps={cam1Source.type === 'backend' ? 15 : (fps || telemetry.acquisition_fps || 0)}
              resolution="1920 × 1080"
              detections={cam1Source.type === 'backend' ? cam1Detections : liveDetections.filter(d => !d.source_id || d.source_id === 'cam1' || d.source_id === 'webcam_local')}
              showOverlays={showOverlays}
              statusReason={cam1StatusReason}
              previewUrl={cam1Source.type === 'backend' ? cam1PreviewUrl : null}
              videoNode={
                cam1Source.type !== 'backend' ? (
                  <LocalVideoViewport
                    stream={cam1MediaStream}
                    src={fileVideoUrl}
                    videoRef={cam1VideoRef}
                    loop={sourceType === 'file'}
                  />
                ) : undefined
              }
              currentSourceId={cam1Source.type === 'device' ? `device:${cam1Source.deviceId}` : cam1Source.type === 'backend' ? `backend:${cam1Source.backendSourceId || 'cam1'}` : 'file:demo'}
              currentSourceLabel={cam1Source.label}
              availableSources={getAvailableSources('cam1', cam1Source)}
              onSelectSource={(opt) => handleSelectSource('cam1', opt)}
              onScanDevices={refreshVideoDevices}
            />

            {/* Camera 2: Góc Bên (Bao quát / Giấy thi) - Active in Dual & Triple mode */}
            {(cameraMode === 'DUAL_CAMERA' || cameraMode === 'TRIPLE_CAMERA') && (
              <CameraCard
                cameraId="cam2"
                title="Camera 2"
                subtitle="Góc bên (Bao quát / Giấy thi)"
                footerLabel="Camera 2 - Góc bên"
                room="Phòng thi số 1"
                isOnline={isCam2Online}
                fps={isCam2Online ? 15 : 0}
                resolution="1920 × 1080"
                detections={cam2Detections.length > 0 ? cam2Detections : liveDetections.filter(d => d.source_id === 'cam2')}
                showOverlays={showOverlays}
                statusReason={cam2StatusReason}
                previewUrl={cam2Source.type === 'backend' ? cam2PreviewUrl : null}
                videoNode={
                  cam2Source.type === 'device' ? (
                    <LocalVideoViewport
                      stream={cam2MediaStream}
                      videoRef={cam2VideoRef}
                    />
                  ) : undefined
                }
                currentSourceId={cam2Source.type === 'device' ? `device:${cam2Source.deviceId}` : cam2Source.type === 'backend' ? `backend:${cam2Source.backendSourceId || 'cam2'}` : 'file:demo'}
                currentSourceLabel={cam2Source.label}
                availableSources={getAvailableSources('cam2', cam2Source)}
                onSelectSource={(opt) => handleSelectSource('cam2', opt)}
                onScanDevices={refreshVideoDevices}
              />
            )}

            {/* Camera 3: Toàn Cảnh (Bao quát phòng) - Active in Triple mode */}
            {cameraMode === 'TRIPLE_CAMERA' && (
              <CameraCard
                cameraId="cam3"
                title="Camera 3"
                subtitle="Toàn cảnh (Bao quát phòng)"
                footerLabel="Camera 3 - Toàn cảnh"
                room="Phòng thi số 1"
                isOnline={isCam3Online}
                fps={isCam3Online ? 15 : 0}
                resolution="1920 × 1080"
                detections={cam3Detections.length > 0 ? cam3Detections : liveDetections.filter(d => d.source_id === 'cam3')}
                showOverlays={showOverlays}
                statusReason={cam3StatusReason}
                previewUrl={cam3Source.type === 'backend' ? cam3PreviewUrl : null}
                videoNode={
                  cam3Source.type === 'device' ? (
                    <LocalVideoViewport
                      stream={cam3MediaStream}
                      videoRef={cam3VideoRef}
                    />
                  ) : undefined
                }
                currentSourceId={cam3Source.type === 'device' ? `device:${cam3Source.deviceId}` : cam3Source.type === 'backend' ? `backend:${cam3Source.backendSourceId || 'cam3'}` : 'file:demo'}
                currentSourceLabel={cam3Source.label}
                availableSources={getAvailableSources('cam3', cam3Source)}
                onSelectSource={(opt) => handleSelectSource('cam3', opt)}
                onScanDevices={refreshVideoDevices}
              />
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: INCIDENT SIDEBAR (Occupies ~22% on Desktop / 343px width) */}
        <IncidentSidebar
          incidents={recentIncidents}
          onOpenVideoModal={onOpenVideoModal}
          onConfirmIncident={handleConfirm}
          onDismissIncident={handleDismiss}
          onDeleteIncident={handleDeleteIncident}
          onPurgeAllVideos={handlePurgeAllVideos}
          error={incidentError || incidentFeedError}
          isReadOnly={isDemoReadOnly}
          onRefresh={fetchIncidents}
          isRefreshing={isPolling}
        />
      </div>

      {/* ========================================================================= */}
      {/* 3. DASHBOARD FOOTER                                                       */}
      {/* ========================================================================= */}
      <DashboardFooter />
    </div>
  );
};
