import { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';

import { useAnalytics, useTheme } from 'src/hooks';
import { type Lang, PALETTE, type Swatch } from 'src/pages/PalettePage.helpers';
import { paths } from 'src/routes/paths';
import { ContinuousCmapsSection } from 'src/sections/palette/ContinuousCmapsSection';
import { CopySnippetsSection } from 'src/sections/palette/CopySnippetsSection';
import { DeltaESection } from 'src/sections/palette/DeltaESection';
import { HeroSection } from 'src/sections/palette/HeroSection';
import { LineageSection } from 'src/sections/palette/LineageSection';
import { PaletteGridSection } from 'src/sections/palette/PaletteGridSection';
import { COMPARISONS } from 'src/sections/palette/paletteHelpers';
import { SemanticAnchorsSection } from 'src/sections/palette/SemanticAnchorsSection';
import type { WheelDot } from 'src/sections/palette/types';
import { WcagContrastSection } from 'src/sections/palette/WcagContrastSection';

// ─────────────────────────────────────────────────────────────────────────────
// Imprint palette — 8 categorical hues + OKLCH coords for the wheel
// ─────────────────────────────────────────────────────────────────────────────

/** Pure-CVD-greedy max-min sort — picks each next slot to maximise ΔE under CVD
 *  against the already-placed set. Best discrimination at n=3..6 but groups
 *  two greens (slot 7 lime + slot 0 brand) and two purples (slot 1 lavender +
 *  slot 3 rose) close together. Order: [brand, lavender, lime, rose, red, cyan, blue, ochre]. */
const CVD_OPTIMAL_ORDER: number[] = [0, 1, 7, 6, 4, 5, 2, 3];

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export function PalettePage() {
  const { trackPageview } = useAnalytics();
  const { isDark } = useTheme();
  const [lang, setLang] = useState<Lang>('python');
  const [oklch, setOklch] = useState(false);
  const [compareId, setCompareId] = useState<string | null>(null);
  /** `imprint` = hybrid-v3 (default, 4 hue families up front).
   *  `cvd` = pure-CVD-greedy max-min (best per-n ΔE under CVD, but groups
   *  two greens + two purples close together in the first 4 slots). */
  const [sort, setSort] = useState<'imprint' | 'cvd'>('imprint');
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  /** Hero wheel: collapsed = small preview; expanded = larger + comparison toggles. */
  const [wheelOpen, setWheelOpen] = useState(false);

  const copyHex = (hex: string) => {
    void navigator.clipboard
      .writeText(hex)
      .then(() => {
        setCopiedHex(hex);
        setTimeout(() => setCopiedHex(c => (c === hex ? null : c)), 1500);
      })
      .catch(() => {
        // Silently ignore — clipboard API can fail in insecure contexts.
      });
  };

  useEffect(() => {
    trackPageview(paths.palette);
  }, [trackPageview]);

  const sortedPalette: Swatch[] = useMemo(
    () => (sort === 'imprint' ? PALETTE : CVD_OPTIMAL_ORDER.map(i => PALETTE[i])),
    [sort]
  );

  // Wheel dots are positioned by hue + chroma, independent of sort order —
  // we keep the canonical PALETTE order so the brand-green outline stays on
  // the same identity dot regardless of sort.
  const imprintDots: WheelDot[] = useMemo(
    () => PALETTE.map(s => ({ hex: s.hex, L: s.L, C: s.C, H: s.H, name: s.name })),
    []
  );
  const overlayDots: WheelDot[] | undefined = useMemo(
    () => COMPARISONS.find(c => c.id === compareId)?.hexes,
    [compareId]
  );

  return (
    <>
      <>
        <title>imprint palette | anyplot.ai</title>
        <meta
          name="description"
          content="imprint — anyplot's categorical palette: 8 colorblind-safe hues plus 3 semantic anchors (amber, neutral, muted), tuned for warm-paper rendering and validated against deuteranopia / protanopia / tritanopia."
        />
        <meta property="og:title" content="imprint palette | anyplot.ai" />
        <meta
          property="og:description"
          content="imprint — anyplot's colorblind-safe categorical palette: 8 hues plus 3 semantic anchors."
        />
        <link rel="canonical" href="https://anyplot.ai/palette" />
      </>

      <Box sx={{ pb: 4 }}>
        {/* 1. HERO — short lede + a compact hue–chroma wheel. Click the wheel to
            enlarge it and reveal the palette-comparison toggles. */}
        <HeroSection
          wheelOpen={wheelOpen}
          setWheelOpen={setWheelOpen}
          imprintDots={imprintDots}
          overlayDots={overlayDots}
          compareId={compareId}
          setCompareId={setCompareId}
        />

        {/* 2. PALETTE GRID + SORT TOGGLE */}
        <PaletteGridSection
          sort={sort}
          setSort={setSort}
          sortedPalette={sortedPalette}
          copiedHex={copiedHex}
          copyHex={copyHex}
        />

        {/* 3. SEMANTIC ANCHORS */}
        <SemanticAnchorsSection copiedHex={copiedHex} copyHex={copyHex} />

        {/* 3b. CONTINUOUS CMAPS — sequential + diverging */}
        <ContinuousCmapsSection />

        {/* 4. COPY SNIPPETS */}
        <CopySnippetsSection
          lang={lang}
          setLang={setLang}
          oklch={oklch}
          setOklch={setOklch}
          sortedPalette={sortedPalette}
        />

        {/* 5. CONTRAST (WCAG) */}
        <WcagContrastSection isDark={isDark} />

        {/* 6. ΔE COLOUR DISTANCE — pairwise distances generated by
            scripts/palette-matrix-export.py (CAM02-UCS + Machado-2009 CVD). */}
        <DeltaESection />

        {/* 7. HISTORY */}
        <LineageSection />
      </Box>
    </>
  );
}
