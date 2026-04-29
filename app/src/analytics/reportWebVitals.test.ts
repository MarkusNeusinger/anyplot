import { describe, it, expect, vi, afterEach } from 'vitest';
import { reportWebVitals } from './reportWebVitals';
import { setAnalyticsAmbientProps } from '../hooks/useAnalytics';

// Single hoisted mock (vi.mock dedupes by module path — last call wins, so
// keeping one shared mock avoids cross-test interference).
vi.mock('web-vitals', () => ({
  onLCP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 2500, rating: 'good' }),
  onCLS: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 0.15, rating: 'needs-improvement' }),
  onINP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 200, rating: 'good' }),
  onFCP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 1200, rating: 'good' }),
  onTTFB: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 400, rating: 'good' }),
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
});
