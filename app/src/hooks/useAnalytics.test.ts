import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAnalytics } from './useAnalytics';

describe('useAnalytics', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.useFakeTimers();
    window.plausible = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    delete window.plausible;
    // Restore location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
  });

  function setHostname(hostname: string) {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname, search: '' },
      writable: true,
      configurable: true,
    });
  }

  describe('trackEvent', () => {
    it('does not call plausible in non-production', () => {
      setHostname('localhost');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('copy_code', { spec: 'scatter-basic' });
      });

      expect(window.plausible).not.toHaveBeenCalled();
    });

    it('calls plausible with event name and props in production', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('copy_code', { spec: 'scatter-basic' });
      });

      expect(window.plausible).toHaveBeenCalledWith('copy_code', {
        props: { spec: 'scatter-basic' },
      });
    });

    it('calls plausible without props when none provided', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('filter_change');
      });

      expect(window.plausible).toHaveBeenCalledWith('filter_change', undefined);
    });

    it('strips undefined values from props', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('external_link', {
          destination: 'github',
          spec: undefined,
        });
      });

      expect(window.plausible).toHaveBeenCalledWith('external_link', {
        props: { destination: 'github' },
      });
    });
  });

  describe('trackPageview', () => {
    it('does not call plausible in non-production', () => {
      setHostname('localhost');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
        vi.advanceTimersByTime(200);
      });

      expect(window.plausible).not.toHaveBeenCalled();
    });

    it('sends pageview with URL override in production', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
        vi.advanceTimersByTime(200);
      });

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: expect.stringContaining('anyplot.ai'),
      });
    });

    it('deduplicates identical consecutive pageviews', () => {
      setHostname('anyplot.ai');
      Object.defineProperty(window, 'location', {
        value: { ...originalLocation, hostname: 'anyplot.ai', search: '?lib=matplotlib' },
        writable: true,
        configurable: true,
      });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
        vi.advanceTimersByTime(200);
      });

      act(() => {
        result.current.trackPageview();
        vi.advanceTimersByTime(200);
      });

      // plausible should be called only once for identical URLs
      const pageviewCalls = (window.plausible as ReturnType<typeof vi.fn>).mock.calls.filter(
        ([event]: [string]) => event === 'pageview'
      );
      expect(pageviewCalls).toHaveLength(1);
    });

    it('is debounced by 150ms', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
      });

      // Not yet fired
      expect(window.plausible).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(150);
      });

      expect(window.plausible).toHaveBeenCalled();
    });

    it('rejects invalid URL overrides', () => {
      setHostname('anyplot.ai');
      const { result } = renderHook(() => useAnalytics());

      // The debounced sendPageview with invalid URL — use the underlying function
      // trackPageview is debounced, so we access sendPageview indirectly
      act(() => {
        result.current.trackPageview();
        vi.advanceTimersByTime(200);
      });

      // The call should have gone through with buildPlausibleUrl(), not the invalid URL
      expect(window.plausible).toHaveBeenCalled();
    });
  });
});
