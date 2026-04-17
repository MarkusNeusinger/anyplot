import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';

import { colors, typography } from '../theme';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import { specPath } from '../utils/paths';
import type { PlotOfTheDayData } from '../hooks/usePlotOfTheDay';

interface PlotOfTheDayTerminalProps {
  potd: PlotOfTheDayData | null;
  /** Sizes attribute for the responsive picture sources. */
  sizes?: string;
  /** Optional max-width override (defaults to `100%`, i.e. fills parent). */
  maxWidth?: number | string;
  /**
   * Hard cap on the plot frame height. With `aspectRatio: 16/10` this also
   * caps the width via `calc(height * 1.6)`. Use viewport units so the hero
   * always fits one screen. Default `55vh`.
   */
  maxPlotHeight?: string;
}

/**
 * Terminal-framed plot-of-the-day card.
 *
 * Looks like a terminal window rendered on the editorial paper: thin border,
 * `~/anyplot` tab label, green prompt + filename header, plot image as console
 * output, status footer. Fills its container by default so parents control width.
 */
export function PlotOfTheDayTerminal({
  potd,
  sizes = '(max-width: 899px) 86vw, 1200px',
  maxWidth = '100%',
  maxPlotHeight = '55vh',
}: PlotOfTheDayTerminalProps) {
  if (!potd?.preview_url) return null;

  const filename = `plots/${potd.spec_id}/${potd.library_id}.py`;

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        maxWidth,
        border: '1px solid var(--ink-muted)',
        borderRadius: '6px',
        bgcolor: 'var(--bg-surface)',
        fontFamily: typography.mono,
        animation: 'rise 1s cubic-bezier(0.2, 0.8, 0.2, 1) 0.3s backwards',
        '&::before': {
          content: '"~/anyplot"',
          position: 'absolute',
          top: '-0.7em',
          left: 24,
          px: 1.25,
          bgcolor: 'var(--bg-page)',
          fontFamily: typography.mono,
          fontSize: '12px',
          color: 'var(--ink-muted)',
          letterSpacing: '0.05em',
        },
      }}
    >
      {/* Prompt header */}
      <Box
        component={RouterLink}
        to={specPath(potd.spec_id, potd.library_id)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
          px: { xs: 2, md: 3 },
          pt: { xs: 2.5, md: 3 },
          pb: 1.5,
          textDecoration: 'none',
          color: 'var(--ink-muted)',
          fontSize: '12px',
          transition: 'color 0.2s',
          '&:hover': { color: colors.primary },
        }}
      >
        <Box component="span" sx={{ color: colors.primary, fontWeight: 700 }}>$</Box>
        <Box
          component="span"
          sx={{
            flex: 1,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          python {filename}
        </Box>
        <Box component="span" sx={{ fontSize: '11px' }}>↗ open</Box>
      </Box>

      {/* Plot image — 16:10 frame, contain so square plots are letterboxed */}
      <Box
        sx={{
          mx: 'auto',
          width: { xs: 'calc(100% - 32px)', md: 'calc(100% - 48px)' },
          maxWidth: `calc(${maxPlotHeight} * 1.6)`,
          maxHeight: maxPlotHeight,
          borderTop: '1px dashed var(--rule)',
          borderBottom: '1px dashed var(--rule)',
          bgcolor: 'var(--bg-elevated)',
          aspectRatio: '16 / 10',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Box
          component="picture"
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <source type="image/webp" srcSet={buildSrcSet(potd.preview_url, 'webp')} sizes={sizes} />
          <source type="image/png" srcSet={buildSrcSet(potd.preview_url, 'png')} sizes={sizes} />
          <Box
            component="img"
            src={getFallbackSrc(potd.preview_url)}
            alt={`${potd.spec_title} — ${potd.library_name}`}
            sx={{
              maxWidth: '100%',
              maxHeight: '100%',
              width: 'auto',
              height: 'auto',
              display: 'block',
              objectFit: 'contain',
            }}
          />
        </Box>
      </Box>

      {/* Status footer */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          flexWrap: 'wrap',
          px: { xs: 2, md: 3 },
          py: 1.5,
          fontSize: '11px',
          color: 'var(--ink-muted)',
        }}
      >
        <Box component="span" sx={{ color: colors.primary }}>&gt;&gt;&gt;</Box>
        <Box component="span" sx={{ color: 'var(--ink-soft)' }}>{potd.spec_title}</Box>
        <Box component="span">·</Box>
        <Box component="span">{potd.library_name}</Box>
        <Box sx={{ flex: 1 }} />
        <Box component="span" sx={{ opacity: 0.8 }}>// plot of the day</Box>
      </Box>
    </Box>
  );
}
