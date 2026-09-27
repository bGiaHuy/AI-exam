import React from 'react';

export const DashboardFooter: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 px-4 sm:px-8 py-2 flex flex-col md:flex-row items-center justify-between gap-3 text-xs select-none shrink-0 z-20 overflow-hidden">
      {/* ========================================================================= */}
      {/* LEFT: SCHOOL ARCHITECTURE LINE-ART                                        */}
      {/* ========================================================================= */}
      <div className="flex items-center shrink-0">
        <img 
          src="/assets/chuyenhvt/school-lineart.png" 
          alt="Hình nét kiến trúc THPT Chuyên Hoàng Văn Thụ" 
          className="h-9 sm:h-11 w-auto object-contain opacity-80 hover:opacity-100 transition-opacity mix-blend-multiply"
        />
      </div>

      {/* ========================================================================= */}
      {/* CENTER: SLOGAN (TRI THỨC HÔM NAY - KIẾN TẠO NGÀY MAI)                     */}
      {/* ========================================================================= */}
      <div className="flex flex-col items-center justify-center shrink-0">
        <img 
          src="/assets/chuyenhvt/footer-slogan.png" 
          alt="Tri thức hôm nay - Kiến tạo ngày mai" 
          className="h-8 sm:h-10 w-auto object-contain mix-blend-multiply"
          onError={(e) => {
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
      </div>

      {/* ========================================================================= */}
      {/* RIGHT: ORNAMENTAL DIVIDER & INSTITUTIONAL ADDRESS                         */}
      {/* ========================================================================= */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Diamond Ornamental Divider */}
        <div className="w-16 sm:w-28 h-4 flex items-center overflow-hidden">
          <img 
            src="/assets/chuyenhvt/footer-divider.svg" 
            alt="Divider hoa văn" 
            className="w-full h-full object-contain opacity-70"
          />
        </div>

        {/* School Name & Province */}
        <div className="font-semibold text-slate-700 tracking-wider text-[11px] sm:text-xs uppercase whitespace-nowrap">
          THPT CHUYÊN HOÀNG VĂN THỤ <span className="text-gray-400 font-normal mx-1">|</span> TỈNH PHÚ THỌ
        </div>
      </div>
    </footer>
  );
};
