/**
 * The stats page's "shared links" tile: per UTC day of the last 28, how often a link to the
 * site was shared, counted from the preview images that messengers and social networks fetch
 * (`GET /insights/shared-links`, `sharedLinks.ts`).
 *
 * - Bars: one column per day, the same 28-day window and geometry as the visitors strip and the
 *   machine readers tile above it (`columnPx`). One series, so one colour, the brand green,
 *   checked with the dataviz validator against both page backgrounds, and no legend swatch: the
 *   title names what the columns are. Each day's full-height column is its own hover and
 *   keyboard-focus target and tooltip.
 * - Below: the first and last date, the platforms with their totals as text, and the most
 *   shared plot pages as links. A spec's hub and one implementation of it are entries of
 *   their own.
 * - A footnote says what a share is and what the count cannot see.
 * - Loading, a failed request and any answer but `ok` are one muted line each.
 */

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { paths, specPath } from 'src/routes/paths';
import { CHART_PX, columnPx } from 'src/sections/stats/machineReaders';
import {
  platformLabel,
  type SharedLinksPlot,
  type SharedLinksResponse,
} from 'src/sections/stats/sharedLinks';
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
          <SharedLinksChart answer={answer} formatNum={formatNum} />
        )}
      </Box>
    </>
  );
}

function SharedLinksChart({
  answer,
  formatNum,
}: {
  answer: SharedLinksResponse;
  formatNum: (value: number) => string;
}) {
  const { days, platforms, top } = answer;
  const busiest = Math.max(...days.map(day => day.shares), 1);

  return (
    <>
      <Box
        role="group"
        aria-label="shared links per day"
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 0.25,
          height: CHART_PX,
          overflow: 'hidden',
        }}
      >
        {days.map(day => (
          <Tooltip key={day.date} title={`${day.date}: ${day.shares} ${shares(day.shares)}`} arrow>
            {/* Focusable, so a keyboard reaches each day's number as a pointer does; the
                Tooltip names the column (`aria-label`), which `role="img"` lets assistive
                technology read. */}
            <Box
              data-testid="shared-links-day"
              role="img"
              tabIndex={0}
              sx={{
                flex: 1,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-end',
                borderRadius: '2px 2px 0 0',
                outline: 'none',
                '&:hover, &:focus-visible': { bgcolor: 'var(--rule)' },
                '&:focus-visible': { boxShadow: `inset 0 -2px 0 ${colors.primary}` },
                transition: 'background-color 0.15s ease',
              }}
            >
              {/* A day without a share draws the strip's floor in muted ink, as the strips
                  above do, so an empty day reads as "none" and not as a gap in the data. */}
              <Box
                data-testid="shared-links-bar"
                sx={{
                  height: `${columnPx(day.shares, busiest)}px`,
                  flexShrink: 0,
                  borderRadius: '2px 2px 0 0',
                  ...(day.shares > 0
                    ? { bgcolor: colors.primary }
                    : { bgcolor: semanticColors.mutedText, opacity: 0.35 }),
                }}
              />
            </Box>
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
        <Typography sx={{ ...smallSx, fontSize: fontSize.micro }}>{days[0]?.date}</Typography>
        <Typography sx={{ ...smallSx, fontSize: fontSize.micro }}>
          {days[days.length - 1]?.date}
        </Typography>
      </Box>
      {platforms.length > 0 && (
        <Box
          data-testid="shared-links-platforms"
          sx={{
            ...smallSx,
            display: 'flex',
            flexWrap: 'wrap',
            columnGap: 1.5,
            rowGap: 0.25,
            mt: 0.75,
          }}
        >
          {platforms.map(entry => (
            <Box key={entry.platform} component="span">
              {platformLabel(entry.platform)} {formatNum(entry.shares)}
            </Box>
          ))}
        </Box>
      )}
      {top.length > 0 && (
        <Box data-testid="shared-links-top" sx={{ ...smallSx, mt: 0.75 }}>
          <Box component="span">most shared</Box>
          <Box
            component="ol"
            sx={{
              listStyle: 'none',
              m: 0,
              mt: 0.25,
              p: 0,
              display: 'flex',
              flexWrap: 'wrap',
              columnGap: 1.5,
              rowGap: 0.25,
            }}
          >
            {top.map(plot => (
              <Box key={plotPath(plot)} component="li">
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
              </Box>
            ))}
          </Box>
        </Box>
      )}
      <Typography data-testid="shared-links-footnote" sx={{ ...smallSx, mt: 0.5, lineHeight: 1.5 }}>
        a share is counted when a messenger or a social network fetches a page&apos;s preview image:
        a count per day, platform and page, nothing about who shared. a preview the platform still
        holds from an earlier share is not seen.
      </Typography>
    </>
  );
}
