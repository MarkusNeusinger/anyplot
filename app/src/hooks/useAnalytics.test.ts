import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import {
  buildPlausibleUrl,
  forgetLastPageview,
  forgetVisit,
  MAX_QUERY_LENGTH,
  normalizeQuery,
  pageKind,
  setAnalyticsAmbientProps,
  UI_FEATURES,
  useAnalytics,
} from 'src/hooks/useAnalytics';

describe('useAnalytics', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    window.plausible = vi.fn();
    // Reset module-level state between tests so each starts clean.
    setAnalyticsAmbientProps({ theme: '' });
    forgetLastPageview();
    forgetVisit();
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
        result.current.trackEvent('agent_open');
      });

      expect(window.plausible).toHaveBeenCalledWith('agent_open', undefined);
    });

    it('strips undefined values from props', () => {
      at('/');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('nav_click', {
          source: 'hero_github',
          spec: undefined,
        });
      });

      expect(window.plausible).toHaveBeenCalledWith('nav_click', {
        props: { source: 'hero_github' },
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
        result.current.trackEvent('agent_open', undefined, 'https://anyplot.ai/specs');
      });

      expect(window.plausible).toHaveBeenCalledWith('plots_scrolled', {
        props: { share: '25-50' },
        url: 'https://anyplot.ai/plots/lib/matplotlib',
      });
      expect(window.plausible).toHaveBeenCalledWith('agent_open', {
        url: 'https://anyplot.ai/specs',
      });
    });
  });

  // `ui_feature` answers "is this used at all": one event per feature and visit, nothing else.
  describe('ui_feature', () => {
    function features() {
      return vi
        .mocked(window.plausible!)
        .mock.calls.filter(([event]) => event === 'ui_feature')
        .map(([, options]) => (options as { props: { feature: string } }).props.feature);
    }

    it('counts a feature once per visit, however often it is used', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());

      for (let use = 0; use < 5; use += 1) {
        result.current.trackEvent('ui_feature', { feature: 'tab_toggle' });
      }
      result.current.trackEvent('ui_feature', { feature: 'theme_toggle' });
      result.current.trackEvent('ui_feature', { feature: 'tab_toggle' });

      expect(features()).toEqual(['tab_toggle', 'theme_toggle']);
    });

    it('shares the visit between every caller: another component counts no second time', () => {
      at('/plots');
      const first = renderHook(() => useAnalytics());
      const second = renderHook(() => useAnalytics());

      first.result.current.trackEvent('ui_feature', { feature: 'grid_resize' });
      second.result.current.trackEvent('ui_feature', { feature: 'grid_resize' });

      expect(features()).toEqual(['grid_resize']);
    });

    it('counts again in a new visit: after 30 minutes without a pageview or an event', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-11-11T08:00:00Z'));
      at('/plots');
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('ui_feature', { feature: 'filter_remove' });
      // 29 minutes later a pageview keeps the visit going, and the next 29 minutes are its too.
      vi.setSystemTime(new Date('2026-11-11T08:29:00Z'));
      result.current.trackPageview();
      vi.setSystemTime(new Date('2026-11-11T08:58:00Z'));
      result.current.trackEvent('ui_feature', { feature: 'filter_remove' });
      expect(features()).toEqual(['filter_remove']);

      // A tab left open: the next use, 31 minutes after the last thing sent, is a new visit's.
      vi.setSystemTime(new Date('2026-11-11T09:00:01Z'));
      result.current.trackEvent('ui_feature', { feature: 'filter_remove' });
      expect(features()).toEqual(['filter_remove', 'filter_remove']);
    });

    it('a use that was not sent does not keep the visit going', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-11-11T08:00:00Z'));
      at('/plots');
      const { result } = renderHook(() => useAnalytics());

      result.current.trackEvent('ui_feature', { feature: 'plot_rotate' });
      // Repeated uses send nothing, so for Plausible the visit ended 30 minutes after the first.
      vi.setSystemTime(new Date('2026-11-11T08:20:00Z'));
      result.current.trackEvent('ui_feature', { feature: 'plot_rotate' });
      vi.setSystemTime(new Date('2026-11-11T08:31:00Z'));
      result.current.trackEvent('ui_feature', { feature: 'plot_rotate' });

      expect(features()).toEqual(['plot_rotate', 'plot_rotate']);
    });

    it('sends nothing without a feature, and carries the feature alone', () => {
      at('/');
      const { result } = renderHook(() => useAnalytics());

      // @ts-expect-error -- the type refuses `ui_feature` without its feature; this line fails
      // to compile if it ever stops doing so. A caller that got around the type sends nothing.
      result.current.trackEvent('ui_feature');
      result.current.trackEvent('ui_feature', { feature: 'feedback_open' });
      // @ts-expect-error -- the type refuses a property beside the feature, likewise.
      result.current.trackEvent('ui_feature', { feature: 'feedback_open', action: 'open' });

      expect(window.plausible).toHaveBeenCalledTimes(1);
      expect(window.plausible).toHaveBeenCalledWith('ui_feature', {
        props: { feature: 'feedback_open' },
      });
    });

    it('does not count while muted, and counts the first use after', () => {
      at('/agent');
      const { result } = renderHook(() => useAnalytics());
      setAnalyticsMuted(true);
      result.current.trackEvent('ui_feature', { feature: 'theme_toggle' });
      setAnalyticsMuted(false);
      result.current.trackEvent('ui_feature', { feature: 'theme_toggle' });

      expect(features()).toEqual(['theme_toggle']);
    });

    it('holds twelve features, each named once', () => {
      expect(new Set(UI_FEATURES).size).toBe(UI_FEATURES.length);
      expect(UI_FEATURES).toHaveLength(12);
    });
  });

  describe('normalizeQuery', () => {
    it.each([
      ['Scatter', 'scatter'],
      ['  scatter  ', 'scatter'],
      ['SCATTER   Plot', 'scatter plot'],
      ['box\tplot\nmatplotlib', 'box plot matplotlib'],
      ['', ''],
      ['   ', ''],
    ])('sends %j as %j', (typed, sent) => {
      expect(normalizeQuery(typed)).toBe(sent);
    });

    it('cuts a long text at 40 characters and leaves no space at the cut', () => {
      const pasted = 'dear team, please find attached the quarterly numbers for the board';
      const sent = normalizeQuery(pasted);
      expect(MAX_QUERY_LENGTH).toBe(40);
      expect(sent).toBe('dear team, please find attached the quar');
      expect(sent.length).toBeLessThanOrEqual(MAX_QUERY_LENGTH);
      expect(normalizeQuery(`${'a'.repeat(39)} bcd`)).toBe('a'.repeat(39));
    });
  });

  describe('pageKind', () => {
    it.each([
      ['/', 'home'],
      ['/plots', 'plots'],
      ['/plots/', 'plots'],
      ['/scatter-basic', 'spec_overview'],
      ['/scatter-basic/python/matplotlib', 'spec_detail'],
      ['/agent', 'agent_chat'],
      ['/specs', 'other'],
      ['/libraries', 'other'],
      ['/stats', 'other'],
      ['/legal', 'other'],
      ['/debug', 'other'],
      // The language redirect's address and an address no route matches.
      ['/scatter-basic/python', 'other'],
      ['/scatter-basic/python/matplotlib/extra', 'other'],
    ])('reads %s as %s', (pathname, kind) => {
      expect(pageKind(pathname)).toBe(kind);
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
        props: { page: 'other' },
      });
    });

    it.each([
      ['/', 'home'],
      ['/plots', 'plots'],
      ['/scatter-basic', 'spec_overview'],
      ['/scatter-basic/python/matplotlib', 'spec_detail'],
      ['/agent', 'agent_chat'],
    ])('names the kind of page: %s is %s', (pathname, page) => {
      at(pathname);
      const { result } = renderHook(() => useAnalytics());

      result.current.trackPageview();

      expect(pageviews()).toHaveLength(1);
      expect(pageviews()[0][1]).toMatchObject({ props: { page } });
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
        result.current.trackEvent('agent_open');
      });

      expect(window.plausible).toHaveBeenCalledWith('agent_open', {
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
        props: { theme: 'dark', page: 'other' },
      });
    });

    it('carries the kind of page alone when no ambient props are set', () => {
      at('/about');
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackPageview();
      });

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        url: 'https://anyplot.ai/about',
        props: { page: 'other' },
      });
    });

    it('event-level props override ambient values for the same key', () => {
      at('/');
      setAnalyticsAmbientProps({ theme: 'dark' });
      const { result } = renderHook(() => useAnalytics());

      act(() => {
        result.current.trackEvent('copy_code', { theme: 'light' });
      });

      expect(window.plausible).toHaveBeenCalledWith('copy_code', {
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
        result.current.trackEvent('agent_plot_rendered', { status: 'ok' });
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
        props: { page: 'plots' },
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
