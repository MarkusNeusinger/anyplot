/**
 * Central API client for the anyplot backend.
 *
 * Thin wrapper around fetch: builds URLs from CONFIG.api.baseUrl via the
 * `endpoints` registry and raises ApiError on non-2xx responses. apiGet
 * retries transient failures (network errors, 408/425/429/5xx gateway
 * statuses) twice with backoff; nothing else retries. Callers keep
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

/**
 * Retry policy for idempotent GETs. A transient edge or network glitch (a
 * Cloudflare challenge or an edge error arrives without CORS headers and
 * surfaces as `TypeError: Failed to fetch`) must not leave a page empty, so
 * apiGet retries network errors and these statuses twice with backoff before
 * it gives up. POSTs, fetchWithAuth and the agent chat's SSE streams never
 * retry: they are not idempotent or not ours to repeat.
 */
const RETRYABLE_STATUSES = new Set([408, 425, 429, 500, 502, 503, 504]);
/** Base wait before retry 1 and retry 2; each gets up to +20 % jitter. */
export const RETRY_DELAYS_MS = [400, 1200] as const;
/** Upper bound for a server-sent `Retry-After`, so a page never stalls long. */
export const RETRY_AFTER_CAP_MS = 3000;

/** `Retry-After` as milliseconds (delta-seconds or HTTP-date), or null. */
function parseRetryAfter(value: string | null | undefined): number | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (/^\d+$/.test(trimmed)) return Number(trimmed) * 1000;
  const date = Date.parse(trimmed);
  return Number.isNaN(date) ? null : Math.max(0, date - Date.now());
}

function retryDelay(attempt: number, response?: Response): number {
  // Test doubles often hand back plain objects without a Headers instance.
  const retryAfter = parseRetryAfter(response?.headers?.get?.('Retry-After'));
  if (retryAfter !== null) return Math.min(retryAfter, RETRY_AFTER_CAP_MS);
  const base = RETRY_DELAYS_MS[attempt];
  return base + Math.random() * base * 0.2;
}

function abortReason(signal: AbortSignal): unknown {
  return signal.reason ?? new DOMException('The operation was aborted.', 'AbortError');
}

/** Resolve after `ms`, or reject with the abort reason as soon as `signal` fires. */
function wait(ms: number, signal?: AbortSignal | null): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortReason(signal));
      return;
    }
    const onAbort = () => {
      clearTimeout(timer);
      reject(abortReason(signal!));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

/**
 * fetch with the GET retry policy above. Returns the final Response (ok, a
 * non-retryable status, or the last retryable one) and rethrows the last
 * network error; an abort is never retried and cuts a pending wait short.
 */
async function fetchWithRetry(url: string, init?: RequestInit): Promise<Response> {
  const signal = init?.signal;
  const idempotent = (init?.method ?? 'GET').toUpperCase() === 'GET';
  const maxRetries = idempotent ? RETRY_DELAYS_MS.length : 0;

  for (let attempt = 0; ; attempt++) {
    let response: Response;
    try {
      response = await fetch(url, init);
    } catch (err) {
      // fetch reports network failures (CORS-less edge errors included) as
      // TypeError; an abort is a DOMException and goes straight back.
      const transient = err instanceof TypeError && !signal?.aborted;
      if (!transient || attempt >= maxRetries) throw err;
      await wait(retryDelay(attempt), signal);
      continue;
    }
    if (response.ok || !RETRYABLE_STATUSES.has(response.status) || attempt >= maxRetries) {
      return response;
    }
    await wait(retryDelay(attempt, response), signal);
  }
}

/**
 * GET a JSON payload; throws ApiError on non-2xx responses. Network errors and
 * transient statuses are retried (see RETRY_DELAYS_MS); a non-retryable status
 * such as 404 throws at once.
 */
export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  const response = await fetchWithRetry(url, init);
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
