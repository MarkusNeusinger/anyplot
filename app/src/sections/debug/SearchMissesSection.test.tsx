import { fireEvent } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { readSearchMisses } from 'src/sections/debug/searchMisses';
import { SearchMissesSection } from 'src/sections/debug/SearchMissesSection';
import { render, screen, waitFor, within } from 'src/test-utils';

const SPIDER = { query: 'spider', count: 12, first_day: '2026-10-02', last_day: '2026-11-17' };
const KREIS = { query: 'kreisdiagramm', count: 4, first_day: '2026-11-01', last_day: '2026-11-16' };
const SPLOM = { query: 'splom', count: 1, first_day: '2026-11-17', last_day: '2026-11-17' };
const GAPMINDER = { query: 'gapminder', count: 1, first_day: '2026-11-03', last_day: '2026-11-03' };
const SPINNE = { query: 'spinne', count: 1, first_day: '2026-11-02', last_day: '2026-11-02' };

const LIST = {
  status: 'ok',
  retention_days: 180,
  day_cap: 1000,
  order: 'count',
  offset: 0,
  texts: 3,
  misses: [SPIDER, KREIS, SPLOM],
  capped_days: [],
};

type Answer = { ok?: boolean; body: unknown };

/** `fetch` that answers each request with what `respond` makes of its URL and options. */
function answerWith(respond: (url: URL, init?: RequestInit) => Answer) {
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    const { ok = true, body } = respond(new URL(url, 'https://anyplot.ai'), init);
    return Promise.resolve({ ok, status: ok ? 200 : 503, json: () => Promise.resolve(body) });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

/** The list for every GET, `{deleted}` for every DELETE (or a refusal when `deleteOk` is false). */
function answerList(body: unknown, { ok = true, deleteOk = true } = {}) {
  return answerWith((_url, init) =>
    init?.method === 'DELETE' ? { ok: deleteOk, body: { deleted: 2 } } : { ok, body }
  );
}

function calls(fetchMock: ReturnType<typeof answerWith>) {
  return fetchMock.mock.calls.map(([url, init]) => ({
    url: new URL(url, 'https://anyplot.ai'),
    init: init as RequestInit | undefined,
  }));
}

const rows = () => screen.getAllByTestId('search-miss-row');
const shownTexts = () => rows().map(row => within(row).getAllByRole('rowheader')[0].textContent);

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('readSearchMisses', () => {
  it('reads an ok answer', () => {
    expect(readSearchMisses(LIST)).toMatchObject({ texts: 3, retention_days: 180, day_cap: 1000 });
  });

  it('keeps the status of an answer without a list, so the section can say which it is', () => {
    expect(readSearchMisses({ status: 'not_configured' })).toBe('not_configured');
    expect(readSearchMisses({ status: 'unavailable' })).toBe('unavailable');
  });

  it('refuses anything else and leaves out an entry without a text or a day', () => {
    expect(readSearchMisses(null)).toBeNull();
    expect(readSearchMisses({ status: 'ok' })).toBeNull();
    const read = readSearchMisses({
      ...LIST,
      misses: [
        ...LIST.misses,
        { query: '', count: 3, first_day: '2026-11-01', last_day: '2026-11-01' },
        { query: 'x' },
      ],
      capped_days: ['2026-11-16', 'yesterday', 5],
    });
    expect(read).toMatchObject({ misses: LIST.misses, capped_days: ['2026-11-16'] });
  });

  it('reads an answer of an older API as the first page, most searched first, with no capped day', () => {
    const older = { status: 'ok', retention_days: 180, texts: 3, misses: LIST.misses };
    expect(readSearchMisses(older)).toMatchObject({ order: 'count', offset: 0, capped_days: [] });
  });
});

describe('SearchMissesSection', () => {
  it('lists the texts most searched first, with their days', async () => {
    const fetchMock = answerList(LIST);

    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);

    await waitFor(() => expect(rows()).toHaveLength(3));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [first] = calls(fetchMock);
    expect(first.url.pathname).toMatch(/\/debug\/search-misses$/);
    expect(first.url.searchParams.get('order')).toBe('count');
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('3 texts');
    // The retention period is the API's, never a number the page keeps.
    expect(screen.getByText(/deleted after 180 days/)).toBeInTheDocument();
    const top = within(rows()[0]);
    expect(top.getByText('spider')).toBeInTheDocument();
    expect(top.getByText('12')).toBeInTheDocument();
    expect(top.getByText('2026-10-02')).toBeInTheDocument();
    expect(top.getByText('2026-11-17')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'most searched' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
    expect(screen.queryByTestId('search-misses-capped')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '.load_more()' })).not.toBeInTheDocument();
  });

  it('reads the list most recent first when asked', async () => {
    const fetchMock = answerWith(url => ({
      body:
        url.searchParams.get('order') === 'recent'
          ? { ...LIST, order: 'recent', misses: [SPLOM, SPIDER, KREIS] }
          : LIST,
    }));
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'most recent' }));

    await waitFor(() => expect(shownTexts()).toEqual(['splom', 'spider', 'kreisdiagramm']));
    expect(calls(fetchMock)[1].url.searchParams.get('order')).toBe('recent');
    expect(screen.getByRole('button', { name: 'most recent' })).toHaveAttribute(
      'aria-pressed',
      'true'
    );
  });

  it('loads the texts beyond the first page, so a text searched once is reachable', async () => {
    const fetchMock = answerWith(url => {
      const offset = Number(url.searchParams.get('offset') ?? 0);
      // The second page repeats the last text of the first: a miss moved it across the border.
      const misses = offset === 0 ? [SPIDER, KREIS, SPLOM] : [SPLOM, GAPMINDER, SPINNE];
      return { body: { ...LIST, offset, texts: 5, misses } };
    });
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('5 texts · 3 shown');

    fireEvent.click(screen.getByRole('button', { name: '.load_more()' }));

    await waitFor(() =>
      expect(shownTexts()).toEqual(['spider', 'kreisdiagramm', 'splom', 'gapminder', 'spinne'])
    );
    expect(calls(fetchMock)[1].url.searchParams.get('offset')).toBe('3');
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('5 texts');
    expect(screen.queryByRole('button', { name: '.load_more()' })).not.toBeInTheDocument();
  });

  it('starts the next page after what the server still holds when a text was deleted', async () => {
    const fetchMock = answerWith((url, init) =>
      init?.method === 'DELETE'
        ? { body: { deleted: 1 } }
        : { body: { ...LIST, texts: 5, offset: Number(url.searchParams.get('offset') ?? 0) } }
    );
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete “kreisdiagramm” from the list' }));
    await waitFor(() => expect(rows()).toHaveLength(2));
    fireEvent.click(screen.getByRole('button', { name: '.load_more()' }));

    await waitFor(() => expect(calls(fetchMock)).toHaveLength(3));
    expect(calls(fetchMock)[2].url.searchParams.get('offset')).toBe('2');
  });

  it('deletes a text with the text in the body, never in the URL, and drops its row', async () => {
    const fetchMock = answerList(LIST);
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete “kreisdiagramm” from the list' }));

    await waitFor(() => expect(rows()).toHaveLength(2));
    const { url, init } = calls(fetchMock)[1];
    expect(url.pathname).toMatch(/\/debug\/search-misses$/);
    expect(url.search).toBe('');
    expect(init?.method).toBe('DELETE');
    expect(JSON.parse(String(init?.body))).toEqual({ query: 'kreisdiagramm' });
    expect((init?.headers as Record<string, string>)['X-Admin-Token']).toBe('admin-token');
    expect(screen.queryByText('kreisdiagramm')).not.toBeInTheDocument();
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('2 texts');
  });

  it('keeps the row and says so when the delete fails', async () => {
    answerList(LIST, { deleteOk: false });
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete “spider” from the list' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('the delete of “spider” failed');
    expect(rows()).toHaveLength(3);
  });

  it('names the days that reached the cap and deletes a whole day, then reads the list again', async () => {
    const fetchMock = answerList({ ...LIST, capped_days: ['2026-11-17', '2026-11-14'] });
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));
    expect(screen.getByTestId('search-misses-capped')).toHaveTextContent(
      'days that reached the cap of 1,000 texts (new texts dropped):'
    );

    fireEvent.click(screen.getByRole('button', { name: 'Delete every text of 2026-11-14' }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    const [, deleted, again] = calls(fetchMock);
    expect(deleted.init?.method).toBe('DELETE');
    expect(JSON.parse(String(deleted.init?.body))).toEqual({ day: '2026-11-14' });
    expect(again.init?.method).toBeUndefined();
    expect(again.url.searchParams.get('order')).toBe('count');
  });

  it('says so when the delete of a day fails', async () => {
    answerList({ ...LIST, capped_days: ['2026-11-17'] }, { deleteOk: false });
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(rows()).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete every text of 2026-11-17' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('the delete of 2026-11-17 failed');
  });

  it.each([
    ['no database', { status: 'not_configured' }, true, 'no database configured'],
    ['a table that is not there yet', { status: 'unavailable' }, true, /misses unavailable/],
    ['a refused request', {}, false, /misses unavailable/],
    ['an empty list', { ...LIST, texts: 0, misses: [] }, true, 'no misses'],
  ])('is one line for %s', async (_, body, ok, line) => {
    answerList(body, { ok });

    render(<SearchMissesSection token="" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('search-misses-empty')).toHaveTextContent(line);
    });
    expect(screen.queryByTestId('search-misses-totals')).not.toBeInTheDocument();
  });

  it('asks again when the page reloads its sections', async () => {
    const fetchMock = answerList(LIST);

    const view = render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    view.rerender(<SearchMissesSection token="admin-token" reloadCounter={1} />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
