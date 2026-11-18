/**
 * The debug page's "search misses" section: the gallery searches that found nothing in the
 * whole catalogue, the owner's private list (`GET /debug/search-misses`, `api/search_misses.py`).
 * It shows what the catalogue lacks and which words the search does not know.
 *
 * - One line: that no public page shows the list, and how long a text is kept.
 * - The days that reached the day's cap, each with `.delete_day()`: on those a new text was
 *   dropped, which is how a flood shows. A day's delete removes all of its rows
 *   (`DELETE /debug/search-misses` with the day in the body) and fetches the list again.
 * - The order: most searched first, or most recently searched first.
 * - A table: the text, how often it was searched, its first and last UTC day, and `.delete()`,
 *   which removes every row of the text (the text in the body). A deleted text leaves the table
 *   at once. Beyond the first page, `.load_more()` fetches the next one, so a text searched once
 *   is reachable too.
 * - A failed delete or load says so in one line and changes nothing. Loading, no database, a
 *   failed request and an empty list are one line each.
 */

import { useCallback, useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { SectionHeader } from 'src/components/SectionHeader';
import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import { visuallyHiddenSx } from 'src/sections/agent-chat/styles';
import {
  readSearchMisses,
  type SearchMiss,
  type SearchMissOrder,
} from 'src/sections/debug/searchMisses';
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

const ORDERS: { order: SearchMissOrder; label: string }[] = [
  { order: 'count', label: 'most searched' },
  { order: 'recent', label: 'most recent' },
];

const number = (value: number): string => value.toLocaleString('en-US');

const buttonSx = { ...debugControlSx, py: 0.25, cursor: 'pointer' } as const;

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

/** What the section did on top of the first page, for one list: one order, one fetch of it. */
interface Additions {
  view: string;
  /** Texts of the pages loaded after the first. */
  more: SearchMiss[];
  /** Texts deleted since the list was fetched. */
  deleted: ReadonlySet<string>;
}

export function SearchMissesSection({ token, reloadCounter }: SearchMissesSectionProps) {
  const [order, setOrder] = useState<SearchMissOrder>('count');
  // A day's delete changes the sums of every text of that day, so the list is fetched again.
  const [refreshes, setRefreshes] = useState(0);
  const reloads = reloadCounter + refreshes;
  const view = `${order}\n${reloads}`;
  const answer = useAnswer(`${SEARCH_MISSES_URL}?order=${order}`, token, reloads, readSearchMisses);
  const [stored, setAdditions] = useState<Additions>({ view, more: [], deleted: new Set() });
  const additions: Additions =
    stored.view === view ? stored : { view, more: [], deleted: new Set() };
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const page = answer && typeof answer === 'object' ? answer : null;
  const loaded = page ? [...page.misses, ...additions.more] : [];
  const misses = loaded.filter(miss => !additions.deleted.has(miss.query));
  const texts = page ? page.texts - additions.deleted.size : 0;

  const act = useCallback(async (action: () => Promise<void>, failure: string) => {
    setBusy(true);
    setNotice(null);
    try {
      await action();
    } catch {
      setNotice(failure);
    } finally {
      setBusy(false);
    }
  }, []);

  const send = useCallback(
    async (body: { query: string } | { day: string }) => {
      const response = await fetchWithAuth(SEARCH_MISSES_URL, token, {
        method: 'DELETE',
        body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error(`delete answered ${response.status}`);
    },
    [token]
  );

  const removeText = (query: string) =>
    act(async () => {
      await send({ query });
      setAdditions({ ...additions, deleted: new Set([...additions.deleted, query]) });
    }, `the delete of “${query}” failed: the row stays`);

  const removeDay = (day: string) =>
    act(async () => {
      await send({ day });
      setRefreshes(value => value + 1);
    }, `the delete of ${day} failed: its rows stay`);

  // The next page starts after what the server still holds of the loaded texts.
  const loadMore = () =>
    act(async () => {
      const offset = loaded.length - additions.deleted.size;
      const response = await fetchWithAuth(
        `${SEARCH_MISSES_URL}?order=${order}&offset=${offset}`,
        token
      );
      const next = response.ok ? readSearchMisses(await response.json()) : null;
      if (!next || typeof next !== 'object') throw new Error('no page');
      // A miss counted since the first page can move a text across the page border: no text twice.
      const shown = new Set(loaded.map(miss => miss.query));
      const fresh = next.misses.filter(miss => !shown.has(miss.query));
      setAdditions({ ...additions, more: [...additions.more, ...fresh] });
    }, 'loading more texts failed');

  return (
    <Box component="section" aria-label="Search misses section" sx={{ mb: 4 }}>
      <Box sx={{ mt: 4 }}>
        <SectionHeader prompt="❯" title={<em>search misses</em>} />
      </Box>
      <Typography sx={{ ...listMutedSx, mb: 1.5 }}>
        gallery searches that found nothing in the whole catalogue · private, on no public page
        {page && page.retention_days > 0 ? ` · deleted after ${page.retention_days} days` : ''}
      </Typography>

      {answer === undefined ? (
        <Typography sx={{ ...listMutedSx, py: 1 }}>loading search misses…</Typography>
      ) : !page ? (
        <Typography data-testid="search-misses-empty" sx={{ ...listMutedSx, py: 1 }}>
          {EMPTY_TEXT[typeof answer === 'string' ? answer : 'unavailable']}
        </Typography>
      ) : (
        <>
          {page.capped_days.length > 0 && (
            <Box
              data-testid="search-misses-capped"
              sx={{ ...listTextSx, display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}
            >
              <span>
                days that reached the cap of {number(page.day_cap)} texts (new texts dropped):
              </span>
              {page.capped_days.map(day => (
                <Box key={day} component="span" sx={{ display: 'inline-flex', gap: 0.5 }}>
                  {day}
                  <Box
                    component="button"
                    type="button"
                    aria-label={`Delete every text of ${day}`}
                    disabled={busy}
                    onClick={() => {
                      void removeDay(day);
                    }}
                    sx={buttonSx}
                  >
                    .delete_day()
                  </Box>
                </Box>
              ))}
            </Box>
          )}
          <Box
            role="group"
            aria-label="Order of the list"
            sx={{ display: 'flex', gap: 0.5, alignItems: 'center', mb: 1 }}
          >
            <Typography component="span" sx={listMutedSx}>
              order:
            </Typography>
            {ORDERS.map(entry => (
              <Box
                key={entry.order}
                component="button"
                type="button"
                aria-pressed={order === entry.order}
                onClick={() => setOrder(entry.order)}
                sx={{
                  ...buttonSx,
                  borderColor: order === entry.order ? 'var(--ink-muted)' : 'var(--rule)',
                }}
              >
                {entry.label}
              </Box>
            ))}
          </Box>
          {notice !== null && (
            <Typography role="alert" sx={{ ...listMutedSx, mb: 0.5 }}>
              {notice}
            </Typography>
          )}
          {misses.length === 0 ? (
            <Typography data-testid="search-misses-empty" sx={{ ...listMutedSx, py: 1 }}>
              no misses: every search found something
            </Typography>
          ) : (
            <>
              <Typography data-testid="search-misses-totals" sx={listTextSx}>
                {number(texts)} texts
                {texts > misses.length ? ` · ${number(misses.length)} shown` : ''}
              </Typography>
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
                            disabled={busy}
                            onClick={() => {
                              void removeText(miss.query);
                            }}
                            sx={buttonSx}
                          >
                            .delete()
                          </Box>
                        </Box>
                      </tr>
                    ))}
                  </tbody>
                </Box>
              </Box>
              {texts > misses.length && (
                <Box
                  component="button"
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    void loadMore();
                  }}
                  sx={{ ...buttonSx, mt: 1 }}
                >
                  .load_more()
                </Box>
              )}
            </>
          )}
        </>
      )}
    </Box>
  );
}
