import { useEffect } from 'react';

import Box from '@mui/material/Box';

import { useAnalytics } from 'src/hooks';
import { paths } from 'src/routes/paths';
import { PaletteAnchors } from 'src/sections/palette/PaletteAnchors';
import { PaletteContrast } from 'src/sections/palette/PaletteContrast';
import { PaletteGrid } from 'src/sections/palette/PaletteGrid';
import { PaletteHero } from 'src/sections/palette/PaletteHero';
import { PaletteHistory } from 'src/sections/palette/PaletteHistory';
import { PaletteSnippets } from 'src/sections/palette/PaletteSnippets';
import { usePaletteData } from 'src/sections/palette/usePaletteData';
import { usePaletteState } from 'src/sections/palette/usePaletteState';

export function PalettePage() {
  const { trackPageview } = useAnalytics();
  const {
    lang,
    setLang,
    oklch,
    setOklch,
    compareId,
    setCompareId,
    sort,
    setSort,
    copiedHex,
    wheelOpen,
    setWheelOpen,
    copyHex,
  } = usePaletteState();

  useEffect(() => {
    trackPageview(paths.palette);
  }, [trackPageview]);

  const { sortedPalette, imprintDots, overlayDots } = usePaletteData(sort, compareId);

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
        <PaletteHero
          wheelOpen={wheelOpen}
          setWheelOpen={setWheelOpen}
          compareId={compareId}
          setCompareId={setCompareId}
          imprintDots={imprintDots}
          overlayDots={overlayDots}
        />

        <PaletteGrid
          sort={sort}
          setSort={setSort}
          sortedPalette={sortedPalette}
          copiedHex={copiedHex}
          copyHex={copyHex}
        />

        <PaletteAnchors copiedHex={copiedHex} copyHex={copyHex} />

        <PaletteSnippets
          lang={lang}
          setLang={setLang}
          oklch={oklch}
          setOklch={setOklch}
          sortedPalette={sortedPalette}
        />

        <PaletteContrast />

        <PaletteHistory />
      </Box>
    </>
  );
}
