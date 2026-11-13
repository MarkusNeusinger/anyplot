import { useCallback } from 'react';

import { analyticsMuted } from 'src/analytics/mute';
import { isPlotsPath, paths, RESERVED_TOP_LEVEL } from 'src/routes/paths';

/**
 * The custom events the app sends. The set is closed: every name is a goal a reader of the
 * public dashboard understands, and the compiler refuses any other
 * (docs/reference/plausible.md).
 */
export type AnalyticsEvent =
  | 'copy_code'
  | 'download_image'
  | 'interactive_open'
  | 'search'
  | 'search_no_results'
  | 'feedback_submitted'
  | 'agent_open'
  | 'agent_plot_rendered'
  | 'plots_scrolled'
  | 'nav_click'
  | 'ui_feature';

/**
 * The features `ui_feature` counts, as its `feature` property. The event answers one question
 * per feature, "is this used at all", so it is sent once per feature and visit and carries
 * nothing else.
 */
export const UI_FEATURES = [
  'tab_toggle',
  'view_mode_change',
  'grid_resize',
  'filter_remove',
  'random_filter',
  'plot_rotate',
  'library_filter',
  'theme_toggle',
  'feedback_open',
  'map_node_click',
  'map_node_pin',
  'map_search_select',
] as const;

export type UiFeature = (typeof UI_FEATURES)[number];

export interface EventProps {
  feature?: UiFeature;
  [key: string]: string | undefined;
}

/**
 * `trackEvent`, for the components that receive it as a prop. `ui_feature` names its feature
 * and nothing else: without a feature the event would say nothing, and with more than it the
 * twelve features would again be twelve kinds of event. The compiler refuses both.
 */
export interface TrackEvent {
  (name: 'ui_feature', props: { feature: UiFeature }, url?: string): void;
  (name: Exclude<AnalyticsEvent, 'ui_feature'>, props?: EventProps, url?: string): void;
}

// The last pageview sent, for the whole app rather than per hook instance: the layout records
// every navigation and the gallery its filter changes, and neither may repeat the other's.
let lastPageviewUrl = '';

/** Forgets the last pageview. For tests: the state above is the module's and outlives one. */
export function forgetLastPageview(): void {
  lastPageviewUrl = '';
}

// A visit as Plausible counts it: it ends after 30 minutes without a pageview or an event.
// The same gap starts a new visit here, so "once per visit" means the same on both sides. A
// tab left open overnight counts a feature again the next day.
const VISIT_GAP_MS = 30 * 60 * 1000;
let lastSentAt = 0;
const featuresThisVisit = new Set<UiFeature>();

/** Forgets the visit and the features it used. For tests, like `forgetLastPageview`. */
export function forgetVisit(): void {
  lastSentAt = 0;
  featuresThisVisit.clear();
}

/**
 * Notes that something is being sent now. A long silence before it began a new visit, in which
 * no feature was used yet. Only what is really sent counts: a repeated feature use sends
 * nothing, so for Plausible the visit does not go on because of it.
 */
function noteSent(now: number): void {
  if (now - lastSentAt > VISIT_GAP_MS) featuresThisVisit.clear();
  lastSentAt = now;
}

/** Whether `ui_feature` still has to be sent for this feature in the visit that is under way at `now`. */
function firstUseThisVisit(feature: UiFeature, now: number): boolean {
  if (now - lastSentAt > VISIT_GAP_MS) featuresThisVisit.clear();
  return !featuresThisVisit.has(feature);
}

/** How long a search query may be when it is sent: catalogue words fit, a pasted text does not. */
export const MAX_QUERY_LENGTH = 40;

/**
 * A typed search query as it is sent: lowercase, single spaces, cut at `MAX_QUERY_LENGTH`. The
 * public dashboard lists these, so "Scatter", "scatter " and "SCATTER" are one entry, and a
 * long text a visitor pasted by mistake does not stand there in full.
 */
export function normalizeQuery(query: string): string {
  return query.toLowerCase().trim().replace(/\s+/g, ' ').slice(0, MAX_QUERY_LENGTH).trimEnd();
}

/** The kinds of page a pageview is recorded as, in its `page` property. */
export type PageKind = 'home' | 'plots' | 'spec_overview' | 'spec_detail' | 'agent_chat' | 'other';

/**
 * The kind of page a path names. `copy_code` and `download_image` send the same values, so one
 * `page` breakdown covers pageviews and the two conversions.
 */
export function pageKind(pathname: string): PageKind {
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length === 0) return 'home';
  if (isPlotsPath(pathname)) return 'plots';
  if (parts[0] === 'agent' && parts.length === 1) return 'agent_chat';
  if (RESERVED_TOP_LEVEL.has(parts[0])) return 'other';
  if (parts.length === 1) return 'spec_overview';
  if (parts.length === 3) return 'spec_detail';
  return 'other';
}

// Module-level ambient props attached to every pageview and custom event.
// Set by the layout once theme/locale-style values are known so we don't have
// to thread them through every component that fires an event. Empty-string
// values clear the key (so callers can effectively reset a prop).
let ambientProps: Record<string, string> = {};

