/**
 * The agent chat's thread as chapters: a pure view over the session's items
 * (`useAgentSession`), for the chapter lines, the folded versions and the counts the
 * chat shows. No component reads it yet; the thread renders the items as before
 * (`shownItems` in `steps.ts`).
 *
 * The items fall into turns: a turn starts at the user's typed message, a page action
 * (`.create_plot()`, the summary of new data) or a paste, and holds what followed it
 * until the next turn starts. A turn is about the data when it brought a data version
 * (a paste, a pick, a change the assistant or the card made), asked for the summary or
 * example data, or changed the data in the user's words; about the plot when it ran the
 * plot pipeline (a plot button's action, a plot card, a failed plot, or a typed turn
 * whose outcome is a plot). Anything else (a question, a refusal, a library switch, a
 * notice) belongs to the chapter it falls in.
 *
 * A chapter is a run of turns about one step: `data` (step 1, the data and the talk
 * about it) or `plot` (step 2). The thread opens with a data chapter; a plot turn after
 * data starts a plot chapter, and a data turn after a plot starts a data chapter again.
 * A library switch stays inside its chapter as a line of its own.
 *
 * Folds: an older data version (a `data_stub`) and every plot card but the latest
 * version's fold to one line; the live data card stays open.
 */

import type { ChatItem } from 'src/hooks/useAgentSession';
import { isPlotAction } from 'src/lib/agent';

/** What a chapter is about: the data (step 1) or the plot (step 2). */
export type ChapterKind = 'data' | 'plot';

export interface Chapter {
  /** The chapter's place in the thread, 1-based. */
  index: number;
  kind: ChapterKind;
  /** The id of the chapter's first item: where its line stands, and where a jump to it lands. */
  start: number;
  /**
   * The questions asked in it, in order: the typed turns that changed nothing (`outcome`
   * `answer`). The chapter line counts them, and its count jumps to them.
   */
  questions: number[];
  /** The data versions it holds (`DataSnapshot.n`), oldest first. */
  dataVersions: number[];
  /** The plot versions it holds, oldest first. */
  plotVersions: number[];
  /** The library switches made in it. */
  switches: number;
}

/** A row of the thread: a chapter's line, or an item with its chapter and whether it folds. */
export type ThreadRow =
  | { kind: 'chapter'; chapter: Chapter }
  | { kind: 'item'; item: ChatItem; chapter: number; folded: boolean };

export interface ThreadModel {
  rows: ThreadRow[];
  chapters: Chapter[];
}

/** Whether an item opens a turn: the user's message, a page action, or a paste. */
const opensTurn = (item: ChatItem) =>
  item.kind === 'user' || item.kind === 'action' || item.kind === 'paste';

/** The data actions: the summary of new data, and example data. */
const DATA_ACTIONS = new Set(['summarize_data', 'example_data']);

/** What a turn's items are about, or null for a turn that stays in the chapter it falls in. */
function turnKind(turn: readonly ChatItem[]): ChapterKind | null {
  const opener = turn[0];
  const brought = turn.some(
    item => item.kind === 'data' || item.kind === 'data_stub' || item.kind === 'transcription'
  );
  if (
    brought ||
    opener.kind === 'paste' ||
    (opener.kind === 'action' && DATA_ACTIONS.has(opener.action)) ||
    (opener.kind === 'user' && opener.outcome === 'data')
  ) {
    return 'data';
  }
  if (
    turn.some(item => item.kind === 'plot' || item.kind === 'plot_failed') ||
    (opener.kind === 'action' && isPlotAction(opener.action)) ||
    (opener.kind === 'user' && opener.outcome === 'plot')
  ) {
    return 'plot';
  }
  return null;
}

/** The items cut into turns; what stands before the first turn (a copied card) is a turn of its own. */
function turnsOf(items: readonly ChatItem[]): ChatItem[][] {
  const turns: ChatItem[][] = [];
  for (const item of items) {
    if (opensTurn(item) || turns.length === 0) turns.push([item]);
    else turns[turns.length - 1].push(item);
  }
  return turns;
}

/** The latest plot version among the items; 0 without one. */
function latestPlot(items: readonly ChatItem[]): number {
  let latest = 0;
  for (const item of items) if (item.kind === 'plot') latest = Math.max(latest, item.version);
  return latest;
}

/** The thread's rows and chapters (see the module notes). */
export function threadModel(items: readonly ChatItem[]): ThreadModel {
  const chapters: Chapter[] = [];
  const rows: ThreadRow[] = [];
  const latest = latestPlot(items);
  for (const turn of turnsOf(items)) {
    const kind = turnKind(turn);
    let chapter: Chapter | undefined = chapters[chapters.length - 1];
    if (!chapter || (kind !== null && kind !== chapter.kind)) {
      chapter = {
        index: chapters.length + 1,
        kind: kind ?? 'data',
        start: turn[0].id,
        questions: [],
        dataVersions: [],
        plotVersions: [],
        switches: 0,
      };
      chapters.push(chapter);
      rows.push({ kind: 'chapter', chapter });
    }
    for (const item of turn) {
      if (item.kind === 'user' && item.outcome === 'answer') chapter.questions.push(item.id);
      if ((item.kind === 'data' || item.kind === 'data_stub') && item.snapshot) {
        chapter.dataVersions.push(item.snapshot.n);
      }
      if (item.kind === 'plot') chapter.plotVersions.push(item.version);
      if (item.kind === 'switch') chapter.switches += 1;
      const folded = item.kind === 'data_stub' || (item.kind === 'plot' && item.version < latest);
      rows.push({ kind: 'item', item, chapter: chapter.index, folded });
    }
  }
  // Oldest first, whatever order their items stand in: a card a turn moved to the end can land
  // below a newer card, when a table read from text waited meanwhile and `.use()` took it.
  for (const chapter of chapters) chapter.dataVersions.sort((a, b) => a - b);
  return { rows, chapters };
}
