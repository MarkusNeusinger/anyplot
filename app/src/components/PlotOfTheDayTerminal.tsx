import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';

import { GITHUB_URL } from '../constants';
import { colors, typography } from '../theme';
import { buildSrcSet, getFallbackSrc } from '../utils/responsiveImage';
import { selectPreviewUrl } from '../utils/themedPreview';
import { useTheme } from '../hooks/useLayoutContext';
import { useAnalytics } from '../hooks';
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
  const { isDark } = useTheme();
  const { trackEvent } = useAnalytics();
  const previewUrl = selectPreviewUrl(potd, isDark);
  if (!potd || !previewUrl) return null;

  const displayFilename = `plots/${potd.spec_id}/${potd.library_id}.py`;
  const implPath = specPath(potd.spec_id, potd.language, potd.library_id);
  const githubFileUrl = `${GITHUB_URL}/blob/main/plots/${potd.spec_id}/implementations/${potd.language}/${potd.library_id}.py`;

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
          content: '"~/anyplot.ai"',
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
      {/* Prompt header — the filename links to the raw source on GitHub */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
          px: { xs: 2, md: 3 },
          pt: { xs: 2.5, md: 3 },
          pb: 1.5,
          color: 'var(--ink-muted)',
          fontSize: '12px',
        }}
      >
        <Box component="span" sx={{ color: colors.primary, fontWeight: 700 }}>$</Box>
        <Box component="span">python</Box>
        <Box
          component="a"
          href={githubFileUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => trackEvent('nav_click', { source: 'potd_terminal_filename', target: 'github', spec: potd.spec_id, library: potd.library_id })}
          sx={{
            flex: 1,
            minWidth: 0,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            color: 'inherit',
            // Use text-decoration rather than border-bottom so the underline
            // only covers the glyphs (ending at `.py`) and not the stretched
            // flex child.
            textDecoration: 'none',
            transition: 'color 0.2s, text-decoration-color 0.2s',
            '&:hover': { color: colors.primary, textDecoration: 'underline dotted', textUnderlineOffset: '3px' },
          }}
        >
          {displayFilename}
        </Box>
        <Box
          component="a"
          href={githubFileUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Open source on GitHub"
          onClick={() => trackEvent('nav_click', { source: 'potd_terminal_github', target: 'github', spec: potd.spec_id, library: potd.library_id })}
          sx={{
            color: 'inherit',
            textDecoration: 'none',
            transition: 'color 0.2s',
            '& .gh-subject': { opacity: 0.7, transition: 'opacity 0.2s' },
            '&:hover': { color: colors.primary },
            '&:hover .gh-subject': { opacity: 1 },
          }}
        >
          <Box component="span" className="gh-subject">github</Box>.open()
        </Box>
      </Box>

      {/* Plot image — 16:10 frame, contain so square plots are letterboxed.
          Click anywhere on the image to open the implementation detail page. */}
      <Box
        component={RouterLink}
        to={implPath}
        aria-label={`Open ${potd.spec_title} implementation for ${potd.library_name}`}
        onClick={() => trackEvent('nav_click', { source: 'potd_terminal_image', target: 'spec_detail', spec: potd.spec_id, library: potd.library_id })}
        sx={{
          display: 'block',
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
          cursor: 'pointer',
          transition: 'background 0.2s',
          '&:hover': { bgcolor: 'var(--bg-page)' },
          '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: -2 },
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
          <source type="image/webp" srcSet={buildSrcSet(previewUrl, 'webp')} sizes={sizes} />
          <source type="image/png" srcSet={buildSrcSet(previewUrl, 'png')} sizes={sizes} />
          <Box
            component="img"
            key={previewUrl}
            src={getFallbackSrc(previewUrl)}
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
