/**
 * ================================================================================
 * CENTRALIZED API SERVICE LAYER - AI EXAM CONTROL
 * ================================================================================
 * Offline-First Local URL: http://localhost:8000/api
 * Single source of truth for all network requests.
 * Zero examinee personal identity handling.
 * ================================================================================
 */

import {
  Incident,
  AISettings,
  CameraMode,
  CameraSystemStatus
} from '../types';

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const envUrl = (import.meta as any).env?.VITE_API_URL;
    if (envUrl) {
      return envUrl.endsWith('/api') ? envUrl : `${envUrl}/api`;
    }
    if (window.location.protocol === 'https:') {
      return `${window.location.origin}/api`;
    }
  }
  return 'http://localhost:8000/api';
}

export function getWsBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const envUrl = (import.meta as any).env?.VITE_WS_URL || (import.meta as any).env?.VITE_API_URL;
    if (envUrl) {
      const clean = envUrl.replace(/^http/, 'ws');
      return clean.endsWith('/api') ? clean : `${clean}/api`;
    }
    if (window.location.protocol === 'https:') {
      return `wss://${window.location.host}/api`;
    }
  }
  return 'ws://localhost:8000/api';
}

export const API_BASE_URL = getApiBaseUrl();

export interface BackendIncident {
  id: string;
  source_id: string;
  source_label?: string;
  source_type?: string;
  session_id?: string;
  track_id?: number;
  violation_type: 'PHONE' | 'HEAD_TURNING';
  confidence: number;
  level: 'yellow' | 'red';
  detected_at: string;
  clip_started_at?: string;
  clip_ended_at?: string;
  video_path?: string;
  snapshot_path?: string;
  status: 'pending' | 'confirmed' | 'dismissed';
  proctor_notes?: string;
  created_at: string;
}

export function mapBackendIncidentToFrontend(bi: BackendIncident): Incident {
  const typeVi = bi.violation_type === 'PHONE'
    ? 'Sử dụng điện thoại di động'
    : 'Nghi vấn quay đầu nhìn bài';

  // Normalize confidence: if raw probability (<= 1.0), convert to percentage for display; otherwise keep legacy percentage
  const displayConfidence = bi.confidence <= 1.0 ? bi.confidence * 100.0 : bi.confidence;

  const baseOrigin = getApiBaseUrl().replace(/\/api$/, '');

  return {
    id: bi.id,
    sourceId: bi.source_id,
    sourceLabel: bi.source_label,
    sourceType: bi.source_type,
    sessionId: bi.session_id,
    trackId: bi.track_id,
    violationType: bi.violation_type,
    typeNameVi: typeVi,
    confidence: displayConfidence,
    level: bi.level === 'red' ? 'red' : 'yellow',
    detectedAt: bi.detected_at,
    clipStartedAt: bi.clip_started_at,
    clipEndedAt: bi.clip_ended_at,
    videoPath: bi.video_path,
    snapshotPath: bi.snapshot_path,
    clipUrl: bi.video_path
      ? (bi.video_path.startsWith('http') ? bi.video_path : `${baseOrigin}${bi.video_path}`)
      : undefined,
    thumbnailUrl: bi.snapshot_path
      ? (bi.snapshot_path.startsWith('http') ? bi.snapshot_path : `${baseOrigin}${bi.snapshot_path}`)
      : undefined,
    status: bi.status,
    proctorNotes: bi.proctor_notes
  };
}

/**
 * Lấy danh sách các sự cố vi phạm
 */
export async function getIncidents(params?: {
  source_id?: string;
  level?: string;
  status?: string;
  limit?: number;
  skip?: number;
}): Promise<Incident[]> {
  try {
    const query = new URLSearchParams();
    if (params?.source_id) query.append('source_id', params.source_id);
    if (params?.level) query.append('level', params.level);
    if (params?.status) query.append('status', params.status);
    if (params?.limit) query.append('limit', String(params.limit));
    if (params?.skip) query.append('skip', String(params.skip));

    const url = `${API_BASE_URL}/incidents${query.toString() ? `?${query.toString()}` : ''}`;
    const res = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: BackendIncident[] = await res.json();
    return data.map(i => mapBackendIncidentToFrontend(i));
  } catch (err) {
    console.warn('[API] Không thể lấy danh sách sự cố:', err);
    return [];
  }
}

