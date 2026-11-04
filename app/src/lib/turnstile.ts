/**
 * Cloudflare Turnstile, the bot check on the calls that open or store something
 * for an anonymous visitor: opening a public chat session, a public chat
 * feedback case, and a site feedback entry (the widget and the plot votes).
 * The API redeems the token (`api/turnstile.py`); the header name and the
 * error codes are in docs/reference/api.md.
 *
 * - Lazy: the script loads on the first protected call (or `preloadTurnstile`
 *   when the feedback widget opens), never on a page that only browses.
 * - One token per call: a token is single-use and valid for 300 seconds, so
 *   every protected call renders its own widget and removes it once the token
 *   is in.
 * - Managed mode with `appearance: 'interaction-only'`: the widget has no size
 *   unless Cloudflare asks this visitor to click. It renders into a fixed
 *   slot at the foot of the window, so it never moves the page; a caller
 *   inside a modal (the feedback popover) passes a slot of its own, where the
 *   modal's focus trap lets the checkbox take the focus.
 * - Without a site key (`VITE_TURNSTILE_SITE_KEY` unset: local development
 *   and the tests) nothing loads and no header is sent; the API skips the check
 *   while its secret is unset, outside production.
 */

/** The request header that carries the token. */
export const TURNSTILE_HEADER = 'X-Turnstile-Token';

/** Cloudflare's script, from the exact URL Cloudflare documents: a proxied or cached copy breaks on their updates. */
export const TURNSTILE_SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js';

/** The protected calls, as the widget's `action`: Cloudflare's dashboard counts the checks per action. */
export type TurnstileAction = 'agent_session' | 'agent_feedback' | 'site_feedback';

/** Why no token came: the check did not pass (`failed`), or Cloudflare's script never ran (`unavailable`). */
export class TurnstileError extends Error {
  readonly code: 'bot_check_failed' | 'bot_check_unavailable';

  constructor(code: 'bot_check_failed' | 'bot_check_unavailable') {
    super(`turnstile: ${code}`);
    this.name = 'TurnstileError';
    this.code = code;
  }
}

/** The part of Cloudflare's `window.turnstile` this module calls. */
export interface TurnstileApi {
  render: (container: HTMLElement, options: Record<string, unknown>) => string | undefined;
  remove: (widgetId: string) => void;
}

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

/** How long the script may take to arrive. */
const LOAD_TIMEOUT_MS = 15_000;
/** How long a check may run without asking the visitor anything; a click it asks for has Cloudflare's own timeout. */
const CHECK_TIMEOUT_MS = 30_000;
const ONLOAD_CALLBACK = '__anyplotTurnstileLoaded';

/** The build's site key, read per call so tests can set it. */
export function turnstileSiteKey(): string {
  return import.meta.env.VITE_TURNSTILE_SITE_KEY ?? '';
}

let loading: Promise<TurnstileApi> | null = null;

/** Load Cloudflare's script once; a failed load is forgotten, so the next call tries again. */
export function loadTurnstile(): Promise<TurnstileApi> {
  if (window.turnstile) return Promise.resolve(window.turnstile);
  loading ??= new Promise<TurnstileApi>((resolve, reject) => {
    const script = document.createElement('script');
    const fail = () => {
      window.clearTimeout(timer);
      delete (window as unknown as Record<string, unknown>)[ONLOAD_CALLBACK];
      script.remove();
      loading = null;
      reject(new TurnstileError('bot_check_unavailable'));
    };
    const timer = window.setTimeout(fail, LOAD_TIMEOUT_MS);
    (window as unknown as Record<string, unknown>)[ONLOAD_CALLBACK] = () => {
      window.clearTimeout(timer);
      if (window.turnstile) resolve(window.turnstile);
      else fail();
    };
    script.src = `${TURNSTILE_SCRIPT_URL}?render=explicit&onload=${ONLOAD_CALLBACK}`;
    script.async = true;
    script.onerror = fail;
    document.head.appendChild(script);
  });
  return loading;
}

/** Start loading the script ahead of a protected call (the feedback widget opening); errors wait for the call. */
export function preloadTurnstile(): void {
  if (turnstileSiteKey()) void loadTurnstile().catch(() => undefined);
}

/** Forget the loaded script, for tests. */
export function resetTurnstile(): void {
  loading = null;
}

function siteTheme(): 'light' | 'dark' {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

/**
 * A slot fixed at the foot of the window, above the page and its floating buttons. As wide as
 * Cloudflare's 300-pixel box: a fixed box at `left: 50%` would otherwise shrink to the half of
 * the window right of its edge, 195 pixels on a phone, and squeeze the check.
 */
function windowSlot(): HTMLElement {
  const slot = document.createElement('div');
  slot.dataset.turnstile = '';
  Object.assign(slot.style, {
    position: 'fixed',
    left: '50%',
    bottom: '16px',
    transform: 'translateX(-50%)',
    width: 'max-content',
    maxWidth: 'calc(100vw - 16px)',
    zIndex: '1500',
  });
  document.body.appendChild(slot);
  return slot;
}

/**
 * A fresh token for one protected call, or null without a site key. Rejects
 * with a `TurnstileError` when the check fails, times out or cannot load.
 */
export async function turnstileToken(
  action: TurnstileAction,
  container?: HTMLElement | null
): Promise<string | null> {
  const sitekey = turnstileSiteKey();
  if (!sitekey) return null;
  const api = await loadTurnstile();
  const host = container ?? windowSlot();
  const slot = document.createElement('div');
  host.appendChild(slot);
  return new Promise<string>((resolve, reject) => {
    let widgetId: string | undefined;
    let settled = false;
    let timer: number | undefined;
    const finish = (settle: () => void) => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timer);
      try {
        if (widgetId !== undefined) api.remove(widgetId);
      } catch {
        /* the widget is gone already */
      }
      slot.remove();
      if (!container) host.remove();
      settle();
    };
    const failed = () => {
      finish(() => reject(new TurnstileError('bot_check_failed')));
      // Handled here: without a truthy answer Turnstile reports the error as an exception too.
      return true;
    };
    const arm = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(failed, CHECK_TIMEOUT_MS);
    };
    arm();
    try {
      widgetId = api.render(slot, {
        sitekey,
        action,
        appearance: 'interaction-only',
        theme: siteTheme(),
        // A failure ends this call; the page's own retry renders a fresh widget.
        retry: 'never',
        'refresh-expired': 'never',
        'refresh-timeout': 'never',
        'response-field': false,
        callback: (token: string) => finish(() => resolve(token)),
        'error-callback': failed,
        'timeout-callback': failed,
        'unsupported-callback': failed,
        // While Cloudflare waits for the visitor's click, only its own timeout runs.
        'before-interactive-callback': () => window.clearTimeout(timer),
        'after-interactive-callback': arm,
      });
    } catch {
      failed();
    }
  });
}

/** The header for one protected call: the token, or nothing without a site key. */
export async function turnstileHeaders(
  action: TurnstileAction,
  container?: HTMLElement | null
): Promise<Record<string, string>> {
  const token = await turnstileToken(action, container);
  return token ? { [TURNSTILE_HEADER]: token } : {};
}
