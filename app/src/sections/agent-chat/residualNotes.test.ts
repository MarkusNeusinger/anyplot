import { describe, expect, it } from 'vitest';

import { plainNote, plainNotes } from 'src/sections/agent-chat/residualNotes';

// The residual lines of the UX walk's first plot (bar-basic in matplotlib), as the server wrote them.
const WALK = [
  'AR-09 (light): text extends 17 px beyond the canvas edge → keep every text inside the canvas. Likely cause: a label position, a long tick label or a large font size.',
  'VQ-02 (light): 71 pairs of tick labels overlap → no overlapping tick labels. Likely cause: too many ticks for the axis length, or unrotated long labels.',
  "VQ-05, AR-09 (light): the x-axis title 'Industry' is cut off at the bottom edge of the canvas → all text fully inside the canvas (+17 px of clearance). Likely cause: fig.subplots_adjust(bottom=0.64).",
  "VQ-01 (light): the rotated industry tick labels are set at 7 pt → 8 pt or larger. Likely cause: ax.tick_params(axis='x', labelsize=7).",
  'VQ-05 (light): the plot area uses only the upper part of the canvas → a taller axes area. Likely cause: figsize=(8, 4.5).',
];

describe('plainNotes', () => {
  it('reads one plain line per issue, without ids, pixels or code', () => {
    expect(plainNotes(WALK)).toEqual([
      'some text is cut off at the edge of the image',
      'some labels overlap',
      'some text is small to read',
      'the plot uses the space of the image poorly',
    ]);
    for (const line of plainNotes(WALK)) expect(line).not.toMatch(/[A-Z]{2}-\d{2}|px|\(|=/);
  });

  it('reads a line with two ids as the more telling one', () => {
    expect(plainNote('VQ-05, AR-09 (dark): the legend is cut off → inside. Likely cause: x.')).toBe(
      'some text is cut off at the edge of the image'
    );
    expect(
      plainNote('SC-03 (code): a column is unused → use it. Likely cause: the adaptation.')
    ).toBe('a column may be drawn in the wrong place');
  });

  it('keeps a line without ids as it is, and names an unknown id generally', () => {
    const plain = 'the review scored the plot 72 of 100, below the ship score of 80';
    expect(plainNote(plain)).toBe(plain);
    expect(plainNote('DE-02 (both): the grid is heavy → lighter. Likely cause: x.')).toBe(
      'a detail of the plot could be better'
    );
  });

  it('reads the ids of a line in another form too, so none shows raw', () => {
    expect(plainNote('VQ-03 light: two markers overlap the label; likely cause: axis limits')).toBe(
      'some marks are hard to see'
    );
    expect(plainNote('VQ-02: the ticks collide')).toBe('some labels overlap');
    // An id inside the text is no id of the line.
    expect(plainNote('see VQ-02 (light) for the overlap')).toBe(
      'see VQ-02 (light) for the overlap'
    );
  });
});
