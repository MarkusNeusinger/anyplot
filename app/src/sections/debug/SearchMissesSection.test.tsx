import { fireEvent } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { readSearchMisses } from 'src/sections/debug/searchMisses';
import { SearchMissesSection } from 'src/sections/debug/SearchMissesSection';
import { render, screen, waitFor, within } from 'src/test-utils';

const LIST = {
  status: 'ok',
  retention_days: 90,
  texts: 3,
  misses: [
    { query: 'spider', count: 12, first_day: '2026-10-02', last_day: '2026-11-17' },
    { query: 'kreisdiagramm', count: 4, first_day: '2026-11-01', last_day: '2026-11-16' },
    { query: 'splom', count: 1, first_day: '2026-11-17', last_day: '2026-11-17' },
  ],
};

/** `fetch` that answers the list, and the delete with `deleteOk`. */
function answerWith(body: unknown, { ok = true, deleteOk = true } = {}) {
  const fetchMock = vi.fn((_url: string, init?: RequestInit) =>
    Promise.resolve(
      init?.method === 'DELETE'
        ? {
            ok: deleteOk,
            status: deleteOk ? 200 : 503,
            json: () => Promise.resolve({ deleted: 2 }),
          }
        : { ok, status: ok ? 200 : 500, json: () => Promise.resolve(body) }
    )
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('readSearchMisses', () => {
  it('reads an ok answer', () => {
    expect(readSearchMisses(LIST)).toMatchObject({ texts: 3, retention_days: 90 });
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
    });
    expect(read).toMatchObject({ misses: LIST.misses });
  });
});

describe('SearchMissesSection', () => {
  it('lists the texts most searched first, with their days', async () => {
    const fetchMock = answerWith(LIST);

    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);

    await waitFor(() => expect(screen.getAllByTestId('search-miss-row')).toHaveLength(3));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/debug\/search-misses$/);
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('3 texts');
    const first = within(screen.getAllByTestId('search-miss-row')[0]);
    expect(first.getByText('spider')).toBeInTheDocument();
    expect(first.getByText('12')).toBeInTheDocument();
    expect(first.getByText('2026-10-02')).toBeInTheDocument();
    expect(first.getByText('2026-11-17')).toBeInTheDocument();
  });

  it('says when the list shows only the most searched texts', async () => {
    answerWith({ ...LIST, texts: 612 });

    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('search-misses-totals')).toHaveTextContent(
        '612 texts · the 3 most searched shown'
      );
    });
  });

  it('deletes a text with the text in the body, never in the URL, and drops its row', async () => {
    const fetchMock = answerWith(LIST);
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(screen.getAllByTestId('search-miss-row')).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete “kreisdiagramm” from the list' }));

    await waitFor(() => expect(screen.getAllByTestId('search-miss-row')).toHaveLength(2));
    const [url, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(url).toMatch(/\/debug\/search-misses$/);
    expect(init.method).toBe('DELETE');
    expect(JSON.parse(String(init.body))).toEqual({ query: 'kreisdiagramm' });
    expect((init.headers as Record<string, string>)['X-Admin-Token']).toBe('admin-token');
    expect(screen.queryByText('kreisdiagramm')).not.toBeInTheDocument();
    expect(screen.getByTestId('search-misses-totals')).toHaveTextContent('2 texts');
  });

  it('keeps the row and says so when the delete fails', async () => {
    answerWith(LIST, { deleteOk: false });
    render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(screen.getAllByTestId('search-miss-row')).toHaveLength(3));

    fireEvent.click(screen.getByRole('button', { name: 'Delete “spider” from the list' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('the delete of “spider” failed');
    expect(screen.getAllByTestId('search-miss-row')).toHaveLength(3);
  });

  it.each([
    ['no database', { status: 'not_configured' }, true, 'no database configured'],
    ['a table that is not there yet', { status: 'unavailable' }, true, /misses unavailable/],
    ['a refused request', {}, false, /misses unavailable/],
    ['an empty list', { ...LIST, texts: 0, misses: [] }, true, 'no misses'],
  ])('is one line for %s', async (_, body, ok, line) => {
    answerWith(body, { ok });

    render(<SearchMissesSection token="" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('search-misses-empty')).toHaveTextContent(line);
    });
    expect(screen.queryByTestId('search-misses-totals')).not.toBeInTheDocument();
  });

  it('asks again when the page reloads its sections', async () => {
    const fetchMock = answerWith(LIST);

    const view = render(<SearchMissesSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    view.rerender(<SearchMissesSection token="admin-token" reloadCounter={1} />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
