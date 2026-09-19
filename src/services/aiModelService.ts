/**
 * ================================================================================
 * AI Model Service & High-Density WebSocket Ingestion Client - AI EXAM CONTROL
 * ================================================================================
 * Zero examinee identity handling.
 * Sprint 1.2:
 * - 15 FPS WebSocket binary ingestion client.
 * - Backpressure guard (bufferedAmount > 65536).
 * - Bounded reconnect with fresh session_id.
 * - Monotonic timestamp & sequence ID header packing (16 bytes).
 * ================================================================================
 */

export interface AIDetectionResult {
  id: string;
  label: string;
  label_vi: string;
  confidence: number;
  bbox: [number, number, number, number]; // [left%, top%, width%, height%]
  level: 'red' | 'yellow' | 'green';
  raw_coords?: [number, number, number, number];
  track_id?: number;
}

export interface FrameDetectionResponse {
  success: boolean;
  timestamp: string;
  detections: AIDetectionResult[];
  has_cheating: boolean;
  has_phone: boolean;
  new_incident?: any;
  total_detections: number;
  error?: string;
  observed_acquisition_fps?: number;
  inference_fps?: number;
}

export interface AIStatusResponse {
  status: 'ONLINE' | 'OFFLINE' | 'STANDBY';
  timestamp: string;
  device: string;
  fps_estimate: number;
  active_models: {
    pose_estimator: string;
    phone_detector: string;
  };
  total_session_incidents: number;
  database_connected: boolean;
  ring_buffer_state?: string;
  inference_queue_stats?: {
    total_enqueued: number;
    total_inferred: number;
    total_superseded: number;
    backlog_depth: number;
  };
}

export interface WebSocketDetectionPayload {
  // Core message identifiers (Required)
  type: string;                               // Message type, e.g. "detection_result"
  source_id: string;                          // Physical video/camera source identifier
  session_id: string;                         // Ephemeral session identifier
  sequence_id: number;                        // Monotonically increasing frame sequence ID (int64)
  timestamp: number;                          // Frame timestamp in seconds (monotonic or epoch)

  // Real-time inference metrics (Required)
  latency_ms: number;                         // Inference latency in milliseconds (ms, instantaneous)
  inference_fps: number;                      // Model inference rate in frames per second (FPS, instantaneous)
  level: 'red' | 'yellow' | 'green';          // Incident escalation level
  has_cheating: boolean;                      // True if RED violation detected
  has_phone: boolean;                         // True if phone detected

  // Incident reference (Optional, present when RED incident triggered)
  incident_id?: string;                       // Unique incident identifier
  detections: AIDetectionResult[];            // Bounding boxes and keypoint results

  // Server Ingest Telemetry (Optional, cumulative counters & arrival metrics)
  server_packets_received?: number;           // Total raw binary packets received on connection (cumulative count)
  server_frames_decoded?: number;             // Total valid JPEG frames decoded by server (cumulative count)
  server_received_frames?: number;            // Alias for server_frames_decoded (backwards compatibility)
  first_decoded_monotonic?: number;           // Server monotonic timestamp of first decoded frame (seconds)
  last_decoded_monotonic?: number;            // Server monotonic timestamp of latest decoded frame (seconds)
  effective_acquisition_fps?: number;         // Server-observed frame acquisition rate (FPS, instantaneous/windowed)

  // Server Inference Queue Telemetry (Optional, cumulative counters & instantaneous queue state)
  inference_submitted_frames?: number;        // Total frames enqueued into SingleSlotInferenceBuffer (cumulative count)
  inference_superseded_frames?: number;       // Total frames superseded in single-slot buffer (cumulative count)
  inference_processed_frames?: number;        // Total frames on which inference completed (cumulative count)
  processed_inference_frames?: number;        // Alias for inference_processed_frames (backwards compatibility)
  inference_pending_frames?: number;          // Frames currently in slot or actively in-flight (instantaneous count, <= 2)
  pending_inference_frames?: number;          // Alias for inference_pending_frames (backwards compatibility)