export function setAnalyticsAmbientProps(props: Record<string, string>): void {
  const merged: Record<string, string> = { ...ambientProps, ...props };
  for (const key of Object.keys(merged)) {
    if (!merged[key]) delete merged[key];
  }
  ambientProps = merged;
}

const ORIGIN = 'https://anyplot.ai';

// The page the current address is recorded as in Plausible.
//
// Every page is its own path, without the query. Two pages have a query that
// names a different page, and for those the query becomes path segments: the
// gallery's filters and a spec hub's language scope.
// Supports repeated params (AND) and comma-separated values (OR)
// /plots?lib=matplotlib&lib=seaborn → /plots/lib/matplotlib/lib/seaborn
// /plots?lib=matplotlib,seaborn → /plots/lib/matplotlib,seaborn
export function buildPlausibleUrl(): string {
  // Preserve the full current pathname so filter segments are appended after
  // it — for the spec hub AND for real reserved pages like /plots. Dropping
  // the reserved prefix recorded every filterless /plots visit as "/" and made
  // the site's #2 page invisible in Plausible.
  const parts = window.location.pathname.split('/').filter(Boolean);
  const pathPrefix = parts.length > 0 ? `/${parts.join('/')}` : '';
  const specRoute = parts.length > 0 && !RESERVED_TOP_LEVEL.has(parts[0]);

  // An implementation page: the language in lowercase, as everywhere else the
  // app compares it, so `/scatter-basic/Python/matplotlib` is no second page.
  if (specRoute && parts.length === 3) {
    return `${ORIGIN}/${parts[0]}/${parts[1].toLowerCase()}/${parts[2]}`;
  }
  const queryNamesThePage = pathPrefix === paths.plots || (specRoute && parts.length === 1);
  if (!queryNamesThePage) return `${ORIGIN}${pathPrefix || '/'}`;

  const params = new URLSearchParams(window.location.search);
  const segments: string[] = [];

  // Defined order of the filter categories (incl. impl-level tags).
  // - `language` covers the spec-hub carousel scope (`/{spec}?language=python`)
  //   that pre-dates the FilterBar lang category.
  // - `lang` covers the new FilterBar category on `/plots?lang=python` —
  //   without it, the lang filter would never show up as a distinct pageview
  //   path in Plausible.
  const orderedKeys = [
    'lang',
    'lib',
    'spec',
    'plot',
    'data',
    'dom',
    'feat',
    'dep',
    'tech',
    'pat',
    'prep',
    'style',
    'language',
  ];

  for (const key of orderedKeys) {
    // getAll() for repeated params with the same key (AND logic)
    const values = params.getAll(key);
    for (const value of values) {
      if (value) {
        // Comma-separated values are preserved (OR logic)
        segments.push(key, value);
      }
    }
  }

  return segments.length > 0
    ? `${ORIGIN}${pathPrefix}/${segments.join('/')}`
    : `${ORIGIN}${pathPrefix || '/'}`;
}

export function useAnalytics() {
  const isProduction = typeof window !== 'undefined' && window.location.hostname === 'anyplot.ai';

  // Records the page the address names now, at once. No page calls this for
  // itself: the layout does on every navigation (`RootLayout`), and the gallery
  // when a filter changes its address without one (`useUrlSync`).
  const trackPageview = useCallback(() => {
    if (!isProduction) return;
    if (analyticsMuted()) {
      // A muted page is a page all the same: coming back from it to the page before it is a
      // new pageview, not a repeat of the last one sent.
      lastPageviewUrl = '';
      return;
    }

    const url = buildPlausibleUrl();
    if (url === lastPageviewUrl) return;
    lastPageviewUrl = url;

    noteSent(Date.now());
    const props = { ...ambientProps, page: pageKind(window.location.pathname) };
    window.plausible?.('pageview', { url, props });
  }, [isProduction]);

  // `url` names the page an event belongs to when it is sent after the visitor
  // left it; without one the script takes the current address.
  const trackEvent: TrackEvent = useCallback(
    (name: AnalyticsEvent, props?: EventProps, url?: string) => {
      if (!isProduction || analyticsMuted()) return;
      const now = Date.now();
      const feature = name === 'ui_feature' ? props?.feature : undefined;
      if (name === 'ui_feature') {
        // Without a feature the event says nothing (the type refuses the call; a caller that
        // got around it sends nothing); a second use in the same visit adds nothing.
        if (!feature || !firstUseThisVisit(feature, now)) return;
      }
      noteSent(now);
      if (feature) featuresThisVisit.add(feature);
      const cleanProps = props
        ? Object.fromEntries(Object.entries(props).filter(([, v]) => v !== undefined))
        : {};
      const merged = { ...ambientProps, ...cleanProps } as Record<string, string>;
      const options = {
        ...(Object.keys(merged).length > 0 ? { props: merged } : {}),
        ...(url ? { url } : {}),
      };
      window.plausible?.(name, Object.keys(options).length > 0 ? options : undefined);
    },
    [isProduction]
  );

  return { trackPageview, trackEvent };
}
