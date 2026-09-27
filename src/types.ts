/**
 * Core Types for AI Exam Control - Minimal Scope (Vision Evidence Only)
 * Zero examinee identity handling.
 */

export type ViewMode = 'live-monitor' | 'ai-settings';

export type AlertLevel = 'red' | 'yellow' | 'green';

export type ViolationType = 'PHONE' | 'HEAD_TURNING';

export interface Incident {
  id: string;
  sourceId: string;
  sourceLabel?: string;
  sourceType?: string;
  sessionId?: string;
  trackId?: number;
  violationType: ViolationType;
  typeNameVi: string;
  confidence: number; // e.g. 92.5
  level: AlertLevel;
  detectedAt: string;
  clipStartedAt?: string;
  clipEndedAt?: string;
  videoPath?: string;
  snapshotPath?: string;
  clipUrl?: string;
  thumbnailUrl?: string;
  status: 'pending' | 'confirmed' | 'dismissed';
  proctorNotes?: string;
}

export type CameraMode = 'SINGLE_CAMERA' | 'DUAL_CAMERA' | 'TRIPLE_CAMERA';

export interface CameraSourceInfo {
  source_id: string;
  source_label: string;
  source_type: string;
  status: 'CONNECTING' | 'ONLINE' | 'DEGRADED' | 'RECONNECTING' | 'OFFLINE' | 'STOPPED';
  acquisition_fps: number;
  inference_fps: number;
  frames_received: number;
  frames_submitted: number;
  frames_processed: number;
  frames_superseded: number;
  frames_dropped: number;
  pending_depth: number;
  reconnect_count: number;
  last_frame_at?: string;
  session_id?: string;
  ring_buffer_frames?: number;
  ring_buffer_bytes?: number;
  ring_buffer_oldest_age?: number;
  ring_buffer_dropped_by_limit?: number;
  corrupt_frames_skipped?: number;
}

export interface CameraSystemStatus {
  mode: CameraMode;
  cameras: CameraSourceInfo[];
  total_online: number;
  scheduler_inference_fps: number;
  scheduler_latency_ms: number;
  demo_read_only?: boolean;
}

export interface AISettings {
  phone_confidence: number;
  posture_alert_seconds: number;
  suspicion_threshold: number; // Normalized Posture Suspicion Score [0.0 - 1.0] (dimensionless)
  pre_roll_seconds: number;
  post_roll_seconds: number;
  cooldown_seconds: number;
}

export type {
  WebSocketDetectionPayload,
  IngestTelemetry,
  AIDetectionResult
} from './services/aiModelService';

