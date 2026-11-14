import { describe, expect, it } from 'vitest';

import { engagedDays, readVisitors } from 'src/sections/stats/visitors';

const ANSWER = {
  points: [
    { date: '2026-11-08', visitors: 264, visits: 275, engaged: null },
    { date: '2026-11-09', visitors: 259, visits: 280, engaged: null },
    { date: '2026-11-10', visitors: 292, visits: 303, engaged: 61 },
    { date: '2026-11-11', visitors: 353, visits: 360, engaged: 76 },
  ],
  engaged_since: '2026-11-10',
};

describe('readVisitors', () => {
  it('reads an answer as it is', () => {
    expect(readVisitors(ANSWER)).toEqual({ points: ANSWER.points, engagedSince: '2026-11-10' });
  });

  it('reads an answer of an older API revision as days with visitors only', () => {
    const older = { points: [{ date: '2026-11-11', visitors: 353 }] };

    expect(readVisitors(older)).toEqual({
      points: [{ date: '2026-11-11', visitors: 353, visits: null, engaged: null }],
      engagedSince: null,
    });
  });

  it.each([
    ['no body', null],
    ['a string', 'ok'],
    ['no points', {}],
    ['points that are no list', { points: 'none' }],
    ['an empty list', { points: [] }],
  ])('reads %s as an answer without days', (_, body) => {
    expect(readVisitors(body).points).toEqual([]);
  });

  it('turns a number that is none into zero, drops a day without a date', () => {
    const answer = readVisitors({
      points: [
        { date: '2026-11-12', visitors: -4, visits: 12.9, engaged: 3.2 },
        { visitors: 9, visits: 9, engaged: 9 },
        null,
        { date: '2026-11-13', visitors: 'many', visits: 20, engaged: 'some' },
      ],
      engaged_since: 'yesterday',
    });

    expect(answer).toEqual({
      points: [
        { date: '2026-11-12', visitors: 0, visits: 12, engaged: 3 },
        { date: '2026-11-13', visitors: 0, visits: 20, engaged: null },
      ],
      engagedSince: null,
    });
  });

  it('never reads more engaged visits than the day has visits', () => {
    const answer = readVisitors({
      points: [{ date: '2026-11-12', visitors: 5, visits: 6, engaged: 40 }],
    });

    expect(answer.points[0].engaged).toBe(6);
  });

  it('reads engaged visits without the day’s visits as no number', () => {
    // A part of nothing: the tile would have no total to set it against.
    const answer = readVisitors({ points: [{ date: '2026-11-12', visitors: 5, engaged: 4 }] });

    expect(answer.points[0]).toMatchObject({ visits: null, engaged: null });
  });
});

describe('engagedDays', () => {
  it('is null while the window still holds a day from before the counting began', () => {
    // The window starts on 2026-11-08, two days before the first counted one: the tile keeps
    // drawing the unique visitors, not a strip that is empty for the days without a number.
    expect(engagedDays(readVisitors(ANSWER))).toBeNull();
  });

  it('sums the engaged visits and all visits once the window’s first day is counted', () => {
    const counted = readVisitors({ ...ANSWER, points: ANSWER.points.slice(2) });

    // 61 + 76, against the 303 + 360 visits of the same two days.
    expect(engagedDays(counted)).toEqual({ engaged: 137, visits: 663 });
  });

  it('leaves a day without a number out of both sums', () => {
    // A day whose answer had visits and no bounce rate.
    const gap = readVisitors({
      points: [
        ...ANSWER.points.slice(2),
        { date: '2026-11-12', visitors: 515, visits: 526, engaged: null },
      ],
      engaged_since: '2026-11-10',
    });

    expect(engagedDays(gap)).toEqual({ engaged: 137, visits: 663 });
  });

  it('is null for an answer that names no day the counting began, or no day at all', () => {
    const older = readVisitors({ points: [{ date: '2026-11-11', visitors: 353 }] });

    expect(engagedDays(older)).toBeNull();
    expect(engagedDays(readVisitors({ points: [], engaged_since: '2026-11-10' }))).toBeNull();
    // Counted days without the date they began: an answer this page does not know.
    expect(engagedDays(readVisitors({ points: ANSWER.points.slice(2) }))).toBeNull();
  });
});
