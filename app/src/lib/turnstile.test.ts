/**
 * The Turnstile client: no site key means no script and no header; with one, every call
 * renders its own invisible widget, takes its token once and removes it, and a failure is a
 * `TurnstileError` the page turns into its one calm message.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  loadTurnstile,
  resetTurnstile,
  TURNSTILE_HEADER,
  TURNSTILE_SCRIPT_URL,
  TurnstileError,
  turnstileHeaders,
  turnstileToken,
} from 'src/lib/turnstile';

/** Cloudflare's test site key that always passes (developers.cloudflare.com/turnstile/troubleshooting/testing/). */
const TEST_SITE_KEY = '1x00000000000000000000AA';

type Options = Record<string, unknown> & {
  callback: (token: string) => void;
  'error-callback': () => boolean;
  'before-interactive-callback': () => void;
};

/** A stand-in for `window.turnstile`; `answer` decides what each render does. */
function fakeTurnstile(answer: (options: Options) => void = o => o.callback('tok-1')) {
  const rendered: { container: HTMLElement; parent: HTMLElement | null; options: Options }[] = [];
  const api = {
    render: vi.fn((container: HTMLElement, options: Record<string, unknown>) => {
      rendered.push({ container, parent: container.parentElement, options: options as Options });
      queueMicrotask(() => answer(options as Options));
      return `w${rendered.length}`;
    }),
    remove: vi.fn(),
  };
  window.turnstile = api;
  return { api, rendered };
}

beforeEach(() => {
  resetTurnstile();
  delete window.turnstile;
  document.head.querySelectorAll('script').forEach(script => script.remove());
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.useRealTimers();
  delete window.turnstile;
  document.body.innerHTML = '';
});

describe('without a site key', () => {
  it('loads nothing and sends no header', async () => {
    vi.stubEnv('VITE_TURNSTILE_SITE_KEY', '');
    const { api } = fakeTurnstile();

    expect(await turnstileToken('agent_session')).toBeNull();
    expect(await turnstileHeaders('site_feedback')).toEqual({});
    expect(api.render).not.toHaveBeenCalled();
    expect(document.head.querySelector('script')).toBeNull();
  });
});

describe('with a site key', () => {
  beforeEach(() => vi.stubEnv('VITE_TURNSTILE_SITE_KEY', TEST_SITE_KEY));

  it('renders an invisible Managed widget per call and removes it once the token is in', async () => {
    const { api, rendered } = fakeTurnstile();

    expect(await turnstileHeaders('agent_session')).toEqual({ [TURNSTILE_HEADER]: 'tok-1' });

    expect(rendered).toHaveLength(1);
    expect(rendered[0].options).toMatchObject({
      sitekey: TEST_SITE_KEY,
      action: 'agent_session',
      appearance: 'interaction-only',
      retry: 'never',
      'response-field': false,
    });
    expect(api.remove).toHaveBeenCalledWith('w1');
    // The fixed slot at the foot of the window is gone with the widget.
    expect(document.body.querySelector('[data-turnstile]')).toBeNull();
  });

  it('takes a fresh token for every call', async () => {
    let n = 0;
    const { rendered } = fakeTurnstile(o => o.callback(`tok-${++n}`));

    expect(await turnstileToken('agent_feedback')).toBe('tok-1');
    expect(await turnstileToken('agent_feedback')).toBe('tok-2');
    expect(rendered).toHaveLength(2);
  });

  it('renders into the slot a caller passes and leaves the slot in place', async () => {
    const { rendered } = fakeTurnstile();
    const slot = document.createElement('div');
    document.body.appendChild(slot);

    await turnstileToken('site_feedback', slot);

    expect(rendered[0].parent).toBe(slot);
    expect(slot.isConnected).toBe(true);
    expect(slot.childElementCount).toBe(0);
    expect(document.body.querySelector('[data-turnstile]')).toBeNull();
  });

  it('follows the site theme', async () => {
    const { rendered } = fakeTurnstile();
    document.documentElement.setAttribute('data-theme', 'dark');

    await turnstileToken('agent_session');

    expect(rendered[0].options.theme).toBe('dark');
    document.documentElement.removeAttribute('data-theme');
  });

  it('turns a failed check into bot_check_failed and cleans up', async () => {
    const { api } = fakeTurnstile(o => o['error-callback']());

    await expect(turnstileToken('agent_session')).rejects.toMatchObject({
      name: 'TurnstileError',
      code: 'bot_check_failed',
    });
    expect(api.remove).toHaveBeenCalledWith('w1');
    expect(document.body.querySelector('[data-turnstile]')).toBeNull();
  });

  it('gives up on a check that never answers, but not while Cloudflare waits for a click', async () => {
    vi.useFakeTimers();
    fakeTurnstile(() => undefined);
    const silent = turnstileToken('agent_session').catch((err: unknown) => err);
    await vi.advanceTimersByTimeAsync(30_000);
    expect(await silent).toBeInstanceOf(TurnstileError);

    let settled = false;
    fakeTurnstile(o => o['before-interactive-callback']());
    const waiting = turnstileToken('agent_session')
      .catch((err: unknown) => err)
      .finally(() => (settled = true));
    await vi.advanceTimersByTimeAsync(120_000);
    expect(settled).toBe(false);
    // A click Cloudflare never reports on still ends within a token's lifetime.
    await vi.advanceTimersByTimeAsync(180_000);
    expect(await waiting).toBeInstanceOf(TurnstileError);
    expect(document.body.querySelector('[data-turnstile]')).toBeNull();
  });

  it('fails at once when Cloudflare renders no widget', async () => {
    window.turnstile = { render: vi.fn(() => undefined), remove: vi.fn() };

    await expect(turnstileToken('agent_session')).rejects.toMatchObject({
      code: 'bot_check_failed',
    });
    expect(document.body.querySelector('[data-turnstile]')).toBeNull();
  });

  it("loads Cloudflare's script from its own URL, once, and tries again after a failed load", async () => {
    const first = loadTurnstile();
    const second = loadTurnstile();
    expect(first).toBe(second);
    const scripts = document.head.querySelectorAll('script');
    expect(scripts).toHaveLength(1);
    expect(scripts[0].src.startsWith(`${TURNSTILE_SCRIPT_URL}?render=explicit&onload=`)).toBe(true);

    scripts[0].dispatchEvent(new Event('error'));
    await expect(first).rejects.toMatchObject({ code: 'bot_check_unavailable' });
    expect(document.head.querySelector('script')).toBeNull();

    void loadTurnstile().catch(() => undefined);
    expect(document.head.querySelectorAll('script')).toHaveLength(1);
  });

  it('resolves the load through the onload callback', async () => {
    const loading = loadTurnstile();
    const src = document.head.querySelector('script')!.src;
    const callback = new URL(src).searchParams.get('onload')!;
    const { api } = fakeTurnstile();
    (window as unknown as Record<string, () => void>)[callback]();

    expect(await loading).toBe(api);
  });
});
