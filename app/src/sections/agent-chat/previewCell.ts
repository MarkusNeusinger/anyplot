/**
 * The preview's cell text with its whitespace made visible (owner decision of 2026-10-15).
 *
 * The server sends each preview cell with its line breaks and runs of spaces as they are
 * (`parse.preview_cell`). A table cell drawn as HTML would fold them into one space, so the
 * preview would show `a  b` or a two-line cell as something the data does not hold. Each
 * line break becomes `↵`, each tab `→` (the cells do not wrap, so a tab would look like a
 * space) and every space of a run of two or more `·`; a single space between words stays
 * a space. The marks are segments of their own, so the page can
 * draw them muted and name them for a screen reader.
 */

export const LINE_BREAK_MARK = '↵';
export const SPACE_MARK = '·';
export const TAB_MARK = '→';

export interface PreviewSegment {
  text: string;
  /** `break` for a line break, `spaces` for a run of spaces, `tab` for a tab; absent for the cell's own text. */
  mark?: 'break' | 'spaces' | 'tab';
}

const WHITESPACE = /\r\n|\r|\n| {2,}|\t/g;

export function previewSegments(cell: string): PreviewSegment[] {
  const segments: PreviewSegment[] = [];
  let last = 0;
  for (const match of cell.matchAll(WHITESPACE)) {
    const at = match.index ?? 0;
    if (at > last) segments.push({ text: cell.slice(last, at) });
    const run = match[0];
    if (run === '\t') segments.push({ text: TAB_MARK, mark: 'tab' });
    else if (run.startsWith(' '))
      segments.push({ text: SPACE_MARK.repeat(run.length), mark: 'spaces' });
    else segments.push({ text: LINE_BREAK_MARK, mark: 'break' });
    last = at + run.length;
  }
  if (last < cell.length) segments.push({ text: cell.slice(last) });
  return segments;
}
