import { useCallback, useEffect, useState } from 'react';

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

export interface PlotOfTheDayState {
  potd: PlotOfTheDayData | null;
  status: PlotOfTheDayStatus;
  /** Asks again after a failure. */
  retry: () => void;
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
    // Aborting, not only ignoring the answer: apiGet retries with backoff, and those retries
    // would keep asking after the visitor has left the page or asked again.
    const controller = new AbortController();
    apiGet<PlotOfTheDayData | null>(endpoints.plotOfTheDay, { signal: controller.signal })
      .then(data => {
        if (controller.signal.aborted) return;
        setPotd(data);
        setStatus(data ? 'ready' : 'none');
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus('failed');
      });
    return () => controller.abort();
  }, [attempt]);

  return { potd, status, retry };
}
