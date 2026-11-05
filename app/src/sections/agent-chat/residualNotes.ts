/**
 * A result card's notes in plain words. The server's residual lines are written for the
 * repair: `<ID>[, <ID>] (<render>): <observed> → <target>. Likely cause: <code element>.`,
 * with rubric ids, pixel counts and the code to change. A visitor reads one plain line per
 * issue instead, by the rubric id, and the lines in full stay behind the notes' ⓘ.
 */

/** A residual line in the review's grammar: its ids, then the render it was seen in. */
const DEFECT_LINE = /^((?:[A-Z]{2}-\d{2})(?:, [A-Z]{2}-\d{2})*) \((?:light|dark|both|code)\): /;

/**
 * Each id's issue in plain words, the most telling first: a line that names two ids (`VQ-05,
 * AR-09`: the axis title cut off at the canvas edge) reads as the first of them in this order.
 */
const PLAIN: [id: string, text: string][] = [
  ['AR-09', 'some text is cut off at the edge of the image'],
  ['VQ-02', 'some labels overlap'],
  ['VQ-01', 'some text is small to read'],
  ['VQ-03', 'some marks are hard to see'],
  ['VQ-04', 'some colors are hard to tell apart'],
  ['SC-03', 'a column may be drawn in the wrong place'],
  ['SC-01', 'the plot may not be the kind the catalogue plot is'],
  ['SC-02', 'something the plot should show may be missing'],
  ['SC-04', 'a title, label or legend may not read as asked'],
  ['DQ-03', 'some values may not be drawn as they are in the data'],
  ['VQ-06', 'an axis label or the title says too little'],
  ['VQ-07', "some colors are not the site's palette"],
  ['VQ-05', 'the plot uses the space of the image poorly'],
];

/** An issue under an id the list does not name. */
const OTHER = 'a detail of the plot could be better';

/** One residual line in plain words; a line outside the grammar is plain already and stays. */
export function plainNote(line: string): string {
  const match = DEFECT_LINE.exec(line);
  if (!match) return line;
  const ids = match[1].split(', ');
  return PLAIN.find(([id]) => ids.includes(id))?.[1] ?? OTHER;
}

/** The card's notes: one plain line per issue, in the order the residual lines first name it. */
export function plainNotes(lines: readonly string[]): string[] {
  return [...new Set(lines.map(plainNote))];
}