  // Server Result Dispatch Telemetry (Optional, cumulative counters)
  result_messages_sent?: number;              // Total WebSocket result messages dispatched (cumulative count)
  detection_results_sent?: number;            // Alias for result_messages_sent (backwards compatibility)
  detected_objects?: number;                  // Cumulative detected objects across all processed frames
}

export interface IngestTelemetry {
  // 12 Standardized Telemetry Counters (Sprint 1.2D)
  capture_attempts: number;
  capture_encoded_frames: number;
  sent_frames: number;
  client_backpressure_drops: number;

  server_packets_received: number;
  server_frames_decoded: number;
  server_received_frames: number;

  inference_submitted_frames: number;
  inference_superseded_frames: number;
  inference_processed_frames: number;
  processed_inference_frames: number;
  inference_pending_frames: number;
  pending_inference_frames: number;
  result_messages_sent: number;
  detection_results_sent: number;

  result_messages_received: number;
  detection_results_received: number;

  // Real-time telemetry metrics
  detected_objects: number;
  acquisition_fps: number;
  effective_acquisition_fps: number;
  inference_fps: number;
  latency_ms: number;

  // Aliases for backwards compatibility
  capture_frames: number;
  transport_dropped_frames: number;
}


export type DetectionCallback = (payload: WebSocketDetectionPayload) => void;
export type TelemetryCallback = (telemetry: IngestTelemetry) => void;
export type StatusCallback = (isConnected: boolean, error?: string) => void;

const API_BASE_URL = 'http://localhost:8000';

class AIModelService {
  private isOnline: boolean = false;

  /**
   * Check connection to Backend Vision Engine
   */
  async checkStatus(): Promise<AIStatusResponse | null> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/status`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        const data: AIStatusResponse = await res.json();
        this.isOnline = true;
        return data;
      }
      this.isOnline = false;
      return null;
    } catch {
      this.isOnline = false;
      return null;
    }
  }

  getIsOnline(): boolean {
    return this.isOnline;
  }

  /**
   * [DEPRECATED in Sprint 1.2]: Sử dụng WebSocketIngestClient để đạt 15 FPS
   */
  async detectFrame(
    imageCanvasOrBase64: HTMLCanvasElement | string,
    sourceId: string = 'webcam_local'
  ): Promise<FrameDetectionResponse> {
    let base64Data = '';

    if (typeof imageCanvasOrBase64 === 'string') {
      base64Data = imageCanvasOrBase64;
    } else if (imageCanvasOrBase64 && imageCanvasOrBase64.toDataURL) {
      base64Data = imageCanvasOrBase64.toDataURL('image/jpeg', 0.75);
    }

    if (!base64Data) {
      return {
        success: false,
        timestamp: new Date().toLocaleTimeString(),
        detections: [],
        has_cheating: false,
        has_phone: false,
        total_detections: 0,
        error: 'No valid image data'
      };
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/detect/frame`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_base64: base64Data,
          source_id: sourceId,
          draw_boxes: true
        })
      });

      if (res.ok) {
        this.isOnline = true;
        return await res.json();
      } else {
        return {
          success: false,
          timestamp: new Date().toLocaleTimeString(),
          detections: [],
          has_cheating: false,
          has_phone: false,
          total_detections: 0,
          error: `HTTP ${res.status}`
        };
      }
    } catch (err: any) {
      this.isOnline = false;
      return {
        success: false,
        timestamp: new Date().toLocaleTimeString(),
        detections: [],
        has_cheating: false,
        has_phone: false,
        total_detections: 0,
        error: err?.message || 'Network error'
      };
    }
  }
}

export const aiModelService = new AIModelService();

/**
 * High-performance WebSocket binary streaming client (15 FPS).
 * Bounded reconnection, backpressure guard, telemetry counters.
 */
export class WebSocketIngestClient {
  private ws: WebSocket | null = null;
  private sourceId: string;
  private sessionId: string;
  private sequenceId: number = 0;
  private isConnected: boolean = false;
  private isReconnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimer: any = null;
  private stopped: boolean = false;

  private onDetection: DetectionCallback | null = null;
  private onTelemetry: TelemetryCallback | null = null;
  private onStatus: StatusCallback | null = null;

