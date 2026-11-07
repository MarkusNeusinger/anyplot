/**
 * The labels the thread's cards carry on their border (`CardFrame.tsx`), each with the same in
 * words for a screen reader, which reads `·` and `×` badly.
 */

import { countOf } from 'src/sections/agent-chat/countOf';

/** A card's label on its border, and the same in words. */
export interface CardLabel {
  text: string;
  spoken: string;
}

/**
 * The data card's label until the thread numbers its versions: what the data holds, `data · 48
 * rows × 4 cols`, read out as "data, 48 rows by 4 columns". A table read from text (`from:
 * 'text'`), which waits for its decision, is `read from text · 3 rows × 2 cols`.
 */
export function dataCardLabel(rows: number, columns: number, from?: 'text'): CardLabel {
  const shape = `${countOf(rows, 'row')} × ${countOf(columns, 'col')}`;
  const words = `${countOf(rows, 'row')} by ${countOf(columns, 'column')}`;
  return from === 'text'
    ? { text: `read from text · ${shape}`, spoken: `table read from text, ${words}` }
    : { text: `data · ${shape}`, spoken: `data, ${words}` };
}

/**
 * A plot card's label on its border and its folded line: `plot v2 · matplotlib · title in German`,
 * the version, its library and what it answered (`plotSummaries` in `threadModel.ts`), read out
 * as "Plot version 2, matplotlib, title in German".
 */
export function plotCardLabel(
  number: number,
  library: string,
  summary: string | null | undefined
): CardLabel {
  return {
    text: `plot v${number} · ${library}${summary ? ` · ${summary}` : ''}`,
    spoken: `Plot version ${number}, ${library}${summary ? `, ${summary}` : ''}`,
  };
}
