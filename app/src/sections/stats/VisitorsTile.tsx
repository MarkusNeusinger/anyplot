/**
 * The stats page's "visitors" tile: per day of the last 28, the unique visitors who stayed ten
 * seconds and did something, from Plausible (`GET /insights/visitors`, `visitors.ts`). The days
 * are the Plausible site's (Europe/Zurich), not UTC days.
 *
 * - Bars: one per day, the day's engaged visitors, drawn like the two tiles below it
 *   (`DayStrip`). Those had the site in front of them for ten seconds of a visit and used a
 *   pointer, a finger or a key in it, before the ten seconds or after them. A crawler farm that
 *   runs the page's scripts seldom stays ten seconds and does nothing when it does, so it shows
 *   in the number of all visitors and not in the bars.
 * - Below: all unique visitors of the same days as one plain line, with a hint on the word "all"
 *   that says what else is in that number.
 * - Until every day of the window is counted (`engagedDays`), the tile draws the unique
 *   visitors per day, as it did before: a strip that is empty for most of its days says less
 *   than the one it replaces. The same holds for an answer without engaged visitors, from an API
 *   revision older than the page or from a day the API could not count them. The switch happens
 *   by itself on the day the window's first day is the one the counting began.
 * - A day inside a counted window that has no number draws the floor and says "not counted",
 *   not "0".
 * - Loading and an answer without days are one muted line each.
 */

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DayStrip } from 'src/sections/stats/DayStrip';
import { HintTerm } from 'src/sections/stats/HintTerm';
import { CHART_PX } from 'src/sections/stats/stripGeometry';
import { ALL_VISITORS_HINT, engagedDays, type VisitorsAnswer } from 'src/sections/stats/visitors';
import { fontSize, semanticColors, typography } from 'src/theme';

const smallSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xxs,
  color: semanticColors.mutedText,
} as const;

const visitors = (n: number): string => (n === 1 ? 'visitor' : 'visitors');

/** What the bars count once every day of the window is counted. */
const ENGAGED = 'visitors who stayed ten seconds and did something';

export interface VisitorsTileProps {
  /** `null` while loading. */
  answer: VisitorsAnswer | null;
  formatNum: (value: number) => string;
}

export function VisitorsTile({ answer, formatNum }: VisitorsTileProps) {
  const points = answer?.points ?? [];
  const engaged = answer ? engagedDays(answer) : null;

  let header = 'unique visitors · last 28 days';
  if (engaged) {
    header = `${ENGAGED} · last 28 days · ${formatNum(engaged.engaged)} total`;
  } else if (points.length > 0) {
    header += ` · ${formatNum(points.reduce((sum, point) => sum + point.visitors, 0))} total`;
  }

  return (
    <>
      {/* `plausible.view()` sits in the section header's link slot, like `libraries.all()` and
          `map.explore()` across the site. */}
      <Box sx={{ mt: 4 }}>
        <SectionHeader
          prompt="❯"
          title={<em>visitors</em>}
          linkText="plausible.view()"
          linkHref="https://plausible.io/anyplot.ai"
        />
      </Box>
      <Box sx={{ mt: 1, mb: 3 }}>
        <Typography
          data-testid="visitors-header"
          sx={{
            fontFamily: typography.fontFamily,
            fontSize: fontSize.xs,
            color: semanticColors.mutedText,
            mb: 0.5,
          }}
        >
          {header}
        </Typography>
        {answer === null ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>loading visitor data...</Typography>
          </Box>
        ) : points.length === 0 ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>
              visitor data unavailable — see plausible.io/anyplot.ai
            </Typography>
          </Box>
        ) : engaged ? (
          <>
            <DayStrip
              days={points.map(point => ({
                date: point.date,
                value: point.engaged ?? 0,
                description: point.engaged === null ? 'not counted' : undefined,
              }))}
              label={`${ENGAGED} per day`}
              describe={n => `${n} ${visitors(n)}`}
              testId="visitors"
            />
            <Box
              component="ul"
              sx={{ ...smallSx, listStyle: 'none', m: 0, mt: 0.75, p: 0, lineHeight: 1.6 }}
            >
              <li data-testid="visitors-all">
                <HintTerm hint={ALL_VISITORS_HINT} testId="visitors-all-term">
                  all
                </HintTerm>{' '}
                visitors: {formatNum(engaged.visitors)}
              </li>
            </Box>
          </>
        ) : (
          <DayStrip
            days={points.map(point => ({ date: point.date, value: point.visitors }))}
            label="unique visitors per day"
            describe={n => `${n} ${visitors(n)}`}
            testId="visitors"
          />
        )}
      </Box>
    </>
  );
}
