/**
 * The debug page's "search misses" section: the gallery searches that found nothing in the
 * whole catalogue, the owner's private list (`GET /debug/search-misses`, `api/search_misses.py`).
 * It shows what the catalogue lacks and which words the search does not know.
 *
 * - One line: how many texts the retention window holds, and that no public page shows them.
 * - A table, most searched first: the text, how often it was searched, its first and last UTC
 *   day, and `.delete()`, which removes every row of the text (`DELETE /debug/search-misses`,
 *   the text in the body). A deleted text leaves the table at once; a failed delete says so in
 *   one line and keeps the row.
 * - Loading, no database, a failed request and an empty list are one line each.
 */

import { useCallback, useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import { readSearchMisses } from 'src/sections/debug/searchMisses';
import {
  debugControlSx,
  listMutedSx,
  listTextSx,
  tableCellSx,
  tableHeadSx,
} from 'src/sections/debug/styles';
import { useAnswer } from 'src/sections/debug/useAnswer';

const SEARCH_MISSES_URL = `${DEBUG_API_URL}/debug/search-misses`;

const EMPTY_TEXT = {
  not_configured: 'no database configured',
  unavailable: 'search misses unavailable (before the first deploy: the table is not there yet)',
} as const;

const number = (value: number): string => value.toLocaleString('en-US');

const textCellSx = {
  ...tableCellSx,
  textAlign: 'left',
  whiteSpace: 'normal',
  wordBreak: 'break-word',
};

export interface SearchMissesSectionProps {
  /** The admin token of the session (empty behind Cloudflare Access). */
  token: string;
  /** The page's reload count: a change fetches the list again. */
  reloadCounter: number;
}

export function SearchMissesSection({ token, reloadCounter }: SearchMissesSectionProps) {
  const answer = useAnswer(SEARCH_MISSES_URL, token, reloadCounter, readSearchMisses);
  // The texts deleted since the list was last fetched; a reload starts over with the server's list.
  const [deleted, setDeleted] = useState<{ reload: number; texts: ReadonlySet<string> }>({
    reload: reloadCounter,
    texts: new Set(),
  });
  const [busy, setBusy] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const deletedNow = deleted.reload === reloadCounter ? deleted.texts : new Set<string>();

  const remove = useCallback(
    async (query: string) => {
      setBusy(query);
      setFailed(null);
      try {
        const response = await fetchWithAuth(SEARCH_MISSES_URL, token, {
          method: 'DELETE',
          body: JSON.stringify({ query }),
        });
        if (!response.ok) throw new Error(`delete answered ${response.status}`);
        setDeleted(previous => ({
          reload: reloadCounter,
          texts: new Set([...(previous.reload === reloadCounter ? previous.texts : []), query]),
        }));
      } catch {
        setFailed(query);
      } finally {
        setBusy(null);
      }
    },
    [token, reloadCounter]
  );

  const misses =
    answer && typeof answer === 'object'
      ? answer.misses.filter(miss => !deletedNow.has(miss.query))
      : [];

  return (
    <Box component="section" aria-label="Search misses section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>search misses</em>} />
      </Box>
      <Typography sx={{ ...listMutedSx, mb: 1.5 }}>
        gallery searches that found nothing in the whole catalogue · private, on no public page ·
        deleted after {answer && typeof answer === 'object' ? answer.retention_days : 90} days
      </Typography>

      {answer === undefined ? (
        <Typography sx={{ ...listMutedSx, py: 1 }}>loading search misses…</Typography>
      ) : answer === null || typeof answer === 'string' ? (
        <Typography data-testid="search-misses-empty" sx={{ ...listMutedSx, py: 1 }}>
          {EMPTY_TEXT[answer ?? 'unavailable']}
        </Typography>
      ) : misses.length === 0 ? (
        <Typography data-testid="search-misses-empty" sx={{ ...listMutedSx, py: 1 }}>
          no misses: every search found something
        </Typography>
      ) : (
        <>
          <Typography data-testid="search-misses-totals" sx={listTextSx}>
            {number(answer.texts - (answer.misses.length - misses.length))} texts
            {answer.texts > answer.misses.length
              ? ` · the ${number(answer.misses.length)} most searched shown`
              : ''}
          </Typography>
          {failed !== null && (
            <Typography role="alert" sx={{ ...listMutedSx, mt: 0.5 }}>
              the delete of “{failed}” failed: the row stays
            </Typography>
          )}
          <Box sx={{ overflowX: 'auto', mt: 1 }}>
            <Box component="table" sx={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead>
                <tr>
                  <Box component="th" scope="col" sx={{ ...tableHeadSx, textAlign: 'left' }}>
                    text
                  </Box>
                  <Box component="th" scope="col" sx={tableHeadSx}>
                    searches
                  </Box>
                  <Box component="th" scope="col" sx={tableHeadSx}>
                    first
                  </Box>
                  <Box component="th" scope="col" sx={tableHeadSx}>
                    last
                  </Box>
                  <Box component="th" scope="col" sx={tableHeadSx}>
                    <Box component="span" sx={visuallyHiddenSx}>
                      delete
                    </Box>
                  </Box>
                </tr>
              </thead>
              <tbody>
                {misses.map(miss => (
                  <tr key={miss.query} data-testid="search-miss-row">
                    <Box component="th" scope="row" sx={{ ...textCellSx, fontWeight: 400 }}>
                      {miss.query}
                    </Box>
                    <Box component="td" sx={tableCellSx}>
                      {number(miss.count)}
                    </Box>
                    <Box component="td" sx={tableCellSx}>
                      {miss.first_day}
                    </Box>
                    <Box component="td" sx={tableCellSx}>
                      {miss.last_day}
                    </Box>
                    <Box component="td" sx={tableCellSx}>
                      <Box
                        component="button"
                        type="button"
                        aria-label={`Delete “${miss.query}” from the list`}
                        disabled={busy !== null}
                        onClick={() => {
                          void remove(miss.query);
                        }}
                        sx={{ ...debugControlSx, py: 0.25, cursor: 'pointer' }}
                      >
                        .delete()
                      </Box>
                    </Box>
                  </tr>
                ))}
              </tbody>
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
