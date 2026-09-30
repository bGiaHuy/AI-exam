import React, { useState, useEffect, useRef } from 'react';
import { 
  Incident, 
  AISettings, 
  ViewMode 
} from './types';
import { 
  getAISettings, 
  updateAISettings, 
  deleteIncident 
} from './services/api';

// Core Components
import { ProctorHeader } from './components/proctoring/ProctorHeader';
import { StreamlinedProctorDashboard } from './components/StreamlinedProctorDashboard';
import { AISettingsView } from './components/AISettingsView';

// Modals
import { VideoEvidenceModal } from './components/modals/VideoEvidenceModal';

// Demo Mode & Watermark
import { DemoWatermark } from './components/demo/DemoWatermark';
import { DEMO_CONFIG } from './config/demoConfig';

const DEFAULT_AI_SETTINGS: AISettings = {
  phone_confidence: 0.55,
  posture_alert_seconds: 1.25,
  suspicion_threshold: 0.50,
  pre_roll_seconds: 5.0,
  post_roll_seconds: 10.0,
  cooldown_seconds: 6.0
};

export default function App() {
  // Navigation: Only 2 essential view modes (Live Monitor & AI Settings)
  const [currentView, setCurrentView] = useState<ViewMode>('live-monitor');

  // Guard navigation in demo mode
  const handleSelectView = (view: ViewMode) => {
    if (DEMO_CONFIG.isDemo && view === 'ai-settings') {
      showToast('Cấu hình AI bị khóa trong phiên bản Demo');
      return;
    }
    setCurrentView(view);
  };

  // Core Configuration State
  const [aiSettings, setAiSettings] = useState<AISettings>(DEFAULT_AI_SETTINGS);

  // Evidence Video Modal State
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [selectedVideoIncident, setSelectedVideoIncident] = useState<Incident | null>(null);
  const [incidentsRevision, setIncidentsRevision] = useState(0);
  const deletionInFlight = useRef(false);

  // Quick Notification Toast
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2500);
  };

  // Initial Data Load from SQLite Backend
  useEffect(() => {
    let isMounted = true;

    const loadBackendSettings = async () => {
      try {
        const apiSettings = await getAISettings();
        if (isMounted && apiSettings) {
          setAiSettings(apiSettings);
        }
      } catch (err) {
        console.warn('[App] Không thể nạp cấu hình AI từ backend:', err);
      }
    };

    loadBackendSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  // Incident Actions
  const handleConfirmIncident = async (incidentId: string) => {
    showToast('Đã xác nhận sự cố vi phạm');
  };

  const handleDismissIncident = async (incidentId: string) => {
    showToast('Đã bỏ qua sự cố');
  };

  const handleDeleteIncident = async (incidentId: string) => {
    if (deletionInFlight.current) return false;
    deletionInFlight.current = true;
    try {
      if (!DEMO_CONFIG.isDemo) await deleteIncident(incidentId);
      setIncidentsRevision(value => value + 1);
      showToast('Đã xóa tệp video sự cố thành công');
      return true;
    } catch (err) {
      console.warn('[App] Lỗi xóa video sự cố:', err);
      showToast(err instanceof Error ? err.message : 'Lỗi khi xóa video sự cố');
      return false;
    } finally {
      deletionInFlight.current = false;
    }
  };

  const handleSaveSettings = async (newCfg: AISettings) => {
    setAiSettings(newCfg);
    try {
      const ok = await updateAISettings(newCfg);
      if (ok) {
        showToast('Đã lưu cấu hình AI vào hệ thống');
      } else {
        showToast('Lỗi khi cập nhật cấu hình AI');
      }
    } catch (err) {
      console.warn('[App] Lỗi lưu cấu hình AI:', err);
      showToast('Lỗi kết nối tới máy chủ AI');
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F8FBFF] text-slate-800 antialiased font-sans select-none">
      {/* Permanent Demo Watermark Bar & Overlay */}
      <DemoWatermark />

      {/* THPT Chuyên Hoàng Văn Thụ Institutional Header */}
      <ProctorHeader
        currentView={currentView}
        onSelectView={handleSelectView}
        activeSource="Camera Giám Sát"
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {currentView === 'live-monitor' && (
          <StreamlinedProctorDashboard
            onOpenVideoModal={(inc) => {
              setSelectedVideoIncident(inc);
              setIsVideoModalOpen(true);
            }}
            onConfirmIncident={handleConfirmIncident}
            onDismissIncident={handleDismissIncident}
            onDeleteIncident={handleDeleteIncident}
            incidentsRevision={incidentsRevision}
          />
        )}

        {currentView === 'ai-settings' && (
          <div className="flex-1 flex flex-col overflow-hidden bg-[#F8FBFF]">
            <div className="p-3 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-2xs">
              <span className="text-xs font-mono font-bold text-slate-800 uppercase tracking-tight">
                CẤU HÌNH ĐỘ NHẠY & THAM SỐ GHI BẰNG CHỨNG AI
              </span>
              <button
                onClick={() => setCurrentView('live-monitor')}
                className="px-3 py-1.5 rounded-lg bg-[#123F7C] hover:bg-[#0E3264] text-white text-xs font-semibold transition-all shadow-xs"
              >
                ← Quay Lại Giám Sát
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 bg-white max-w-4xl mx-auto my-4 rounded-xl border border-gray-200 shadow-sm w-full">
              <AISettingsView
                settings={aiSettings}
                onSaveSettings={handleSaveSettings}
              />
            </div>
          </div>
        )}
      </main>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-24 right-6 z-50 px-4 py-2 rounded-xl bg-white border border-gray-200 shadow-lg text-xs text-slate-800 font-sans font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-2">
          <div className="w-2 h-2 rounded-full bg-[#00A95C] animate-pulse" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Video Evidence Playback Modal */}
      <VideoEvidenceModal
        isOpen={isVideoModalOpen}
        incident={selectedVideoIncident}
        onClose={() => setIsVideoModalOpen(false)}
        onDeleteVideo={handleDeleteIncident}
      />
    </div>
  );
}
