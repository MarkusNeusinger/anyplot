import { useEffect, useMemo, useState } from 'react';
import { API_URL } from '../constants';
import type { PlotImage } from '../types';
import { useAppData } from './useLayoutContext';


export interface FeaturedImpl {
  spec_id: string;
  spec_title: string;
  spec_description: string | null;
  library_id: string;
  language: string;
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
    fetch(`${API_URL}/plots/filter`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { images?: PlotImage[] } | null) => {
        if (cancelled || !data?.images) return;
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

    const candidates = specsData.filter((spec) => imagesBySpec[spec.id]?.length);
    const shuffled = [...candidates].sort(() => Math.random() - 0.5).slice(0, count);

    return shuffled.map((spec) => {
      const impls = imagesBySpec[spec.id];
      const pick = impls[Math.floor(Math.random() * impls.length)];
      return {
        spec_id: spec.id,
        spec_title: spec.title,
        spec_description: spec.description ?? null,
        library_id: pick.library,
        language: pick.language,
        preview_url: pick.url ?? null,
      };
    });
  }, [images, specsData, count]);
}
