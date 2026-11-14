import { describe, expect, it } from 'vitest';

import { CHART_PX, columnPx, STRIP_BAR } from 'src/sections/stats/stripGeometry';
import { ALL_VISITS_HINT, readVisitors } from 'src/sections/stats/visitors';
import { VisitorsTile } from 'src/sections/stats/VisitorsTile';
import { render, screen, userEvent, within } from 'src/test-utils';

const formatNum = (value: number): string => value.toLocaleString('en-US');

/** 28 days, oldest first, starting on *first*: each with visitors, visits and engaged visits. */
const window28 = (first: string) => {
  const start = new Date(`${first}T00:00:00Z`).getTime();
  return Array.from({ length: 28 }, (_, index) => ({
    date: new Date(start + index * 86400000).toISOString().slice(0, 10),
    visitors: 100 + index,
    visits: 150 + index,
    engaged: 40 + index,
  }));
};

const SINCE = '2026-11-10';
/** The first window that is counted on every day: it starts on the day the counting began. */
const COUNTED = readVisitors({ points: window28(SINCE), engaged_since: SINCE });
/** The day before: the window's first day has no number yet. */
const NOT_YET = readVisitors({
  points: window28('2026-11-09').map((point, index) =>
    index === 0 ? { ...point, engaged: null } : point
  ),
  engaged_since: SINCE,
});

describe('VisitorsTile', () => {
  it('heads the tile and links the public dashboard', () => {
    render(<VisitorsTile answer={COUNTED} formatNum={formatNum} />);

    expect(screen.getByText('visitors')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /plausible\.view\(\)/ })).toHaveAttribute(
      'href',
      'https://plausible.io/anyplot.ai'
    );
  });

  it('says what a bar is and the sum, once every day of the window is counted', () => {
    render(<VisitorsTile answer={COUNTED} formatNum={formatNum} />);

    // 40 + 41 + ... + 67.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'visits with a second page or an interaction · last 28 days · 1,498 total'
    );
  });

  it('draws one column per day, its height the day’s engaged visits and not its visitors', () => {
    render(<VisitorsTile answer={COUNTED} formatNum={formatNum} />);

    const bars = screen.getAllByTestId('visitors-bar');
    expect(bars).toHaveLength(28);
    // 67 engaged visits on the last day fill the strip; the first day's 40 are its share.
    expect(bars[27]).toHaveStyle({ height: `${CHART_PX}px`, backgroundColor: STRIP_BAR.color });
    expect(bars[0]).toHaveStyle({ height: `${columnPx(40, 67)}px` });
    const days = within(
      screen.getByRole('group', { name: 'visits with a second page or an interaction per day' })
    ).getAllByRole('img');
    expect(days[0]).toHaveAccessibleName('2026-11-10: 40 visits');
    expect(days[27]).toHaveAccessibleName('2026-12-07: 67 visits');
  });

  it('sets all visits of the same days under the strip', () => {
    render(<VisitorsTile answer={COUNTED} formatNum={formatNum} />);

    // 150 + 151 + ... + 177.
    expect(screen.getByTestId('visitors-all').textContent).toBe('all visits: 4,578');
  });

  it('explains the word "all" as a hint: what else is in that number', async () => {
    render(<VisitorsTile answer={COUNTED} formatNum={formatNum} />);

    const term = screen.getByRole('button', { name: 'all' });
    expect(term).toHaveAccessibleDescription(ALL_VISITS_HINT);
    expect(ALL_VISITS_HINT).toMatch(/a visit of one page without a click/);
    expect(ALL_VISITS_HINT).toMatch(/automated traffic/);

    await userEvent.setup().click(term);

    expect(await screen.findByText(ALL_VISITS_HINT)).toBeInTheDocument();
  });

  it('names a day without a number "not counted", and keeps it out of both sums', () => {
    // A day whose answer had visits and no bounce rate: no number, never "every visit engaged".
    const gap = readVisitors({
      points: window28(SINCE).map((point, index) =>
        index === 26 ? { ...point, engaged: null } : point
      ),
      engaged_since: SINCE,
    });
    render(<VisitorsTile answer={gap} formatNum={formatNum} />);

    const days = within(
      screen.getByRole('group', { name: 'visits with a second page or an interaction per day' })
    ).getAllByRole('img');
    expect(days[26]).toHaveAccessibleName('2026-12-06: not counted');
    // The 66 engaged of that day and its 176 visits are in neither sum.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'visits with a second page or an interaction · last 28 days · 1,432 total'
    );
    expect(screen.getByTestId('visitors-all').textContent).toBe('all visits: 4,402');
  });

  it('keeps drawing the unique visitors until every day of the window is counted', () => {
    // One day too early: a strip with engaged visits would be empty for the first day, and
    // for 24 of 28 days on the day this shipped.
    render(<VisitorsTile answer={NOT_YET} formatNum={formatNum} />);

    // 100 + 101 + ... + 127.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'unique visitors · last 28 days · 3,178 total'
    );
    const days = within(
      screen.getByRole('group', { name: 'unique visitors per day' })
    ).getAllByRole('img');
    expect(days[0]).toHaveAccessibleName('2026-11-09: 100 visitors');
    expect(days[27]).toHaveAccessibleName('2026-12-06: 127 visitors');
    expect(screen.getAllByTestId('visitors-bar')[27]).toHaveStyle({ height: `${CHART_PX}px` });
    expect(screen.queryByTestId('visitors-all')).not.toBeInTheDocument();
  });

  it('draws the unique visitors for an answer without engaged visits', () => {
    // An API revision older than the page: it claims nothing about engaged visits.
    const older = readVisitors({
      points: window28(SINCE).map(({ date, visitors }) => ({ date, visitors })),
    });
    render(<VisitorsTile answer={older} formatNum={formatNum} />);

    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'unique visitors · last 28 days · 3,178 total'
    );
    expect(screen.queryByTestId('visitors-all')).not.toBeInTheDocument();
  });

  it.each([
    ['while the answer is out', null, 'loading visitor data...'],
    [
      'for an answer without days',
      readVisitors({ points: [] }),
      'visitor data unavailable — see plausible.io/anyplot.ai',
    ],
  ])('is one muted line %s', (_, answer, line) => {
    render(<VisitorsTile answer={answer} formatNum={formatNum} />);

    expect(screen.getByText(line)).toBeInTheDocument();
    expect(screen.queryByTestId('visitors-day')).not.toBeInTheDocument();
    // No total in the header line before there is one.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'unique visitors · last 28 days'
    );
  });
});
