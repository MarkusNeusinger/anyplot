import { useMemo } from 'react';

import { PALETTE, type Swatch } from 'src/pages/PalettePage.helpers';

import { COMPARISONS, CVD_OPTIMAL_ORDER, type WheelDot } from './constants';

export function usePaletteData(sort: 'imprint' | 'cvd', compareId: string | null) {
  const sortedPalette: Swatch[] = useMemo(
    () => (sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i])),
    [sort]
  );
  const imprintDots: WheelDot[] = useMemo(
    () => PALETTE.map(s => ({ hex: s.hex, L: s.L, C: s.C, H: s.H, name: s.name })),
    []
  );
  const overlayDots: WheelDot[] | undefined = useMemo(
    () => COMPARISONS.find(c => c.id === compareId)?.hexes,
    [compareId]
  );
  return { sortedPalette, imprintDots, overlayDots };
}
