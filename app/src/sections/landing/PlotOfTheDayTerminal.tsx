import { useContext } from 'react';

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';

import { RetryButton } from 'src/components/RetryButton';
import { GITHUB_URL } from 'src/constants';
import { useAnalytics } from 'src/hooks';
import { useAgentEligibility } from 'src/hooks/useAgentEligibility';
import { useTheme } from 'src/hooks/useLayoutContext';
import { type PlotOfTheDayData, PlotOfTheDayLoadContext } from 'src/hooks/usePlotOfTheDay';
import { agentChatPath, specPath } from 'src/routes/paths';
import { USE_MY_DATA_LABEL } from 'src/sections/spec-detail/LibraryPills';
import { colors, typography } from 'src/theme';
import { buildSrcSet, getFallbackSrc } from 'src/utils/responsiveImage';
import { selectPreviewUrl } from 'src/utils/themedPreview';

/** `agent_open{source}` for the chat opened from this card (`docs/reference/plausible.md`). */
const AGENT_SOURCE = 'plot_of_the_day';

/** The line in the reserved frame once the request still failed after apiGet's retries. */
export const POTD_LOAD_ERROR = 'plot of the day did not load';

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

/** The prompt header: `$ runner filename` on the left, the actions on the right. */
const headerSx = {
  display: 'flex',
  flexWrap: 'wrap',
  alignItems: 'center',
  gap: 0.75,
  px: { xs: 2, md: 3 },
  pt: { xs: 2.5, md: 3 },
  pb: 1.5,
  color: 'var(--ink-muted)',
  fontSize: '12px',
} as const;

/** The status footer: `>>> title · library`, and `// plot of the day` at the right. */
const footerSx = {
  display: 'flex',
  alignItems: 'center',
  gap: 1.5,
  flexWrap: 'wrap',
  px: { xs: 2, md: 3 },
  py: 1.5,
  fontSize: '11px',
  color: 'var(--ink-muted)',
} as const;

/** The 16:10 plot frame between the dashed rules, capped at `maxPlotHeight`. */
function plotFrameSx(maxPlotHeight: string) {
  return {
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
  } as const;
}

/**
 * Terminal-framed plot-of-the-day card.
 *
 * Looks like a terminal window rendered on the editorial paper: thin border,
 * `~/anyplot` tab label, green prompt + filename header, plot image as console
 * output, status footer. Fills its container by default so parents control width.
 *
 * Until the plot of the day is there to show, it renders the same frame empty, so
 * the box is reserved and the content below it does not jump down when the plot
 * arrives (in the one-column layout of a tablet the card sits above the numbers).
 * If the request fails, the frame stays and says so, with a `.retry()`; the request's
 * status comes from `PlotOfTheDayLoadContext`, which the landing page provides.
 */
export function PlotOfTheDayTerminal({
  potd,
  sizes = '(max-width: 899px) 86vw, 1200px',
  maxWidth = '100%',
  maxPlotHeight = '55vh',
}: PlotOfTheDayTerminalProps) {
  const { isDark } = useTheme();
  const { trackEvent } = useAnalytics();
  const load = useContext(PlotOfTheDayLoadContext);
  // `.use_my_data()` for the plot of the day: one eligibility request per view, as on the
  // spec pages; no entry while it probes, for a closed lane, or for an ineligible pair.
  const agentLane = useAgentEligibility(potd?.spec_id, potd?.library_id);
  const previewUrl = selectPreviewUrl(potd, isDark);
  // The root keeps the same element and styles in both states, so React keeps its node
  // and the `rise` entrance does not play a second time when the plot arrives.
  const frameSx = {
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
  } as const;

  if (!potd || !previewUrl) {
    // An answer without a plot to show will not change on its own: no card, as before the
    // frame was reserved.
    if (load.status === 'none' || potd) return null;
    // A failed request keeps the frame, so the content below does not move up, and says so
    // inside the 16:10 box, with a `.retry()`.
    const retry = load.status === 'failed' ? load.retry : undefined;
    return (
      <Box
        sx={frameSx}
        aria-hidden={retry ? undefined : 'true'}
        data-testid="potd-terminal-placeholder"
      >
        <Box sx={headerSx} aria-hidden="true">
          <Box component="span" sx={{ color: colors.primary, fontWeight: 700 }}>
            $
          </Box>
        </Box>
        <Box
          sx={{
            ...plotFrameSx(maxPlotHeight),
            bgcolor: 'var(--bg-elevated)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {retry && (
            <Box
              role="alert"
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1.5,
                px: 2,
              }}
            >
              <Box component="span" sx={{ fontSize: '12px', color: 'var(--ink-muted)' }}>
                {POTD_LOAD_ERROR}
              </Box>
              <RetryButton onClick={retry} label="Retry loading the plot of the day" />
            </Box>
          )}
        </Box>
        <Box sx={footerSx} aria-hidden="true">
          <Box component="span" sx={{ color: colors.primary }}>
            &gt;&gt;&gt;
          </Box>
          <Box sx={{ flex: 1 }} />
          <Box component="span" sx={{ opacity: 0.8 }}>
            // plot of the day
          </Box>
        </Box>
      </Box>
    );
  }

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
  // One chat page for visitors and admins, an ordinary route: the lane only picked the API the
  // eligibility was asked of, and the chat picks its own (`AgentChatPage`). It records `agent_open`.
  const agentLink = agentLane
    ? {
        component: RouterLink,
        to: agentChatPath(potd.spec_id, potd.library_id, potd.language, AGENT_SOURCE),
      }
    : null;

  return (
    <Box sx={frameSx}>
      {/* Prompt header — the filename links to the raw source on GitHub */}
      <Box sx={headerSx}>
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
          ...plotFrameSx(maxPlotHeight),
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
      <Box sx={footerSx}>
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
