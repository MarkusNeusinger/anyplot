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
