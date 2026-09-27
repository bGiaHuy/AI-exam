import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  Settings, 
  User, 
  ChevronDown, 
  Maximize2, 
  Minimize2,
  Sliders,
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

  // Real-time Clock
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
    <header className="relative border-b border-[#b3d4f0] shadow-xs z-30 select-none overflow-hidden" style={{ background: '#f5faff' }}>
      {/* ========================================================================= */}
      {/* PHÌN HỒ – BACKGROUND: Mountain panorama, ruộng bậc thang, hoa ban          */}
      {/* ========================================================================= */}
      {/* 1. Full-width mountain header bg (right half) */}
      <div
        className="absolute pointer-events-none z-0"
        style={{
          top: 0,
          right: 0,
          width: '55%',
          height: '100%',
          opacity: 0.22,
        }}
      >
        <img
          src="/assets/pinhho/header-bg.svg"
          alt="Phong cảnh núi rừng Phìn Hồ"
          className="w-full h-full object-cover object-right-top"
        />
      </div>

      {/* 2. Hoa Ban blossom watermark (center-right) */}
      <div
        className="absolute pointer-events-none z-0"
        style={{
          top: '-30px',
          right: '42%',
          width: '150px',
          height: '160px',
          opacity: 0.09,
        }}
      >
        <img
          src="/assets/pinhho/hoa-ban.svg"
          alt="Hoa Ban Tây Bắc"
          className="w-full h-full object-contain"
        />
      </div>

      {/* 3. Textile strip along the very bottom of header */}
      <div
        className="absolute pointer-events-none z-0 bottom-0 left-0 right-0"
        style={{ height: '6px', opacity: 0.55 }}
      >
        <img
          src="/assets/pinhho/textile-strip.svg"
          alt="Họa tiết dệt Tây Bắc"
          className="w-full h-full object-cover object-center"
        />
      </div>

      {/* ========================================================================= */}
      {/* HEADER MAIN CONTAINER                                                     */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col md:flex-row items-stretch md:items-center justify-between px-3 sm:px-6 py-2 sm:py-3 gap-3 min-h-[92px]">
        {/* LEFT IDENTITY AREA */}
        <div className="flex items-center gap-3 sm:gap-4 pl-0">
          {/* School Mark (Biểu trưng núi minh họa) */}
          <div
            onClick={() => onSelectView('live-monitor')}
            className="cursor-pointer shrink-0 transition-transform hover:scale-105 active:scale-95"
            title="PTDTBT TH&THCS Phìn Hồ - Lai Châu"
          >
            <img
              src="/assets/pinhho/school-mark.svg"
              alt="Biểu trưng trường PTDTBT TH&THCS Phìn Hồ"
              className="w-14 h-14 sm:w-16 sm:h-16 object-contain drop-shadow-xs"
            />
          </div>

          {/* Institutional Typography Lockup */}
          <div className="flex flex-col justify-center select-text">
            {/* School type label */}
            <p className="font-semibold text-[#0a59ad] text-[10px] sm:text-[11px] tracking-wider uppercase leading-tight">
              TRƯỜNG PTDTBT TH &amp; THCS
            </p>
            {/* School Name */}
            <h1 className="font-extrabold text-[#0a59ad] tracking-tight uppercase text-base sm:text-lg md:text-xl leading-tight mt-0.5">
              PHÌN HỒ
            </h1>
            {/* System Name */}
            <h2 className="font-bold text-[#1684ea] tracking-tight text-xs sm:text-sm leading-tight mt-0.5">
              HỆ THỐNG GIÁM SÁT THI BẰNG AI
            </h2>
            {/* Location / Motto */}
            <p className="font-medium text-[#4a7db5] text-[10px] sm:text-[11px] tracking-wider uppercase mt-0.5">
              Nậm Xe, Phong Thổ, Lai Châu • Trung Thực – Kỷ Cương – Chất Lượng
            </p>
          </div>
        </div>

        {/* RIGHT STATUS & CONTROL AREA */}
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3 shrink-0">
          {/* Clock Card */}
          <div className="flex items-center gap-2.5 bg-white border border-[#b3d4f0] px-3 sm:px-3.5 py-1.5 rounded-xl shadow-xs">
            <Clock className="w-4 h-4 text-[#0a59ad] shrink-0" />
            <div className="flex flex-col text-left">
              <span className="font-mono font-bold text-xs sm:text-sm text-slate-800 leading-none">
                {timeStr || '11:31:40 UTC'}
              </span>
              <span className="font-mono text-[10px] text-gray-500 leading-none mt-1">
                {dateStr || 'Hôm nay'}
              </span>
            </div>
          </div>

          {/* System Status Badge */}
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

          {/* Quick Settings & Admin */}
          <div className="flex items-center gap-1.5">
            {!DEMO_CONFIG.isDemo && (
              <button
                onClick={() => onSelectView(currentView === 'ai-settings' ? 'live-monitor' : 'ai-settings')}
                title="Cấu hình độ nhạy AI"
                className={`p-2 rounded-xl border transition-colors shadow-xs cursor-pointer ${
                  currentView === 'ai-settings'
                    ? 'bg-[#0a59ad] text-white border-[#0a59ad]'
                    : 'bg-white hover:bg-[#f0f7ff] border-[#b3d4f0] text-gray-700'
                }`}
              >
                <Settings className="w-4 h-4" />
              </button>
            )}

            {/* Admin Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                className="flex items-center gap-2 bg-white hover:bg-[#f0f7ff] border border-[#b3d4f0] px-3 py-1.5 rounded-xl shadow-xs transition-colors text-xs font-semibold text-slate-700 cursor-pointer"
              >
                <div className="w-6 h-6 rounded-full bg-[#0a59ad] text-white flex items-center justify-center shrink-0">
                  <User className="w-3.5 h-3.5" />
                </div>
                <span className="hidden sm:inline">Giám thị Phìn Hồ</span>
                <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform ${isAdminMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {isAdminMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl border border-[#b3d4f0] shadow-lg py-1.5 z-50 text-xs">
                  <div className="px-3 py-1.5 border-b border-gray-100 text-gray-500 text-[11px]">
                    Đăng nhập: <strong className="text-slate-800">giamthi@pinhho.edu.vn</strong>
                  </div>
                  <button
                    onClick={() => { onSelectView('live-monitor'); setIsAdminMenuOpen(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-[#f0f7ff] text-slate-700 font-medium cursor-pointer"
                  >
                    Bàn Giám Sát Trực Tiếp
                  </button>
                  {!DEMO_CONFIG.isDemo && (
                    <button
                      onClick={() => { onSelectView('ai-settings'); setIsAdminMenuOpen(false); }}
                      className="w-full text-left px-3 py-2 hover:bg-[#f0f7ff] text-slate-700 font-medium cursor-pointer"
                    >
                      Cấu Hình Độ Nhạy AI
                    </button>
                  )}
                  <button
                    onClick={toggleFullscreen}
                    className="w-full text-left px-3 py-2 hover:bg-[#f0f7ff] text-slate-700 font-medium border-t border-gray-100 flex items-center justify-between cursor-pointer"
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
