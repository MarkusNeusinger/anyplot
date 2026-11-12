/**
 * The debug page's "shared links" section: the share counters of the last 28
 * UTC days as the public tile on /stats has them, plus what that tile leaves
 * out (`GET /debug/shared-links`, `api/shared_links.py`).
 *
 * - One line of totals: the shares by named platforms, and `other`, the preview
 *   images fetched by a client that is neither a preview platform nor a known
 *   crawler. A rising `other` is how a platform missing from the list shows
 *   itself; the request log names it.
 * - The platforms with their totals, and the most shared plot pages.
 * - Beside each total, how many of the fetches Cloudflare verified as a bot it
 *   knows. The platform's name is read from a user agent anyone can write, so
 *   this is what shows a client that only signs as a platform: a platform
 *   Cloudflare verifies, with shares that are mostly unverified. WhatsApp and
 *   Signal fetch from the sender's phone and are never verified. Where the
 *   answer lacks a verdict (an API revision older than the page), a platform
 *   and `other` stand without that part: no count, not a zero nobody measured.
 * - Loading, no database, a failed request and an empty window are one line each.
 */

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL } from 'src/constants';
import { listMutedSx, listTextSx } from 'src/sections/debug/styles';
import { useAnswer } from 'src/sections/debug/useAnswer';
import { platformLabel, readSharedLinksDetail } from 'src/sections/stats/sharedLinks';

const EMPTY_TEXT = {
  not_configured: 'no database configured',
  unavailable:
    'shared link counters unavailable (before the first deploy: the table is not there yet)',
} as const;

const number = (value: number): string => value.toLocaleString('en-US');

export interface SharedLinksSectionProps {
  /** The admin token of the session (empty behind Cloudflare Access). */
  token: string;
  /** The page's reload count: a change fetches the numbers again. */
  reloadCounter: number;
}

export function SharedLinksSection({ token, reloadCounter }: SharedLinksSectionProps) {
  const detail = useAnswer(
    `${DEBUG_API_URL}/debug/shared-links`,
    token,
    reloadCounter,
    readSharedLinksDetail
  );

  return (
    <Box component="section" aria-label="Shared links section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>shared links</em>} />
      </Box>
      <Typography sx={{ ...listMutedSx, mb: 1.5 }}>
        preview images fetched by messengers and social networks · last 28 days · verified: the
        fetcher is a bot cloudflare knows
      </Typography>

      {detail === undefined ? (
        <Typography sx={{ ...listMutedSx, py: 1 }}>loading shared links…</Typography>
      ) : detail === null || typeof detail === 'string' ? (
        <Typography data-testid="shared-links-empty" sx={{ ...listMutedSx, py: 1 }}>
          {EMPTY_TEXT[detail ?? 'unavailable']}
        </Typography>
      ) : (
        <>
          <Typography data-testid="shared-links-totals" sx={listTextSx}>
            {number(detail.total)} by named platforms (on /stats) · {number(detail.other)} other
            (not counted as shares
            {detail.other_verified === null ? '' : `, ${number(detail.other_verified)} verified`})
          </Typography>
          {detail.platforms.length > 0 && (
            <Typography data-testid="shared-links-platforms" sx={{ ...listMutedSx, mt: 0.5 }}>
              {detail.platforms
                .map(entry => {
                  const total = `${platformLabel(entry.platform)} ${number(entry.shares)}`;
                  return entry.verified === null
                    ? total
                    : `${total} (${number(entry.verified)} verified)`;
                })
                .join(' · ')}
            </Typography>
          )}
          {detail.top.length > 0 && (
            <Typography data-testid="shared-links-top" sx={{ ...listMutedSx, mt: 0.5 }}>
              most shared:{' '}
              {detail.top
                .map(
                  plot =>
                    `${plot.library ? `${plot.spec_id} · ${plot.library}` : plot.spec_id} ${number(plot.shares)}`
                )
                .join(', ')}
            </Typography>
          )}
        </>
      )}
    </Box>
  );
}