/**
 * Xác nhận hoặc bỏ qua cảnh báo sự cố vi phạm
 */
export async function confirmIncident(
  id: string,
  payload: { status?: 'confirmed' | 'dismissed' | 'pending'; notes?: string }
): Promise<Incident> {
  const res = await fetch(`${API_BASE_URL}/incidents/${id}/confirm`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: 'Lỗi cập nhật sự cố' }));
    throw new Error(errData.detail || `HTTP ${res.status}`);
  }

  const data: BackendIncident = await res.json();
  return mapBackendIncidentToFrontend(data);
}

/**
 * Xóa vĩnh viễn sự cố vi phạm và file video bằng chứng trên ổ đĩa
 */
export async function deleteIncident(incidentId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/incidents/${encodeURIComponent(incidentId)}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' }
    });
    return res.ok;
  } catch (err) {
    console.error('[API] Lỗi xóa sự cố vi phạm:', err);
    return false;
  }
}

/**
 * Xóa toàn bộ video bằng chứng vi phạm và làm sạch dữ liệu
 */
export async function purgeAllIncidentVideos(): Promise<{ success: boolean; deleted_files_count?: number }> {
  try {
    const res = await fetch(`${API_BASE_URL}/incidents/videos/purge-all`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('[API] Lỗi xóa toàn bộ video sự cố:', err);
    return { success: false };
  }
}

/**
 * Lấy cấu hình độ nhạy AI và tham số RingBuffer
 */
export async function getAISettings(): Promise<AISettings> {
  try {
    const res = await fetch(`${API_BASE_URL}/settings/ai`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] Không thể lấy cấu hình AI, dùng giá trị mặc định:', err);
    return {
      phone_confidence: 0.55,
      posture_alert_seconds: 1.25,
      suspicion_threshold: 0.50,
      pre_roll_seconds: 5.0,
      post_roll_seconds: 10.0,
      cooldown_seconds: 6.0
    };
  }
}

/**
 * Cập nhật cấu hình độ nhạy AI và tham số RingBuffer
 */
export async function updateAISettings(payload: AISettings): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/settings/ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return res.ok;
  } catch (err) {
    console.warn('[API] Không thể cập nhật cấu hình AI:', err);
    return false;
  }
}

/**
 * Yêu cầu máy chủ reset trạng thái AI session (ByteTrack, temporal tracker, buffer)
 */
export async function resetSessionState(sessionId?: string): Promise<boolean> {
  try {
    const url = `${API_BASE_URL}/session/reset${sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Accept': 'application/json' }
    });
    return res.ok;
  } catch (err) {
    console.warn('[API] Không thể reset session state:', err);
    return false;
  }
}

/**
 * Lấy chế độ camera hiện tại (SINGLE_CAMERA hoặc DUAL_CAMERA)
 */
export async function getCameraMode(): Promise<CameraMode> {
  try {
    const res = await fetch(`${API_BASE_URL}/camera/mode`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.mode;
  } catch (err) {
    console.warn('[API] Không thể lấy chế độ camera:', err);
    return 'SINGLE_CAMERA';
  }
}

/**
 * Cập nhật chế độ camera (SINGLE_CAMERA hoặc DUAL_CAMERA)
 */
export async function setCameraMode(mode: CameraMode): Promise<CameraMode> {
  try {
    const res = await fetch(`${API_BASE_URL}/camera/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.mode;
  } catch (err) {
    console.warn('[API] Không thể cập nhật chế độ camera:', err);
    return 'SINGLE_CAMERA';
  }
}

/**
 * Lấy danh sách camera và trạng thái telemetry chi tiết
 */
export async function getCameraSources(): Promise<CameraSystemStatus | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/camera/sources`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[API] Không thể lấy danh sách camera sources:', err);
    return null;
  }
}


