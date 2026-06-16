import { useEffect, useState } from 'react';

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

export function usePlotOfTheDay(): PlotOfTheDayData | null {
  const [potd, setPotd] = useState<PlotOfTheDayData | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<PlotOfTheDayData>(endpoints.plotOfTheDay)
      .then(data => {
        if (!cancelled) setPotd(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return potd;
}
