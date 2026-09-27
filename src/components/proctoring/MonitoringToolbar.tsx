import React from 'react';
import { 
  AlertTriangle, 
  Eye, 
  EyeOff, 
  PlayCircle, 
  SlidersHorizontal,
  Lock,
  Camera
} from 'lucide-react';
import { CameraMode } from '../../types';
import { DEMO_CONFIG } from '../../config/demoConfig';

interface MonitoringToolbarProps {
  acqFps: number;
  aiFps: number;
  latencyMs?: number;
  violationCount: number;
  cameraMode: CameraMode;
  onToggleCameraMode: (mode: CameraMode) => void;
  isDemoReadOnly: boolean;
  sourceType: 'webcam' | 'file';
  onTriggerDemoUpload: () => void;
  showOverlays: boolean;
  onToggleOverlays: () => void;
}

export const MonitoringToolbar: React.FC<MonitoringToolbarProps> = ({
  acqFps,
  aiFps,
  latencyMs = 0,
  violationCount,
  cameraMode,
  onToggleCameraMode,
  isDemoReadOnly,
  sourceType,
  onTriggerDemoUpload,
  showOverlays,
  onToggleOverlays,
}) => {
  return (
    <div className="bg-[#F7FAFF] border-b border-[#DCE6F5] px-3 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-sans select-none z-20">
      {/* ========================================================================= */}
      {/* LEFT SECTION: LIVE STATUS, METRICS, VIOLATION COUNTER                     */}
      {/* ========================================================================= */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {/* LIVE Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-[#EF3340] text-white font-bold text-xs tracking-wider shadow-xs">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          <span>LIVE</span>
        </div>

        {/* Live Proctoring Label */}
        <span className="font-bold text-[#173B7A] text-xs sm:text-sm tracking-tight whitespace-nowrap">
          Giám sát thi trực tiếp
        </span>

        {/* Vertical Divider */}
        <div className="hidden sm:block h-4 w-px bg-[#DCE6F5]" />

        {/* Telemetry FPS Pills */}
        <div className="flex items-center gap-1.5">
          {/* Acquisition FPS */}
          <div className="px-2.5 py-1 rounded-md bg-white border border-[#DCE6F5] shadow-2xs font-mono text-[11px] text-gray-600">
            Acq: <strong className="text-[#16B364] font-bold">{acqFps} FPS</strong>
          </div>

          {/* AI Inference FPS */}
          <div className="px-2.5 py-1 rounded-md bg-white border border-[#DCE6F5] shadow-2xs font-mono text-[11px] text-gray-600">
            AI: <strong className="text-[#16B364] font-bold">{aiFps} FPS</strong>
            {latencyMs > 0 && <span className="text-gray-400 ml-1">({latencyMs}ms)</span>}
          </div>
        </div>

        {/* Violation Counter Badge */}
        <div 
          className={`flex items-center gap-1.5 px-3 py-1 rounded-md border font-bold text-xs tracking-tight shadow-2xs transition-colors ${
            violationCount > 0
              ? 'bg-red-50/90 border-red-200 text-[#EF3340]'
              : 'bg-emerald-50/90 border-[#A7F3D0] text-[#16B364]'
          }`}
        >
          <AlertTriangle className={`w-3.5 h-3.5 ${violationCount > 0 ? 'text-[#EF3340]' : 'text-[#16B364]'}`} />
          <span>{violationCount > 0 ? `${violationCount} VI PHẠM (CỜ ĐỎ)` : '0 VI PHẠM'}</span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* RIGHT SECTION: CAMERA SELECTOR, DEMO INPUT, AI FRAME TOGGLE               */}
      {/* ========================================================================= */}
      <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
        {/* Camera Selector (Segmented Control) */}
        {isDemoReadOnly ? (
          <div 
            className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-amber-300 text-amber-700 text-xs font-semibold shadow-2xs"
            title="Bản demo chỉ đọc: 2 camera cố định"
          >
            <Lock className="w-3.5 h-3.5 text-amber-500" />
            <span>BẢN DEMO CHỈ ĐỌC (2 CAMERA CỐ ĐỊNH)</span>
          </div>
        ) : (
          <div className="flex items-center bg-[#EDF3FD] p-0.5 rounded-lg border border-[#DCE6F5] shadow-2xs">
            <button
              onClick={() => onToggleCameraMode('SINGLE_CAMERA')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                cameraMode === 'SINGLE_CAMERA'
                  ? 'bg-[#2344B6] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#173B7A]'
              }`}
              title="Chế độ giám sát 1 camera đơn"
            >
              1 CAMERA
            </button>
            <button
              onClick={() => onToggleCameraMode('DUAL_CAMERA')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                cameraMode === 'DUAL_CAMERA'
                  ? 'bg-[#2344B6] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#173B7A]'
              }`}
              title="Chế độ giám sát 2 camera đồng thời (Góc trước & Góc bên)"
            >
              2 CAMERA
            </button>
            <button
              onClick={() => onToggleCameraMode('TRIPLE_CAMERA')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                cameraMode === 'TRIPLE_CAMERA'
                  ? 'bg-[#2344B6] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#173B7A]'
              }`}
              title="Chế độ giám sát 3 camera đồng thời (Góc trước, Góc bên & Toàn cảnh)"
            >
              3 CAMERA
            </button>
          </div>
        )}

        {/* Demo Video Load Button */}
        {!DEMO_CONFIG.isDemo && !isDemoReadOnly && (
          <button
            onClick={onTriggerDemoUpload}
            className="px-3 py-1 rounded-md bg-white hover:bg-blue-50/60 border border-[#DCE6F5] hover:border-[#9DB9EA] text-[#2344B6] text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
            title={sourceType === 'webcam' ? 'Chọn file MP4 để kiểm thử' : 'Chuyển về sử dụng Webcam trực tiếp'}
          >
            <PlayCircle className="w-3.5 h-3.5 text-[#2344B6]" />
            <span>{sourceType === 'webcam' ? 'Nạp video demo' : 'Dùng webcam'}</span>
          </button>
        )}

        {/* AI Frame Toggle Button */}
        <button
          onClick={onToggleOverlays}
          className={`px-3 py-1 rounded-md border text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors ${
            showOverlays
              ? 'bg-white hover:bg-blue-50/60 border-[#DCE6F5] hover:border-[#9DB9EA] text-[#2344B6]'
              : 'bg-gray-100 hover:bg-gray-200 border-gray-300 text-gray-500'
          }`}
          title="Bật hoặc tắt lớp phủ bounding box nhận diện AI"
        >
          {showOverlays ? <Eye className="w-3.5 h-3.5 text-[#2344B6]" /> : <EyeOff className="w-3.5 h-3.5 text-gray-500" />}
          <span>Khung AI: {showOverlays ? 'BẬT' : 'TẮT'}</span>
        </button>
      </div>
    </div>
  );
};
