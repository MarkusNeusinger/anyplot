import { afterEach, describe, expect, it, vi } from 'vitest';

import { resetAnalyticsMute, setAnalyticsMuted } from 'src/analytics/mute';
import { reportWebVitals } from 'src/analytics/reportWebVitals';
import { setAnalyticsAmbientProps } from 'src/hooks/useAnalytics';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

// Single hoisted mock (vi.mock dedupes by module path — last call wins, so
// keeping one shared mock avoids cross-test interference).
vi.mock('web-vitals', () => ({
  onLCP: (cb: (m: { value: number; rating: string }) => void) =>
    cb({ value: 2500, rating: 'good' }),
  onCLS: (cb: (m: { value: number; rating: string }) => void) =>
    cb({ value: 0.15, rating: 'needs-improvement' }),
  onINP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 200, rating: 'good' }),
  onFCP: (cb: (m: { value: number; rating: string }) => void) =>
    cb({ value: 1200, rating: 'good' }),
  onTTFB: (cb: (m: { value: number; rating: string }) => void) =>
    cb({ value: 400, rating: 'good' }),
}));

describe('reportWebVitals', () => {
  const originalLocation = window.location;

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
    delete window.plausible;
    setAnalyticsAmbientProps({ theme: '' });
    resetAnalyticsMute();
  });

  it('does nothing in non-production environment', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'localhost' },
      writable: true,
      configurable: true,
    });

    // Should return early without importing web-vitals
    reportWebVitals();
    // No error = success, web-vitals is not imported
  });

  it('does nothing when hostname is not anyplot.ai', () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'staging.anyplot.ai' },
      writable: true,
      configurable: true,
    });

    reportWebVitals();
    // No error = success
  });

  it('attempts to load web-vitals in production', async () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'anyplot.ai' },
      writable: true,
      configurable: true,
    });
    window.plausible = vi.fn();

    reportWebVitals();
    await vi.dynamicImportSettled();

    expect(window.plausible).toHaveBeenCalledWith('LCP', {
      props: { value: '2500', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('CLS', {
      props: { value: '0.15', rating: 'needs-improvement' },
    });
    expect(window.plausible).toHaveBeenCalledWith('INP', {
      props: { value: '200', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('FCP', {
      props: { value: '1200', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('TTFB', {
      props: { value: '400', rating: 'good' },
    });
  });

  it('merges ambient analytics props (e.g. theme) into CWV events', async () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'anyplot.ai' },
      writable: true,
      configurable: true,
    });
    window.plausible = vi.fn();
    setAnalyticsAmbientProps({ theme: 'dark' });

    reportWebVitals();
    await vi.dynamicImportSettled();

    expect(window.plausible).toHaveBeenCalledWith('LCP', {
      props: { theme: 'dark', value: '2500', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('CLS', {
      props: { theme: 'dark', value: '0.15', rating: 'needs-improvement' },
    });
    expect(window.plausible).toHaveBeenCalledWith('INP', {
      props: { theme: 'dark', value: '200', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('FCP', {
      props: { theme: 'dark', value: '1200', rating: 'good' },
    });
    expect(window.plausible).toHaveBeenCalledWith('TTFB', {
      props: { theme: 'dark', value: '400', rating: 'good' },
    });
  });

  it("reports nothing for a load in which the admin's use of the chat muted analytics", async () => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'anyplot.ai' },
      writable: true,
      configurable: true,
    });
    window.plausible = vi.fn();
    // The admin left the chat for another page of the same load: a late metric (CLS and INP
    // report when the page is hidden) measured the chat's time too.
    setAnalyticsMuted(true);
    setAnalyticsMuted(false);

    reportWebVitals();
    await vi.dynamicImportSettled();

    expect(window.plausible).not.toHaveBeenCalled();
  });

  // The chat mutes only once it has mounted; TTFB and FCP can report before that.
  it.each([
    ['/agent with the admin hint', '/agent', true, false],
    ['the old admin address', '/debug/agent', false, false],
    ["a visitor's /agent", '/agent', false, true],
  ])('decides a load that starts on %s when the metrics register', async (_, path, hint, sent) => {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname: 'anyplot.ai', pathname: path },
      writable: true,
      configurable: true,
    });
    window.plausible = vi.fn();
    if (hint) localStorage.setItem(ADMIN_HINT_KEY, '1');

    reportWebVitals();
    await vi.dynamicImportSettled();

    expect((window.plausible as ReturnType<typeof vi.fn>).mock.calls.length > 0).toBe(sent);
    localStorage.clear();
  });
});
