import { describe, expect, it } from 'vitest';

import { PIPELINE_STEPS, splitDetail } from 'src/sections/about/figureData';
import { PipelineFlow } from 'src/sections/about/PipelineFlow';
import { render, screen, styleAt, within } from 'src/test-utils';

/** The text a screen reader reads: without the parts hidden from it, whitespace collapsed. */
function spoken(element: Element): string {
  const copy = element.cloneNode(true) as Element;
  for (const hidden of copy.querySelectorAll('[aria-hidden="true"]')) hidden.remove();
  return (copy.textContent ?? '').replace(/\s+/g, ' ').trim();
}

describe('PipelineFlow', () => {
  // The words of the ASCII list the figure replaced, in its order.
  it('reads the steps in order, each with what ai does and what I do in it', () => {
    render(<PipelineFlow />);

    const figure = screen.getByRole('figure', { name: '// pipeline' });
    const steps = within(figure).getByRole('list');
    expect(steps.tagName).toBe('OL');
    expect(within(steps).getAllByRole('listitem').map(spoken)).toEqual([
      'idea a github issue',
      'spec ai drafts I approve',
      'code ai writes (per library)',
      'review ai scores (24 criteria)',
      'fix ai repairs (up to 4 times)',
    ]);
    // The rules stand under every step, after the list, as the figure's last line.
    expect(steps.nextElementSibling).toBe(figure.lastElementChild);
    expect(spoken(steps.nextElementSibling!)).toBe('rules I set and change them');
  });

  // Green text in the site's text shade, never the brand green, which reads 3.08:1 on cream.
  it('marks my own steps in the green text shade, and only those', () => {
    render(<PipelineFlow />);

    for (const mine of ['I approve', 'I set and change them']) {
      expect(styleAt(screen.getByText(mine)).color).toBe('var(--code-comment)');
    }
    expect(styleAt(screen.getByText('ai drafts')).color).not.toBe('var(--code-comment)');
    expect(styleAt(screen.getByText('rules')).color).toBe('var(--ink)');
  });

  it('hides the arrows from screen readers', () => {
    render(<PipelineFlow />);

    const arrows = screen.getAllByText(/^[→⇄]$/);
    // Four between the five steps, one between "rules" and my part.
    expect(arrows).toHaveLength(5);
    for (const arrow of arrows) expect(arrow).toHaveAttribute('aria-hidden', 'true');
  });

  it('splits a detail in brackets from its action', () => {
    expect(splitDetail('ai scores (24 criteria)')).toEqual(['ai scores', '(24 criteria)']);
    expect(splitDetail('ai repairs (up to 4 times)')).toEqual(['ai repairs', '(up to 4 times)']);
    expect(splitDetail('a github issue')).toEqual(['a github issue', null]);
    expect(PIPELINE_STEPS.map(({ step }) => step)).toEqual([
      'idea',
      'spec',
      'code',
      'review',
      'fix',
    ]);
  });
});
