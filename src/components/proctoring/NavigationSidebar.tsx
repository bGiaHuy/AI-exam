import React from 'react';
import { 
  Video, 
  Sliders, 
  Database,
  Radio,
  Cpu,
} from 'lucide-react';
import { ViewMode } from '../../types';

interface NavigationSidebarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  activeIncidentsCount?: number;
}

export const NavigationSidebar: React.FC<NavigationSidebarProps> = ({
  currentView,
  onSelectView,
  activeIncidentsCount = 0
}) => {
  const navItems = [
    {
      id: 'live-monitor' as ViewMode,
      label: 'Giám Sát Trực Tiếp',
      sublabel: '3 Camera phòng thi',
      icon: Video,
      badge: null
    },
    {
      id: 'ai-settings' as ViewMode,
      label: 'Cấu Hình AI',
      sublabel: 'Độ nhạy & RingBuffer',
      icon: Sliders,
      badge: null
    }
  ];

  return (
    <aside className="w-[205px] shrink-0 flex flex-col justify-between select-none z-20 overflow-hidden shadow-md border-r border-[#b3d4f0] relative">
      {/* ================================================================= */}
      {/* PHÌN HỒ SIDEBAR: Light sky gradient + mountain background SVG     */}
      {/* ================================================================= */}

      {/* Background SVG — mountain + ruộng bậc thang motif */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <img
          src="/assets/pinhho/sidebar-bg.svg"
          alt="Nền sidebar núi Phìn Hồ"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Top Section: Navigation Links */}
      <div className="p-3 space-y-4 relative z-10">
        {/* Navigation Category Label */}
        <div className="px-2 pt-1 flex items-center justify-between">
          <p className="text-[10px] font-mono font-bold text-[#0a59ad] uppercase tracking-wider">
            ĐIỀU HÀNH PHÒNG THI
          </p>
          <span className="w-1.5 h-1.5 rounded-full bg-[#1FB45B] animate-pulse" />
        </div>

        {/* Menu Items */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelectView(item.id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#0a59ad] text-white shadow-md font-semibold border-l-4 border-[#1684ea]'
                    : 'text-[#0a59ad] hover:text-[#0a59ad] hover:bg-[#ddeeff]/60 border-l-4 border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#1684ea]'}`} />
                <div className="flex-1 truncate">
                  <div className="text-xs leading-tight font-medium truncate">{item.label}</div>
                  <div className={`text-[10px] leading-tight truncate mt-0.5 ${isActive ? 'text-blue-100' : 'text-[#4a7db5]'}`}>
                    {item.sublabel}
                  </div>
                </div>
                {item.badge && (
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white text-[#0a59ad]' : 'bg-[#1684ea] text-white'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Quick Room Status Card */}
        <div className="p-2.5 rounded-xl bg-white/70 border border-[#b3d4f0] space-y-1.5 shadow-xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-[#0a59ad]">
            <span className="tracking-tight">Phòng Thi: P.201</span>
            <span className="w-2 h-2 rounded-full bg-[#1FB45B] animate-pulse" />
          </div>
          <p className="text-[10px] text-[#4a7db5] font-sans">
            Môn thi: Tiếng Việt / Toán
          </p>
          <div className="pt-1 border-t border-[#b3d4f0]/60 flex items-center justify-between text-[10px] font-mono text-[#4a7db5]">
            <span>Sĩ số: <strong className="text-[#0a59ad]">18/18</strong></span>
            <span className="text-[#1FB45B] font-semibold">Đủ</span>
          </div>
        </div>
      </div>

      {/* Bottom Section: Mountain motif + Diagnostics */}
      <div className="border-t border-[#b3d4f0]/60 bg-white/50 relative overflow-hidden z-10">
        {/* Hoa ban + mountain decorative illustration */}
        <div className="px-3 pt-3 pb-1 flex flex-col items-center gap-1">
          <img
            src="/assets/pinhho/mountains.svg"
            alt="Núi rừng Phìn Hồ"
            className="w-full h-auto object-contain opacity-60 hover:opacity-90 transition-opacity"
          />
          <div className="flex items-center gap-2">
            <img
              src="/assets/pinhho/hoa-ban.svg"
              alt="Hoa Ban"
              className="w-8 h-8 object-contain opacity-70"
            />
            <span className="text-[9px] font-mono text-[#4a7db5] uppercase tracking-widest">Phìn Hồ • Lai Châu</span>
          </div>
        </div>

        {/* Diagnostics Info */}
        <div className="p-3 pt-1 space-y-1.5 border-t border-[#b3d4f0]/40">
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#4a7db5]">
            <Radio className="w-3 h-3 text-[#1FB45B]" />
            <span>Trạm Offline: Localhost</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#4a7db5]">
            <Database className="w-3 h-3 text-[#0a59ad]" />
            <span>SQLite 3 (WAL mode)</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#4a7db5]">
            <Cpu className="w-3 h-3 text-[#1684ea]" />
            <span>YOLOv11 & Phone v5</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
