import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import {
  buildPlausibleUrl,
  forgetLastPageview,
  setAnalyticsAmbientProps,
  useAnalytics,
} from 'src/hooks/useAnalytics';

describe('useAnalytics', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    window.plausible = vi.fn();
    // Reset module-level state between tests so each starts clean.
    setAnalyticsAmbientProps({ theme: '' });
    forgetLastPageview();
  });

  afterEach(() => {
    delete window.plausible;
    // Restore location
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
  });

  /** The browser at `pathname` + `search` on a host: production unless told otherwise. */
  function at(pathname: string, search = '', hostname = 'anyplot.ai') {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname, pathname, search },
      writable: true,
      configurable: true,
    });
  }

  function pageviews() {
    return vi.mocked(window.plausible!).mock.calls.filter(([event]) => event === 'pageview');
  }

  describe('trackEvent', () => {
    it('does not call plausible in non-production', () => {
      at('/', '', 'localhost');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('copy_code', { spec: 'scatter-basic' });
      });

      expect(window.plausible).not.toHaveBeenCalled();
    });

    it('calls plausible with event name and props in production', () => {
      at('/');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('copy_code', { spec: 'scatter-basic' });
      });

      expect(window.plausible).toHaveBeenCalledWith('copy_code', {
        props: { spec: 'scatter-basic' },
      });
    });

    it('calls plausible without props when none provided', () => {
      at('/');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('suggest_spec');
      });

      expect(window.plausible).toHaveBeenCalledWith('suggest_spec', undefined);
    });

    it('strips undefined values from props', () => {
      at('/');
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

    it('names the page an event belongs to when it is sent after the visitor left it', () => {
      // `plots_scrolled` goes out when the gallery unmounts: the address is the next page's by then.
      at('/scatter-basic/python/matplotlib');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent(
          'plots_scrolled',
          { share: '25-50' },
          'https://anyplot.ai/plots/lib/matplotlib'
        );
        result.current.trackEvent('suggest_spec', undefined, 'https://anyplot.ai/specs');
      });

      expect(window.plausible).toHaveBeenCalledWith('plots_scrolled', {
        props: { share: '25-50' },
        url: 'https://anyplot.ai/plots/lib/matplotlib',
      });
      expect(window.plausible).toHaveBeenCalledWith('suggest_spec', {
        url: 'https://anyplot.ai/specs',
      });
    });
  });

  describe('trackPageview', () => {
    it('does not call plausible in non-production', () => {
      at('/plots', '', 'localhost');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
      });

      expect(window.plausible).not.toHaveBeenCalled();
    });

    it('sends the pageview at once: the call closes the page being left while it is still there', () => {
      // A delay let the next page render first, and Plausible's script then measured the page
      // being left against the next page's height (`RootLayout`). No timer may come back.
      at('/specs');
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageview();

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: 'https://anyplot.ai/specs',
      });
    });

    it('sends each address once, whichever caller comes second', () => {
      // The layout records the navigation and the gallery its filter changes, through two
      // instances of the hook: one must not repeat the other.
      at('/plots', '?lib=matplotlib');
      const layout = renderHook(() => useAnalytics());
      const gallery = renderHook(() => useAnalytics());

      layout.result.current.trackPageview();
      gallery.result.current.trackPageview();
      layout.result.current.trackPageview();
      expect(pageviews()).toHaveLength(1);

      // A page visited again after another one is a new pageview.
      at('/plots', '?lib=seaborn');
      gallery.result.current.trackPageview();
      at('/plots', '?lib=matplotlib');
      gallery.result.current.trackPageview();
      expect(pageviews().map(([, options]) => options?.url)).toEqual([
        'https://anyplot.ai/plots/lib/matplotlib',
        'https://anyplot.ai/plots/lib/seaborn',
        'https://anyplot.ai/plots/lib/matplotlib',
      ]);
    });
  });

  describe('buildPlausibleUrl', () => {
    it.each([
      // Every page is its own path.
      ['/', '', 'https://anyplot.ai/'],
      ['/legal', '', 'https://anyplot.ai/legal'],
      ['/plots/', '', 'https://anyplot.ai/plots'],
      // `/plots` is a real page — the prefix must survive so Plausible attributes the pageview
      // to /plots, not to "/". (Dropping the reserved prefix made the site's #2 page invisible.)
      ['/plots', '?lang=python', 'https://anyplot.ai/plots/lang/python'],
      [
        '/plots',
        '?lib=matplotlib&plot=scatter',
        'https://anyplot.ai/plots/lib/matplotlib/plot/scatter',
      ],
      ['/plots', '?lib=matplotlib,seaborn', 'https://anyplot.ai/plots/lib/matplotlib,seaborn'],
      [
        '/plots',
        '?lib=matplotlib&lib=seaborn',
        'https://anyplot.ai/plots/lib/matplotlib/lib/seaborn',
      ],
      // A query that names no filter is no page: the search pill's `?focus=search`.
      ['/plots', '?focus=search', 'https://anyplot.ai/plots'],
      // The spec hub and its language scope.
      ['/biplot-pca', '', 'https://anyplot.ai/biplot-pca'],
      ['/biplot-pca', '?language=python', 'https://anyplot.ai/biplot-pca/language/python'],
      // An implementation page is its path alone: the carousel's language scope and the
      // interactive view are the same page, and so is a language in another case.
      [
        '/scatter-basic/python/matplotlib',
        '',
        'https://anyplot.ai/scatter-basic/python/matplotlib',
      ],
      [
        '/scatter-basic/python/matplotlib',
        '?language=python&view=interactive',
        'https://anyplot.ai/scatter-basic/python/matplotlib',
      ],
      [
        '/scatter-basic/Python/matplotlib',
        '',
        'https://anyplot.ai/scatter-basic/python/matplotlib',
      ],
      // The chat's query names the pair it opened with, and two of its names are filter names
      // too (`spec`, `language`): still one page.
      [
        '/agent',
        '?spec=scatter-basic&library=matplotlib&language=python',
        'https://anyplot.ai/agent',
      ],
      // Every other reserved page ignores its query as well.
      ['/stats', '?lib=matplotlib', 'https://anyplot.ai/stats'],
      // An address no route serves is recorded as it was asked for (the 404 page).
      ['/no/such/page/here', '?lib=matplotlib', 'https://anyplot.ai/no/such/page/here'],
    ])('records %s%s as %s', (pathname, search, url) => {
      at(pathname, search);
      expect(buildPlausibleUrl()).toBe(url);
    });
  });

  describe('ambient props', () => {
    it('attaches ambient props to custom events', () => {
      at('/');
      setAnalyticsAmbientProps({ theme: 'dark' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('nav_click', { source: 'nav_logo' });
      });

      expect(window.plausible).toHaveBeenCalledWith('nav_click', {
        props: { theme: 'dark', source: 'nav_logo' },
      });
    });

    it('attaches ambient props to events fired without explicit props', () => {
      at('/');
      setAnalyticsAmbientProps({ theme: 'light' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('suggest_spec');
      });

      expect(window.plausible).toHaveBeenCalledWith('suggest_spec', {
        props: { theme: 'light' },
      });
    });

    it('attaches ambient props to pageviews', () => {
      at('/specs');
      setAnalyticsAmbientProps({ theme: 'dark' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
      });

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: 'https://anyplot.ai/specs',
        props: { theme: 'dark' },
      });
    });

    it('omits the props key when no ambient props are set', () => {
      at('/about');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
      });

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: 'https://anyplot.ai/about',
      });
    });

    it('event-level props override ambient values for the same key', () => {
      at('/');
      setAnalyticsAmbientProps({ theme: 'dark' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('theme_toggle', { theme: 'light' });
      });

      expect(window.plausible).toHaveBeenCalledWith('theme_toggle', {
        props: { theme: 'light' },
      });
    });

    it('clears a key when set to empty string', () => {
      at('/');
      setAnalyticsAmbientProps({ theme: 'dark' });
      setAnalyticsAmbientProps({ theme: '' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('search_no_results');
      });

      expect(window.plausible).toHaveBeenCalledWith('search_no_results', undefined);
    });
  });

  // The agent chat mutes analytics while it serves an admin: no visitor numbers from the owner.
  describe('muted', () => {
    afterEach(() => setAnalyticsMuted(false));

    it('sends no event and no pageview while muted, and both again after', () => {
      at('/agent');
      const { result } = renderHook(() => useAnalytics());
      setAnalyticsMuted(true);

      act(() => {
        result.current.trackEvent('agent_data_parsed', { format: 'csv' });
        result.current.trackPageview();
      });
      expect(window.plausible).not.toHaveBeenCalled();

      setAnalyticsMuted(false);
      at('/plots');
      act(() => {
        result.current.trackEvent('nav_click');
        result.current.trackPageview();
      });
      expect(window.plausible).toHaveBeenCalledWith('nav_click', undefined);
      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: 'https://anyplot.ai/plots',
      });
    });

    it('does not remember a pageview it never sent: the page counts once the mute is off', () => {
      at('/agent');
      const { result } = renderHook(() => useAnalytics());
      setAnalyticsMuted(true);
      result.current.trackPageview();
      setAnalyticsMuted(false);

      result.current.trackPageview();

      expect(pageviews()).toHaveLength(1);
    });

    it('records the page before a muted one again when the visitor comes back to it', () => {
      // An admin goes from a page to the chat and back: the chat is a page all the same, so
      // the way back is a new pageview, not a repeat of the last one sent.
      at('/legal');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();

      setAnalyticsMuted(true);
      at('/agent');
      result.current.trackPageview();
      setAnalyticsMuted(false);

      at('/legal');
      result.current.trackPageview();

      expect(pageviews().map(([, options]) => options?.url)).toEqual([
        'https://anyplot.ai/legal',
        'https://anyplot.ai/legal',
      ]);
    });
  });
});
