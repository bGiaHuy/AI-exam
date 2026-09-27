import React from 'react';

export const DashboardFooter: React.FC = () => {
  return (
    <footer className="relative border-t border-[#b3d4f0] px-4 sm:px-8 py-2.5 flex flex-col md:flex-row items-center justify-between gap-3 text-xs select-none shrink-0 z-20 overflow-hidden" style={{ background: '#f5faff' }}>
      {/* ========================================================================= */}
      {/* BACKGROUND: Ruộng bậc thang / textile strip bottom                        */}
      {/* ========================================================================= */}
      <div
        className="absolute inset-x-0 bottom-0 pointer-events-none z-0 h-10 overflow-hidden opacity-35"
      >
        <img
          src="/assets/pinhho/terraces.svg"
          alt="Ruộng bậc thang Tây Bắc trang trí chân trang"
          className="w-full h-full object-cover object-bottom"
        />
      </div>

      {/* Textile color strip along very bottom */}
      <div className="absolute inset-x-0 bottom-0 pointer-events-none z-0 h-[5px] opacity-50">
        <img
          src="/assets/pinhho/textile-strip.svg"
          alt="Họa tiết dệt Tây Bắc"
          className="w-full h-full object-cover"
        />
      </div>

      {/* ========================================================================= */}
      {/* LEFT: SCHOOL MARK & NAME                                                   */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-2.5 shrink-0">
        <img
          src="/assets/pinhho/school-mark.svg"
          alt="Biểu trưng trường PTDTBT TH&THCS Phìn Hồ"
          className="h-7 w-auto object-contain"
        />
        <div className="flex flex-col">
          <span className="font-bold text-[#0a59ad] tracking-tight uppercase text-xs">
            PTDTBT TH &amp; THCS PHÌN HỒ
          </span>
          <span className="text-[10px] text-[#4a7db5] font-mono">
            Nậm Xe, Phong Thổ, Lai Châu
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* CENTER: SLOGAN                                                            */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex flex-col items-center justify-center shrink-0">
        <span className="font-bold text-[#0a59ad] tracking-wide uppercase text-xs">
          KHOA HỌC KỸ THUẬT &amp; TRÍ TUỆ NHÂN TẠO TRONG GIÁO DỤC
        </span>
        <span className="text-[10px] text-[#4a7db5] font-medium tracking-wider uppercase mt-0.5">
          Trung Thực • Kỷ Cương • Chất Lượng • Lai Châu
        </span>
      </div>

      {/* ========================================================================= */}
      {/* RIGHT: SYSTEM STATUS & ROOM BADGE                                         */}
      {/* ========================================================================= */}
      <div className="relative z-10 flex items-center gap-3 shrink-0">
        <div className="px-2.5 py-1 rounded-lg bg-white border border-[#b3d4f0] font-mono text-[11px] text-[#0a59ad] font-semibold shadow-2xs">
          <span className="text-[#1FB45B] mr-1.5 font-bold">●</span>
          <span>BÀN GIÁM THỊ SỐ 01</span>
        </div>

        <div className="font-semibold text-[#4a7db5] tracking-wider text-[11px] uppercase whitespace-nowrap">
          PHONG THỔ <span className="text-[#b3d4f0] font-normal mx-1">|</span> LAI CHÂU
        </div>
      </div>
    </footer>
  );
};
