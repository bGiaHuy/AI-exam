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
    <header className="relative bg-white border-b border-gray-200 shadow-xs z-30 select-none overflow-hidden">
      {/* ========================================================================= */}
      {/* ĐÔNG SƠN DUAL-LAYER BACKGROUND WATERMARK SYSTEM                          */}
      {/* ========================================================================= */}
      {/* 1. Large Center Drum Pattern */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-120px',
          left: '38%',
          transform: 'translateX(-50%)',
          width: '500px',
          height: '500px',
          opacity: 0.11,
        }}
      >
        <img 
          src="/assets/chuyenhvt/dongson-watermark.svg" 
          alt="Trống đồng Đông Sơn trung tâm" 
          className="w-full h-full object-contain"
        />
      </div>

      {/* 2. Top-Right Cropped Drum Ring */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-140px',
          right: '-40px',
          width: '420px',
          height: '420px',
          opacity: 0.09,
        }}
      >
        <img 
          src="/assets/chuyenhvt/dongson-watermark.svg" 
          alt="Trống đồng Đông Sơn góc phải" 
          className="w-full h-full object-contain"
        />
      </div>

      {/* ========================================================================= */}
      {/* HEADER MAIN CONTAINER                                                     */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col md:flex-row items-stretch md:items-center justify-between px-3 sm:px-6 py-2.5 sm:py-3.5 gap-3 min-h-[96px]">
        {/* LEFT IDENTITY AREA */}
        <div className="flex items-center gap-2 sm:gap-4 pl-0">
          {/* Institutional Ribbon at Left Edge */}
          <div className="shrink-0 -my-3.5 -ml-3 sm:-ml-6 mr-1 h-20 sm:h-24 w-6 sm:w-8 overflow-hidden">
            <img 
              src="/assets/chuyenhvt/header-ribbon.png" 
              alt="Dải ruy-băng trường" 
              className="h-full w-full object-cover object-left"
              onError={(e) => {
                // Fallback to SVG if PNG fails
                (e.target as HTMLImageElement).src = '/assets/chuyenhvt/header-ribbon.svg';
              }}
            />
          </div>

          {/* School Emblem Logo */}
          <div 
            onClick={() => onSelectView('live-monitor')} 
            className="cursor-pointer shrink-0 transition-transform hover:scale-105 active:scale-95"
            title="THPT Chuyên Hoàng Văn Thụ - Trang chủ giám sát"
          >
            <img 
              src="/assets/chuyenhvt/school-logo.png" 
              alt="Logo THPT Chuyên Hoàng Văn Thụ" 
              className="w-14 h-14 sm:w-18 sm:h-18 object-contain drop-shadow-xs"
            />
          </div>

          {/* Institutional Typography Lockup */}
          <div className="flex flex-col justify-center select-text">
            {/* School Name: Bold Red Uppercase */}
            <h1 className="font-extrabold text-[#ED1B2F] tracking-tight uppercase text-sm sm:text-base md:text-lg leading-tight">
              THPT CHUYÊN HOÀNG VĂN THỤ
            </h1>
            {/* System Name: Navy Blue Uppercase */}
            <h2 className="font-extrabold text-[#123F7C] tracking-tight uppercase text-base sm:text-lg md:text-xl leading-tight mt-0.5">
              HỆ THỐNG GIÁM SÁT THI BẰNG AI
            </h2>
            {/* Institutional Motto: Muted Blue-Gray */}
            <p className="font-medium text-[#64748B] text-[10px] sm:text-[11px] md:text-xs tracking-wider uppercase mt-0.5">
              KỶ CƯƠNG • TRUNG THỰC • VƯƠN TỚI TRI THỨC
            </p>
          </div>
        </div>

        {/* RIGHT STATUS & CONTROL AREA */}
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3 shrink-0">
          {/* Clock Card */}
          <div className="flex items-center gap-2.5 bg-white border border-gray-200 px-3 sm:px-3.5 py-1.5 rounded-xl shadow-xs">
            <Clock className="w-4 h-4 text-[#123F7C] shrink-0" />
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
              ? 'bg-[#E8F8F0] border-[#A7F3D0] text-[#00A95C]'
              : 'bg-amber-50 border-amber-200 text-amber-600'
          }`}>
            <span className="flex h-2 w-2 relative">
              {isSystemOnline && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00A95C] opacity-75" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isSystemOnline ? 'bg-[#00A95C]' : 'bg-amber-500'}`} />
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
                className={`p-2 rounded-xl border transition-colors shadow-xs ${
                  currentView === 'ai-settings'
                    ? 'bg-[#123F7C] text-white border-[#123F7C]'
                    : 'bg-white hover:bg-gray-50 border-gray-200 text-gray-700'
                }`}
              >
                <Settings className="w-4 h-4" />
              </button>
            )}

            {/* Admin Profile Dropdown Pill */}
            <div className="relative">
              <button
                onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                className="flex items-center gap-2 bg-white hover:bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-xl shadow-xs transition-colors text-xs font-semibold text-slate-700"
              >
                <div className="w-6 h-6 rounded-full bg-[#0969FF] text-white flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5" />
                </div>
                <span className="hidden sm:inline">Quản trị viên</span>
                <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Admin Dropdown Menu */}
              {isAdminMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl border border-gray-200 shadow-lg py-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 border-b border-gray-100 text-gray-500 text-[11px]">
                    Đăng nhập: <strong className="text-slate-800">admin@chuyenhvt</strong>
                  </div>
                  <button
                    onClick={() => {
                      onSelectView('live-monitor');
                      setIsAdminMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium"
                  >
                    Bàn Giám Sát Trực Tiếp
                  </button>
                  {!DEMO_CONFIG.isDemo && (
                    <button
                      onClick={() => {
                        onSelectView('ai-settings');
                        setIsAdminMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium"
                    >
                      Cấu Hình Độ Nhạy AI
                    </button>
                  )}
                  <button
                    onClick={toggleFullscreen}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 text-slate-700 font-medium border-t border-gray-100 flex items-center justify-between"
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
