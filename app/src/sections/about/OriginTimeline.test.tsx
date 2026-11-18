import { describe, expect, it } from 'vitest';

import { OriginTimeline } from 'src/sections/about/OriginTimeline';
import { render, screen } from 'src/test-utils';

const NOW = new Date('2026-11-17T12:00:00Z');

describe('OriginTimeline', () => {
  // The picks' labels; test_readme_claims.py holds the dates and releases to CHANGELOG.md.
  it('lists the points in date order, each date with what happened, ending today', () => {
    render(<OriginTimeline now={NOW} />);

    const list = screen.getByRole('list');
    expect(list.tagName).toBe('OL');
    expect(
      Array.from(list.children).map(item => item.textContent?.replace(/\s+/g, ' ').trim())
    ).toEqual([
      'nov 2025 pyplots.ai',
      'apr 2026 · 1.0.0 first github release',
      'apr 2026 · 2.0.0 anyplot.ai',
      'may 2026 · 2.4.0 r / ggplot2',
      'jun 2026 · 3.0.0 julia & javascript · 15 libraries',
      'nov 2026 · 4.0.0 use with my data',
      'today',
    ]);
  });

  // 1.0.0 is when the GitHub releases began; the site was live before it.
  it('names 1.0.0 the first github release, not a launch', () => {
    render(<OriginTimeline now={NOW} />);

    expect(screen.getByText('first github release')).toBeInTheDocument();
    expect(screen.queryByText(/launch/)).not.toBeInTheDocument();
  });

  it('marks each date up for machines', () => {
    const { container } = render(<OriginTimeline now={NOW} />);

    expect(
      Array.from(container.querySelectorAll('time')).map(time => time.getAttribute('datetime'))
    ).toEqual(['2025-11', '2026-04-07', '2026-04-23', '2026-05-18', '2026-06-10', '2026-11-03']);
  });
});
