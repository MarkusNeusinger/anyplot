import { describe, expect, it } from 'vitest';

import { RUBRIC_CAPTION, RUBRIC_PARTS } from 'src/sections/about/figureData';
import { monoWidth } from 'src/sections/about/monoWidth';
import { RubricBar } from 'src/sections/about/RubricBar';
import { render, screen, styleAt, within } from 'src/test-utils';

describe('RubricBar', () => {
  // test_readme_claims.py holds the points to prompts/quality-criteria.md; here, the order a
  // screen reader hears them in and that the caption's total is their sum.
  it('lists the six parts in the rubric order with their points, under its caption', () => {
    render(<RubricBar />);

    const figure = screen.getByRole('figure', { name: '// rubric · 100 points · 24 criteria' });
    expect(
      within(figure)
        .getAllByRole('listitem')
        .map(item => item.textContent?.replace(/\s+/g, ' ').trim())
    ).toEqual([
      '30 visual quality',
      '20 design',
      '15 spec compliance',
      '15 data quality',
      '10 code quality',
      '10 library mastery',
    ]);
    const total = RUBRIC_PARTS.reduce((sum, [, points]) => sum + points, 0);
    expect(RUBRIC_CAPTION).toContain(`· ${total} points ·`);
  });

  // The bar repeats the list's points for the eye, so a screen reader hears each part once.
  it('draws the bar in one neutral ink, hidden from screen readers', () => {
    render(<RubricBar />);

    const segments = screen.getAllByText(/^\d+$/).filter(e => e.closest('[aria-hidden="true"]'));
    expect(segments.map(segment => segment.textContent)).toEqual([
      '30',
      '20',
      '15',
      '15',
      '10',
      '10',
    ]);
    for (const segment of segments) {
      expect(styleAt(segment).backgroundColor).toBe('var(--ink-muted)');
      expect(styleAt(segment).color).toBe('var(--bg-page)');
    }
  });

  // A 10-point part of a 288px bar (a 320px phone) is 28.8px wide: with the full 8px of padding
  // and the 2px gap, 10.8px would be left for a "10" that needs 16.8px.
  it('gives up padding before a number leaves its part on a narrow phone', () => {
    render(<RubricBar />);

    const smallest = screen.getAllByText('10').filter(e => e.closest('[aria-hidden="true"]'))[0];
    const number = monoWidth('10', 14);
    for (const [bar, padding] of [
      [288, 4],
      [328, 4],
      [400, 8],
      [740, 8],
    ]) {
      const style = styleAt(smallest, bar, bar);
      expect(style.paddingLeft).toBe(`${padding}px`);
      expect(style.paddingRight).toBe(`${padding}px`);
      expect(bar * 0.1 - 2 - 2 * padding).toBeGreaterThanOrEqual(number);
    }
  });
});
