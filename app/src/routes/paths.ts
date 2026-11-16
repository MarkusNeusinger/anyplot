import { LIBRARIES } from 'src/constants';

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
 * The agent chat for one catalogue pair, one page for visitors and admins:
 * `/agent?spec=&library=&language=` (plus `source` for `agent_open`). An
 * ordinary route; the page picks the lane itself (`AgentChatPage`).
 */
export function agentChatPath(
  spec: string,
  library: string,
  language: string,
  source?: string
): string {
  const params = new URLSearchParams({ spec, library, language });
  if (source) params.set('source', source);
  return `/agent?${params.toString()}`;
}

/**
 * The query parameters the chat page reads, which the redirect from the old
 * admin address `/debug/agent` keeps (`agentChatRedirect`).
 */
export const AGENT_CHAT_PARAMS = ['spec', 'library', 'language', 'source'] as const;

/** A spec id as the chat takes it from its query. */
const AGENT_SPEC_PATTERN = /^[a-z0-9-]{1,100}$/;

/**
 * Whether an `/agent` query names a chat: a well-formed spec id and a library the catalogue has.
 * With one the page is the chat on that pair, without one the explainer (`AgentChatPage`). The
 * layout decides by the same rule where the site's feedback button stands (`RootLayout`), so the
 * two never disagree about which page is a chat. `LIBRARIES` is read at the call, not at import.
 */
export function namesAgentChat(query: URLSearchParams): boolean {
  return (
    AGENT_SPEC_PATTERN.test(query.get('spec') ?? '') &&
    LIBRARIES.includes(query.get('library') ?? '')
  );
}

/**
 * Whether an address is the agent chat: `/agent`, also with a trailing slash as the router serves
 * it, with a query that names a chat (`namesAgentChat`).
 */
export function isAgentChatAddress(pathname: string, search: string): boolean {
  return pathname.replace(/\/+$/, '') === '/agent' && namesAgentChat(new URLSearchParams(search));
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
  'agent',
  'map',
  'api',
  'og',
  'sitemap.xml',
  'robots.txt',
]);

/** Whether a pathname is the gallery's: the router serves `/plots/` as it serves `/plots`. */
export function isPlotsPath(pathname: string): boolean {
  return pathname.replace(/\/+$/, '') === '/plots';
}

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
  agent: '/agent',
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
