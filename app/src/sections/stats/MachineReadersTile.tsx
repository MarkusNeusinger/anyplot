/**
 * The stats page's "machine readers" tile: per UTC day of the last 28, how many
 * requests verified crawlers and AI assistants made, split into the three
 * audiences of `GET /insights/machine-readers` (`machineReaders.ts`).
 *
 * - Bars: one stacked column per day, the same 28-day window and geometry as the
 *   visitors strip above it. Bottom to top: reads for a person (the brand green),
 *   AI index and training reads (the bulk, de-emphasised in muted ink), search
 *   engines (blue). A 2px gap in the page colour separates the segments; each
 *   day's column is its own hover target and tooltip.
 * - Colours: green and blue at full strength, the muted ink at 35%, checked with
 *   the dataviz validator against both page backgrounds: adjacent segments stay
 *   apart for normal and colour-blind vision in light and dark. The muted
 *   segment is below 3:1 on purpose; the legend carries every total in text.
 * - Below: the first and last date, a legend with the totals and the MCP
 *   requests of every client, and a footnote naming the unverified requests that
 *   are not counted. Public copy says "unverified", never "spoofed".
 * - Loading, a failed request and any answer but `ok` are one muted line each.
 */

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { paths } from 'src/routes/paths';
import type { MachineReaderPoint, MachineReadersResponse } from 'src/sections/stats/machineReaders';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

/** The three audiences, bottom to top, with their colour and the label the legend and tooltip use. */
const SEGMENTS = [
  { key: 'for_person', label: 'for a person', color: colors.primary, opacity: 1 },
  {
    key: 'index_training',
    label: 'ai index & training',
    color: semanticColors.mutedText,
    opacity: 0.35,
  },
  { key: 'search', label: 'search engines', color: colors.info, opacity: 1 },
] as const;

const CHART_PX = 70;
const GAP_PX = 2;
/** A day without reads still draws an honest stub (3% of the strip), as the visitors strip does. */
const MIN_BAR_PX = CHART_PX * 0.03;

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
          <MachineReadersChart answer={answer} formatNum={formatNum} />
        )}
      </Box>
    </>
  );
}

function MachineReadersChart({
  answer,
  formatNum,
}: {
  answer: MachineReadersResponse;
  formatNum: (value: number) => string;
}) {
  const { points, totals } = answer;
  const maxTotal = Math.max(...points.map(dayTotal), 1);
  // The tallest column's three segments and their two gaps fill the strip's height.
  const scale = (CHART_PX - 2 * GAP_PX) / maxTotal;

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 0.25,
          height: CHART_PX,
          overflow: 'hidden',
        }}
      >
        {points.map(point => {
          const parts = SEGMENTS.filter(segment => point[segment.key] > 0);
          const n = dayTotal(point);
          const title =
            `${point.date}: ${n} ${requests(n)} · ${point.for_person} for a person · ` +
            `${point.index_training} ai index & training · ${point.search} search engines`;
          return (
            <Tooltip key={point.date} title={title} arrow>
              <Box
                data-testid="machine-readers-day"
                sx={{
                  flex: 1,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column-reverse',
                  gap: `${GAP_PX}px`,
                  borderRadius: '2px 2px 0 0',
                  '&:hover': { bgcolor: 'var(--rule)' },
                  '&:hover .machine-readers-muted': { opacity: 0.45 },
                  transition: 'background-color 0.15s ease',
                }}
              >
                {parts.length === 0 ? (
                  <Box
                    sx={{
                      height: `${MIN_BAR_PX}px`,
                      flexShrink: 0,
                      bgcolor: semanticColors.mutedText,
                      opacity: 0.35,
                      borderRadius: '2px 2px 0 0',
                    }}
                  />
                ) : (
                  parts.map((segment, index) => (
                    <Box
                      key={segment.key}
                      className={segment.opacity < 1 ? 'machine-readers-muted' : undefined}
                      sx={{
                        height: `${Math.max(point[segment.key] * scale, 1)}px`,
                        flexShrink: 0,
                        bgcolor: segment.color,
                        opacity: segment.opacity,
                        // Rounded at the data end only: the topmost segment.
                        borderRadius: index === parts.length - 1 ? '2px 2px 0 0' : 0,
                        transition: 'opacity 0.15s ease',
                      }}
                    />
                  ))
                )}
              </Box>
            </Tooltip>
          );
        })}
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.25 }}>
        <Typography sx={{ ...smallSx, fontSize: fontSize.micro }}>{points[0]?.date}</Typography>
        <Typography sx={{ ...smallSx, fontSize: fontSize.micro }}>
          {points[points.length - 1]?.date}
        </Typography>
      </Box>
      <Box
        data-testid="machine-readers-legend"
        sx={{
          ...smallSx,
          display: 'flex',
          flexWrap: 'wrap',
          columnGap: 1.5,
          rowGap: 0.25,
          mt: 0.75,
        }}
      >
        {SEGMENTS.map(segment => (
          <Box
            key={segment.key}
            component="span"
            sx={{ display: 'inline-flex', alignItems: 'center' }}
          >
            <Box
              component="span"
              aria-hidden
              sx={{
                width: 8,
                height: 8,
                mr: 0.5,
                borderRadius: '2px',
                bgcolor: segment.color,
                opacity: segment.opacity,
              }}
            />
            {segment.label} {formatNum(totals[segment.key])}
          </Box>
        ))}
        <Box component="span">· {formatNum(totals.mcp)} over mcp (all clients)</Box>
      </Box>
      <Typography
        data-testid="machine-readers-footnote"
        sx={{ ...smallSx, mt: 0.5, lineHeight: 1.5 }}
      >
        requests that reached the server, each from a crawler cloudflare verified against its
        vendor&apos;s published addresses; people are counted in visitors above.{' '}
        {totals.unverified === 1
          ? "1 request that carried a crawler's name without that verification is not counted."
          : `${formatNum(totals.unverified)} requests that carried a crawler's name without that verification are not counted.`}
      </Typography>
    </>
  );
}