  public telemetry: IngestTelemetry = {
    capture_attempts: 0,
    capture_encoded_frames: 0,
    sent_frames: 0,
    client_backpressure_drops: 0,
    server_packets_received: 0,
    server_frames_decoded: 0,
    server_received_frames: 0,
    inference_submitted_frames: 0,
    inference_superseded_frames: 0,
    inference_processed_frames: 0,
    processed_inference_frames: 0,
    inference_pending_frames: 0,
    pending_inference_frames: 0,
    result_messages_sent: 0,
    detection_results_sent: 0,
    result_messages_received: 0,
    detection_results_received: 0,
    detected_objects: 0,
    acquisition_fps: 0,
    effective_acquisition_fps: 0,
    inference_fps: 0,
    latency_ms: 0,
    capture_frames: 0,
    transport_dropped_frames: 0
  };

  private lastRenderedSequenceId: number = -1;
  private lastFrameSentTime: number = 0;
  private sentTimestamps: number[] = [];
  private sessionStartTime: number = 0;

  constructor(sourceId: string = 'webcam_local', sessionId?: string) {
    this.sourceId = sourceId;
    this.sessionId = sessionId || this.generateSessionId();
  }

  private generateSessionId(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
  }

  public recordCaptureAttempt() {
    this.telemetry.capture_attempts++;
    this.telemetry.capture_frames = this.telemetry.capture_attempts;
  }

  public recordCaptureEncoded() {
    this.telemetry.capture_encoded_frames++;
  }

  public recordBackpressureDrop() {
    this.telemetry.client_backpressure_drops++;
    this.telemetry.transport_dropped_frames = this.telemetry.client_backpressure_drops;
    if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
  }

  public async resetSession(newSessionId: string): Promise<boolean> {
    console.log(`[WS_INGEST] Resetting session to ${newSessionId}...`);
    this.stopped = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      try {
        this.ws.close();
      } catch (e) {}
      this.ws = null;
    }
    this.sessionId = newSessionId;
    this.sequenceId = 0;
    this.lastRenderedSequenceId = -1;
    this.telemetry = {
      capture_attempts: 0,
      capture_encoded_frames: 0,
      sent_frames: 0,
      client_backpressure_drops: 0,
      server_packets_received: 0,
      server_frames_decoded: 0,
      server_received_frames: 0,
      inference_submitted_frames: 0,
      inference_superseded_frames: 0,
      inference_processed_frames: 0,
      processed_inference_frames: 0,
      inference_pending_frames: 0,
      pending_inference_frames: 0,
      result_messages_sent: 0,
      detection_results_sent: 0,
      result_messages_received: 0,
      detection_results_received: 0,
      detected_objects: 0,
      acquisition_fps: 0,
      effective_acquisition_fps: 0,
      inference_fps: 0,
      latency_ms: 0,
      capture_frames: 0,
      transport_dropped_frames: 0
    };
    this.sentTimestamps = [];
    this.sessionStartTime = performance.now() / 1000.0;
    (window as any).__EXAM_TELEMETRY__ = { ...this.telemetry };
    (window as any).__EXAM_BENCHMARK_READY__ = false;

