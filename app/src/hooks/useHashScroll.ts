import { useEffect } from 'react';

import { useLocation } from 'react-router-dom';

/** Where a linked section lands: below the sticky masthead (42 to 44 px), with a little air. */
export const ANCHOR_SX = { scrollMarginTop: '56px' } as const;

/**
 * Scrolls to the element the address's fragment names, once the page is there.
 *
 * A route that loads lazily renders after the browser has looked for the fragment and not found
 * it, so a fresh load of `/legal#assistant` or `/about#transparency` would otherwise stay at the
 * top. Give the target `ANCHOR_SX` so it lands clear of the sticky masthead.
 */
export function useHashScroll() {
  const { hash } = useLocation();

  useEffect(() => {
    if (!hash) return;
    document.getElementById(hash.slice(1))?.scrollIntoView?.();
  }, [hash]);
}
