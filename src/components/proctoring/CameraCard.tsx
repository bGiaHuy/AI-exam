import React, { useState, useRef, useEffect } from 'react';
import { 
  Camera, 
  VideoOff, 
  CheckCircle2, 
  AlertTriangle,
  ChevronDown,
  RefreshCw,
  Video,
  Monitor,
  Check,
  FileVideo
} from 'lucide-react';
import { AIDetectionResult } from '../../services/aiModelService';
import { DetectionOverlay } from './DetectionOverlay';
import { VideoStatusBar } from './VideoStatusBar';

export interface CameraSourceOption {
  id: string; // e.g. 'device:devId123', 'backend:cam1', 'file:demo'
  label: string; // Human-readable name
  type: 'device' | 'backend' | 'file';
  deviceId?: string;
  backendSourceId?: string;
  isCurrent?: boolean;
}

interface CameraCardProps {
  cameraId: string;
  title: string;
  subtitle: string;
  footerLabel?: string;
  room?: string;
  isOnline: boolean;
  fps?: number;
  resolution?: string;
  detections: AIDetectionResult[];
  showOverlays?: boolean;
  statusReason?: string;
  previewUrl?: string | null;
  videoNode?: React.ReactNode;
  onFullscreen?: () => void;
  // Camera Source Selection Props
  currentSourceId?: string;
  currentSourceLabel?: string;
  availableSources?: CameraSourceOption[];
  onSelectSource?: (source: CameraSourceOption) => void;
  onScanDevices?: () => void;
}

