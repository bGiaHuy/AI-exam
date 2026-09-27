import React from 'react';
import { ShieldAlert, AlertOctagon, Clock } from 'lucide-react';
import { DEMO_CONFIG, isDemoExpired } from '../../config/demoConfig';

export const DemoWatermark: React.FC = () => {
  if (!DEMO_CONFIG.isDemo) return null;

  const expired = isDemoExpired();

  return (
    <>
      {/* 1. Permanent Top Watermark Bar */}
      <aside 
        aria-label="Demo Watermark Bar"
        className="w-full bg-amber-950/90 border-b border-amber-600/80 px-4 py-1.5 z-50 flex items-center justify-between text-xs font-mono text-amber-200 select-none shrink-0 shadow-sm"
      >
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 animate-pulse" />
          <span className="font-bold tracking-wide">
            {DEMO_CONFIG.watermarkText}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-amber-300/90">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span>Thời hạn demo: <strong className="text-amber-100">{DEMO_CONFIG.expiresAt}</strong></span>
        </div>
      </aside>

      {/* 2. Repeating Subtle Diagonal Watermark Overlay */}
      <div 
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-40 overflow-hidden flex flex-col justify-around opacity-[0.06] select-none"
      >
        {Array.from({ length: 7 }).map((_, rowIndex) => (
          <div 
            key={rowIndex} 
            className="flex justify-around transform -rotate-12 whitespace-nowrap text-xl font-mono font-black text-white tracking-widest uppercase"
          >
            <span>{DEMO_CONFIG.watermarkText}</span>
            <span>{DEMO_CONFIG.watermarkText}</span>
          </div>
        ))}
      </div>

      {/* 3. Expired Screen Lock Modal */}
      {expired && (
        <div className="fixed inset-0 z-[9999] bg-black/95 backdrop-blur-md flex items-center justify-center p-6 text-center select-none">
          <div className="max-w-md w-full bg-zinc-900 border border-rose-700/80 rounded-lg p-6 space-y-4 shadow-2xl">
            <div className="w-12 h-12 rounded-full bg-rose-950/80 border border-rose-600 flex items-center justify-center mx-auto text-rose-400">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <h2 className="text-base font-bold text-white font-mono tracking-tight uppercase">
              PHIÊN BẢN DEMO ĐÃ HẾT HẠN
            </h2>
            <p className="text-xs text-zinc-300 leading-relaxed">
              Quyền truy cập bản dùng thử sản phẩm cho tài khoản <strong>{DEMO_CONFIG.clientEmail}</strong> đã kết thúc theo thời hạn cam kết.
            </p>
            <div className="p-3 rounded bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-zinc-400">
              Hạn dùng ghi nhận: {DEMO_CONFIG.expiresAt}
            </div>
            <p className="text-[11px] text-zinc-500">
              Vui lòng liên hệ đơn vị phát triển để hoàn tất nghiệm thu và kích hoạt hệ thống chính thức.
            </p>
          </div>
        </div>
      )}
    </>
  );
};
