import React from 'react';

export const DashboardFooter: React.FC = () => {
  return (
    <footer className="relative bg-white border-t border-[#DDE6F2] px-4 sm:px-8 py-2.5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs select-none shrink-0 z-20 overflow-hidden">
      {/* ========================================================================= */}
      {/* BACKGROUND DECORATIVE WAVE PATTERN (Đà Nẵng Ocean Wave)                  */}
      {/* ========================================================================= */}
      <div 
        className="absolute inset-x-0 bottom-0 pointer-events-none opacity-25 z-0 h-12 overflow-hidden"
      >
        <img 
          src="/assets/tranphu/footer-wave.svg" 
          alt="Dải sóng biển Đà Nẵng trang trí chân trang" 
          className="w-full h-full object-cover object-bottom"
        />
      </div>

      {/* ========================================================================= */}
      {/* LEFT: SCHOOL EMBLEM & NAME                                                */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-2.5 shrink-0">
        <img 
          src="/assets/tranphu/school-logo.png" 
          alt="Logo THPT Trần Phú - Đà Nẵng" 
          className="h-7 w-auto object-contain drop-shadow-2xs"
        />
        <div className="flex flex-col">
          <span className="font-bold text-[#163474] tracking-tight uppercase text-xs">
            TRƯỜNG THPT TRẦN PHÚ
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            Quận Hải Châu, TP. Đà Nẵng
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CENTER: SLOGAN                                                            */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col items-center justify-center shrink-0">
        <span className="font-bold text-[#1C49B6] tracking-wide uppercase text-xs">
          KHOA HỌC KỸ THUẬT & TRÍ TUỆ NHÂN TẠO TRONG GIÁO DỤC
        </span>
        <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase mt-0.5">
          Trung Thực • Trách Nhiệm • Khát Vọng • Đà Nẵng
        </span>
      </div>

      {/* ========================================================================= */}
      {/* RIGHT: SYSTEM STATUS & ROOM BADGE                                         */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-3 shrink-0">
        <div className="px-2.5 py-1 rounded-lg bg-[#F7FAFF] border border-[#DDE6F2] font-mono text-[11px] text-slate-700 font-semibold shadow-2xs">
          <span className="text-[#1FB45B] mr-1.5 font-bold">●</span>
          <span>BÀN GIÁM THỊ SỐ 01</span>
        </div>

        <div className="font-semibold text-slate-600 tracking-wider text-[11px] uppercase whitespace-nowrap">
          HẢI CHÂU <span className="text-gray-400 font-normal mx-1">|</span> ĐÀ NẴNG
        </div>
      </div>
    </footer>
  );
};
