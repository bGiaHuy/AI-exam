import React from 'react';
import { 
  Video, 
  LayoutGrid, 
  ShieldAlert, 
  Sliders, 
  HelpCircle,
  Cpu,
  Database,
  Radio
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
    <aside className="w-[205px] shrink-0 bg-gradient-to-b from-[#0E1E45] via-[#122858] to-[#163474] text-white border-r border-[#1C49B6]/40 flex flex-col justify-between select-none z-20 overflow-hidden shadow-md">
      {/* Top Section: Navigation Links */}
      <div className="p-3 space-y-4">
        {/* Navigation Category Label */}
        <div className="px-2 pt-1 flex items-center justify-between">
          <p className="text-[10px] font-mono font-bold text-[#B7CBEF] uppercase tracking-wider">
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
                    ? 'bg-[#1C49B6] text-white shadow-md font-semibold border-l-4 border-[#E8465A]'
                    : 'text-slate-200 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#B7CBEF]'}`} />
                <div className="flex-1 truncate">
                  <div className="text-xs leading-tight font-medium truncate">{item.label}</div>
                  <div className={`text-[10px] leading-tight truncate mt-0.5 ${isActive ? 'text-blue-100' : 'text-slate-400'}`}>
                    {item.sublabel}
                  </div>
                </div>
                {item.badge && (
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white text-[#1C49B6]' : 'bg-[#E8465A] text-white'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Quick Room Status Card */}
        <div className="p-2.5 rounded-xl bg-[#091533]/80 border border-[#B7CBEF]/25 space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-bold text-white">
            <span className="tracking-tight">Phòng Thi: P.201</span>
            <span className="w-2 h-2 rounded-full bg-[#1FB45B] animate-pulse" />
          </div>
          <p className="text-[10px] text-slate-300 font-sans">
            Môn thi: Tin Học / Ngoại Ngữ
          </p>
          <div className="pt-1 border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-slate-300">
            <span>Sĩ số: <strong className="text-white">24/24</strong></span>
            <span className="text-[#1FB45B] font-semibold">Đủ</span>
          </div>
        </div>
      </div>

      {/* Bottom Section: Da Nang Dragon Bridge Decorative Illustration & Diagnostics */}
      <div className="border-t border-white/10 bg-[#091533]/60 relative overflow-hidden">
        {/* Decorative Dragon Bridge Graphic */}
        <div className="px-3 pt-3 pb-1 opacity-70 hover:opacity-100 transition-opacity">
          <img 
            src="/assets/tranphu/dragon-bridge.svg" 
            alt="Cầu Rồng Đà Nẵng" 
            className="w-full h-auto object-contain filter drop-shadow-sm" 
          />
          <div className="text-center text-[9px] font-mono text-[#B7CBEF]/80 uppercase tracking-widest mt-1">
            Đà Nẵng City
          </div>
        </div>

        {/* Diagnostics Info */}
        <div className="p-3 pt-1 space-y-1.5 border-t border-white/5">
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-300">
            <Radio className="w-3 h-3 text-[#1FB45B]" />
            <span>Trạm Offline: Localhost</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-300">
            <Database className="w-3 h-3 text-[#B7CBEF]" />
            <span>SQLite 3 (WAL mode)</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-300">
            <Cpu className="w-3 h-3 text-purple-300" />
            <span>YOLOv11 & Phone v5</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
