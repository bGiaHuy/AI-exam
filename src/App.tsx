import React, { useState, useEffect } from 'react';
import { 
  Incident, 
  AISettings, 
  ViewMode 
} from './types';
import { 
  getAISettings, 
  updateAISettings, 
  confirmIncident 
} from './services/api';

// Core Components
import { TopNavBar } from './components/TopNavBar';
import { StreamlinedProctorDashboard } from './components/StreamlinedProctorDashboard';
import { AISettingsView } from './components/AISettingsView';

// Modals
import { VideoEvidenceModal } from './components/modals/VideoEvidenceModal';

const DEFAULT_AI_SETTINGS: AISettings = {
  phone_confidence: 0.35,
  posture_alert_seconds: 1.25,
  suspicion_threshold: 0.50,
  pre_roll_seconds: 5.0,
  post_roll_seconds: 10.0,
  cooldown_seconds: 6.0
};

export default function App() {
  // Navigation: Only 2 essential view modes (Live Monitor & AI Settings)
  const [currentView, setCurrentView] = useState<ViewMode>('live-monitor');

  // Core Configuration State
  const [aiSettings, setAiSettings] = useState<AISettings>(DEFAULT_AI_SETTINGS);

  // Evidence Video Modal State
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [selectedVideoIncident, setSelectedVideoIncident] = useState<Incident | null>(null);

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
    try {
      await confirmIncident(incidentId, { status: 'confirmed' });
      showToast('Đã xác nhận sự cố vi phạm');
    } catch (err) {
      console.warn('[App] Lỗi xác nhận vi phạm:', err);
      showToast('Lỗi khi xác nhận vi phạm');
    }
  };

  const handleDismissIncident = async (incidentId: string) => {
    try {
      await confirmIncident(incidentId, { status: 'dismissed' });
      showToast('Đã bỏ qua sự cố');
    } catch (err) {
      console.warn('[App] Lỗi bỏ qua vi phạm:', err);
      showToast('Lỗi khi bỏ qua sự cố');
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
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100 antialiased font-sans select-none">
      {/* Streamlined Top Navigation Header */}
      <TopNavBar
        currentView={currentView}
        onSelectView={setCurrentView}
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
          />
        )}

        {currentView === 'ai-settings' && (
          <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
            <div className="p-3 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between px-6">
              <span className="text-xs font-mono font-semibold text-zinc-300">
                CẤU HÌNH ĐỘ NHẠY & THAM SỐ GHI BẰNG CHỨNG AI
              </span>
              <button
                onClick={() => setCurrentView('live-monitor')}
                className="px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-medium transition-all border border-zinc-700"
              >
                ← Quay Lại Giám Sát
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
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
        <div className="fixed top-16 right-6 z-50 px-3.5 py-1.5 rounded-md bg-zinc-900 border border-zinc-700 shadow-xl text-xs text-white font-mono flex items-center gap-2 backdrop-blur animate-in fade-in slide-in-from-top-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Video Evidence Playback Modal */}
      <VideoEvidenceModal
        isOpen={isVideoModalOpen}
        incident={selectedVideoIncident}
        onClose={() => setIsVideoModalOpen(false)}
      />
    </div>
  );
}
