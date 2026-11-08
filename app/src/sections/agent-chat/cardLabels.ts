/**
 * The labels the thread's cards carry on their border (`CardFrame.tsx`), each with the same in
 * words for a screen reader, which reads `·` and `×` badly.
 */

import type { DataSnapshot, VersionDecision } from 'src/hooks/useAgentSession';
import { countOf } from 'src/sections/agent-chat/countOf';
import { cutRequest } from 'src/sections/agent-chat/threadModel';

/** A card's label on its border, and the same in words. */
export interface CardLabel {
  text: string;
  spoken: string;
}

/** A table's shape on a label, `48 rows × 4 cols`, and the same in words, `48 rows by 4 columns`. */
function shapeOf(rows: number, columns: number): CardLabel {
  return {
    text: `${countOf(rows, 'row')} × ${countOf(columns, 'col')}`,
    spoken: `${countOf(rows, 'row')} by ${countOf(columns, 'column')}`,
  };
}

/**
 * The label of a data card without a version number: what the data holds, `data · 48 rows × 4
 * cols`, read out as "data, 48 rows by 4 columns", for a card whose item carries no snapshot (a
 * thread built by hand). A table read from text (`from: 'text'`), which waits for its decision, is
 * `read from text · 3 rows × 2 cols`.
 */
export function dataCardLabel(rows: number, columns: number, from?: 'text'): CardLabel {
  const shape = shapeOf(rows, columns);
  return from === 'text'
    ? { text: `read from text · ${shape.text}`, spoken: `table read from text, ${shape.spoken}` }
    : { text: `data · ${shape.text}`, spoken: `data, ${shape.spoken}` };
}

/**
 * A data version's label, on the live card's border and as an older version's folded line: its
 * number in the session, how it came about and its shape, `data v3 · made long · 48 rows × 4
 * cols` (`DataSnapshot.label`). A folded version's label is the button that opens it, so its name
 * keeps the words on screen in their order, `Data v3, made long, 48 rows by 4 columns`, and a voice
 * command that says them finds it (WCAG 2.5.3); the live card's label reads the same words.
 */
export function dataVersionLabel(
  snapshot: Pick<DataSnapshot, 'n' | 'summary' | 'label' | 'rows' | 'columns'>
): CardLabel {
  const shape = shapeOf(snapshot.rows, snapshot.columns);
  return {
    text: `${snapshot.label} · ${shape.text}`,
    spoken: `Data v${snapshot.n}, ${snapshot.summary}, ${shape.spoken}`,
  };
}

/** What the server keeps for a file's name its content check refused (`dataset_context.FILE_NAME_WITHHELD`). */
const FILE_NAME_WITHHELD = '(name withheld)';

/**
 * The file a data version came from, as its card's source line names it: `from "sales.csv"`, or
 * that the content check withheld the name. The live card and an older version's folded card say
 * it alike.
 */
export function fileSource(name: string): string {
  return name === FILE_NAME_WITHHELD
    ? 'from a file, name withheld by the content check'
    : `from "${name}"`;
}

/**
 * A plot card's label on its border and its folded line: `plot v2 · matplotlib · title in German`,
 * the version, its library and what it answered (`plotSummaries` in `threadModel.ts`). What the
 * version kept of the remembered decisions is not the label's, so a folded version still says what
 * it answered: the open card's first line names it (`decisionsText`). It
 * names the button the label is, so its name keeps the words on screen in their order, `Plot v2,
 * matplotlib, title in German`, and a voice command that says them finds it (WCAG 2.5.3); only the
 * `·` give way to commas.
 */
export function plotCardLabel(
  number: number,
  library: string,
  summary: string | null | undefined
): CardLabel {
  return {
    text: `plot v${number} · ${library}${summary ? ` · ${summary}` : ''}`,
    spoken: `Plot v${number}, ${library}${summary ? `, ${summary}` : ''}`,
  };
}

/**
 * One part of a plot card's decisions line: `kept: y = 7 line · x label` or `new: log scale on
 * y`, each text cut as a label quotes a request (`cutRequest`), and in words with the full texts;
 * `null` for an empty list. A decision whose text no list named counts all the same, as `1 more`
 * after the texts (`kept: 3 decisions` when none has one), so the line names every decision the
 * server listed for the version.
 */
export function decisionsText(part: 'kept' | 'new', list: VersionDecision[]): CardLabel | null {
  if (list.length === 0) return null;
  const texts = list.flatMap(item => (item.text === null ? [] : [item.text]));
  const unnamed = list.length - texts.length;
  if (texts.length === 0) {
    const count = countOf(unnamed, 'decision');
    return { text: `${part}: ${count}`, spoken: `${part}: ${count}` };
  }
  return {
    text: `${part}: ${[...texts.map(cutRequest), ...(unnamed ? [`${unnamed} more`] : [])].join(' · ')}`,
    spoken: `${part}: ${texts.join(', ')}${unnamed ? `, and ${countOf(unnamed, 'more decision')}` : ''}`,
  };
}
