import { describe, expect, it } from 'vitest';

import type { SharedLinksResponse } from 'src/sections/stats/sharedLinks';
import { SharedLinksTile } from 'src/sections/stats/SharedLinksTile';
import { CHART_PX, MIN_BAR_PX, STRIP_BAR } from 'src/sections/stats/stripGeometry';
import { render, screen, within } from 'src/test-utils';

const formatNum = (value: number): string => value.toLocaleString('en-US');

/** 28 days, oldest first: quiet but for the last three (1, 4 and 2 shares). */
const DAYS = Array.from({ length: 28 }, (_, index) => ({
  date: new Date(Date.UTC(2026, 9, 15 + index)).toISOString().slice(0, 10),
  shares: [1, 4, 2][index - 25] ?? 0,
}));

const ANSWER: SharedLinksResponse = {
  status: 'ok',
  window_days: 28,
  total: 7,
  days: DAYS,
  platforms: [
    { platform: 'whatsapp', shares: 4 },
    { platform: 'teams', shares: 2 },
    { platform: 'whatsapp-lite', shares: 1 },
  ],
  top: [
    { spec_id: 'scatter-basic', language: 'python', library: 'matplotlib', shares: 3 },
    { spec_id: 'heatmap-basic', language: null, library: null, shares: 2 },
  ],
};

describe('SharedLinksTile', () => {
  it('heads the tile and links the privacy text that describes the counter', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    expect(screen.getByText('shared links')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /legal\.privacy\(\)/ })).toHaveAttribute(
      'href',
      '/legal#shared-links'
    );
    expect(
      screen.getByText(/link previews on messengers and social networks · last 28 days · 7 shares/)
    ).toBeInTheDocument();
  });

  it('draws one column per day, its height the day’s shares and nothing else', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    const bars = screen.getAllByTestId('shared-links-bar');
    expect(bars).toHaveLength(28);
    // The busiest day fills the strip, half of it is half as high, a day without a share is
    // the floor: the same geometry as the strips above (`columnPx`).
    expect(bars[26]).toHaveStyle({ height: `${CHART_PX}px` });
    expect(bars[27]).toHaveStyle({ height: `${CHART_PX / 2}px` });
    expect(bars[25]).toHaveStyle({ height: `${CHART_PX / 4}px` });
    expect(bars[0]).toHaveStyle({ height: `${MIN_BAR_PX}px` });
  });

  it('names every day for a pointer, a keyboard and a screen reader', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    const strip = screen.getByRole('group', { name: 'shared links per day' });
    const days = within(strip).getAllByRole('img');
    expect(days).toHaveLength(28);
    expect(days[26]).toHaveAccessibleName('2026-11-10: 4 shares');
    expect(days[25]).toHaveAccessibleName('2026-11-09: 1 share');
    expect(days[0]).toHaveAccessibleName('2026-10-15: 0 shares');
    for (const day of days) expect(day).toHaveAttribute('tabindex', '0');
    // The first and the last day stand under the strip.
    expect(screen.getByText('2026-10-15')).toBeInTheDocument();
    expect(screen.getByText('2026-11-11')).toBeInTheDocument();
  });

  it('draws its bars in the strips’ one green, and a day without a share as the muted floor', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    const bars = screen.getAllByTestId('shared-links-bar');
    expect(bars[26]).toHaveStyle({
      backgroundColor: STRIP_BAR.color,
      opacity: String(STRIP_BAR.opacity),
    });
    expect(bars[0]).not.toHaveStyle({ backgroundColor: STRIP_BAR.color });
  });

  it('lists the platforms with their 28-day sums, largest first, in one line', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    expect(screen.getByTestId('shared-links-platforms').textContent).toBe(
      'by platform: whatsapp 4 · teams 2 · signal & similar 1'
    );
  });

  it('links the most shared plot pages: an implementation and a hub are entries of their own', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    const top = screen.getByTestId('shared-links-top');
    const links = within(top).getAllByRole('link');
    expect(links.map(link => [link.textContent, link.getAttribute('href')])).toEqual([
      ['scatter-basic · matplotlib', '/scatter-basic/python/matplotlib'],
      ['heatmap-basic', '/heatmap-basic'],
    ]);
    expect(top.textContent).toBe('most shared: scatter-basic · matplotlib 3 · heatmap-basic 2');
  });

  it('holds no paragraph of its own: what a share is stands on the legal page it links', () => {
    render(<SharedLinksTile answer={ANSWER} formatNum={formatNum} />);

    expect(screen.queryByTestId('shared-links-footnote')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'legal.privacy()' })).toHaveAttribute(
      'href',
      '/legal#shared-links'
    );
  });

  it('shows no platform line and no list for a window without a share', () => {
    const quiet = {
      ...ANSWER,
      total: 0,
      platforms: [],
      top: [],
      days: DAYS.map(day => ({ ...day, shares: 0 })),
    };
    render(<SharedLinksTile answer={quiet} formatNum={formatNum} />);

    expect(screen.getByText(/last 28 days · 0 shares/)).toBeInTheDocument();
    expect(screen.getAllByTestId('shared-links-bar')).toHaveLength(28);
    expect(screen.queryByTestId('shared-links-platforms')).not.toBeInTheDocument();
    expect(screen.queryByTestId('shared-links-top')).not.toBeInTheDocument();
  });

  it.each([
    ['while the answer is out', undefined, 'loading shared link data...'],
    ['for a failed request or an answer that is not ok', null, 'shared link data unavailable'],
  ])('is one muted line %s', (_, answer, line) => {
    render(<SharedLinksTile answer={answer} formatNum={formatNum} />);

    expect(screen.getByText(line)).toBeInTheDocument();
    expect(screen.queryByTestId('shared-links-day')).not.toBeInTheDocument();
    // No total in the header line before there is one.
    expect(screen.getByText(/last 28 days$/)).toBeInTheDocument();
  });
});
