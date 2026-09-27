import React from 'react';

export const DashboardFooter: React.FC = () => {
  return (
    <footer className="relative bg-white border-t border-[#DCE6F5] px-4 sm:px-8 py-2.5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs select-none shrink-0 z-20 overflow-hidden">
      {/* ========================================================================= */}
      {/* BACKGROUND DECORATIVE WAVE PATTERN                                        */}
      {/* ========================================================================= */}
      <div 
        className="absolute inset-x-0 bottom-0 pointer-events-none opacity-20 z-0 h-12 overflow-hidden"
      >
        <img 
          src="/assets/tanlap/footer-wave.svg" 
          alt="Dải sóng trang trí chân trang Tân Lập" 
          className="w-full h-full object-cover object-bottom"
        />
      </div>

      {/* ========================================================================= */}
      {/* LEFT: SCHOOL EMBLEM & NAME                                                */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-2.5 shrink-0">
        <img 
          src="/assets/tanlap/school-logo.png" 
          alt="Logo THPT Tân Lập" 
          className="h-7 w-auto object-contain drop-shadow-2xs"
        />
        <div className="flex flex-col">
          <span className="font-bold text-[#173B7A] tracking-tight uppercase text-xs">
            TRƯỜNG THPT TÂN LẬP
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            Huyện Đan Phượng, Thành phố Hà Nội
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CENTER: SLOGAN (KỶ CƯƠNG - TRUNG THỰC - CHẤT LƯỢNG)                       */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col items-center justify-center shrink-0">
        <span className="font-bold text-[#2344B6] tracking-wide uppercase text-xs">
          KHOA HỌC KỸ THUẬT & TRÍ TUỆ NHÂN TẠO TRONG GIÁO DỤC
        </span>
        <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase mt-0.5">
          Kỷ Cương • Trung Thực • Đổi Mới Sáng Tạo
        </span>
      </div>

      {/* ========================================================================= */}
      {/* RIGHT: SYSTEM STATUS & ROOM BADGE                                         */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-3 shrink-0">
        <div className="px-2.5 py-1 rounded-lg bg-[#F7FAFF] border border-[#DCE6F5] font-mono text-[11px] text-slate-700 font-semibold shadow-2xs">
          <span className="text-[#16B364] mr-1.5 font-bold">●</span>
          <span>BÀN GIÁM THỊ SỐ 01</span>
        </div>

        <div className="font-semibold text-slate-600 tracking-wider text-[11px] uppercase whitespace-nowrap">
          ĐAN PHƯỢNG <span className="text-gray-400 font-normal mx-1">|</span> HÀ NỘI
        </div>
      </div>
    </footer>
  );
};
