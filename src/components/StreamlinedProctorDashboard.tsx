import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  SlidersHorizontal, 
  Check, 
  X, 
  AlertTriangle, 
  Clock, 
  Film, 
  RefreshCw, 
  Eye, 
  EyeOff,
  ShieldCheck, 
  ShieldAlert,
  Camera
} from 'lucide-react';
import { Incident } from '../types';
import { getIncidents, confirmIncident, resetSessionState } from '../services/api';
import { 
  aiModelService, 
  AIDetectionResult, 
  WebSocketIngestClient, 
  IngestTelemetry, 
  WebSocketDetectionPayload 
} from '../services/aiModelService';

export interface CameraDevice {
  deviceId: string;
  label: string;
}

interface StreamlinedDashboardProps {
  onOpenVideoModal: (incident: Incident) => void;
  onConfirmIncident?: (incidentId: string) => void;
  onDismissIncident?: (incidentId: string) => void;
  onActiveSourceChange?: (sourceName: string) => void;
}

export const StreamlinedProctorDashboard: React.FC<StreamlinedDashboardProps> = ({
  onOpenVideoModal,
  onConfirmIncident,
  onDismissIncident,
  onActiveSourceChange
}) => {
  // Video Stream Source & Camera Selection
  const [sourceType, setSourceType] = useState<'webcam' | 'file'>('webcam');
  const [availableCameras, setAvailableCameras] = useState<CameraDevice[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>(() => {
    return localStorage.getItem('ai_exam_selected_camera_id') || '';
  });
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [showOverlays, setShowOverlays] = useState(true);
  const [fps, setFps] = useState(15);
  const [wsConnected, setWsConnected] = useState(true);
  const [wsError, setWsError] = useState<string | null>(null);

  // Video Element & Stream Refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);
  const offscreenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const ingestClientRef = useRef<WebSocketIngestClient | null>(null);
  const captureInFlightRef = useRef<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Telemetry state
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
  const [activeIncidentLevel, setActiveIncidentLevel] = useState<'normal' | 'yellow' | 'red'>('normal');

  // Enumerate all connected video input devices
  const updateCameraList = async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return [];
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices
        .filter(d => d.kind === 'videoinput')
        .map((d, index) => ({
          deviceId: d.deviceId,
          label: d.label || `Camera ${index + 1}`
        }));
      setAvailableCameras(videoDevices);
      return videoDevices;
    } catch (err) {
      console.warn('[Dashboard] Lỗi liệt kê camera:', err);
      return [];
    }
  };

  // 1. Initialize Webcam Stream with device selection
  useEffect(() => {
    let isCancelled = false;

    if (sourceType === 'webcam') {
      const startCamera = async () => {
        try {
          if (webcamStreamRef.current) {
            webcamStreamRef.current.getTracks().forEach(t => t.stop());
            webcamStreamRef.current = null;
          }

          const constraints: MediaStreamConstraints = {
            video: selectedCameraId 
              ? { deviceId: { exact: selectedCameraId }, width: { ideal: 1280 }, height: { ideal: 720 } }
              : { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
          };

          let stream: MediaStream;
          try {
            stream = await navigator.mediaDevices.getUserMedia(constraints);
          } catch (deviceErr) {
            console.warn('[Dashboard] Không thể mở camera đã chọn, thử camera mặc định:', deviceErr);
            stream = await navigator.mediaDevices.getUserMedia({
              video: { width: { ideal: 1280 }, height: { ideal: 720 } },
              audio: false
            });
          }

          if (isCancelled) {
            stream.getTracks().forEach(t => t.stop());
            return;
          }

          webcamStreamRef.current = stream;
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(() => {});
          }

          // Liệt kê danh sách camera sau khi đã được cấp quyền duyệt MediaDevices
          const cams = await updateCameraList();
          if (cams && cams.length > 0) {
            const currentTrack = stream.getVideoTracks()[0];
            const currentSettings = currentTrack?.getSettings();
            const activeId = currentSettings?.deviceId || cams[0].deviceId;

            if (!selectedCameraId || !cams.some(c => c.deviceId === selectedCameraId)) {
              setSelectedCameraId(activeId);
              localStorage.setItem('ai_exam_selected_camera_id', activeId);
            }

            const activeCam = cams.find(c => c.deviceId === (selectedCameraId || activeId));
            const label = activeCam?.label || 'Webcam Giám Sát';
            onActiveSourceChange?.(label);
          } else {
            onActiveSourceChange?.('Webcam Giám Sát');
          }
        } catch (err) {
          console.warn('[Dashboard] Không thể mở webcam:', err);
        }
      };

      startCamera();

      // Lắng nghe sự kiện cắm/rút webcam USB để tự cập nhật danh sách
      const handleDeviceChange = () => {
        updateCameraList();
      };
      navigator.mediaDevices?.addEventListener?.('devicechange', handleDeviceChange);

      return () => {
        isCancelled = true;
        navigator.mediaDevices?.removeEventListener?.('devicechange', handleDeviceChange);
        if (webcamStreamRef.current) {
          webcamStreamRef.current.getTracks().forEach(t => t.stop());
          webcamStreamRef.current = null;
        }
      };
    } else {
      if (webcamStreamRef.current) {
        webcamStreamRef.current.getTracks().forEach(t => t.stop());
        webcamStreamRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    }
  }, [sourceType, selectedCameraId]);

  // 2. High-Density WebSocket Ingestion Pipeline (15 FPS, Decoupled Recording & Inference)
  useEffect(() => {
    if (!isMonitoring) {
      if (ingestClientRef.current) {
        const oldSession = ingestClientRef.current.getSessionId();
        ingestClientRef.current.disconnect();
        ingestClientRef.current = null;
        resetSessionState(oldSession).catch(() => {});
      }
      return;
    }

    const sourceId = sourceType === 'webcam' ? 'webcam_local' : 'video_file_local';
    const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
    const initialSessionId = urlParams?.get('session_id') || undefined;
    const client = new WebSocketIngestClient(sourceId, initialSessionId);
    ingestClientRef.current = client;

    // Connect WebSocket
    client.connect(
      // onDetection callback
      (payload: WebSocketDetectionPayload) => {
        if (payload.detections) {
          setLiveDetections(payload.detections);
        }
        if (payload.level === 'red') {
          setActiveIncidentLevel('red');
        } else if (payload.level === 'yellow') {
          setActiveIncidentLevel('yellow');
        } else {
          setActiveIncidentLevel('normal');
        }
      },
      // onTelemetry callback
      (t: IngestTelemetry) => {
        setTelemetry({ ...t });
        (window as any).__EXAM_TELEMETRY__ = { ...t };
        if (t.acquisition_fps > 0) {
          setFps(t.acquisition_fps);
        }
      },
      // onStatus callback
      (isConnected: boolean, error?: string) => {
        setWsConnected(isConnected);
        setWsError(error || null);
        if (isConnected) {
          (window as any).__EXAM_BENCHMARK_READY__ = true;
        }
      }
    );

    // Global hook for automated reproducible benchmark synchronization
    (window as any).__EXAM_RESET_BENCHMARK__ = async (newSessionId?: string) => {
      const sid = newSessionId || `bench_${Date.now()}`;
      return await client.resetSession(sid);
    };

    // Capture & Stream frames at target 15 FPS (~66ms)
    const intervalMs = 66; // 15 FPS
    const frameTimer = setInterval(() => {
      client.recordCaptureAttempt();
      if (captureInFlightRef.current) {
        return;
      }
      const videoEl = videoRef.current;
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

    // Global hook to cleanly freeze capture and close session during benchmarks
    (window as any).__EXAM_STOP_BENCHMARK__ = () => {
      clearInterval(frameTimer);
      captureInFlightRef.current = false;
      client.disconnect();
      return (window as any).__EXAM_TELEMETRY__;
    };

    return () => {
      clearInterval(frameTimer);
      captureInFlightRef.current = false;
      const oldSession = client.getSessionId();
      client.disconnect();
      if (ingestClientRef.current === client) {
        ingestClientRef.current = null;
      }
      resetSessionState(oldSession).catch(() => {});
    };
  }, [isMonitoring, sourceType]);

  // 3. Polling Incident Feed from SQLite every 2 seconds
  const fetchIncidents = async () => {
    try {
      setIsPolling(true);
      const data = await getIncidents({ limit: 30 });
      if (data && data.length > 0) {
        setRecentIncidents(data);
      }
    } catch (err) {
      console.warn('[Dashboard] Lỗi polling sự cố từ SQLite:', err);
    } finally {
      setIsPolling(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const timer = setInterval(fetchIncidents, 2000);
    return () => clearInterval(timer);
  }, []);

  // 4. File Video Upload Handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !videoRef.current) return;
    const url = URL.createObjectURL(file);
    setSourceType('file');
    onActiveSourceChange?.(`Tập tin: ${file.name}`);
    videoRef.current.srcObject = null;
    videoRef.current.src = url;
    videoRef.current.play().catch(() => {});
  };

  // Handle switching camera device
  const handleCameraChange = (deviceId: string) => {
    setSelectedCameraId(deviceId);
    localStorage.setItem('ai_exam_selected_camera_id', deviceId);
    const cam = availableCameras.find(c => c.deviceId === deviceId);
    if (cam) {
      onActiveSourceChange?.(cam.label);
    }
  };

  // 5. Operator Action Handlers
  const handleConfirm = async (incId: string) => {
    try {
      await confirmIncident(incId, { status: 'confirmed' });
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'confirmed' } : i));
    } catch (err) {
      console.error('Lỗi xác nhận sự cố:', err);
    }
    if (onConfirmIncident) onConfirmIncident(incId);
  };

  const handleDismiss = async (incId: string) => {
    try {
      await confirmIncident(incId, { status: 'dismissed' });
      setRecentIncidents(prev => prev.map(i => i.id === incId ? { ...i, status: 'dismissed' } : i));
    } catch (err) {
      console.error('Lỗi bỏ qua sự cố:', err);
    }
    if (onDismissIncident) onDismissIncident(incId);
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-zinc-950 p-3 gap-3 font-sans select-none">
      {/* ========================================================================= */}
      {/* CỘT TRÁI (70%): VIEWPORT CAMERA & TELEMETRY                                */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col min-w-0 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        {/* Offline Warning Banner (Rule 9: Graceful Fallback) */}
        {!wsConnected && (
          <div className="px-3 py-1.5 bg-zinc-900 border-b border-rose-800 text-rose-300 text-xs flex items-center justify-between font-mono">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              MẤT KẾT NỐI WEBSOCKET MÁY CHỦ ({wsError || 'Đang tự động kết nối lại...'})
            </span>
            <span className="text-[10px] text-rose-400">Offline-First</span>
          </div>
        )}

        {/* Telemetry Header Bar */}
        <div className="h-11 px-3 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between text-xs">
          {/* Left: Source Status & Camera Selector */}
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 font-mono text-[11px]">
              <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {wsConnected ? 'LIVE' : 'DISCONNECTED'}
            </span>

            {sourceType === 'webcam' ? (
              <div className="flex items-center gap-1.5 bg-zinc-950 border border-zinc-750 rounded px-2 py-0.5">
                <Camera className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                <select
                  value={selectedCameraId}
                  onChange={(e) => handleCameraChange(e.target.value)}
                  className="bg-transparent text-zinc-200 text-xs font-mono focus:outline-none cursor-pointer max-w-[150px] sm:max-w-[210px] truncate"
                  title="Chọn nguồn camera đầu vào"
                >
                  {availableCameras.length === 0 ? (
                    <option value="" className="bg-zinc-900 text-zinc-400">Đang tìm camera...</option>
                  ) : (
                    availableCameras.map((cam, idx) => (
                      <option key={cam.deviceId || idx} value={cam.deviceId} className="bg-zinc-900 text-zinc-200">
                        {cam.label || `Camera ${idx + 1}`}
                      </option>
                    ))
                  )}
                </select>
                <button
                  type="button"
                  onClick={() => updateCameraList()}
                  title="Làm mới danh sách camera"
                  className="text-zinc-400 hover:text-zinc-200 transition-colors p-0.5 ml-0.5"
                >
                  <RefreshCw className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <span className="text-zinc-300 font-medium text-xs">
                Tập Tin Video Demo
              </span>
            )}
          </div>

          {/* Right: Telemetry & Controls */}
          <div className="flex items-center gap-2">
            {/* Acquisition FPS */}
            <div className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 font-mono text-[11px] text-zinc-300">
              Acq: <span className="text-emerald-400 font-semibold">{fps} FPS</span>
            </div>

            {/* AI Inference FPS & Latency */}
            <div className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 font-mono text-[11px] text-zinc-300">
              AI: <span className="text-cyan-400 font-semibold">{telemetry.inference_fps} FPS</span>
              {telemetry.latency_ms > 0 && <span className="text-zinc-400 ml-1">({telemetry.latency_ms}ms)</span>}
            </div>

            {/* Backpressure Dropped Frames */}
            {telemetry.transport_dropped_frames > 0 && (
              <div className="px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800 font-mono text-[11px] text-amber-300">
                Drop: <span className="font-semibold">{telemetry.transport_dropped_frames}</span>
              </div>
            )}

            {/* Inference Superseded Frames */}
            {telemetry.inference_superseded_frames > 0 && (
              <div className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 font-mono text-[11px] text-zinc-400" title="Frame bị thay thế bởi frame mới hơn khi AI bận">
                Superseded: <span className="font-semibold text-zinc-200">{telemetry.inference_superseded_frames}</span>
              </div>
            )}

            {/* AI Status Badge */}
            <div className={`px-2.5 py-0.5 rounded font-mono text-[11px] font-medium border flex items-center gap-1.5 ${
              activeIncidentLevel === 'red'
                ? 'bg-rose-950/80 text-rose-300 border-rose-800'
                : activeIncidentLevel === 'yellow'
                ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                : 'bg-zinc-800 text-emerald-400 border-zinc-700'
            }`}>
              {activeIncidentLevel === 'red' ? (
                <>
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  <span>VI PHẠM (CỜ ĐỎ)</span>
                </>
              ) : activeIncidentLevel === 'yellow' ? (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>NGHI VẤN (CỜ VÀNG)</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>BÌNH THƯỜNG</span>
                </>
              )}
            </div>

            {/* Hidden Video File Input */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              accept="video/mp4,video/webm" 
              className="hidden" 
            />

            {/* Source Switcher Button */}
            <button
              onClick={() => {
                if (sourceType === 'webcam') {
                  fileInputRef.current?.click();
                } else {
                  setSourceType('webcam');
                }
              }}
              className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-750 border border-zinc-700 text-zinc-200 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <SlidersHorizontal className="w-3 h-3 text-zinc-400" />
              <span>{sourceType === 'webcam' ? 'Nạp Video Demo' : 'Dùng Webcam'}</span>
            </button>

            {/* Toggle Bounding Box Overlays */}
            <button
              onClick={() => setShowOverlays(!showOverlays)}
              title="Bật/tắt hiển thị khung nhận diện AI"
              className={`px-2.5 py-1 rounded border text-xs font-medium flex items-center gap-1.5 transition-colors ${
                showOverlays 
                  ? 'bg-zinc-800 border-zinc-600 text-zinc-100' 
                  : 'bg-zinc-900 border-zinc-800 text-zinc-500'
              }`}
            >
              {showOverlays ? <Eye className="w-3 h-3 text-zinc-300" /> : <EyeOff className="w-3 h-3 text-zinc-500" />}
              <span>Khung AI: {showOverlays ? 'BẬT' : 'TẮT'}</span>
            </button>
          </div>
        </div>

        {/* Viewport Video Canvas Container */}
        <div className="relative flex-1 bg-black flex items-center justify-center overflow-hidden">
          <video
            ref={videoRef}
            playsInline
            autoPlay
            loop={sourceType === 'file'}
            muted
            className="w-full h-full object-contain"
          />

          {/* AI Bounding Box Overlays */}
          {showOverlays && (
            <div className="absolute inset-0 pointer-events-none">
              {liveDetections.map((det) => {
                const [left, top, width, height] = det.bbox;
                const isRed = det.level === 'red';
                const isYellow = det.level === 'yellow';

                return (
                  <div
                    key={det.id}
                    style={{
                      left: `${left}%`,
                      top: `${top}%`,
                      width: `${width}%`,
                      height: `${height}%`,
                    }}
                    className={`absolute rounded border transition-all duration-75 ${
                      isRed
                        ? 'border-rose-500 bg-rose-500/10'
                        : isYellow
                        ? 'border-amber-400 bg-amber-400/10'
                        : 'border-emerald-500/80 bg-emerald-500/5'
                    }`}
                  >
                    <span
                      className={`absolute -top-5 left-0 text-[10px] font-mono font-medium px-1.5 py-0.2 rounded text-white ${
                        isRed ? 'bg-rose-600' : isYellow ? 'bg-amber-600' : 'bg-emerald-600'
                      }`}
                    >
                      {det.label_vi} ({det.confidence}%)
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Bottom Stream Status Strip */}
          <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between px-3 py-1.5 rounded bg-zinc-950/90 border border-zinc-800 text-[11px] font-mono text-zinc-400">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMonitoring(!isMonitoring)}
                className="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-[11px] flex items-center gap-1 transition-colors"
              >
                {isMonitoring ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                <span>{isMonitoring ? 'Tạm Dừng AI' : 'Bật Giám Sát'}</span>
              </button>
              <span>Trạng thái: <strong className={isMonitoring ? 'text-emerald-400' : 'text-zinc-500'}>{isMonitoring ? 'Đang phân tích' : 'Tạm ngừng'}</strong></span>
            </div>

            <div className="flex items-center gap-2">
              <span>RingBuffer: <strong className="text-zinc-200">15 FPS Realtime (Pre 5.0s / Post 10.0s)</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CỘT PHẢI (30%): INCIDENT FEED & VIDEO CLIPS                               */}
      {/* ========================================================================= */}
      <div className="w-full lg:w-[380px] flex flex-col min-w-0 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden shrink-0">
        {/* Header */}
        <div className="h-11 px-3 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Film className="w-4 h-4 text-zinc-400" />
            <h2 className="font-semibold text-zinc-200 tracking-tight">
              SỰ CỐ VI PHẠM ({recentIncidents.length})
            </h2>
          </div>
          <button 
            onClick={fetchIncidents} 
            title="Làm mới danh sách sự cố"
            className={`p-1 text-zinc-400 hover:text-zinc-200 rounded hover:bg-zinc-800 transition-colors ${isPolling ? 'animate-spin' : ''}`}
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Incident List Cards */}
        <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5 divide-y-0">
          {recentIncidents.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-center p-4 text-zinc-500">
              <ShieldCheck className="w-8 h-8 text-emerald-500/40 mb-2" />
              <p className="text-xs font-medium text-zinc-400">Chưa ghi nhận vi phạm</p>
              <p className="text-[11px] text-zinc-600 mt-0.5">Hệ thống AI sẽ tự động ghi clip khi phát hiện quay đầu hoặc điện thoại.</p>
            </div>
          ) : (
            recentIncidents.map((inc) => {
              const isRed = inc.level === 'red';
              const snapTargetUrl = inc.thumbnailUrl || `http://localhost:8000/evidence/${inc.id}_snap.jpg`;
              const trackLabel = inc.trackId !== undefined ? `Track ${inc.trackId}` : 'Track không xác định';
              const timeDisplay = inc.detectedAt ? new Date(inc.detectedAt).toLocaleTimeString('vi-VN') : 'Vừa xong';

              return (
                <div
                  key={inc.id}
                  className={`p-2.5 rounded-md border text-xs flex flex-col gap-2 transition-colors ${
                    isRed
                      ? 'bg-zinc-950 border-rose-900/60 hover:border-rose-700'
                      : 'bg-zinc-950 border-amber-900/60 hover:border-amber-700'
                  }`}
                >
                  {/* Card Header: Level Badge & Time */}
                  <div className="flex items-center justify-between">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                      isRed ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {isRed ? 'Cờ Đỏ' : 'Cờ Vàng'} • {inc.typeNameVi}
                    </span>
                    <span className="text-[11px] font-mono text-zinc-400 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-zinc-500" />
                      {timeDisplay}
                    </span>
                  </div>

                  {/* Thumbnail & Click to Play Clip */}
                  <div 
                    onClick={() => onOpenVideoModal(inc)}
                    className="relative aspect-video rounded overflow-hidden bg-black border border-zinc-800 cursor-pointer group"
                  >
                    <img
                      src={snapTargetUrl}
                      alt="Thumbnail vi phạm"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180"><rect fill="%2318181b" width="320" height="180"/><text fill="%2371717a" font-family="sans-serif" font-size="12" x="50%" y="50%" text-anchor="middle" dominant-baseline="middle">Evidence Snapshot</text></svg>';
                      }}
                    />
                    {/* Play Button Overlay */}
                    <div className="absolute inset-0 bg-black/40 group-hover:bg-black/20 flex items-center justify-center transition-colors">
                      <div className="w-8 h-8 rounded-full bg-zinc-900/90 border border-zinc-700 text-zinc-100 flex items-center justify-center shadow">
                        <Play className="w-4 h-4 ml-0.5 text-zinc-200" />
                      </div>
                    </div>
                    <span className="absolute bottom-1 right-1 px-1 py-0.2 rounded bg-black/80 font-mono text-[9px] text-zinc-300">
                      Clip MP4
                    </span>
                  </div>

                  {/* Footer Meta & Actions */}
                  <div className="flex items-center justify-between pt-1 border-t border-zinc-800/80">
                    <span className="text-[11px] font-mono text-zinc-400">
                      {trackLabel} • <strong>{inc.confidence.toFixed(1)}%</strong>
                    </span>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => onOpenVideoModal(inc)}
                        className="px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-750 text-zinc-200 text-[11px] font-medium border border-zinc-700 transition-colors flex items-center gap-1"
                      >
                        <Play className="w-3 h-3" />
                        <span>Xem Clip</span>
                      </button>

                      {inc.status === 'pending' ? (
                        <>
                          <button
                            onClick={() => handleDismiss(inc.id)}
                            title="Bỏ qua cảnh báo"
                            className="px-1.5 py-0.5 rounded bg-zinc-800 hover:bg-zinc-750 text-zinc-400 hover:text-zinc-200 text-[11px] border border-zinc-700 transition-colors"
                          >
                            <X className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => handleConfirm(inc.id)}
                            title="Xác nhận vi phạm"
                            className="px-1.5 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 text-[11px] font-medium border border-emerald-700 transition-colors"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                        </>
                      ) : (
                        <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                          inc.status === 'confirmed' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                        }`}>
                          {inc.status === 'confirmed' ? 'Đã duyệt' : 'Đã bỏ qua'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
