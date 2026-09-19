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

