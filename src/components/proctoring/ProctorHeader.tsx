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
    <header className="relative bg-white border-b border-[#DCE6F5] shadow-xs z-30 select-none overflow-hidden">
      {/* ========================================================================= */}
      {/* TÂN LẬP DUAL-LAYER BACKGROUND WATERMARK SYSTEM                            */}
      {/* ========================================================================= */}
      {/* 1. Large Torch & Book Watermark (Biểu trưng Tri Thức Tân Lập) */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-110px',
          left: '42%',
          transform: 'translateX(-50%)',
          width: '420px',
          height: '420px',
          opacity: 0.08,
        }}
      >
        <img 
          src="/assets/tanlap/torch-book-watermark.svg" 
          alt="Biểu trưng ngọn đuốc và trang sách Tân Lập" 
          className="w-full h-full object-contain"
        />
      </div>

      {/* 2. Top-Right Leaf Pattern (Cành nguyệt quế tri thức) */}
      <div 
        className="absolute pointer-events-none z-0"
        style={{
          top: '-60px',
          right: '-20px',
          width: '380px',
          height: '180px',
          opacity: 0.14,
        }}
      >
        <img 
          src="/assets/tanlap/header-leaf-pattern.svg" 
          alt="Họa tiết lá cách điệu Tân Lập" 
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
            title="THPT Tân Lập - Bàn giám sát AI"
          >
            <img 
              src="/assets/tanlap/school-logo.png" 
              alt="Logo THPT Tân Lập" 
              className="w-13 h-13 sm:w-16 sm:h-16 object-contain drop-shadow-xs"
            />
          </div>

          {/* Institutional Typography Lockup */}
          <div className="flex flex-col justify-center select-text">
            {/* School Name: Bold Red Uppercase */}
            <h1 className="font-extrabold text-[#EF3340] tracking-tight uppercase text-sm sm:text-base md:text-lg leading-tight">
              TRƯỜNG THPT TÂN LẬP
            </h1>
            {/* System Name: Navy Blue Uppercase */}
            <h2 className="font-extrabold text-[#173B7A] tracking-tight uppercase text-base sm:text-lg md:text-xl leading-tight mt-0.5">
              HỆ THỐNG GIÁM SÁT THI BẰNG AI
            </h2>
            {/* Institutional Motto: Muted Blue-Gray */}
            <p className="font-semibold text-[#64748B] text-[10px] sm:text-[11px] md:text-xs tracking-wider uppercase mt-0.5">
              KỶ CƯƠNG • TRUNG THỰC • CHẤT LƯỢNG <span className="text-slate-400 font-normal">|</span> ĐAN PHƯỢNG - HÀ NỘI
            </p>
          </div>
        </div>

        {/* RIGHT STATUS & CONTROL AREA */}
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3 shrink-0">
          {/* Clock Card */}
          <div className="flex items-center gap-2.5 bg-white border border-[#DCE6F5] px-3 sm:px-3.5 py-1.5 rounded-xl shadow-xs">
            <Clock className="w-4 h-4 text-[#173B7A] shrink-0" />
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
              ? 'bg-[#E8F8F0] border-[#A7F3D0] text-[#16B364]'
              : 'bg-amber-50 border-amber-200 text-[#F59E0B]'
          }`}>
            <span className="flex h-2 w-2 relative">
              {isSystemOnline && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#16B364] opacity-75" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isSystemOnline ? 'bg-[#16B364]' : 'bg-[#F59E0B]'}`} />
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
                    ? 'bg-[#2344B6] text-white border-[#2344B6]'
                    : 'bg-white hover:bg-gray-50 border-[#DCE6F5] text-gray-700'
                }`}
              >
                <Settings className="w-4 h-4" />
              </button>
            )}

            {/* Admin Profile Dropdown Pill */}
            <div className="relative">
              <button
                onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                className="flex items-center gap-2 bg-white hover:bg-gray-50 border border-[#DCE6F5] px-3 py-1.5 rounded-xl shadow-xs transition-colors text-xs font-semibold text-slate-700 cursor-pointer"
              >
                <div className="w-6 h-6 rounded-full bg-[#2344B6] text-white flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5" />
                </div>
                <span className="hidden sm:inline">Giám thị Tân Lập</span>
                <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Admin Dropdown Menu */}
              {isAdminMenuOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl border border-[#DCE6F5] shadow-lg py-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 border-b border-gray-100 text-gray-500 text-[11px]">
                    Đăng nhập: <strong className="text-slate-800">giamthi@thpt-tanlap.edu.vn</strong>
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
