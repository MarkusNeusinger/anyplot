import { describe, it, expect, vi, afterEach } from 'vitest';
import { reportWebVitals } from './reportWebVitals';

describe('reportWebVitals', () => {
  const originalLocation = window.location;

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
    delete window.plausible;
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

    // Mock the dynamic import
    vi.mock('web-vitals', () => ({
      onLCP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 2500, rating: 'good' }),
      onCLS: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 0.15, rating: 'needs-improvement' }),
      onINP: (cb: (m: { value: number; rating: string }) => void) => cb({ value: 200, rating: 'good' }),
    }));

    reportWebVitals();

    // Wait for dynamic import to resolve
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

    vi.restoreAllMocks();
  });
});
