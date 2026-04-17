import { useEffect, useState } from 'react';
import { API_URL } from '../constants';

export interface PlotOfTheDayData {
  spec_id: string;
  spec_title: string;
  library_id: string;
  library_name: string;
  preview_url: string | null;
  description?: string | null;
  image_description?: string | null;
  quality_score?: number;
  library_version?: string | null;
  python_version?: string | null;
  date?: string;
}

export function usePlotOfTheDay(): PlotOfTheDayData | null {
  const [potd, setPotd] = useState<PlotOfTheDayData | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/insights/plot-of-the-day`)
      .then(r => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((data: PlotOfTheDayData) => {
        if (!cancelled) setPotd(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return potd;
}
