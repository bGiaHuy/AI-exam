import React from 'react';
import { Maximize2, Scan } from 'lucide-react';

interface VideoStatusBarProps {
  isOnline: boolean;
  resolution?: string;
  fps?: number;
  onFullscreen?: () => void;
}

export const VideoStatusBar: React.FC<VideoStatusBarProps> = ({
  isOnline,
  resolution = "1920 × 1080",
  fps = 0,
  onFullscreen
}) => {
  return (
    <div className="h-8 px-3 bg-[#0F1E36] text-gray-300 flex items-center justify-between text-[11px] font-mono select-none border-t border-[#1C2E4C] shrink-0">
      {/* Left: Fullscreen / Scan Icon */}
      <button 
        onClick={onFullscreen}
        title="Phóng to luồng camera"
        className="text-gray-400 hover:text-white transition-colors p-0.5 rounded"
      >
        <Scan className="w-3.5 h-3.5" />
      </button>

      {/* Middle & Right: Status, Resolution, FPS */}
      <div className="flex items-center gap-2.5">
        {/* Status indicator */}
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-[#16B364] animate-pulse' : 'bg-[#EF3340]'}`} />
          <span className="text-gray-200 font-medium">
            {isOnline ? 'Trực tiếp' : 'Ngoại tuyến'}
          </span>
        </div>

        <span className="text-gray-500">|</span>

        {/* Resolution */}
        <span className="text-gray-300">
          {resolution}
        </span>

        <span className="text-gray-500">|</span>

        {/* FPS */}
        <span className="text-gray-300">
          fps: <strong className="text-gray-100 font-semibold">{fps}</strong>
        </span>
      </div>
    </div>
  );
};
