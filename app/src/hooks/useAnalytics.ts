import { useCallback } from 'react';

import { analyticsMuted } from 'src/analytics/mute';
import { paths, RESERVED_TOP_LEVEL } from 'src/routes/paths';

interface EventProps {
  [key: string]: string | undefined;
}

// The last pageview sent, for the whole app rather than per hook instance: the layout records
// every navigation and the gallery its filter changes, and neither may repeat the other's.
let lastPageviewUrl = '';

/** Forgets the last pageview. For tests: the state above is the module's and outlives one. */
export function forgetLastPageview(): void {
  lastPageviewUrl = '';
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

    const props = Object.keys(ambientProps).length > 0 ? { ...ambientProps } : undefined;
    window.plausible?.('pageview', props ? { url, props } : { url });
  }, [isProduction]);

  // `url` names the page an event belongs to when it is sent after the visitor
  // left it; without one the script takes the current address.
  const trackEvent = useCallback(
    (name: string, props?: EventProps, url?: string) => {
      if (!isProduction || analyticsMuted()) return;
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
