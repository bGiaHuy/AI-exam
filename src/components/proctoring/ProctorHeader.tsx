import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Settings, 
  User, 
  ChevronDown, 
  Maximize2, 
  Minimize2,
  Sliders,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { ViewMode } from '../../types';
import { aiModelService, AIStatusResponse } from '../../services/aiModelService';
import { DEMO_CONFIG } from '../../config/demoConfig';

interface ProctorHeaderProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  activeSource?: string;
}

export const ProctorHeader: React.FC<ProctorHeaderProps> = ({
  currentView,
  onSelectView,
  activeSource = "Camera Giám Sát"
}) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const [dateStr, setDateStr] = useState<string>('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [isAdminMenuOpen, setIsAdminMenuOpen] = useState(false);

  // Poll Backend AI status every 5s
  useEffect(() => {
    let isMounted = true;
    const checkAI = async () => {
      try {
        const status = await aiModelService.checkStatus();
        if (isMounted) setAiStatus(status);
      } catch (e) {
        if (isMounted) setAiStatus({ status: 'STANDBY', message: 'Offline' });
      }
    };
    checkAI();
    const interval = setInterval(checkAI, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Real-time Clock (Format matches reference: 11:31:40 UTC / Thứ 6, 23/05/2025)
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString('vi-VN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        }) + ' UTC'
      );

      const days = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
      const dayName = days[now.getDay()];
      const day = String(now.getDate()).padStart(2, '0');
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const year = now.getFullYear();
      setDateStr(`${dayName}, ${day}/${month}/${year}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const isSystemOnline = aiStatus?.status === 'ONLINE';

  return (
    <header className="relative bg-white border-b border-[#DDE6F2] shadow-xs z-30 select-none overflow-hidden">
      {/* ========================================================================= */}
      {/* TRẦN PHÚ - ĐÀ NẴNG DUAL-LAYER BACKGROUND WATERMARK SYSTEM                */}
      {/* ========================================================================= */}
      {/* 1. Large School Emblem Watermark (Biểu trưng Tri Thức Trần Phú) */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-70px',
          left: '38%',
          transform: 'translateX(-50%)',
          width: '320px',
          height: '240px',
          opacity: 0.07,
        }}
      >
        <img 
          src="/assets/tranphu/school-watermark.svg" 
          alt="Biểu trưng trường THPT Trần Phú" 
          className="w-full h-full object-contain"
        />
      </div>

      {/* 2. Top-Right Da Nang Skyline Pattern (Đường chân trời TP. Đà Nẵng) */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-35px',
          right: '-20px',
          width: '450px',
          height: '140px',
          opacity: 0.16,
        }}
      >
        <img 
          src="/assets/tranphu/danang-skyline.svg" 
          alt="Đường chân trời TP. Đà Nẵng" 
          className="w-full h-full object-contain"
        />
      </div>

      {/* ========================================================================= */}
      {/* HEADER MAIN CONTAINER                                                     */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col md:flex-row items-stretch md:items-center justify-between px-3 sm:px-6 py-2 sm:py-3 gap-3 min-h-[92px]">
        {/* LEFT IDENTITY AREA */}
        <div className="flex items-center gap-3 sm:gap-4 pl-0">
          {/* School Emblem Logo */}
          <div 
            onClick={() => onSelectView('live-monitor')} 
            className="cursor-pointer shrink-0 transition-transform hover:scale-105 active:scale-95"
            title="THPT Trần Phú - Đà Nẵng / Bàn giám sát AI"
          >
            <img 
              src="/assets/tranphu/school-logo.png" 
              alt="Logo THPT Trần Phú - Đà Nẵng" 
              className="w-13 h-13 sm:w-16 sm:h-16 object-contain drop-shadow-xs"
            />
          </div>

          {/* Institutional Typography Lockup */}
          <div className="flex flex-col justify-center select-text">
            {/* School Name: Bold Red Uppercase */}
            <h1 className="font-extrabold text-[#E8465A] tracking-tight uppercase text-sm sm:text-base md:text-lg leading-tight">
              TRƯỜNG THPT TRẦN PHÚ - ĐÀ NẴNG
            </h1>
            {/* System Name: Navy Blue Uppercase */}
            <h2 className="font-extrabold text-[#163474] tracking-tight uppercase text-base sm:text-lg md:text-xl leading-tight mt-0.5">
              HỆ THỐNG GIÁM SÁT THI BẰNG AI
            </h2>
            {/* Institutional Motto: Muted Blue-Gray */}
            <p className="font-semibold text-[#64748B] text-[10px] sm:text-[11px] md:text-xs tracking-wider uppercase mt-0.5">
              ĐÀ NẴNG - THÀNH PHỐ ĐÁNG SỐNG • TRUNG THỰC - TRÁCH NHIỆM - KHÁT VỌNG
            </p>
          </div>
        </div>

        {/* RIGHT STATUS & CONTROL AREA */}
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3 shrink-0">
          {/* Clock Card */}
          <div className="flex items-center gap-2.5 bg-white border border-[#DDE6F2] px-3 sm:px-3.5 py-1.5 rounded-xl shadow-xs">
            <Clock className="w-4 h-4 text-[#163474] shrink-0" />
            <div className="flex flex-col text-left">
              <span className="font-mono font-bold text-xs sm:text-sm text-slate-800 leading-none">
                {timeStr || '11:31:40 UTC'}
              </span>
              <span className="font-mono text-[10px] text-gray-500 leading-none mt-1">
                {dateStr || 'Hôm nay'}
              </span>
            </div>
          </div>

          {/* System Status Badge (Pill) */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold shadow-xs transition-colors ${
            isSystemOnline
              ? 'bg-[#E8F8F0] border-[#A7F3D0] text-[#1FB45B]'
              : 'bg-amber-50 border-amber-200 text-[#F2B34C]'
          }`}>
            <span className="flex h-2 w-2 relative">
              {isSystemOnline && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#1FB45B] opacity-75" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isSystemOnline ? 'bg-[#1FB45B]' : 'bg-[#F2B34C]'}`} />
            </span>
            <span className="tracking-wide uppercase text-[11px] sm:text-xs whitespace-nowrap">
              {isSystemOnline ? '((•)) HỆ THỐNG ĐANG HOẠT ĐỘNG' : 'HỆ THỐNG CHỜ KẾT NỐI'}
            </span>
          </div>

          {/* Quick Settings & Admin Lockup */}
          <div className="flex items-center gap-1.5">
            {/* AI Settings Gear Button */}
            {!DEMO_CONFIG.isDemo && (
              <button
                onClick={() => onSelectView(currentView === 'ai-settings' ? 'live-monitor' : 'ai-settings')}
                title="Cấu hình độ nhạy AI"
                className={`p-2 rounded-xl border transition-colors shadow-xs cursor-pointer ${
                  currentView === 'ai-settings'
                    ? 'bg-[#1C49B6] text-white border-[#1C49B6]'
                    : 'bg-white hover:bg-gray-50 border-[#DDE6F2] text-gray-700'
                }`}
              >
                <Settings className="w-4 h-4" />
              </button>
            )}

            {/* Admin Profile Dropdown Pill */}
            <div className="relative">
              <button
                onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                className="flex items-center gap-2 bg-white hover:bg-gray-50 border border-[#DDE6F2] px-3 py-1.5 rounded-xl shadow-xs transition-colors text-xs font-semibold text-slate-700 cursor-pointer"
              >
                <div className="w-6 h-6 rounded-full bg-[#1C49B6] text-white flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5" />
                </div>
                <span className="hidden sm:inline">Giám thị Trần Phú</span>
                <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Admin Dropdown Menu */}
              {isAdminMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl border border-[#DDE6F2] shadow-lg py-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 border-b border-gray-100 text-gray-500 text-[11px]">
                    Đăng nhập: <strong className="text-slate-800">giamthi@thpt-tranphu-danang.edu.vn</strong>
                  </div>
                  <button
                    onClick={() => {
                      onSelectView('live-monitor');
                      setIsAdminMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium cursor-pointer"
                  >
                    Bàn Giám Sát Trực Tiếp
                  </button>
                  {!DEMO_CONFIG.isDemo && (
                    <button
                      onClick={() => {
                        onSelectView('ai-settings');
                        setIsAdminMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium cursor-pointer"
                    >
                      Cấu Hình Độ Nhạy AI
                    </button>
                  )}
                  <button
                    onClick={toggleFullscreen}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium border-t border-gray-100 flex items-center justify-between cursor-pointer"
                  >
                    <span>{isFullscreen ? 'Thu nhỏ cửa sổ' : 'Toàn màn hình'}</span>
                    {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
