/**
 * Central API client for the anyplot backend.
 *
 * Thin wrapper around fetch: builds URLs from CONFIG.api.baseUrl via the
 * `endpoints` registry and raises ApiError on non-2xx responses. Callers keep
 * their own caching/abort/dedup strategies (see useCodeFetch/useFilterFetch).
 */

import { CONFIG } from 'src/global-config';

export class ApiError extends Error {
  readonly status: number;
  readonly url: string;

  constructor(status: number, statusText: string, url: string) {
    super(`API request failed: ${status} ${statusText} (${url})`);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
  }
}

export const endpoints = {
  // Only append the language query param when it diverges from the API
  // default — keeps URLs for the common Python case unchanged.
  code: (specId: string, library: string, language = 'python') =>
    language === 'python'
      ? `/specs/${specId}/${library}/code`
      : `/specs/${specId}/${library}/code?language=${encodeURIComponent(language)}`,
  download: (specId: string, library: string) => `/download/${specId}/${library}`,
  feedback: '/feedback',
  insightsDashboard: '/insights/dashboard',
  insightsVisitors: '/insights/visitors',
  languages: '/languages',
  libraries: '/libraries',
  plotOfTheDay: '/insights/plot-of-the-day',
  plotsFilter: (queryString = '') => `/plots/filter${queryString ? `?${queryString}` : ''}`,
  relatedSpecs: (specId: string, queryString: string) =>
    `/insights/related/${specId}?${queryString}`,
  spec: (specId: string) => `/specs/${specId}`,
  specs: '/specs',
  specsMap: '/specs/map',
  stats: '/stats',
} as const;

export function apiUrl(path: string): string {
  return `${CONFIG.api.baseUrl}${path}`;
}

/** GET a JSON payload; throws ApiError on non-2xx responses. */
export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  const response = await fetch(url, init);
  if (!response.ok) throw new ApiError(response.status, response.statusText, url);
  return response.json() as Promise<T>;
}

/** POST a JSON body and return the JSON payload; throws ApiError on non-2xx. */
export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  const response = await fetch(url, {
    ...init,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(init?.headers as Record<string, string>) },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new ApiError(response.status, response.statusText, url);
  return response.json() as Promise<T>;
}

/**
 * Fetch against the debug API (Cloudflare Access): sends cookies for the
 * same-origin /api/* Worker route and attaches the X-Admin-Token header when
 * a token is present. Returns the raw Response — the debug page inspects
 * status codes itself.
 */
export function fetchWithAuth(
  url: string,
  token: string,
  init: RequestInit = {}
): Promise<Response> {
  const headers: Record<string, string> = { ...((init.headers as Record<string, string>) || {}) };
  if (token) headers['X-Admin-Token'] = token;
  if (init.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  return fetch(url, { credentials: 'include', ...init, headers });
}
