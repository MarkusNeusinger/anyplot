/**
 * Admin auth helpers shared by the `/debug` pages and the agent chat.
 *
 * Browser state, all best effort (storage may be unavailable in private mode,
 * so every access is wrapped):
 *
 * - The admin token (`X-Admin-Token` fallback for the `/debug` API) lives in
 *   sessionStorage, so it survives reloads of one tab and nothing more.
 * - The admin hint is a localStorage flag that `DebugPage` sets once
 *   `/debug/status` answered 200 and clears when it is refused. It is a UI
 *   hint, never an authorization: it only decides whether a public page may
 *   ask `/debug/agent/*` at all (the `.use_my_data()` entry, the chat at
 *   `/agent`), so public visitors never send a request to the debug API. The
 *   server's admin gate still decides every call.
 * - "View as visitor" is a sessionStorage flag of the chat's admin menu: while
 *   it is set, the chat at `/agent` runs on the public lane for this tab,
 *   exactly as a visitor's (`AgentChatPage`). It only picks the API the page
 *   calls, and it grants nothing.
 *
 * The Access reload guard keeps the `/debug` page's Cloudflare Access
 * bootstrap from looping: an expired or missing Access session turns an API
 * call into a cross-origin redirect that `fetch` reports as a `TypeError`, and
 * only a top-level navigation of a page behind Access lets Access intercept it
 * and sign the admin in. `reloadOnceForAccess` does that navigation once per
 * tab until an answer arrives again (`clearAccessReloadGuard`). The chat at
 * `/agent` is not behind Access, so it never reloads: it falls back to the
 * public lane and links to `/debug` instead.
 */

const ADMIN_TOKEN_KEY = 'anyplot.adminToken';
export const ADMIN_HINT_KEY = 'anyplot.adminHint';
export const ACCESS_RELOAD_KEY = 'anyplot.debugAuthReloaded';
export const VIEW_AS_VISITOR_KEY = 'anyplot.agentAsVisitor';

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

/** True while the admin chose "view as visitor" in this tab's chat. */
export function readViewAsVisitor(): boolean {
  try {
    return sessionStorage.getItem(VIEW_AS_VISITOR_KEY) === '1';
  } catch {
    return false;
  }
}

export function setViewAsVisitor(on: boolean): void {
  try {
    if (on) sessionStorage.setItem(VIEW_AS_VISITOR_KEY, '1');
    else sessionStorage.removeItem(VIEW_AS_VISITOR_KEY);
  } catch {
    /* sessionStorage may be unavailable: the choice lasts as long as the page */
  }
}

/**
 * Reload the page once so Cloudflare Access can intercept it and sign the
 * admin in again; false when this tab already tried since the last answer.
 * `replace`, not `assign`: the broken pre-auth page must not stay in history.
 */
export function reloadOnceForAccess(): boolean {
  try {
    if (sessionStorage.getItem(ACCESS_RELOAD_KEY)) return false;
    sessionStorage.setItem(ACCESS_RELOAD_KEY, '1');
  } catch {
    return false; // without the guard a reload could loop
  }
  window.location.replace(window.location.href);
  return true;
}

/** An answer arrived: a later Access redirect may reload again. */
export function clearAccessReloadGuard(): void {
  try {
    sessionStorage.removeItem(ACCESS_RELOAD_KEY);
  } catch {
    /* sessionStorage may be unavailable */
  }
}
