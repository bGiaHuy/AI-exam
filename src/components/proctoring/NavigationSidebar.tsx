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
    <aside className="w-[195px] shrink-0 bg-white border-r border-[#DCE6F5] flex flex-col justify-between select-none z-20 overflow-hidden shadow-2xs">
      {/* Top Section: Navigation Links */}
      <div className="p-3 space-y-4">
        {/* Navigation Category Label */}
        <div className="px-2 pt-1">
          <p className="text-[10px] font-mono font-bold text-[#173B7A] uppercase tracking-wider">
            ĐIỀU HÀNH PHÒNG THI
          </p>
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
                    ? 'bg-[#2344B6] text-white shadow-xs font-semibold'
                    : 'text-slate-600 hover:text-[#173B7A] hover:bg-[#F0F5FF]'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-[#2344B6]'}`} />
                <div className="flex-1 truncate">
                  <div className="text-xs leading-tight font-medium truncate">{item.label}</div>
                  <div className={`text-[10px] leading-tight truncate mt-0.5 ${isActive ? 'text-blue-100' : 'text-slate-400'}`}>
                    {item.sublabel}
                  </div>
                </div>
                {item.badge && (
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                    isActive ? 'bg-white text-[#2344B6]' : 'bg-[#EF3340] text-white'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Quick Room Status Card */}
        <div className="p-2.5 rounded-xl bg-[#F7FAFF] border border-[#DCE6F5] space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-bold text-[#173B7A]">
            <span>Phòng Thi: P.201</span>
            <span className="w-2 h-2 rounded-full bg-[#16B364] animate-pulse" />
          </div>
          <p className="text-[10px] text-slate-500 font-sans">
            Môn thi: Tin Học / Ngoại Ngữ
          </p>
          <div className="pt-1 border-t border-[#E3EDFA] flex items-center justify-between text-[10px] font-mono text-slate-600">
            <span>Sĩ số: <strong>24/24</strong></span>
            <span className="text-[#16B364] font-semibold">Đủ</span>
          </div>
        </div>
      </div>

      {/* Bottom Section: System Diagnostics */}
      <div className="p-3 border-t border-[#DCE6F5] bg-[#FAF8FE]/50 space-y-2">
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
          <Radio className="w-3 h-3 text-[#16B364]" />
          <span>Trạm Offline: Localhost</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
          <Database className="w-3 h-3 text-[#2344B6]" />
          <span>SQLite 3 (WAL mode)</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500">
          <Cpu className="w-3 h-3 text-purple-600" />
          <span>YOLOv11 & Phone v5</span>
        </div>
      </div>
    </aside>
  );
};
