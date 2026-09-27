import React from 'react';
import { 
  Play, 
  Check, 
  X, 
  AlertCircle, 
  Clock, 
  Eye,
  CheckCircle2,
  AlertTriangle,
  Trash2
} from 'lucide-react';
import { Incident } from '../../types';
import { getApiBaseUrl } from '../../services/api';

interface IncidentCardProps {
  incident: Incident;
  onOpenVideoModal: (incident: Incident) => void;
  onConfirm?: (incidentId: string) => void;
  onDismiss?: (incidentId: string) => void;
  onDelete?: (incidentId: string) => void;
  isReadOnly?: boolean;
}

export const IncidentCard: React.FC<IncidentCardProps> = ({
  incident,
  onOpenVideoModal,
  onConfirm,
  onDismiss,
  onDelete,
  isReadOnly = false,
}) => {
  const isRed = incident.level === 'red';
  const evidenceBase = getApiBaseUrl().replace(/\/api\/?$/, '');
  const snapTargetUrl = incident.thumbnailUrl || (incident.id ? `${evidenceBase}/evidence/${incident.id}_snap.jpg` : '');
  
  // Format timestamp (HH:mm:ss)
  let timeStr = 'Vừa xong';
  if (incident.detectedAt) {
    try {
      timeStr = new Date(incident.detectedAt).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch {
      timeStr = '15:08:24';
    }
  }

  // Camera source label
  const cameraLabel = incident.sourceLabel || (
    incident.sourceId === 'cam3' 
      ? 'Camera 3 (Toàn cảnh)' 
      : incident.sourceId === 'cam2' 
      ? 'Camera 2 (Laptop - Góc bên / Bàn thi)' 
      : 'Camera 1 (USB Ngoài - Góc trước)'
  );

  const trackText = incident.trackId !== undefined ? `Track ${incident.trackId}` : 'Track 1';
  // Confidence formatted (e.g. 90.0%)
  const confValue = incident.confidence <= 1.0 ? incident.confidence * 100 : incident.confidence;
  const confText = `${confValue.toFixed(1)}%`;

  return (
    <div 
      className={`p-3 rounded-xl border bg-white shadow-2xs transition-all hover:shadow-xs flex flex-col gap-2.5 ${
        isRed 
          ? 'border-red-200 hover:border-red-300' 
          : 'border-amber-200 hover:border-amber-300'
      }`}
    >
      {/* ========================================================================= */}
      {/* 1. CARD HEADER: SEVERITY BADGE & TIMESTAMP                                */}
      {/* ========================================================================= */}
      <div className="flex items-center justify-between gap-1 select-none">
        {/* Severity Badge */}
        {isRed ? (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-[#FEE2E2] text-[#ED1B2F] font-bold text-[11px] border border-red-200 shadow-2xs">
            <AlertCircle className="w-3.5 h-3.5 text-[#ED1B2F]" />
            <span>Cờ đỏ - Nghiêm trọng</span>
          </span>
        ) : (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-[#FEF3C7] text-[#D97706] font-bold text-[11px] border border-amber-200 shadow-2xs">
            <AlertTriangle className="w-3.5 h-3.5 text-[#D97706]" />
            <span>Cờ vàng - Sử dụng thiết bị</span>
          </span>
        )}

        {/* Timestamp */}
        <div className="flex items-center gap-1 text-gray-500 font-mono text-[11px]">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span>{timeStr}</span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. VIDEO / EVIDENCE THUMBNAIL WITH PLAY OVERLAY                           */}
      {/* ========================================================================= */}
      <div 
        onClick={() => onOpenVideoModal(incident)}
        className="relative aspect-video rounded-lg overflow-hidden bg-black border border-gray-200 cursor-pointer group select-none shadow-2xs"
        title="Nhấn để phát video clip bằng chứng"
      >
        <img
          src={snapTargetUrl}
          alt={`Bằng chứng vi phạm ${incident.typeNameVi}`}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-102"
          onError={(e) => {
            (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180"><rect fill="%230F172A" width="320" height="180"/><text fill="%2364748B" font-family="sans-serif" font-size="12" x="50%" y="50%" text-anchor="middle" dominant-baseline="middle">Ảnh chụp bằng chứng</text></svg>';
          }}
        />

        {/* Dark Bottom Strip with Camera Source */}
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent pt-3 pb-1.5 px-2 text-[10px] text-gray-200 font-mono truncate">
          {cameraLabel}
        </div>

        {/* Circular Play Button in Center */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/10 transition-colors">
          <div className="w-9 h-9 rounded-full bg-white/90 border border-white text-slate-800 flex items-center justify-center shadow-md transition-transform group-hover:scale-110">
            <Play className="w-4 h-4 ml-0.5 text-slate-800 fill-slate-800" />
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. CARD FOOTER: TRACK ID, CONFIDENCE & OPERATOR ACTIONS                   */}
      {/* ========================================================================= */}
      <div className="flex items-center justify-between pt-1 border-t border-gray-100 select-none">
        {/* Track ID & Confidence */}
        <span className="font-mono text-xs text-gray-600 font-semibold">
          <span className="text-[#ED1B2F] font-bold">{trackText}</span>
          <span className="text-gray-400 mx-1">|</span>
          <span className="text-[#ED1B2F] font-bold">{confText}</span>
        </span>

        {/* Actions Lockup */}
        <div className="flex items-center gap-1.5">
          {/* Xem clip Button */}
          <button
            onClick={() => onOpenVideoModal(incident)}
            className="px-2.5 py-1 rounded-md bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 text-xs font-semibold flex items-center gap-1 shadow-2xs transition-colors"
          >
            <Eye className="w-3.5 h-3.5 text-gray-500" />
            <span>Xem clip</span>
          </button>

          {/* Confirm or Status Badge */}
          {incident.status === 'pending' ? (
            <div className="flex items-center gap-1">
              {onDismiss && !isReadOnly && (
                <button
                  onClick={() => onDismiss(incident.id)}
                  title="Bỏ qua cảnh báo"
                  className="p-1 rounded-md bg-white hover:bg-gray-100 border border-gray-200 text-gray-500 hover:text-gray-700 transition-colors shadow-2xs cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
              {onConfirm && !isReadOnly && (
                <button
                  onClick={() => onConfirm(incident.id)}
                  title="Xác nhận vi phạm"
                  className="p-1 rounded-md bg-[#00A95C] hover:bg-emerald-600 text-white transition-colors shadow-2xs cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : (
            <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border shadow-2xs ${
              incident.status === 'confirmed'
                ? 'bg-emerald-50 text-[#00A95C] border-emerald-200'
                : 'bg-gray-100 text-gray-500 border-gray-200'
            }`}>
              {incident.status === 'confirmed' ? '✓ Đã duyệt' : 'Đã bỏ qua'}
            </span>
          )}

          {/* Delete Incident / Video Button */}
          {onDelete && !isReadOnly && (
            <button
              onClick={() => onDelete(incident.id)}
              title="Xóa video và dữ liệu vi phạm này khỏi hệ thống"
              className="p-1 rounded-md bg-white hover:bg-rose-50 border border-gray-200 hover:border-rose-200 text-gray-400 hover:text-[#ED1B2F] transition-colors shadow-2xs cursor-pointer ml-0.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
