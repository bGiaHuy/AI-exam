import React, { useState } from 'react';
import { 
  AlertCircle, 
  Filter, 
  RefreshCw, 
  ShieldCheck,
  Trash2
} from 'lucide-react';
import { Incident } from '../../types';
import { IncidentCard } from './IncidentCard';

interface IncidentSidebarProps {
  incidents: Incident[];
  onOpenVideoModal: (incident: Incident) => void;
  onConfirmIncident?: (incidentId: string) => void;
  onDismissIncident?: (incidentId: string) => void;
  onDeleteIncident?: (incidentId: string) => void;
  onPurgeAllVideos?: () => void;
  isReadOnly?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  error?: string | null;
}

export const IncidentSidebar: React.FC<IncidentSidebarProps> = ({
  incidents,
  onOpenVideoModal,
  onConfirmIncident,
  onDismissIncident,
  onDeleteIncident,
  onPurgeAllVideos,
  isReadOnly = false,
  onRefresh,
  isRefreshing = false,
  error,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'red' | 'yellow'>('all');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showPurgeConfirm, setShowPurgeConfirm] = useState(false);

  // Filter incidents based on selected severity
  const filteredIncidents = incidents.filter(inc => {
    if (filterSeverity === 'all') return true;
    return inc.level === filterSeverity;
  });

  return (
    <div className="bg-white border border-[#DCE6F5] rounded-xl shadow-xs overflow-hidden flex flex-col w-full lg:w-[280px] xl:w-[343px] shrink-0 h-full max-h-[820px] select-none">
      {/* ========================================================================= */}
      {/* 1. SIDEBAR HEADER                                                         */}
      {/* ========================================================================= */}
      <div className="h-11 px-3.5 bg-white border-b border-[#DCE6F5] flex items-center justify-between shrink-0">
        {/* Left: Red Alert Icon & Title */}
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-[#EF3340] text-white flex items-center justify-center shrink-0 shadow-2xs">
            <AlertCircle className="w-3.5 h-3.5" />
          </div>
          <h2 className="font-extrabold text-[#173B7A] tracking-tight text-xs sm:text-sm uppercase">
            SỰ CỐ VI PHẠM ({incidents.length})
          </h2>
        </div>

        {/* Right: Filter & Action Buttons */}
        <div className="flex items-center gap-1">
          {/* Purge All Videos Button */}
          {onPurgeAllVideos && !isReadOnly && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowPurgeConfirm(!showPurgeConfirm)}
                title="Xóa toàn bộ video bằng chứng vi phạm"
                className="p-1.5 rounded-lg border border-[#DCE6F5] bg-white hover:bg-rose-50 text-gray-400 hover:text-[#EF3340] transition-colors shadow-2xs cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>

              {showPurgeConfirm && (
                <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl border border-[#DCE6F5] shadow-xl p-2.5 z-40 text-xs">
                  <p className="font-semibold text-slate-800 mb-1">Xóa toàn bộ video?</p>
                  <p className="text-[11px] text-gray-500 mb-2 leading-relaxed">
                    Tất cả các video và bản ghi vi phạm sẽ bị xóa sạch khỏi máy tính.
                  </p>
                  <div className="flex justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => setShowPurgeConfirm(false)}
                      className="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-[11px] cursor-pointer"
                    >
                      Hủy
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowPurgeConfirm(false);
                        onPurgeAllVideos();
                      }}
                      className="px-2 py-1 rounded bg-[#EF3340] hover:bg-red-700 text-white text-[11px] font-semibold cursor-pointer"
                    >
                      Xác nhận xóa
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Filter Button */}
          <div className="relative">
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              title="Lọc mức độ vi phạm"
              className={`p-1.5 rounded-lg border transition-colors shadow-2xs cursor-pointer ${
                filterSeverity !== 'all'
                  ? 'bg-blue-50 border-[#2344B6] text-[#2344B6]'
                  : 'bg-white hover:bg-gray-50 border-[#DCE6F5] text-gray-500 hover:text-gray-800'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
            </button>

            {/* Filter Dropdown */}
            {showFilterDropdown && (
              <div className="absolute right-0 mt-2 w-36 bg-white rounded-xl border border-[#DCE6F5] shadow-lg py-1 z-30 text-xs">
                <button
                  onClick={() => { setFilterSeverity('all'); setShowFilterDropdown(false); }}
                  className={`w-full text-left px-3 py-1.5 hover:bg-gray-50 font-medium cursor-pointer ${filterSeverity === 'all' ? 'text-[#2344B6] font-bold' : 'text-gray-700'}`}
                >
                  Tất cả ({incidents.length})
                </button>
                <button
                  onClick={() => { setFilterSeverity('red'); setShowFilterDropdown(false); }}
                  className={`w-full text-left px-3 py-1.5 hover:bg-gray-50 font-medium cursor-pointer ${filterSeverity === 'red' ? 'text-[#EF3340] font-bold' : 'text-gray-700'}`}
                >
                  Cờ đỏ (Nghiêm trọng)
                </button>
                <button
                  onClick={() => { setFilterSeverity('yellow'); setShowFilterDropdown(false); }}
                  className={`w-full text-left px-3 py-1.5 hover:bg-gray-50 font-medium cursor-pointer ${filterSeverity === 'yellow' ? 'text-amber-600 font-bold' : 'text-gray-700'}`}
                >
                  Cờ vàng (Nghi vấn)
                </button>
              </div>
            )}
          </div>

          {/* Refresh Button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              title="Làm mới danh sách sự cố"
              className={`p-1.5 rounded-lg border border-[#DCE6F5] bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-800 transition-colors shadow-2xs cursor-pointer ${
                isRefreshing ? 'animate-spin text-[#2344B6]' : ''
              }`}
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. SCROLLABLE INCIDENTS LIST                                              */}
      {/* ========================================================================= */}
      {error && <p role="alert" className="px-3 py-2 text-xs border bg-zinc-900 border-rose-800 text-rose-300">{error}</p>}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
        {filteredIncidents.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center p-4 text-gray-400">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-[#16B364] flex items-center justify-center mb-2">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <p className="text-xs font-semibold text-slate-700">Chưa ghi nhận vi phạm</p>
            <p className="text-[11px] text-gray-500 mt-1 max-w-[200px] leading-relaxed">
              Hệ thống AI đang giám sát liên tục và sẽ trích xuất clip bằng chứng ngay khi có sự cố.
            </p>
          </div>
        ) : (
          filteredIncidents.map((incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              onOpenVideoModal={onOpenVideoModal}
              onConfirm={onConfirmIncident}
              onDismiss={onDismissIncident}
              onDelete={onDeleteIncident}
              isReadOnly={isReadOnly}
            />
          ))
        )}
      </div>
    </div>
  );
};