    return new Promise<boolean>((resolve) => {
      this.connect(
        this.onDetection || undefined,
        (t) => {
          if (this.onTelemetry) this.onTelemetry(t);
          (window as any).__EXAM_TELEMETRY__ = { ...t };
        },
        (isConnected, err) => {
          if (this.onStatus) this.onStatus(isConnected, err);
          if (isConnected) {
            (window as any).__EXAM_BENCHMARK_READY__ = true;
            resolve(true);
          }
        }
      );
    });
  }

  public connect(
    onDetection?: DetectionCallback,
    onTelemetry?: TelemetryCallback,
    onStatus?: StatusCallback
  ) {
    this.stopped = false;
    if (onDetection) this.onDetection = onDetection;
    if (onTelemetry) this.onTelemetry = onTelemetry;
    if (onStatus) this.onStatus = onStatus;

    if (!this.sessionId) {
      this.sessionId = this.generateSessionId();
    }
    this.sequenceId = 0;
    this.lastRenderedSequenceId = -1;

    const wsUrl = `ws://localhost:8000/api/ws/ingest?source_id=${encodeURIComponent(this.sourceId)}&session_id=${encodeURIComponent(this.sessionId)}`;
    console.log(`[WS_INGEST] Connecting to ${wsUrl}`);

    try {
      this.ws = new WebSocket(wsUrl);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = () => {
        console.log(`[WS_INGEST] Connected: session=${this.sessionId}`);
        this.isConnected = true;
        this.isReconnecting = false;
        this.reconnectAttempts = 0;

        // Reset telemetry for new session - start cleanly at 0
        this.telemetry = {
          capture_attempts: 0,
          capture_encoded_frames: 0,
          sent_frames: 0,
          client_backpressure_drops: 0,
          server_packets_received: 0,
          server_frames_decoded: 0,
          server_received_frames: 0,
          inference_submitted_frames: 0,
          inference_superseded_frames: 0,
          inference_processed_frames: 0,
          processed_inference_frames: 0,
          inference_pending_frames: 0,
          pending_inference_frames: 0,
          result_messages_sent: 0,
          detection_results_sent: 0,
          result_messages_received: 0,
          detection_results_received: 0,
          detected_objects: 0,
          acquisition_fps: 0,
          effective_acquisition_fps: 0,
          inference_fps: 0,
          latency_ms: 0,
          capture_frames: 0,
          transport_dropped_frames: 0
        };
        this.sentTimestamps = [];
        this.sessionStartTime = performance.now() / 1000.0;

        if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
        if (this.onStatus) this.onStatus(true);
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          if (typeof event.data === 'string') {
            const data: WebSocketDetectionPayload = JSON.parse(event.data);
            // Verify session_id matches active session
            if (data.session_id !== this.sessionId) return;
            // Verify sequence_id is not older than last rendered
            if (data.sequence_id < this.lastRenderedSequenceId) return;

            this.lastRenderedSequenceId = data.sequence_id;
            this.telemetry.result_messages_received++;
            this.telemetry.detection_results_received = this.telemetry.result_messages_received;

            if (data.server_packets_received !== undefined) {
              this.telemetry.server_packets_received = data.server_packets_received;
            }
            if (data.server_frames_decoded !== undefined) {
              this.telemetry.server_frames_decoded = data.server_frames_decoded;
              this.telemetry.server_received_frames = data.server_frames_decoded;
            } else if (data.server_received_frames !== undefined) {
              this.telemetry.server_received_frames = data.server_received_frames;
              this.telemetry.server_frames_decoded = data.server_received_frames;
            }

            if (data.inference_submitted_frames !== undefined) {
              this.telemetry.inference_submitted_frames = data.inference_submitted_frames;
            }
            if (data.inference_superseded_frames !== undefined) {
              this.telemetry.inference_superseded_frames = data.inference_superseded_frames;
            }
            if (data.inference_processed_frames !== undefined) {
              this.telemetry.inference_processed_frames = data.inference_processed_frames;
              this.telemetry.processed_inference_frames = data.inference_processed_frames;
            } else if (data.processed_inference_frames !== undefined) {
              this.telemetry.processed_inference_frames = data.processed_inference_frames;
              this.telemetry.inference_processed_frames = data.processed_inference_frames;
            }
            if (data.inference_pending_frames !== undefined) {
              this.telemetry.inference_pending_frames = data.inference_pending_frames;
              this.telemetry.pending_inference_frames = data.inference_pending_frames;
            } else if (data.pending_inference_frames !== undefined) {
              this.telemetry.pending_inference_frames = data.pending_inference_frames;
              this.telemetry.inference_pending_frames = data.pending_inference_frames;
            }
            if (data.result_messages_sent !== undefined) {
              this.telemetry.result_messages_sent = data.result_messages_sent;
              this.telemetry.detection_results_sent = data.result_messages_sent;
            } else if (data.detection_results_sent !== undefined) {
              this.telemetry.detection_results_sent = data.detection_results_sent;
              this.telemetry.result_messages_sent = data.detection_results_sent;
            }
            if (data.detected_objects !== undefined) {
              this.telemetry.detected_objects = data.detected_objects;
            }
            if (data.effective_acquisition_fps !== undefined) {
              this.telemetry.effective_acquisition_fps = data.effective_acquisition_fps;
            }
            this.telemetry.inference_fps = data.inference_fps || 0;
            this.telemetry.latency_ms = data.latency_ms || 0;

            if (this.onDetection) this.onDetection(data);
            if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
          }
        } catch (err) {
          console.warn('[WS_INGEST] Error parsing detection message:', err);
        }
      };

      this.ws.onerror = (err) => {
        console.warn('[WS_INGEST] WebSocket error:', err);
        if (this.onStatus) this.onStatus(false, 'Lỗi kết nối WebSocket máy chủ');
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        console.log('[WS_INGEST] WebSocket closed.');
        if (this.onStatus) this.onStatus(false, 'Mất kết nối');
        if (!this.stopped) {
          this.scheduleReconnect();
        }
      };
    } catch (e: any) {
      console.warn('[WS_INGEST] Initialization error:', e);
      if (this.onStatus) this.onStatus(false, e?.message || 'Lỗi khởi tạo');
      if (!this.stopped) {
        this.scheduleReconnect();
      }
    }
  }

  private scheduleReconnect() {
    if (this.isReconnecting || this.stopped) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn(`[WS_INGEST] Max reconnect attempts (${this.maxReconnectAttempts}) reached.`);
      if (this.onStatus) this.onStatus(false, 'Mất kết nối máy chủ (đã thử 5 lần)');
      return;
    }

    this.isReconnecting = true;
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 8000);
    console.log(`[WS_INGEST] Reconnecting attempt ${this.reconnectAttempts} in ${delay}ms...`);

    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.isReconnecting = false;
      this.connect(this.onDetection || undefined, this.onTelemetry || undefined, this.onStatus || undefined);
    }, delay);
  }

  public sendFrame(jpegBuffer: ArrayBuffer): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.telemetry.client_backpressure_drops++;
      this.telemetry.transport_dropped_frames = this.telemetry.client_backpressure_drops;
      if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
      return false;
    }

    // Backpressure guard: drop frame if buffer exceeds 64KB
    if (this.ws.bufferedAmount > 65536) {
      this.telemetry.client_backpressure_drops++;
      this.telemetry.transport_dropped_frames = this.telemetry.client_backpressure_drops;
      if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
      return false;
    }

    const seq = ++this.sequenceId;
    const nowSec = performance.now() / 1000.0;

    // Sliding window of 15 frames to smooth acquisition FPS and avoid single-frame jitter spike
    this.sentTimestamps.push(nowSec);
    if (this.sentTimestamps.length > 15) {
      this.sentTimestamps.shift();
    }
    if (this.sentTimestamps.length >= 2) {
      const windowDt = this.sentTimestamps[this.sentTimestamps.length - 1] - this.sentTimestamps[0];
      if (windowDt > 0.001) {
        this.telemetry.acquisition_fps = Math.round(((this.sentTimestamps.length - 1) / windowDt) * 10) / 10;
      }
    }
    this.lastFrameSentTime = nowSec;

    // Pack 16-byte header: (int64 seq_id, float64 monotonic_timestamp)
    const headerBuffer = new ArrayBuffer(16);
    const view = new DataView(headerBuffer);
    if (typeof view.setBigInt64 === 'function') {
      view.setBigInt64(0, BigInt(seq), false);
    } else {
      const high = Math.floor(seq / 0x100000000);
      const low = seq >>> 0;
      view.setUint32(0, high, false);
      view.setUint32(4, low, false);
    }
    view.setFloat64(8, nowSec, false);

    const combined = new Uint8Array(16 + jpegBuffer.byteLength);
    combined.set(new Uint8Array(headerBuffer), 0);
    combined.set(new Uint8Array(jpegBuffer), 16);

    try {
      this.ws.send(combined.buffer);
      this.telemetry.sent_frames++;
      if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
      return true;
    } catch {
      this.telemetry.client_backpressure_drops++;
      this.telemetry.transport_dropped_frames = this.telemetry.client_backpressure_drops;
      if (this.onTelemetry) this.onTelemetry({ ...this.telemetry });
      return false;
    }
  }

  public disconnect() {
    this.stopped = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public getIsConnected(): boolean {
    return this.isConnected;
  }

}
