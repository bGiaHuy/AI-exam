import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Smartphone, 
  Eye, 
  Clock, 
  Film, 
  Save, 
  RotateCcw, 
  CheckCircle2, 
  ShieldAlert,
  SlidersHorizontal
} from 'lucide-react';
import { AISettings } from '../types';

interface AISettingsViewProps {
  settings: AISettings;
  onSaveSettings: (settings: AISettings) => void;
}

export const AISettingsView: React.FC<AISettingsViewProps> = ({ settings, onSaveSettings }) => {
  const [config, setConfig] = useState<AISettings>(settings);
  const [savedToast, setSavedToast] = useState(false);

  useEffect(() => {
    setConfig(settings);
  }, [settings]);

  const handleSave = () => {
    onSaveSettings(config);
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 2500);
  };

  const handleResetDefaults = () => {
    setConfig({
      phone_confidence: 0.35,
      posture_alert_seconds: 1.25,
      suspicion_threshold: 0.50,
      pre_roll_seconds: 5.0,
      post_roll_seconds: 10.0,
      cooldown_seconds: 6.0
    });
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6 max-w-4xl mx-auto font-sans select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-zinc-800">
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-emerald-400" />
            <span>CẤU HÌNH ĐỘ NHẠY AI & THAM SỐ GHI BẰNG CHỨNG</span>
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Cấu hình thời gian trễ nhận diện, ngưỡng phát hiện điện thoại và bộ đệm RingBuffer (đồng bộ trực tiếp với Backend).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetDefaults}
            className="px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-850 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Mặc định</span>
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Lưu Cấu Hình</span>
          </button>
        </div>
      </div>

      {savedToast && (
        <div className="p-3 rounded-md bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Đã lưu cấu hình và đồng bộ hóa thành công vào Backend & RingBuffer!</span>
        </div>
      )}

      {/* Grid Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Phát hiện Điện thoại */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-rose-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Ngưỡng Điện Thoại (YOLO)</h3>
            </div>
            <span className="font-mono text-xs font-bold text-rose-400">
              {Math.round(config.phone_confidence * 100)}%
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Độ tin cậy tối thiểu để mô hình xác nhận đối tượng là điện thoại và gán vào người gần nhất.
          </p>
          <input
            type="range"
            min="0.10"
            max="0.90"
            step="0.05"
            value={config.phone_confidence}
            onChange={(e) => setConfig({ ...config, phone_confidence: parseFloat(e.target.value) })}
            className="w-full accent-rose-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>10% (Nhạy cao)</span>
            <span>Mặc định: 35%</span>
            <span>90% (Nghiêm ngặt)</span>
          </div>
        </div>

        {/* Card 2: Thời gian duy trì quay đầu */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Thời Gian Leo Thang Cờ Đỏ</h3>
            </div>
            <span className="font-mono text-xs font-bold text-amber-400">
              {config.posture_alert_seconds.toFixed(2)}s
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Thời gian tư thế quay đầu bất thường phải duy trì liên tục để nâng cấp từ cờ Vàng lên cờ Đỏ (cắt clip).
          </p>
          <input
            type="range"
            min="0.50"
            max="3.00"
            step="0.25"
            value={config.posture_alert_seconds}
            onChange={(e) => setConfig({ ...config, posture_alert_seconds: parseFloat(e.target.value) })}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>0.5s (Tức thời)</span>
            <span>Mặc định: 1.25s</span>
            <span>3.0s (Trễ cao)</span>
          </div>
        </div>

        {/* Card 3: Ngưỡng nghi vấn tư thế */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Ngưỡng Nghi Vấn Tư Thế</h3>
            </div>
            <span className="font-mono text-xs font-bold text-indigo-400">
              {Math.round(config.suspicion_threshold * 100)}%
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Ngưỡng điểm bất thường từ thuật toán hình học Pose để bắt đầu đếm thời gian nghi ngờ (cờ Vàng).
          </p>
          <input
            type="range"
            min="0.20"
            max="0.80"
            step="0.05"
            value={config.suspicion_threshold}
            onChange={(e) => setConfig({ ...config, suspicion_threshold: parseFloat(e.target.value) })}
            className="w-full accent-indigo-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>20% (Dễ nghi ngờ)</span>
            <span>Mặc định: 50%</span>
            <span>80% (Khắt khe)</span>
          </div>
        </div>

        {/* Card 4: Cooldown chống trùng */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Giãn Cách Cooldown Clip</h3>
            </div>
            <span className="font-mono text-xs font-bold text-emerald-400">
              {config.cooldown_seconds.toFixed(1)}s
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Khoảng thời gian tối thiểu trước khi một đối tượng có thể kích hoạt tạo clip thứ hai cùng loại.
          </p>
          <input
            type="range"
            min="2.0"
            max="15.0"
            step="1.0"
            value={config.cooldown_seconds}
            onChange={(e) => setConfig({ ...config, cooldown_seconds: parseFloat(e.target.value) })}
            className="w-full accent-emerald-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>2.0s (Ngắn)</span>
            <span>Mặc định: 6.0s</span>
            <span>15.0s (Dài)</span>
          </div>
        </div>

        {/* Card 5: Pre-roll Buffer */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Film className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Đoạn Video Trước Sự Kiện (Pre-Roll)</h3>
            </div>
            <span className="font-mono text-xs font-bold text-cyan-400">
              {config.pre_roll_seconds.toFixed(1)}s
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Thời lượng video lấy từ bộ nhớ đệm RAM trước khoảnh khắc hệ thống phát hiện vi phạm.
          </p>
          <input
            type="range"
            min="2.0"
            max="10.0"
            step="1.0"
            value={config.pre_roll_seconds}
            onChange={(e) => setConfig({ ...config, pre_roll_seconds: parseFloat(e.target.value) })}
            className="w-full accent-cyan-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>2.0s</span>
            <span>Mặc định: 5.0s</span>
            <span>10.0s</span>
          </div>
        </div>

        {/* Card 6: Post-roll Buffer */}
        <div className="p-4 rounded-lg bg-zinc-900 border border-zinc-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Film className="w-4 h-4 text-teal-400" />
              <h3 className="text-xs font-semibold text-zinc-200 uppercase">Đoạn Video Sau Sự Kiện (Post-Roll)</h3>
            </div>
            <span className="font-mono text-xs font-bold text-teal-400">
              {config.post_roll_seconds.toFixed(1)}s
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-relaxed">
            Thời lượng video tiếp tục thu thập sau khi phát hiện vi phạm để hoàn thiện clip chứng cứ.
          </p>
          <input
            type="range"
            min="2.0"
            max="20.0"
            step="1.0"
            value={config.post_roll_seconds}
            onChange={(e) => setConfig({ ...config, post_roll_seconds: parseFloat(e.target.value) })}
            className="w-full accent-teal-500 cursor-pointer"
          />
          <div className="flex justify-between text-[10px] font-mono text-zinc-500">
            <span>2.0s</span>
            <span>Mặc định: 10.0s</span>
            <span>20.0s</span>
          </div>
        </div>
      </div>
    </div>
  );
};
