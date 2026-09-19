import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Clock, 
  Sliders,
  Maximize2,
  Minimize2,
  Activity
} from 'lucide-react';
import { ViewMode } from '../types';
import { aiModelService, AIStatusResponse } from '../services/aiModelService';

interface TopNavBarProps {
  currentView: ViewMode;
  onSelectView: (view: ViewMode) => void;
  activeSource?: string;
}

export const TopNavBar: React.FC<TopNavBarProps> = ({
  currentView,
  onSelectView,
  activeSource = "Webcam máy trạm"
}) => {
  const [time, setTime] = useState<string>('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);

  // Poll Backend AI status
  useEffect(() => {
    const checkAI = async () => {
      const status = await aiModelService.checkStatus();
      setAiStatus(status);
    };
    checkAI();
    const interval = setInterval(checkAI, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('vi-VN', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        }) + ' UTC'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <header className="h-14 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur px-4 lg:px-6 flex items-center justify-between z-40 sticky top-0 shrink-0 select-none">
      {/* Brand & Source Info */}
      <div className="flex items-center gap-3">
        <div 
          onClick={() => onSelectView('live-monitor')} 
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-lg bg-zinc-900 flex items-center justify-center border border-zinc-700 group-hover:border-zinc-500 transition-colors">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-white font-mono">ExamVision AI</span>
              <span className="px-1.5 py-0.2 text-[9px] font-mono font-semibold uppercase rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                EDGE PROCTOR
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 font-mono hidden sm:block">
              Nguồn: <strong className="text-zinc-200">{activeSource}</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Right Telemetry & Utility Actions */}
      <div className="flex items-center gap-2.5">
        {/* Real-time Clock */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono bg-zinc-900 px-2.5 py-1 rounded border border-zinc-800 text-zinc-300">
          <Clock className="w-3.5 h-3.5 text-zinc-400" />
          <span>{time}</span>
        </div>

        {/* AI Engine Status Badge */}
        <div 
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-mono transition-colors ${
            aiStatus?.status === 'ONLINE'
              ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-400'
              : 'bg-amber-950/40 border-amber-800/80 text-amber-400'
          }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${aiStatus?.status === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
          <span className="font-semibold text-[11px] hidden sm:inline">
            {aiStatus?.status === 'ONLINE' ? 'AI SẴN SÀNG' : 'AI STANDBY'}
          </span>
        </div>

        {/* AI Sensitivity Settings Toggle Button */}
        <button
          onClick={() => onSelectView(currentView === 'ai-settings' ? 'live-monitor' : 'ai-settings')}
          title="Cấu hình độ nhạy AI"
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-medium transition-colors ${
            currentView === 'ai-settings'
              ? 'bg-zinc-800 text-white border-zinc-600'
              : 'bg-zinc-900 hover:bg-zinc-850 border-zinc-800 text-zinc-300'
          }`}
        >
          <Sliders className="w-3.5 h-3.5 text-zinc-400" />
          <span className="hidden md:inline text-xs">Cấu Hình AI</span>
        </button>

        {/* Fullscreen Toggle */}
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Thu nhỏ" : "Toàn màn hình"}
          className="p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 hover:text-white transition-colors"
        >
          {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>
    </header>
  );
};
