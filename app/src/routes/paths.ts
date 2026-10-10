/**
 * URL builder for spec/language/library pages.
 *
 *   /{specId}                       Cross-language hub
 *   /{specId}/{language}            Language overview
 *   /{specId}/{language}/{library}  Implementation detail
 */
export function specPath(specId: string, language?: string, library?: string): string {
  if (language && library) return `/${specId}/${language}/${library}`;
  if (language) return `/${specId}/${language}`;
  return `/${specId}`;
}

/**
 * The admin-only agent chat for one catalogue pair:
 * `/debug/agent?spec=&library=&language=` (plus `source` for `agent_open`).
 * Navigate to it with a full page load, never the router, so Cloudflare
 * Access can intercept the `/debug*` path.
 */
export function agentChatPath(
  spec: string,
  library: string,
  language: string,
  source?: string
): string {
  const params = new URLSearchParams({ spec, library, language });
  if (source) params.set('source', source);
  return `/debug/agent?${params.toString()}`;
}

/**
 * Reserved top-level paths that must never be assigned as spec ids.
 *
 * Keep in sync with `RESERVED_SLUGS` in `.github/workflows/spec-create.yml`.
 */
export const RESERVED_TOP_LEVEL = new Set([
  'plots',
  'specs',
  'libraries',
  'palette',
  'about',
  'legal',
  'mcp',
  'stats',
  'debug',
  'map',
  'api',
  'og',
  'sitemap.xml',
  'robots.txt',
]);

/**
 * Parse the language segment from a pathname, returns undefined if not present
 * or if the first segment is reserved.
 */
export function langFromPath(pathname: string): string | undefined {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length < 2) return undefined;
  if (RESERVED_TOP_LEVEL.has(segments[0])) return undefined;
  return segments[1];
}

/**
 * Parse the spec id from a pathname, returns undefined for the root path or
 * when the first segment is a reserved top-level route.
 */
export function specIdFromPath(pathname: string): string | undefined {
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return undefined;
  if (RESERVED_TOP_LEVEL.has(segments[0])) return undefined;
  return segments[0];
}

/**
 * Central route registry — the single source of truth for app URLs.
 * Components navigate via `paths.*` instead of hardcoded strings; spec-detail
 * URLs go through `specPath` (also exposed as `paths.spec`).
 */
export const paths = {
  home: '/',
  about: '/about',
  agentChat: agentChatPath,
  debug: '/debug',
  legal: '/legal',
  libraries: '/libraries',
  map: '/map',
  mcp: '/mcp',
  palette: '/palette',
  plots: '/plots',
  plotsSearch: '/plots?focus=search',
  specs: '/specs',
  stats: '/stats',
  plotsFiltered: (param: string, value: string) => `/plots?${param}=${encodeURIComponent(value)}`,
  spec: specPath,
} as const;
