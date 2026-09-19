import React, { useState, useRef } from 'react';
import { X, ShieldAlert, RotateCcw, Clock, Film } from 'lucide-react';
import { Incident } from '../../types';

interface VideoEvidenceModalProps {
  incident: Incident | null;
  isOpen: boolean;
  onClose: () => void;
}

export const VideoEvidenceModal: React.FC<VideoEvidenceModalProps> = ({
  incident,
  isOpen,
  onClose,
}) => {
  const [isLooping, setIsLooping] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  if (!isOpen || !incident) return null;

  const directMp4Url = incident.clipUrl && incident.clipUrl.startsWith('http')
    ? incident.clipUrl
    : `http://localhost:8000/evidence/${incident.id}.mp4`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-lg p-4 shadow-2xl space-y-3">
        {/* Header Bar */}
        <div className="flex items-center justify-between pb-2.5 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <ShieldAlert className={`w-4 h-4 ${incident.level === 'red' ? 'text-rose-400' : 'text-amber-400'}`} />
            <div>
              <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-tight">
                CLIP BẰNG CHỨNG TỰ ĐỘNG: {incident.typeNameVi}
              </h2>
              <p className="text-[11px] text-zinc-400 font-mono">
                Mã sự cố: {incident.id} • {incident.trackId !== undefined ? `Track ID: ${incident.trackId}` : 'Track không xác định'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 rounded text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Video Player Container */}
        <div className="relative aspect-video rounded overflow-hidden bg-black border border-zinc-800 flex items-center justify-center">
          <video 
            ref={videoRef}
            src={directMp4Url}
            controls
            autoPlay
            loop={isLooping}
            className="w-full h-full object-contain"
            onError={() => {
              console.warn('[VideoModal] Không thể tải video MP4 trực tiếp:', directMp4Url);
            }}
          />

          <div className="absolute top-2 left-2 bg-zinc-950/85 border border-zinc-800 px-2 py-0.5 rounded text-[10px] font-mono text-zinc-300 flex items-center gap-1.5">
            <Film className="w-3 h-3 text-emerald-400" />
            <span>MP4 (1.0x Real-time Resampled)</span>
          </div>
        </div>

        {/* Incident Summary Metadata Box */}
        <div className="p-3 rounded bg-zinc-950 border border-zinc-800 text-xs space-y-2 font-sans">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-zinc-200 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${incident.level === 'red' ? 'bg-rose-500' : 'bg-amber-500'}`} />
              {incident.typeNameVi} ({incident.violationType})
            </span>
            <span className="font-mono text-zinc-400">
              Điểm tin cậy: <strong className="text-zinc-100">{incident.confidence.toFixed(1)}%</strong>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-zinc-400 pt-1 border-t border-zinc-900">
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-zinc-500" />
              <span>Phát hiện: {new Date(incident.detectedAt).toLocaleTimeString('vi-VN')} UTC</span>
            </div>
            <div>
              <span>Nguồn camera: <strong className="text-zinc-300">{incident.sourceId}</strong></span>
            </div>
          </div>

          <p className="text-[11px] text-zinc-400 leading-relaxed font-sans">
            {incident.proctorNotes || `Hành vi được ghi nhận tự động bởi Time-based RingBuffer và lưu trữ tại ${directMp4Url}.`}
          </p>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-1 border-t border-zinc-800">
          <button
            onClick={() => setIsLooping(!isLooping)}
            className={`px-2.5 py-1 rounded text-xs font-mono flex items-center gap-1.5 border transition-colors ${
              isLooping ? 'bg-zinc-800 border-zinc-700 text-emerald-400' : 'bg-zinc-900 border-zinc-800 text-zinc-500'
            }`}
          >
            <RotateCcw className="w-3 h-3" />
            <span>Lặp video: {isLooping ? 'BẬT' : 'TẮT'}</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium border border-zinc-700 transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
