/**
 * The plot pages' 👍/👎: each vote carries a fresh Turnstile token, and a failed check reads as
 * a refused vote, so the page rolls its optimistic thumb back.
 */

import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useQuickReaction } from 'src/hooks/useQuickReaction';
import { resetTurnstile, TURNSTILE_HEADER } from 'src/lib/turnstile';

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const TARGET = {
  specId: 'scatter-basic',
  language: 'python',
  libraryId: 'matplotlib',
  version: '2026-11-08T04:54:13',
};

function stubTurnstile(pass: boolean) {
  window.turnstile = {
    render: vi.fn((_container: HTMLElement, options: Record<string, unknown>) => {
      queueMicrotask(() =>
        pass
          ? (options.callback as (token: string) => void)('tok-v')
          : (options['error-callback'] as () => void)()
      );
      return 'w1';
    }),
    remove: vi.fn(),
  };
}

beforeEach(() => {
  localStorage.clear();
  analytics.trackEvent.mockClear();
  vi.stubEnv('VITE_TURNSTILE_SITE_KEY', '1x00000000000000000000AA');
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
  resetTurnstile();
  delete window.turnstile;
  document.body.innerHTML = '';
});

describe('useQuickReaction', () => {
  it('sends the vote with a fresh token', async () => {
    stubTurnstile(true);
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), { status: 200 }));
    const { result } = renderHook(() => useQuickReaction());

    expect(await result.current('thumbs_up', TARGET)).toBe(true);

    const headers = (fetchSpy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers[TURNSTILE_HEADER]).toBe('tok-v');
    expect(analytics.trackEvent).toHaveBeenCalledWith(
      'feedback_submitted',
      expect.objectContaining({ source: 'plot_vote' })
    );
  });

  it('reports a failed check as a refused vote and sends nothing', async () => {
    stubTurnstile(false);
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    const { result } = renderHook(() => useQuickReaction());

    expect(await result.current('thumbs_down', TARGET)).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(analytics.trackEvent).not.toHaveBeenCalled();
  });
});
