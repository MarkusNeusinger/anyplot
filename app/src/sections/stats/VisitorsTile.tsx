/**
 * The stats page's "visitors" tile: per UTC day of the last 28, the visits with a second page
 * or an interaction, from Plausible (`GET /insights/visitors`, `visitors.ts`).
 *
 * - Bars: one per day, the day's engaged visits, drawn like the two tiles below it (`DayStrip`).
 *   Those are the visits Plausible does not count as bounced. A crawler farm that runs the
 *   page's scripts loads one page per visit, so it shows in the number of all visits and not in
 *   the bars.
 * - A day before the counting began has no number: it draws the floor and says so, not "0".
 *   Until the window has moved past that day, the header names it in place of "last 28 days".
 * - Below: all visits of the same days as one plain line, with a hint on the word "all" that
 *   says what else is in that number.
 * - An answer without engaged visits (an API revision older than the page) draws the unique
 *   visitors per day, as the tile did before.
 * - Loading and an answer without days are one muted line each.
 */

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DayStrip } from 'src/sections/stats/DayStrip';
import { HintTerm } from 'src/sections/stats/HintTerm';
import { CHART_PX } from 'src/sections/stats/stripGeometry';
import { ALL_VISITS_HINT, engagedDays, type VisitorsAnswer } from 'src/sections/stats/visitors';
import { fontSize, semanticColors, typography } from 'src/theme';

const smallSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xxs,
  color: semanticColors.mutedText,
} as const;

const visits = (n: number): string => (n === 1 ? 'visit' : 'visits');
const visitors = (n: number): string => (n === 1 ? 'visitor' : 'visitors');

export interface VisitorsTileProps {
  /** `null` while loading. */
  answer: VisitorsAnswer | null;
  formatNum: (value: number) => string;
}

export function VisitorsTile({ answer, formatNum }: VisitorsTileProps) {
  const points = answer?.points ?? [];
  const engaged = engagedDays(points);
  const since = answer?.engagedSince ?? null;

  let header = 'unique visitors · last 28 days';
  if (engaged) {
    // The window still holds days from before the counting began: name the day it began.
    const span = engaged.wholeWindow || !since ? 'last 28 days' : `since ${since}`;
    header = `visits with a second page or an interaction · ${span} · ${formatNum(engaged.engaged)} total`;
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
                description:
                  point.engaged === null
                    ? // A day before the counting began says so. A later day without a number
                      // is one whose answer had no bounce rate.
                      since && point.date < since
                      ? `not counted before ${since}`
                      : 'not counted'
                    : undefined,
              }))}
              label="visits with a second page or an interaction per day"
              describe={n => `${n} ${visits(n)}`}
              testId="visitors"
            />
            <Box
              component="ul"
              sx={{ ...smallSx, listStyle: 'none', m: 0, mt: 0.75, p: 0, lineHeight: 1.6 }}
            >
              <li data-testid="visitors-all">
                <HintTerm hint={ALL_VISITS_HINT} testId="visitors-all-term">
                  all
                </HintTerm>{' '}
                visits: {formatNum(engaged.visits)}
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
