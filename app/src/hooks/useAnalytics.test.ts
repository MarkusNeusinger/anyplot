import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import { noteStayInput, setStayActive, STAY_MS } from 'src/analytics/stay';
import searchQueryCases from 'src/hooks/searchQuery.cases.json';
import {
  buildPlausibleUrl,
  forgetLastPageview,
  forgetVisit,
  MAX_QUERY_LENGTH,
  normalizeQuery,
  pageKind,
  setAnalyticsAmbientProps,
  STAYED_EVENT,
  STAYED_INTERACTIVE,
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

    it('holds thirteen features, each named once', () => {
      expect(new Set(UI_FEATURES).size).toBe(UI_FEATURES.length);
      expect(UI_FEATURES).toHaveLength(13);
    });
  });

  describe('stayed_10s', () => {
    /** Puts the page in front of the visitor, or takes it away. */
    function page(active: boolean) {
      vi.spyOn(document, 'visibilityState', 'get').mockReturnValue(active ? 'visible' : 'hidden');
      vi.spyOn(document, 'hasFocus').mockReturnValue(active);
    }

    function stayed() {
      return vi.mocked(window.plausible!).mock.calls.filter(([event]) => event === STAYED_EVENT);
    }

    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-11-14T08:00:00Z'));
      page(true);
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it('is sent ten seconds after the pageview that began the visit, and not again for its next page', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();

      vi.advanceTimersByTime(STAY_MS - 1);
      expect(stayed()).toEqual([]);
      vi.advanceTimersByTime(1);
      // While it is measured, it keeps no visit from counting as bounced.
      expect(STAYED_INTERACTIVE).toBe(false);
      expect(stayed()).toEqual([[STAYED_EVENT, { props: { input: 'no' }, interactive: false }]]);

      // A second page of the same visit does not start the clock again.
      at('/plots');
      result.current.trackPageview();
      vi.advanceTimersByTime(5 * 60_000);
      expect(stayed()).toHaveLength(1);
    });

    it('keeps counting through what the visitor does: a click after five seconds changes nothing', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();

      vi.advanceTimersByTime(5_000);
      result.current.trackEvent('copy_code', { spec: 'scatter-basic' });
      vi.advanceTimersByTime(2_000);
      result.current.trackEvent('ui_feature', { feature: 'tab_toggle' });
      vi.advanceTimersByTime(2_999);
      expect(stayed()).toEqual([]);

      // Ten seconds after the visit began, not after the last thing the visitor did.
      vi.advanceTimersByTime(1);
      expect(stayed()).toHaveLength(1);
    });

    it('says when the visitor used a pointer, a finger or a key in those seconds', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(2_000);
      noteStayInput();
      vi.advanceTimersByTime(8_000);

      expect(stayed()).toEqual([[STAYED_EVENT, { props: { input: 'yes' }, interactive: false }]]);

      // That is the visit's one event: more input sends nothing more.
      noteStayInput();
      vi.advanceTimersByTime(60_000);
      expect(stayed()).toHaveLength(1);
    });

    it('is sent once more, with yes, at the first input after ten seconds without one', () => {
      // Someone opens a page, fetches a coffee, then clicks around: they count all the same.
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);
      vi.advanceTimersByTime(3 * 60_000);
      // On a second page of the same visit.
      at('/plots');
      result.current.trackPageview();
      noteStayInput();

      expect(stayed()).toEqual([
        [STAYED_EVENT, { props: { input: 'no' }, interactive: false }],
        [STAYED_EVENT, { props: { input: 'yes' }, interactive: false }],
      ]);

      noteStayInput();
      vi.advanceTimersByTime(60_000);
      noteStayInput();
      expect(stayed()).toHaveLength(2);
    });

    it('sends no yes for an input after the visit is over for Plausible', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);
      // More than 30 minutes after the `no`, the last thing sent.
      vi.advanceTimersByTime(31 * 60_000);
      noteStayInput();

      expect(stayed()).toEqual([[STAYED_EVENT, { props: { input: 'no' }, interactive: false }]]);
    });

    it('waits for the new visit’s own ten seconds, not for the input the visit before lacked', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);
      vi.advanceTimersByTime(45 * 60_000);

      at('/heatmap-basic');
      result.current.trackPageview();
      vi.advanceTimersByTime(2_000);
      noteStayInput();
      // Two seconds into the new visit: no late `yes` for the one before.
      expect(stayed()).toHaveLength(1);

      vi.advanceTimersByTime(8_000);
      expect(stayed()).toEqual([
        [STAYED_EVENT, { props: { input: 'no' }, interactive: false }],
        [STAYED_EVENT, { props: { input: 'yes' }, interactive: false }],
      ]);
    });

    it('sends the yes of an input that comes after a no that was muted', () => {
      // Each send is checked when it comes: the visit stayed ten seconds, and the visitor did
      // something once the mute was off.
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      setAnalyticsMuted(true);
      vi.advanceTimersByTime(STAY_MS);
      setAnalyticsMuted(false);
      expect(stayed()).toEqual([]);

      noteStayInput();
      expect(stayed()).toEqual([[STAYED_EVENT, { props: { input: 'yes' }, interactive: false }]]);
    });

    it('uses up an input that comes while the mute is on, and sends nothing for it', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);
      setAnalyticsMuted(true);
      noteStayInput();
      setAnalyticsMuted(false);
      noteStayInput();

      expect(stayed()).toEqual([[STAYED_EVENT, { props: { input: 'no' }, interactive: false }]]);
    });

    it('is not sent for a page that is never in front of the visitor', () => {
      page(false);
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(10 * 60_000);

      expect(stayed()).toEqual([]);
    });

    it('is not sent once the visit is over for Plausible', () => {
      // Four seconds, an hour in another tab, six more: together ten, but 30 minutes after
      // the pageview the visit ended, and the event would open one of its own, without a page.
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(4_000);
      setStayActive(false, Date.now());
      vi.advanceTimersByTime(60 * 60_000);
      setStayActive(true, Date.now());
      vi.advanceTimersByTime(60_000);

      expect(stayed()).toEqual([]);
    });

    it('starts again with the next visit', () => {
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);
      expect(stayed()).toHaveLength(1);

      // More than 30 minutes without anything sent, then a page: a new visit.
      vi.advanceTimersByTime(45 * 60_000);
      at('/heatmap-basic');
      result.current.trackPageview();
      vi.advanceTimersByTime(STAY_MS);

      expect(stayed()).toHaveLength(2);
    });

    it('is not sent while the admin’s own use is muted', () => {
      at('/agent');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      setAnalyticsMuted(true);
      vi.advanceTimersByTime(STAY_MS);
      setAnalyticsMuted(false);
      vi.advanceTimersByTime(60_000);

      expect(stayed()).toEqual([]);
    });

    it('is not sent anywhere but on the live site, whatever the page was ten seconds before', () => {
      // The moment comes from a timer, so the pageview's own check is long past by then.
      at('/scatter-basic');
      const { result } = renderHook(() => useAnalytics());
      result.current.trackPageview();
      at('/scatter-basic', '', 'localhost');
      vi.advanceTimersByTime(60_000);

      expect(stayed()).toEqual([]);
    });

    it('is the tracker’s own event: no component can send it', () => {
      at('/');
      const { result } = renderHook(() => useAnalytics());

      // @ts-expect-error -- the type refuses the call; this line fails to compile if it ever
      // stops doing so. A caller that got around the type sends nothing.
      result.current.trackEvent('stayed_10s');

      expect(window.plausible).not.toHaveBeenCalled();
    });
  });

  describe('normalizeQuery', () => {
    // The API's `normalize_query` reads the same cases (tests/unit/api/test_search_misses.py).
    it.each(searchQueryCases.cases.map(item => [item.rule, item] as const))(
      'keeps the rule: %s',
      (_rule, item) => {
        expect(normalizeQuery(item.typed)).toBe(item.sent);
      }
    );

    it('cuts at the length the API keeps, counted in characters', () => {
      expect(MAX_QUERY_LENGTH).toBe(searchQueryCases.max_length);
      // Forty whole characters: a cut in UTF-16 units would keep twenty and a half.
      expect(normalizeQuery('😀'.repeat(45))).toBe('😀'.repeat(MAX_QUERY_LENGTH));
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
