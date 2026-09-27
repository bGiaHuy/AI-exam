/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEMO_MODE?: string;
  readonly VITE_DEMO_CLIENT_EMAIL?: string;
  readonly VITE_DEMO_EXPIRES_AT?: string;
  readonly VITE_DEMO_MOCK_DATA?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
