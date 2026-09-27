/**
 * ================================================================================
 * SANITIZED MOCK DEMO DATA (ZERO PII)
 * ================================================================================
 * Realistic proctoring incidents for demonstration without exposing real examinee
 * personal records, real evidence files, or internal training data.
 * ================================================================================
 */

import { Incident } from '../types';

export const MOCK_DEMO_INCIDENTS: Incident[] = [
  {
    id: 'demo_inc_001',
    sourceId: 'Camera Giám Sát Demo #1',
    trackId: 1,
    violationType: 'PHONE',
    typeNameVi: 'Sử dụng điện thoại di động',
    confidence: 92.4,
    level: 'red',
    detectedAt: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    status: 'pending',
    proctorNotes: 'Hệ thống tự động phát hiện thiết bị di động trong vùng làm bài (Bản mô phỏng Demo).'
  },
  {
    id: 'demo_inc_002',
    sourceId: 'Camera Giám Sát Demo #1',
    trackId: 2,
    violationType: 'HEAD_TURNING',
    typeNameVi: 'Nghi vấn quay đầu nhìn bài',
    confidence: 86.8,
    level: 'yellow',
    detectedAt: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
    status: 'confirmed',
    proctorNotes: 'Góc quay đầu lệch quá ngưỡng quy định kéo dài > 1.2s (Bản mô phỏng Demo).'
  },
  {
    id: 'demo_inc_003',
    sourceId: 'Camera Giám Sát Demo #1',
    trackId: 3,
    violationType: 'HEAD_TURNING',
    typeNameVi: 'Nghi vấn quay đầu nhìn bài',
    confidence: 94.1,
    level: 'red',
    detectedAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    status: 'pending',
    proctorNotes: 'Hành vi quay đầu liên tục sang bàn bên cạnh (Bản mô phỏng Demo).'
  }
];
