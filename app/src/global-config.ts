// Named import, not a default one: `import packageJson from '../package.json'`
// inlines the whole manifest — the full dependency list included — into the
// client bundle. Only `version` is needed here.
import { version as packageVersion } from '../package.json';

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
  // Read from app/package.json, NOT the repo-root pyproject.toml: the frontend
  // image is built with `docker build -f app/Dockerfile app`, so the build
  // context is app/ alone and anything above it does not exist at build time
  // (reading ../pyproject.toml here broke the Cloud Build deploy in #10485).
  // The two version fields are kept identical by tests/unit/test_version_sync.py,
  // which runs on every PR that touches pyproject.toml — including release PRs.
  appVersion: packageVersion,
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
