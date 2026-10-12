import { describe, expect, it } from 'vitest';

import { UnifiedDiff } from 'src/sections/debug/UnifiedDiff';
import { render, screen } from 'src/test-utils';

const DIFF = [
  '--- catalogue/scatter-basic/matplotlib.py',
  '+++ case/plot.py',
  '@@ -1,3 +1,3 @@',
  ' import pandas as pd',
  '-ax.legend()',
  '+ax.legend(loc="upper left")',
  '@@ -9,2 +9,2 @@',
  '--- a removed line that starts with two dashes',
  '+++ an added line that starts with two pluses',
  '',
].join('\n');

describe('UnifiedDiff', () => {
  it('renders one span per line, typed by its prefix', () => {
    render(<UnifiedDiff diff={DIFF} label="Diff of the case" />);
    const block = screen.getByLabelText('Diff of the case');
    const lines = Array.from(block.querySelectorAll('[data-line]'));
    expect(lines.map(line => line.getAttribute('data-line'))).toEqual([
      'file',
      'file',
      'hunk',
      'context',
      'del',
      'add',
      'hunk',
      'del',
      'add',
    ]);
    expect(lines[5]).toHaveTextContent('+ax.legend(loc="upper left")');
  });

  it('tints additions and deletions and keeps the text in ink', () => {
    render(<UnifiedDiff diff={DIFF} label="Diff of the case" />);
    const block = screen.getByLabelText('Diff of the case');
    const add = block.querySelector('[data-line="add"]') as HTMLElement;
    const del = block.querySelector('[data-line="del"]') as HTMLElement;
    expect(getComputedStyle(add).backgroundColor).toBe('rgba(0, 158, 115, 0.16)');
    expect(getComputedStyle(del).backgroundColor).toBe('rgba(174, 48, 48, 0.16)');
    expect(getComputedStyle(add).color).toBe('var(--ink)');
  });
});
