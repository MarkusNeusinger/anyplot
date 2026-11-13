import { afterEach, describe, expect, it, vi } from 'vitest';

import { SharedLinksSection } from 'src/sections/debug/SharedLinksSection';
import { readSharedLinksDetail } from 'src/sections/stats/sharedLinks';
import { render, screen, waitFor } from 'src/test-utils';

const DETAIL = {
  status: 'ok',
  window_days: 28,
  total: 1234,
  days: Array.from({ length: 28 }, (_, offset) => ({
    date: new Date(Date.UTC(2026, 9, 15 + offset)).toISOString().slice(0, 10),
    shares: offset === 27 ? 1234 : 0,
  })),
  platforms: [
    { platform: 'teams', shares: 1200, verified: 1150 },
    { platform: 'whatsapp-lite', shares: 34, verified: 0 },
  ],
  top: [
    { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 900 },
    { spec_id: 'heatmap-basic', language: null, library: null, shares: 334 },
  ],
  other: 5678,
  other_verified: 12,
};

function answerWith(body: unknown, ok = true) {
  const fetchMock = vi.fn().mockResolvedValue({ ok, json: () => Promise.resolve(body) });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('readSharedLinksDetail', () => {
  it('reads an ok answer with its uncounted fetches', () => {
    expect(readSharedLinksDetail(DETAIL)).toMatchObject({ total: 1234, other: 5678 });
  });

  it('keeps the status of an answer without numbers, so the section can say which it is', () => {
    expect(readSharedLinksDetail({ status: 'not_configured' })).toBe('not_configured');
    expect(readSharedLinksDetail({ status: 'unavailable' })).toBe('unavailable');
  });

  it('refuses anything else', () => {
    expect(readSharedLinksDetail(null)).toBeNull();
    expect(readSharedLinksDetail({ status: 'ok', days: [] })).toBeNull();
  });

  it('reads a missing or broken other as none', () => {
    expect(readSharedLinksDetail({ ...DETAIL, other: undefined })).toMatchObject({ other: 0 });
    expect(readSharedLinksDetail({ ...DETAIL, other: -3 })).toMatchObject({ other: 0 });
  });

  it('reads the verified part of other: at most other, and a missing or broken one as unknown', () => {
    expect(readSharedLinksDetail(DETAIL)).toMatchObject({ other_verified: 12 });
    expect(readSharedLinksDetail({ ...DETAIL, other_verified: undefined })).toMatchObject({
      other_verified: null,
    });
    expect(readSharedLinksDetail({ ...DETAIL, other_verified: 'many' })).toMatchObject({
      other_verified: null,
    });
    expect(readSharedLinksDetail({ ...DETAIL, other_verified: 9999 })).toMatchObject({
      other_verified: 5678,
    });
  });
});

describe('SharedLinksSection', () => {
  it('asks the admin endpoint once and shows the shares beside what /stats leaves out', async () => {
    const fetchMock = answerWith(DETAIL);

    render(<SharedLinksSection token="admin-token" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('shared-links-totals')).toHaveTextContent(
        '1,234 by named platforms (on /stats) · 5,678 other (not counted as shares, 12 verified)'
      );
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/debug\/shared-links$/);
    // An app that fetches from the sender's phone has no verified fetch at all.
    expect(screen.getByTestId('shared-links-platforms')).toHaveTextContent(
      'teams 1,200 (1,150 verified) · signal & similar 34 (0 verified)'
    );
    expect(screen.getByTestId('shared-links-top')).toHaveTextContent(
      'most shared: scatter-basic · matplotlib 900, heatmap-basic 334'
    );
  });

  it('shows a total without the verified part when the answer names no verdict', async () => {
    // An API revision older than the page, which kept the verdicts in an object of their own:
    // no count is better than a zero nobody measured.
    answerWith({
      ...DETAIL,
      other_verified: undefined,
      platforms: DETAIL.platforms.map(({ platform, shares }) => ({ platform, shares })),
      verified: { teams: 1150, other: 12 },
    });

    render(<SharedLinksSection token="admin-token" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('shared-links-platforms')).toHaveTextContent(
        'teams 1,200 · signal & similar 34'
      );
    });
    expect(screen.getByTestId('shared-links-platforms')).not.toHaveTextContent('verified');
    expect(screen.getByTestId('shared-links-totals')).toHaveTextContent(
      '1,234 by named platforms (on /stats) · 5,678 other (not counted as shares)'
    );
  });

  it.each([
    ['no database', { status: 'not_configured' }, true, 'no database configured'],
    ['a table that is not there yet', { status: 'unavailable' }, true, /counters unavailable/],
    ['a refused request', {}, false, /counters unavailable/],
  ])('is one line for %s', async (_, body, ok, line) => {
    answerWith(body, ok);

    render(<SharedLinksSection token="" reloadCounter={0} />);

    await waitFor(() => {
      expect(screen.getByTestId('shared-links-empty')).toHaveTextContent(line);
    });
    expect(screen.queryByTestId('shared-links-totals')).not.toBeInTheDocument();
  });

  it('asks again when the page reloads its sections', async () => {
    const fetchMock = answerWith(DETAIL);

    const view = render(<SharedLinksSection token="admin-token" reloadCounter={0} />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    view.rerender(<SharedLinksSection token="admin-token" reloadCounter={1} />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });
});
