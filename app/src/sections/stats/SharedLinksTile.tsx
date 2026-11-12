/**
 * The stats page's "shared links" tile: per UTC day of the last 28, how often a link to the
 * site was shared, counted from the preview images that messengers and social networks fetch
 * (`GET /insights/shared-links`, `sharedLinks.ts`).
 *
 * - Bars: one per day, the day's sum of shares, drawn like the visitors strip and the machine
 *   readers tile above it (`DayStrip`).
 * - Below: the window's sums as short lines. The shares by platform, and the most shared plot
 *   pages as links. A spec's hub and one implementation of it are entries of their own.
 * - What a share is and what the count cannot see is on the legal page the header links.
 * - Loading, a failed request and any answer but `ok` are one muted line each.
 */

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { paths, specPath } from 'src/routes/paths';
import { DayStrip } from 'src/sections/stats/DayStrip';
import {
  platformLabel,
  type SharedLinksPlot,
  type SharedLinksResponse,
} from 'src/sections/stats/sharedLinks';
import { CHART_PX } from 'src/sections/stats/stripGeometry';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

const shares = (n: number): string => (n === 1 ? 'share' : 'shares');

const smallSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xxs,
  color: semanticColors.mutedText,
} as const;

/** The page a list entry leads to, and how it is named: `scatter-basic` or `scatter-basic · matplotlib`. */
const plotPath = (plot: SharedLinksPlot): string =>
  plot.language && plot.library
    ? specPath(plot.spec_id, plot.language, plot.library)
    : specPath(plot.spec_id);

const plotName = (plot: SharedLinksPlot): string =>
  plot.library ? `${plot.spec_id} · ${plot.library}` : plot.spec_id;

export interface SharedLinksTileProps {
  /** `undefined` while loading, `null` when the request failed or the answer is not `ok`. */
  answer: SharedLinksResponse | null | undefined;
  formatNum: (value: number) => string;
}

export function SharedLinksTile({ answer, formatNum }: SharedLinksTileProps) {
  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader
          prompt="❯"
          title={<em>shared links</em>}
          linkText="legal.privacy()"
          linkTo={`${paths.legal}#shared-links`}
        />
      </Box>
      <Box sx={{ mt: 1, mb: 3 }}>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: semanticColors.mutedText,
            mb: 0.5,
          }}
        >
          link previews on messengers and social networks · last 28 days
          {answer ? ` · ${formatNum(answer.total)} ${shares(answer.total)}` : ''}
        </Typography>
        {answer === undefined ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>loading shared link data...</Typography>
          </Box>
        ) : answer === null ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>shared link data unavailable</Typography>
          </Box>
        ) : (
          <>
            <DayStrip
              days={answer.days.map(day => ({ date: day.date, value: day.shares }))}
              label="shared links per day"
              describe={n => `${n} ${shares(n)}`}
              testId="shared-links"
            />
            <SharedLinksSums answer={answer} formatNum={formatNum} />
          </>
        )}
      </Box>
    </>
  );
}

/** The window's sums under the strip; a window without a share has none. */
function SharedLinksSums({
  answer,
  formatNum,
}: {
  answer: SharedLinksResponse;
  formatNum: (value: number) => string;
}) {
  const { platforms, top } = answer;
  if (platforms.length === 0 && top.length === 0) return null;

  return (
    <Box
      component="ul"
      sx={{ ...smallSx, listStyle: 'none', m: 0, mt: 0.75, p: 0, lineHeight: 1.6 }}
    >
      {platforms.length > 0 && (
        <li data-testid="shared-links-platforms">
          by platform:{' '}
          {platforms
            .map(entry => `${platformLabel(entry.platform)} ${formatNum(entry.shares)}`)
            .join(' · ')}
        </li>
      )}
      {top.length > 0 && (
        <li data-testid="shared-links-top">
          most shared:{' '}
          {top.map((plot, index) => (
            <span key={plotPath(plot)}>
              {index > 0 && ' · '}
              <Box
                component={RouterLink}
                to={plotPath(plot)}
                sx={{
                  fontFamily: typography.mono,
                  color: 'var(--ink)',
                  textDecoration: 'none',
                  '&:hover': { color: colors.primary, textDecoration: 'underline' },
                  '&:focus-visible': {
                    outline: `2px solid ${colors.primary}`,
                    outlineOffset: 2,
                    borderRadius: '2px',
                  },
                }}
              >
                {plotName(plot)}
              </Box>{' '}
              {formatNum(plot.shares)}
            </span>
          ))}
        </li>
      )}
    </Box>
  );
}
