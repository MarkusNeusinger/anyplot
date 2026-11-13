import { describe, expect, it } from 'vitest';

import { CHART_PX, MIN_BAR_PX, STRIP_BAR } from 'src/sections/stats/stripGeometry';
import { ALL_VISITS_HINT, readVisitors } from 'src/sections/stats/visitors';
import { VisitorsTile } from 'src/sections/stats/VisitorsTile';
import { render, screen, userEvent, within } from 'src/test-utils';

const formatNum = (value: number): string => value.toLocaleString('en-US');

/**
 * 28 days, oldest first. The counting began on the 25th of them: the days before have visits
 * and no engaged ones, the last four have 61, 76, 68 and 80 engaged visits among hundreds.
 */
const SINCE_INDEX = 24;
const dateOf = (index: number): string =>
  new Date(Date.UTC(2026, 9, 17 + index)).toISOString().slice(0, 10);
const ANSWER = readVisitors({
  points: Array.from({ length: 28 }, (_, index) => ({
    date: dateOf(index),
    visitors: 100 + index,
    visits: [303, 360, 526, 614][index - SINCE_INDEX] ?? 150,
    engaged: [61, 76, 68, 80][index - SINCE_INDEX] ?? null,
  })),
  engaged_since: dateOf(SINCE_INDEX),
});

describe('VisitorsTile', () => {
  it('heads the tile and links the public dashboard', () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    expect(screen.getByText('visitors')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /plausible\.view\(\)/ })).toHaveAttribute(
      'href',
      'https://plausible.io/anyplot.ai'
    );
  });

  it('says what a bar is, since when it is counted, and the sum', () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    // 61 + 76 + 68 + 80. The window still holds days from before the counting began, so the
    // header names the day it began in place of "last 28 days".
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'visits with a second page or an interaction · since 2026-11-10 · 285 total'
    );
  });

  it('says "last 28 days" once every day of the window is counted', () => {
    const full = readVisitors({
      points: ANSWER.points.map(point => ({ ...point, engaged: point.engaged ?? 10 })),
      engaged_since: '2026-10-01',
    });
    render(<VisitorsTile answer={full} formatNum={formatNum} />);

    // 24 days of 10 and the four counted ones.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'visits with a second page or an interaction · last 28 days · 525 total'
    );
  });

  it('draws one column per day, its height the day’s engaged visits and not its visitors', () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    const bars = screen.getAllByTestId('visitors-bar');
    expect(bars).toHaveLength(28);
    // 80 is the busiest day although 614 visits and 127 visitors stand behind it; 61 of 80 is
    // its share of the strip.
    expect(bars[27]).toHaveStyle({ height: `${CHART_PX}px`, backgroundColor: STRIP_BAR.color });
    expect(bars[24]).toHaveStyle({ height: `${(CHART_PX * 61) / 80}px` });
  });

  it('draws a day before the counting began as the floor and says so, not "0 visits"', () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    const strip = screen.getByRole('group', {
      name: 'visits with a second page or an interaction per day',
    });
    const days = within(strip).getAllByRole('img');
    expect(days[0]).toHaveAccessibleName('2026-10-17: not counted before 2026-11-10');
    expect(days[23]).toHaveAccessibleName('2026-11-09: not counted before 2026-11-10');
    expect(days[24]).toHaveAccessibleName('2026-11-10: 61 visits');
    expect(days[27]).toHaveAccessibleName('2026-11-13: 80 visits');
    const bars = screen.getAllByTestId('visitors-bar');
    expect(bars[0]).toHaveStyle({ height: `${MIN_BAR_PX}px` });
    expect(bars[0]).not.toHaveStyle({ backgroundColor: STRIP_BAR.color });
  });

  it('sets all visits of the same days under the strip', () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    // 303 + 360 + 526 + 614: the days before the counting began are in neither number.
    expect(screen.getByTestId('visitors-all').textContent).toBe('all visits: 1,803');
  });

  it('names a later day without a number "not counted", and keeps it out of both sums', () => {
    // A day whose answer had visits and no bounce rate: no number, never "every visit engaged".
    const gap = readVisitors({
      points: ANSWER.points.map((point, index) =>
        index === 26 ? { ...point, engaged: null } : point
      ),
      engaged_since: dateOf(SINCE_INDEX),
    });
    render(<VisitorsTile answer={gap} formatNum={formatNum} />);

    const days = within(
      screen.getByRole('group', { name: 'visits with a second page or an interaction per day' })
    ).getAllByRole('img');
    expect(days[26]).toHaveAccessibleName('2026-11-12: not counted');
    // 61 + 76 + 80, against 303 + 360 + 614.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'visits with a second page or an interaction · since 2026-11-10 · 217 total'
    );
    expect(screen.getByTestId('visitors-all').textContent).toBe('all visits: 1,277');
  });

  it('explains the word "all" as a hint: what else is in that number', async () => {
    render(<VisitorsTile answer={ANSWER} formatNum={formatNum} />);

    const term = screen.getByRole('button', { name: 'all' });
    expect(term).toHaveAccessibleDescription(ALL_VISITS_HINT);
    expect(ALL_VISITS_HINT).toMatch(/a visit of one page without a click/);
    expect(ALL_VISITS_HINT).toMatch(/automated traffic/);

    await userEvent.setup().click(term);

    expect(await screen.findByText(ALL_VISITS_HINT)).toBeInTheDocument();
  });

  it('draws the unique visitors, as before, for an answer without engaged visits', () => {
    // An API revision older than the page: it claims nothing about engaged visits.
    const older = readVisitors({
      points: ANSWER.points.map(({ date, visitors }) => ({ date, visitors })),
    });
    render(<VisitorsTile answer={older} formatNum={formatNum} />);

    // 100 + 101 + ... + 127.
    expect(screen.getByTestId('visitors-header').textContent).toBe(
      'unique visitors · last 28 days · 3,178 total'
    );
    const days = within(
      screen.getByRole('group', { name: 'unique visitors per day' })
    ).getAllByRole('img');
    expect(days[27]).toHaveAccessibleName('2026-11-13: 127 visitors');
    expect(screen.getAllByTestId('visitors-bar')[27]).toHaveStyle({ height: `${CHART_PX}px` });
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
