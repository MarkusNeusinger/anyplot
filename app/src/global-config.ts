import packageJson from '../package.json';

interface GlobalConfig {
  appName: string;
  appVersion: string;
  api: {
    baseUrl: string;
    debugBaseUrl: string;
  };
  isDev: boolean;
}

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const CONFIG: GlobalConfig = {
  appName: 'anyplot',
  appVersion: packageJson.version,
  api: {
    baseUrl: apiBaseUrl,
    // DebugPage uses this — set to "/api" in prod (same-origin via the
    // Cloudflare Worker on anyplot.ai/api/*) so the CF Access cookie can be
    // sent with fetch. Falls back to the API base locally where there's no
    // Worker.
    debugBaseUrl: import.meta.env.VITE_DEBUG_API_URL || apiBaseUrl,
  },
  isDev: import.meta.env.DEV,
};