export const CameraCard: React.FC<CameraCardProps> = ({
  cameraId,
  title,
  subtitle,
  footerLabel,
  room = "Phòng thi số 1",
  isOnline,
  fps = 0,
  resolution = "1920 × 1080",
  detections = [],
  showOverlays = true,
  statusReason,
  previewUrl,
  videoNode,
  onFullscreen,
  currentSourceId,
  currentSourceLabel,
  availableSources = [],
  onSelectSource,
  onScanDevices
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [isSourceMenuOpen, setIsSourceMenuOpen] = useState(false);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsSourceMenuOpen(false);
      }
    };
    if (isSourceMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isSourceMenuOpen]);

  // Determine overall alert state for this camera
  const hasRedViolation = detections.some(d => d.level === 'red');
  const hasYellowWarning = detections.some(d => d.level === 'yellow');
  const isViolating = hasRedViolation || hasYellowWarning;

  const handleToggleLocalFullscreen = () => {
    if (onFullscreen) {
      onFullscreen();
      return;
    }
    if (containerRef.current) {
      if (!document.fullscreenElement) {
        containerRef.current.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  const displayFooterLabel = footerLabel || `${title} - Bàn thi`;

  return (
    <div 
      ref={containerRef}
      className={`bg-white border rounded-xl shadow-xs overflow-hidden flex flex-col flex-1 min-w-0 transition-all duration-200 ${
        isViolating && isOnline
          ? 'border-red-300 ring-1 ring-red-200'
          : 'border-[#DCE6F5] hover:border-[#9DB9EA]'
      }`}
    >
      {/* ========================================================================= */}
      {/* 1. CAMERA HEADER                                                          */}
      {/* ========================================================================= */}
      <div className="h-10 px-3.5 bg-white border-b border-[#DCE6F5] flex items-center justify-between text-xs select-none shrink-0 relative z-30">
        {/* Left: Status Dot & Title */}
        <div className="flex items-center gap-2 min-w-0">
          <span 
            className={`w-2.5 h-2.5 rounded-full shrink-0 ${
              !isOnline
                ? 'bg-gray-400'
                : hasRedViolation
                ? 'bg-[#EF3340] animate-ping'
                : hasYellowWarning
                ? 'bg-[#F59E0B] animate-pulse'
                : 'bg-[#16B364]'
            }`} 
          />
          <div className="flex items-baseline gap-1.5 truncate">
            <span className="font-bold text-[#173B7A] text-xs sm:text-sm">
              {title}
            </span>
            <span className="text-gray-500 text-[11px] truncate hidden md:inline">
              {subtitle}
            </span>
          </div>
        </div>

        {/* Right: Camera Source Selector & Options */}
        <div className="relative flex items-center gap-2 shrink-0" ref={dropdownRef}>
          {availableSources && availableSources.length > 0 && onSelectSource ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsSourceMenuOpen(!isSourceMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-50 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-300 rounded-md text-[11px] font-medium transition-all shadow-2xs cursor-pointer"
                title="Chọn nguồn camera cho góc này"
              >
                <Video className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                <span className="truncate max-w-[100px] sm:max-w-[130px]">
                  {currentSourceLabel || 'Chọn nguồn'}
                </span>
                <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isSourceMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {isSourceMenuOpen && (
                <div className="absolute right-0 top-full mt-1.5 w-72 bg-white border border-slate-200 rounded-lg shadow-xl z-50 py-1.5 text-xs text-slate-800 animate-in fade-in duration-100 divide-y divide-slate-100">
                  <div className="px-3 py-1.5 flex items-center justify-between text-[11px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-50">
                    <span>Nguồn Camera ({title})</span>
                    {onScanDevices && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onScanDevices();
                        }}
                        className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-slate-200/50 flex items-center gap-1 text-[10px] font-normal cursor-pointer"
                        title="Quét lại danh sách camera cắm vào máy"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Quét lại</span>
                      </button>
                    )}
                  </div>

                  {/* Group 1: Physical / USB / Browser Webcams */}
                  <div className="py-1">
                    <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Camera cắm máy tính (USB / Webcam)
                    </div>
                    {availableSources.filter(s => s.type === 'device').length === 0 ? (
                      <div className="px-3 py-1.5 text-[11px] text-slate-400 italic">
                        Chưa phát hiện thiết bị USB (bấm Quét lại)
                      </div>
                    ) : (
                      availableSources.filter(s => s.type === 'device').map(src => {
                        const isSelected = src.id === currentSourceId || src.isCurrent;
                        return (
                          <button
                            key={src.id}
                            type="button"
                            onClick={() => {
                              onSelectSource(src);
                              setIsSourceMenuOpen(false);
                            }}
                            className={`w-full text-left px-3 py-1.5 flex items-center justify-between gap-2 hover:bg-blue-50 transition-colors cursor-pointer ${
                              isSelected ? 'bg-blue-50/70 text-blue-700 font-semibold' : 'text-slate-700'
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <Camera className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                              <span className="truncate">{src.label}</span>
                            </div>
                            {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
                          </button>
                        );
                      })
                    )}
                  </div>

                  {/* Group 2: Backend AI Streams */}
                  <div className="py-1">
                    <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      Luồng Máy chủ AI (Backend WebSocket)
                    </div>
                    {availableSources.filter(s => s.type === 'backend').map(src => {
                      const isSelected = src.id === currentSourceId || src.isCurrent;
                      return (
                        <button
                          key={src.id}
                          type="button"
                          onClick={() => {
                            onSelectSource(src);
                            setIsSourceMenuOpen(false);
                          }}
                          className={`w-full text-left px-3 py-1.5 flex items-center justify-between gap-2 hover:bg-blue-50 transition-colors cursor-pointer ${
                            isSelected ? 'bg-blue-50/70 text-blue-700 font-semibold' : 'text-slate-700'
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <Monitor className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                            <span className="truncate">{src.label}</span>
                          </div>
                          {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
                        </button>
                      );
                    })}
                  </div>

                  {/* Group 3: File Demo */}
                  {availableSources.some(s => s.type === 'file') && (
                    <div className="py-1">
                      <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        Video Demo
                      </div>
                      {availableSources.filter(s => s.type === 'file').map(src => {
                        const isSelected = src.id === currentSourceId || src.isCurrent;
                        return (
                          <button
                            key={src.id}
                            type="button"
                            onClick={() => {
                              onSelectSource(src);
                              setIsSourceMenuOpen(false);
                            }}
                            className={`w-full text-left px-3 py-1.5 flex items-center justify-between gap-2 hover:bg-blue-50 transition-colors cursor-pointer ${
                              isSelected ? 'bg-blue-50/70 text-blue-700 font-semibold' : 'text-slate-700'
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <FileVideo className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                              <span className="truncate">{src.label}</span>
                            </div>
                            {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 shrink-0" />}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="font-mono text-[10px] text-gray-400 shrink-0">
              RingBuffer: <strong className="text-gray-600 font-semibold">Độc lập</strong>
            </div>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. VIDEO VIEWPORT (Expands to fill height)                                */}
      {/* ========================================================================= */}
      <div className="relative flex-1 min-h-[260px] bg-[#0A0F1D] flex items-center justify-center overflow-hidden w-full select-none z-10">
        {isOnline ? (
          <>
            {/* Stream Content */}
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={`${title} Preview`}
                className="w-full h-full object-contain"
              />
            ) : videoNode ? (
              videoNode
            ) : (
              <div className="text-gray-500 font-mono text-xs">Đang tải luồng...</div>
            )}

            {/* AI Bounding Box Overlays */}
            <DetectionOverlay
              detections={detections}
              show={showOverlays}
            />
          </>
        ) : (
          /* Offline / Disconnected Fallback Viewport */
          <div className="flex flex-col items-center justify-center text-center p-6 text-gray-400 select-none">
            <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-3">
              <VideoOff className="w-6 h-6 text-gray-400" />
            </div>
            <span className="font-semibold text-gray-200 text-xs sm:text-sm tracking-tight">
              Chưa có kết nối camera
            </span>
            <span className="text-[11px] text-gray-400 mt-1 max-w-[240px] leading-relaxed">
              {statusReason || "Chọn camera USB đã cắm vào máy tính hoặc luồng backend để bắt đầu giám sát."}
            </span>

            {/* Quick Action Button to Select Camera Source */}
            {onSelectSource && availableSources && availableSources.length > 0 && (
              <button
                type="button"
                onClick={() => setIsSourceMenuOpen(true)}
                className="mt-3.5 px-3.5 py-1.5 bg-[#2344B6] hover:bg-[#173B7A] text-white rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Chọn nguồn camera cho {title}</span>
                <ChevronDown className="w-3 h-3 ml-0.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 3. VIDEO STATUS BAR                                                       */}
      {/* ========================================================================= */}
      <VideoStatusBar
        isOnline={isOnline}
        resolution={resolution}
        fps={isOnline ? fps : 0}
        onFullscreen={handleToggleLocalFullscreen}
      />

      {/* ========================================================================= */}
      {/* 4. CAMERA META FOOTER                                                     */}
      {/* ========================================================================= */}
      <div className="p-3 bg-white border-t border-[#DCE6F5] flex items-center justify-between text-xs select-none shrink-0">
        {/* Left: Camera Icon & Room Label */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#F0F5FF] text-[#2344B6] flex items-center justify-center shrink-0">
            <Camera className="w-4 h-4 text-[#2344B6]" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-[#173B7A] text-xs leading-tight">
              {displayFooterLabel}
            </span>
            <span className="text-gray-500 text-[11px] leading-tight mt-0.5">
              {room}
            </span>
          </div>
        </div>

        {/* Right: Semantic Badge */}
        <div>
          {!isOnline ? (
            <span className="px-2.5 py-1 rounded-md bg-gray-100 border border-gray-200 text-gray-500 font-medium text-[11px] flex items-center gap-1.5">
              <span>✓ Chưa kết nối</span>
            </span>
          ) : isViolating ? (
            <span className="px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-[#EF3340] font-bold text-[11px] flex items-center gap-1.5 shadow-2xs animate-pulse">
              <AlertTriangle className="w-3 h-3" />
              <span>Đang phát hiện</span>
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-[#16B364] font-semibold text-[11px] flex items-center gap-1.5 shadow-2xs">
              <CheckCircle2 className="w-3 h-3" />
              <span>Bình thường</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
