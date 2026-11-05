import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { GITHUB_URL } from 'src/constants';
import { useAnalytics } from 'src/hooks';
import { useAgentEligibility } from 'src/hooks/useAgentEligibility';
import { useTheme } from 'src/hooks/useLayoutContext';
import type { PlotOfTheDayData } from 'src/hooks/usePlotOfTheDay';
import { agentChatPath, publicAgentChatPath, specPath } from 'src/routes/paths';
import { USE_MY_DATA_LABEL } from 'src/sections/spec-detail/LibraryPills';
import { colors, typography } from 'src/theme';
import { buildSrcSet, getFallbackSrc } from 'src/utils/responsiveImage';
import { selectPreviewUrl } from 'src/utils/themedPreview';

/** `agent_open{source}` for the chat opened from this card (`docs/reference/plausible.md`). */
const AGENT_SOURCE = 'plot_of_the_day';

/** A text action in the prompt header, beside the filename: muted, green on hover. */
const headerActionSx = {
  flexShrink: 0,
  whiteSpace: 'nowrap',
  color: 'inherit',
  textDecoration: 'none',
  transition: 'color 0.2s',
  '&:hover': { color: colors.primary },
  '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
} as const;

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
  // `.use_my_data()` for the plot of the day: one eligibility request per view, as on the
  // spec pages; no entry while it probes, for a closed lane, or for an ineligible pair.
  const agentLane = useAgentEligibility(potd?.spec_id, potd?.library_id);
  const previewUrl = selectPreviewUrl(potd, isDark);
  if (!potd || !previewUrl) return null;

  // File extension + runner command follow the implementation language:
  // - ggplot2 (R) ships as .R + Rscript
  // - makie (Julia) ships as .jl + `julia --project=.`
  // - chartjs/d3/echarts/highcharts (JavaScript) ship as .js + node (browser render harness)
  // - muix (React/MUI X) is the .tsx exception within JavaScript, still + node
  // - every Python library as .py + python
  const ext =
    potd.library_id === 'muix'
      ? '.tsx'
      : potd.language === 'r'
        ? '.R'
        : potd.language === 'julia'
          ? '.jl'
          : potd.language === 'javascript'
            ? '.js'
            : '.py';
  const runner =
    potd.language === 'r'
      ? 'Rscript'
      : potd.language === 'julia'
        ? 'julia --project=.'
        : potd.language === 'javascript'
          ? 'node'
          : 'python';
  const displayFilename = `plots/${potd.spec_id}/${potd.library_id}${ext}`;
  const implPath = specPath(potd.spec_id, potd.language, potd.library_id);
  const githubFileUrl = `${GITHUB_URL}/blob/main/plots/${potd.spec_id}/implementations/${potd.language}/${potd.library_id}${ext}`;
  // The public chat is an ordinary route; the admin chat needs a full page load so
  // Cloudflare Access can intercept the /debug path. The chat records `agent_open`.
  const agentLink =
    agentLane === 'public'
      ? {
          component: RouterLink,
          to: publicAgentChatPath(potd.spec_id, potd.library_id, potd.language, AGENT_SOURCE),
        }
      : agentLane === 'admin'
        ? {
            component: 'a' as const,
            href: agentChatPath(potd.spec_id, potd.library_id, potd.language, AGENT_SOURCE),
          }
        : null;

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
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 0.75,
          px: { xs: 2, md: 3 },
          pt: { xs: 2.5, md: 3 },
          pb: 1.5,
          color: 'var(--ink-muted)',
          fontSize: '12px',
        }}
      >
        <Box component="span" sx={{ color: colors.primary, fontWeight: 700 }}>
          $
        </Box>
        <Box component="span">{runner}</Box>
        <Box
          component="a"
          href={githubFileUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() =>
            trackEvent('nav_click', {
              source: 'potd_terminal_filename',
              target: 'github',
              spec: potd.spec_id,
              library: potd.library_id,
            })
          }
          sx={{
            flex: 1,
            minWidth: 0,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            color: 'inherit',
            // Use text-decoration rather than border-bottom so the underline
            // only covers the glyphs (ending at the filename) and not the
            // stretched flex child.
            textDecoration: 'none',
            transition: 'color 0.2s, text-decoration-color 0.2s',
            '&:hover': {
              color: colors.primary,
              textDecoration: 'underline dotted',
              textUnderlineOffset: '3px',
            },
          }}
        >
          {displayFilename}
        </Box>
        {/* The actions. With `.use_my_data()` beside it, the pair takes its own line on a
            phone, right-aligned below the filename, so the filename keeps its width. */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 1.75,
            ml: 'auto',
            flexBasis: agentLink ? { xs: '100%', sm: 'auto' } : 'auto',
          }}
        >
          {agentLink && (
            <Box
              {...agentLink}
              aria-label={USE_MY_DATA_LABEL}
              sx={{
                ...headerActionSx,
                animation: 'useMyDataFadeIn 0.3s ease-out',
                '@keyframes useMyDataFadeIn': { from: { opacity: 0 }, to: { opacity: 1 } },
                '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
              }}
            >
              .use_my_data()
            </Box>
          )}
          <Box
            component="a"
            href={githubFileUrl}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open source on GitHub"
            onClick={() =>
              trackEvent('nav_click', {
                source: 'potd_terminal_github',
                target: 'github',
                spec: potd.spec_id,
                library: potd.library_id,
              })
            }
            sx={{
              color: 'inherit',
              textDecoration: 'none',
              transition: 'color 0.2s',
              '& .gh-subject': { opacity: 0.7, transition: 'opacity 0.2s' },
              '&:hover': { color: colors.primary },
              '&:hover .gh-subject': { opacity: 1 },
            }}
          >
            <Box component="span" className="gh-subject">
              github
            </Box>
            .open()
          </Box>
        </Box>
      </Box>

      {/* Plot image — 16:10 frame, contain so square plots are letterboxed.
          Click anywhere on the image to open the implementation detail page. */}
      <Box
        component={RouterLink}
        to={implPath}
        aria-label={`Open ${potd.spec_title} implementation for ${potd.library_name}`}
        onClick={() =>
          trackEvent('nav_click', {
            source: 'potd_terminal_image',
            target: 'spec_detail',
            spec: potd.spec_id,
            library: potd.library_id,
          })
        }
        sx={{
          display: 'block',
          mx: 'auto',
          width: { xs: 'calc(100% - 32px)', md: 'calc(100% - 48px)' },
          maxWidth: `calc(${maxPlotHeight} * 1.6)`,
          maxHeight: maxPlotHeight,
          borderTop: '1px dashed var(--rule)',
          borderBottom: '1px dashed var(--rule)',
          bgcolor: 'var(--bg-surface)',
          aspectRatio: '16 / 10',
          position: 'relative',
          overflow: 'hidden',
          cursor: 'pointer',
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
        <Box component="span" sx={{ color: colors.primary }}>
          &gt;&gt;&gt;
        </Box>
        <Box component="span" sx={{ color: 'var(--ink-soft)' }}>
          {potd.spec_title}
        </Box>
        <Box component="span">·</Box>
        <Box component="span">{potd.library_name}</Box>
        <Box sx={{ flex: 1 }} />
        <Box component="span" sx={{ opacity: 0.8 }}>
          // plot of the day
        </Box>
      </Box>
    </Box>
  );
}
