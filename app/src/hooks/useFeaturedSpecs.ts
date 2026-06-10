import { useEffect, useMemo, useState } from 'react';

import { useAppData } from 'src/hooks/useLayoutContext';
import { apiGet, endpoints } from 'src/lib/api';
import type { PlotImage } from 'src/types';
import { shuffleArray } from 'src/utils/shuffle';

function pickRandom<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

export interface FeaturedImpl {
  spec_id: string;
  spec_title: string;
  spec_description: string | null;
  library_id: string;
  language: string;
  // Theme-aware (Phase C). Legacy preview_url is retained as the light-variant fallback.
  preview_url_light: string | null;
  preview_url_dark: string | null;
  preview_url: string | null;
}

/**
 * Returns `count` randomly-picked specs, each paired with the preview image of
 * a randomly-picked implementation. Reuses `/plots/filter` (same source as
 * /specs) + the pre-loaded specsData so no dedicated backend route is needed.
 *
 * Randomness is computed once the data is available; the set is stable for
 * the page's lifetime. Reload the page to re-shuffle.
 */
export function useFeaturedSpecs(count: number = 5): FeaturedImpl[] | null {
  const { specsData } = useAppData();
  const [images, setImages] = useState<PlotImage[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<{ images?: PlotImage[] }>(endpoints.plotsFilter())
      .then(data => {
        if (cancelled || !data.images) return;
        setImages(data.images);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return useMemo(() => {
    if (!images || specsData.length === 0) return null;

    const imagesBySpec: Record<string, PlotImage[]> = {};
    for (const img of images) {
      if (!img.spec_id) continue;
      if (!imagesBySpec[img.spec_id]) imagesBySpec[img.spec_id] = [];
      imagesBySpec[img.spec_id].push(img);
    }

    const candidates = specsData.filter(spec => imagesBySpec[spec.id]?.length);
    // Fisher-Yates (in shuffleArray) gives a uniform distribution; the prior
    // `.sort(() => Math.random() - 0.5)` is biased per V8's sort implementation.
    const shuffled = shuffleArray(candidates).slice(0, count);

    return shuffled.map(spec => {
      const impls = imagesBySpec[spec.id];
      const pick = pickRandom(impls);
      return {
        spec_id: spec.id,
        spec_title: spec.title,
        spec_description: spec.description ?? null,
        library_id: pick.library,
        language: pick.language,
        preview_url_light: pick.url_light ?? pick.url ?? null,
        preview_url_dark: pick.url_dark ?? null,
        preview_url: pick.url ?? null,
      };
    });
  }, [images, specsData, count]);
}
