import React from 'react';
import { Smartphone, UserCheck } from 'lucide-react';
import { AIDetectionResult } from '../../services/aiModelService';

interface DetectionOverlayProps {
  detections: AIDetectionResult[];
  show?: boolean;
}

export const DetectionOverlay: React.FC<DetectionOverlayProps> = ({
  detections,
  show = true
}) => {
  if (!show || !detections || detections.length === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
      {detections.map((det) => {
        const [left, top, width, height] = det.bbox;
        const isRed = det.level === 'red';
        const isYellow = det.level === 'yellow';
        const isViolation = isRed || isYellow;

        const strokeColor = isRed ? '#ED1B2F' : isYellow ? '#F59E0B' : '#00A95C';
        const badgeBgColor = isRed ? 'bg-[#ED1B2F]' : isYellow ? 'bg-[#F59E0B]' : 'bg-[#00A95C]';
        const fillColor = isRed ? 'rgba(237, 27, 47, 0.08)' : isYellow ? 'rgba(245, 158, 11, 0.08)' : 'rgba(0, 169, 92, 0.05)';

        // Confidence display
        const confPercent = Math.round(det.confidence <= 1.0 ? det.confidence * 100 : det.confidence);
        const hasPhone = det.label.toLowerCase().includes('phone') || det.label_vi.toLowerCase().includes('thoại');

        return (
          <div
            key={det.id}
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: `${width}%`,
              height: `${height}%`,
              backgroundColor: fillColor,
            }}
            className="absolute transition-all duration-75 select-none"
          >
            {/* SVG Corner Bracket Accents (Reference Style: Crisp L-shaped corners) */}
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none"
              style={{ overflow: 'visible' }}
            >
              {/* Thin bounding box outline */}
              <rect
                x="0"
                y="0"
                width="100%"
                height="100%"
                fill="none"
                stroke={strokeColor}
                strokeWidth="1.5"
                opacity="0.65"
                rx="6"
              />
              {/* Top-Left Corner Bracket */}
              <path
                d="M 0 20 L 0 4 Q 0 0 4 0 L 20 0"
                fill="none"
                stroke={strokeColor}
                strokeWidth="3.5"
                strokeLinecap="round"
              />
              {/* Top-Right Corner Bracket */}
              <path
                d="M calc(100% - 20px) 0 L calc(100% - 4px) 0 Q 100% 0 100% 4 L 100% 20"
                fill="none"
                stroke={strokeColor}
                strokeWidth="3.5"
                strokeLinecap="round"
              />
              {/* Bottom-Left Corner Bracket */}
              <path
                d="M 0 calc(100% - 20px) L 0 calc(100% - 4px) Q 0 100% 4 100% L 20 100%"
                fill="none"
                stroke={strokeColor}
                strokeWidth="3.5"
                strokeLinecap="round"
              />
              {/* Bottom-Right Corner Bracket */}
              <path
                d="M calc(100% - 20px) 100% L calc(100% - 4px) 100% Q 100% 100% 100% calc(100% - 4px) L 100% calc(100% - 20px)"
                fill="none"
                stroke={strokeColor}
                strokeWidth="3.5"
                strokeLinecap="round"
              />
            </svg>

            {/* Top-Left Semantic Detection Label */}
            <div 
              className={`absolute -top-6 left-0 px-2 py-0.5 rounded-t-md text-white font-mono text-[11px] font-bold shadow-xs flex items-center gap-1.5 whitespace-nowrap ${badgeBgColor}`}
            >
              <span>{det.label_vi}</span>
              {det.track_id !== undefined && <span>(Track {det.track_id})</span>}
              <span className="font-extrabold">{confPercent}%</span>
            </div>

            {/* Top-Right Phone / State Indicator Icon if phone detected */}
            {hasPhone && (
              <div 
                className="absolute -top-2 -right-2 w-6 h-6 rounded-md bg-[#ED1B2F] text-white flex items-center justify-center shadow-xs"
                title="Phát hiện điện thoại"
              >
                <Smartphone className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
