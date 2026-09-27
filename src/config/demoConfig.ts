/**
 * ================================================================================
 * DEMO MODE CONFIGURATION & ACCESS GUARDS
 * ================================================================================
 * Governs demo mode behavior, client watermark, capability locks, and expiration.
 * No secrets or sensitive keys are embedded here.
 * ================================================================================
 */

export interface DemoConfig {
  isDemo: boolean;
  clientEmail: string;
  expiresAt: string;
  watermarkText: string;
  allowSettings: boolean;
  allowFileUpload: boolean;
  allowClipDownload: boolean;
  isMockData: boolean;
}

// In Vite, variables prefixed with VITE_ are exposed to the client bundle.
// DO NOT put secrets in VITE_* variables.
const isDemoEnv = import.meta.env.VITE_DEMO_MODE === 'true';
const clientEmail = import.meta.env.VITE_DEMO_CLIENT_EMAIL || '[EMAIL_KHÁCH]';
const expiresAt = import.meta.env.VITE_DEMO_EXPIRES_AT || '48 giờ kể từ khi kích hoạt';

export const DEMO_CONFIG: DemoConfig = {
  isDemo: isDemoEnv,
  clientEmail,
  expiresAt,
  watermarkText: `BẢN DEMO – ${clientEmail} – KHÔNG PHẢI BẢN BÀN GIAO`,
  allowSettings: false,
  allowFileUpload: false,
  allowClipDownload: false,
  isMockData: isDemoEnv,
};

/**
 * Validates if the demo session has expired.
 */
export function isDemoExpired(): boolean {
  if (!DEMO_CONFIG.isDemo) return false;
  const expStr = import.meta.env.VITE_DEMO_EXPIRES_AT;
  if (!expStr) return false;
  const expDate = new Date(expStr);
  if (isNaN(expDate.getTime())) return false;
  return Date.now() > expDate.getTime();
}
