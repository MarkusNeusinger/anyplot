import { createContext, useCallback, useEffect, useState } from 'react';

import { apiGet, endpoints } from 'src/lib/api';

export interface PlotOfTheDayData {
  spec_id: string;
  spec_title: string;
  library_id: string;
  library_name: string;
  language: string;
  // Theme-aware (Phase C). Backend may still only emit preview_url during transition.
  preview_url_light?: string | null;
  preview_url_dark?: string | null;
  preview_url: string | null;
  description?: string | null;
  image_description?: string | null;
  quality_score?: number;
  library_version?: string | null;
  python_version?: string | null;
  language_version?: string | null;
  date?: string;
}

/**
 * Where the plot-of-the-day request stands: `loading` until it answers (and again after a
 * retry), `ready` with a plot, `none` when the API answered that there is no plot of the
 * day (it may return null), and `failed` when the request still failed after apiGet's
 * own retries.
 */
export type PlotOfTheDayStatus = 'loading' | 'ready' | 'none' | 'failed';

export interface PlotOfTheDayLoad {
  status: PlotOfTheDayStatus;
  /** Asks again after a failure. */
  retry?: () => void;
}

/**
 * The request's status for the terminal card, which sits inside the hero: the landing page
 * provides it, so the card can tell a request in flight from a failed one. The default is
 * `loading`, which keeps the reserved empty frame.
 */
export const PlotOfTheDayLoadContext = createContext<PlotOfTheDayLoad>({ status: 'loading' });

export interface PlotOfTheDayState extends Required<PlotOfTheDayLoad> {
  potd: PlotOfTheDayData | null;
}

export function usePlotOfTheDay(): PlotOfTheDayState {
  const [potd, setPotd] = useState<PlotOfTheDayData | null>(null);
  const [status, setStatus] = useState<PlotOfTheDayStatus>('loading');
  // Bumped by `retry` so the effect asks again.
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => {
    setStatus('loading');
    setAttempt(a => a + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiGet<PlotOfTheDayData | null>(endpoints.plotOfTheDay)
      .then(data => {
        if (cancelled) return;
        setPotd(data);
        setStatus(data ? 'ready' : 'none');
      })
      .catch(() => {
        if (!cancelled) setStatus('failed');
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  return { potd, status, retry };
}
