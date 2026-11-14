/**
 * The stats page's "shared links" tile: per UTC day of the last 28, how often a link to the
 * site was shared, counted from the preview images that messengers and social networks fetch
 * (`GET /insights/shared-links`, `sharedLinks.ts`).
 *
 * - Bars: one per day, the day's sum of shares, drawn like the visitors strip and the machine
 *   readers tile above it (`DayStrip`).
 * - Below: the window's sums as short lines, worded like the machine readers tile's. The shares
 *   whose fetch Cloudflare verified, by platform, and the rest as one sum under no name
 *   (`byVerdict`): a platform's name is read from a user agent anyone can write, and an app
 *   that fetches from the sender's phone is never verified. Then the most shared specs (a
 *   spec's hub and all of its implementations together, linked to the hub) and the most shared
 *   libraries (a library's implementations across specs, linked to the gallery filtered by it).
 * - What a share is and what the count cannot see is on the legal page the header links.
 * - Loading, a failed request and any answer but `ok` are one muted line each.
 */

import { Link as RouterLink } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { paths, specPath } from 'src/routes/paths';
import { DayStrip } from 'src/sections/stats/DayStrip';
import { HintTerm } from 'src/sections/stats/HintTerm';
import {
  byVerdict,
  platformLabel,
  type SharedLinksPart,
  type SharedLinksResponse,
  UNVERIFIED_HINT,
} from 'src/sections/stats/sharedLinks';
import { CHART_PX } from 'src/sections/stats/stripGeometry';
import { colors, fontSize, semanticColors, typography } from 'src/theme';

const shares = (n: number): string => (n === 1 ? 'share' : 'shares');

const smallSx = {
  fontFamily: typography.fontFamily,
  fontSize: fontSize.xxs,
  color: semanticColors.mutedText,
} as const;

const entryLinkSx = {
  fontFamily: typography.mono,
  color: 'var(--ink)',
  textDecoration: 'none',
  '&:hover': { color: colors.primary, textDecoration: 'underline' },
  '&:focus-visible': {
    outline: `2px solid ${colors.primary}`,
    outlineOffset: 2,
    borderRadius: '2px',
  },
} as const;

/** One entry of a "most shared" line: its name, where the name leads, and its 28-day sum. */
interface SumEntry {
  name: string;
  to: string;
  shares: number;
}

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
  const { platforms } = answer;
  // A spec leads to its hub, a library to the gallery filtered by it.
  const specs = answer.top_specs.map(entry => ({
    name: entry.spec_id,
    to: specPath(entry.spec_id),
    shares: entry.shares,
  }));
  const libraries = answer.top_libraries.map(entry => ({
    name: entry.library,
    to: paths.plotsFiltered('lib', entry.library),
    shares: entry.shares,
  }));
  if (platforms.length === 0 && specs.length === 0 && libraries.length === 0) return null;
  const verdict = byVerdict(platforms);

  return (
    <Box
      component="ul"
      sx={{ ...smallSx, listStyle: 'none', m: 0, mt: 0.75, p: 0, lineHeight: 1.6 }}
    >
      {verdict ? (
        <>
          <PlatformLine
            testId="shared-links-verified"
            label="cloudflare verified"
            parts={verdict.verified}
            formatNum={formatNum}
          />
          {verdict.unverified > 0 && (
            <li data-testid="shared-links-unverified">
              <HintTerm hint={UNVERIFIED_HINT} testId="shared-links-unverified-term">
                unverified
              </HintTerm>{' '}
              shares: {formatNum(verdict.unverified)}
            </li>
          )}
        </>
      ) : (
        // An answer without the verdicts: one line that claims nothing about them.
        <PlatformLine
          testId="shared-links-platforms"
          label="by platform"
          parts={platforms}
          formatNum={formatNum}
        />
      )}
      <SumLine
        testId="shared-links-specs"
        label="most shared specs"
        entries={specs}
        formatNum={formatNum}
      />
      <SumLine
        testId="shared-links-libraries"
        label="most shared libraries"
        entries={libraries}
        formatNum={formatNum}
      />
    </Box>
  );
}

/** One line of platforms with their sums; no line without a platform. */
function PlatformLine({
  testId,
  label,
  parts,
  formatNum,
}: {
  testId: string;
  label: string;
  parts: SharedLinksPart[];
  formatNum: (value: number) => string;
}) {
  if (parts.length === 0) return null;
  return (
    <li data-testid={testId}>
      {label}:{' '}
      {parts
        .map(entry => `${platformLabel(entry.platform)} ${formatNum(entry.shares)}`)
        .join(' · ')}
    </li>
  );
}

/** One "most shared" line: every entry a link with its sum; no line without an entry. */
function SumLine({
  testId,
  label,
  entries,
  formatNum,
}: {
  testId: string;
  label: string;
  entries: SumEntry[];
  formatNum: (value: number) => string;
}) {
  if (entries.length === 0) return null;
  return (
    <li data-testid={testId}>
      {label}:{' '}
      {entries.map((entry, index) => (
        <span key={entry.name}>
          {index > 0 && ' · '}
          <Box component={RouterLink} to={entry.to} sx={entryLinkSx}>
            {entry.name}
          </Box>{' '}
          {formatNum(entry.shares)}
        </span>
      ))}
    </li>
  );
}
