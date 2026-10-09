/**
 * Admin auth helpers shared by the `/debug` pages.
 *
 * Two pieces of browser state, both best effort (storage may be unavailable in
 * private mode, so every access is wrapped):
 *
 * - The admin token (`X-Admin-Token` fallback for the `/debug` API) lives in
 *   sessionStorage, so it survives reloads of one tab and nothing more.
 * - The admin hint is a localStorage flag that `DebugPage` sets once
 *   `/debug/status` answered 200 and clears when it is refused. It is a UI
 *   hint, never an authorization: it only decides whether a public page may
 *   probe `/debug/agent/*` at all (the `.adapt()` button), so public visitors
 *   never send a request to the debug API. The server's admin gate still
 *   decides every call.
 */

const ADMIN_TOKEN_KEY = 'anyplot.adminToken';
export const ADMIN_HINT_KEY = 'anyplot.adminHint';

export function readAdminToken(): string {
  try {
    return sessionStorage.getItem(ADMIN_TOKEN_KEY) ?? '';
  } catch {
    return '';
  }
}

export function writeAdminToken(value: string): void {
  try {
    sessionStorage.setItem(ADMIN_TOKEN_KEY, value);
  } catch {
    /* sessionStorage may be unavailable */
  }
}

export function clearAdminToken(): void {
  try {
    sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  } catch {
    /* noop */
  }
}

/** True once this browser passed the `/debug` admin gate (and was not refused since). */
export function readAdminHint(): boolean {
  try {
    return localStorage.getItem(ADMIN_HINT_KEY) === '1';
  } catch {
    return false;
  }
}

export function setAdminHint(isAdmin: boolean): void {
  try {
    if (isAdmin) localStorage.setItem(ADMIN_HINT_KEY, '1');
    else localStorage.removeItem(ADMIN_HINT_KEY);
  } catch {
    /* localStorage may be unavailable */
  }
}
