/**
 * The stats page's "machine readers" tile: per UTC day of the last 28, how many requests
 * crawlers and AI assistants made that Cloudflare verified (`GET /insights/machine-readers`,
 * `machineReaders.ts`).
 *
 * - Bars: one per day, the day's sum of verified requests, drawn like the visitors strip above
 *   it (`DayStrip`).
 * - Below: the window's sums as three short lines. The verified requests by audience (for a
 *   person, AI index and training, search engines), which add up to the bars; the MCP requests,
 *   which are every client's and so stand on a line of their own; and the requests that carried
 *   a crawler's name without Cloudflare's verification, which the bars leave out. Public copy
 *   says "unverified", never "spoofed".
 * - Loading, a failed request and any answer but `ok` are one muted line each.
 */

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { paths } from 'src/routes/paths';
import { DayStrip } from 'src/sections/stats/DayStrip';
import {
  type MachineReaderPoint,
  type MachineReadersResponse,
} from 'src/sections/stats/machineReaders';
import { CHART_PX } from 'src/sections/stats/stripGeometry';
import { fontSize, semanticColors, typography } from 'src/theme';

/** The three audiences of a verified request, with the label the sums use. */
const AUDIENCES = [
  { key: 'for_person', label: 'for a person' },
  { key: 'index_training', label: 'ai index & training' },
  { key: 'search', label: 'search engines' },
] as const;

const dayTotal = (point: MachineReaderPoint): number =>
  point.for_person + point.index_training + point.search;

const requests = (n: number): string => (n === 1 ? 'request' : 'requests');

const smallSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xxs,
  color: semanticColors.mutedText,
} as const;

export interface MachineReadersTileProps {
  /** `undefined` while loading, `null` when the request failed or the answer is not `ok`. */
  answer: MachineReadersResponse | null | undefined;
  formatNum: (value: number) => string;
}

export function MachineReadersTile({ answer, formatNum }: MachineReadersTileProps) {
  const totals = answer?.totals;
  const total = totals ? totals.for_person + totals.index_training + totals.search : 0;

  return (
    <>
      <Box sx={{ mt: 4 }}>
        <SectionHeader
          prompt="❯"
          title={<em>machine readers</em>}
          linkText="legal.privacy()"
          linkTo={`${paths.legal}#machine-readers`}
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
          verified crawlers and ai assistants · last 28 days
          {answer ? ` · ${formatNum(total)} ${requests(total)}` : ''}
        </Typography>
        {answer === undefined ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>loading machine reader data...</Typography>
          </Box>
        ) : answer === null ? (
          <Box sx={{ height: CHART_PX, display: 'flex', alignItems: 'center' }}>
            <Typography sx={smallSx}>machine reader data unavailable</Typography>
          </Box>
        ) : (
          <>
            <DayStrip
              days={answer.points.map(point => ({ date: point.date, value: dayTotal(point) }))}
              label="machine readers per day"
              describe={n => `${n} ${requests(n)}`}
              testId="machine-readers"
            />
            <Box
              data-testid="machine-readers-totals"
              component="ul"
              sx={{ ...smallSx, listStyle: 'none', m: 0, mt: 0.75, p: 0, lineHeight: 1.6 }}
            >
              <li>
                cloudflare verified:{' '}
                {AUDIENCES.map(
                  audience => `${audience.label} ${formatNum(answer.totals[audience.key])}`
                ).join(' · ')}
              </li>
              <li>mcp requests: {formatNum(answer.totals.mcp)}</li>
              <li>unverified requests: {formatNum(answer.totals.unverified)}</li>
            </Box>
          </>
        )}
      </Box>
    </>
  );
}
