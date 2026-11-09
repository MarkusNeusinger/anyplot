/**
 * The agent chat's two steps, data first, as the page, the status line at the chat frame's foot
 * and the data card read them from the session state, and the working line at the thread's foot
 * of a turn the assistant is still working on.
 */

import type { AgentSessionState, ChatItem, RunState } from 'src/hooks/useAgentSession';
import { isPlotAction } from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  CONFIRM_LOST_STEP_TEXT,
  DRAWING_SHORT,
  DRAWING_TEXT,
  NEW_DATA_PLOT,
  queuePlace,
  RECONNECTING_TEXT,
  USUAL_PLOT_TIME,
} from 'src/sections/agent-chat/messages';
import { roundLabel } from 'src/sections/agent-chat/timeline';

/** The step the session is in: 1 the data, 2 the plot. */
export type AgentStep = 1 | 2;

/**
 * The status line at the chat frame's foot (`StatusLine`, `ChatFrame.tsx`), which the composer's
 * plot button names as its description, and the message box while `all` holds it. It stands in
 * every state of an open session, so a description that points at it stays valid while the
 * composer changes around it.
 */
export const STATUS_LINE_ID = 'agent-status-line';

/**
 * Step 2: the stored data and its bindings are confirmed, and no table read
 * from text waits for its decision. A transcription stores nothing, so the
 * server keeps the confirmation and the hook keeps its flag; the page holds
 * step 1 until the user decided, and `.discard()` returns to step 2, while
 * `.use()` stores the table as a new, unconfirmed version.
 */
export function inStep2(state: AgentSessionState): boolean {
  return state.dataConfirmed && !!state.dataset && !state.transcription;
}

/** Data the user had confirmed changed since (a data change, a new paste, an undo): step 1 again. */
export function dataChanged(state: AgentSessionState): boolean {
  return state.confirmLoss === 'data';
}

/** The server files a version under its (spec, library) pair: whether the library in use has one. */
export function hasPlotHere(state: AgentSessionState): boolean {
  return Object.values(state.versions).some(version => version.library === state.library);
}

/**
 * What the composer's plot button is, in its one fixed place at the row's end (`Composer.tsx`):
 * `create` (`.create_plot() →`) until the library has a plot, `update` (`.update_plot() →`) once
 * it has one, `new_data` (`plot the new data`) after a change to data the user had confirmed or a
 * paste after the plot, and `all` (`.plot_all()`) while the admin's fan-out is on. A switch keeps
 * the name: the line at the frame's foot names the decisions a carry keeps. `boxData`: new data
 * waits in the message box, which the click reads and plots (`plotChain.ts`), so the button names
 * what the click makes of it: the first plot, or once the library has one the new data's.
 */
export type PlotButtonKind = 'create' | 'update' | 'new_data' | 'all';

export function plotButtonKind(
  state: AgentSessionState,
  plotAll = false,
  boxData = false
): PlotButtonKind {
  if (plotAll) return 'all';
  if (boxData) return hasPlotHere(state) ? 'new_data' : 'create';
  if (dataChanged(state)) return 'new_data';
  if (!hasPlotHere(state)) return 'create';
  // A paste after the plot clears what dropped the confirmation, and is new data all the same.
  const pastedSince = !!state.dataset && !state.dataConfirmed && state.confirmLoss === null;
  return pastedSince ? 'new_data' : 'update';
}

/**
 * The plot button's name as the lines that lead to it say it, without the arrow the button
 * carries: `.create_plot()`, `.update_plot()` once the library has a plot, and `plot the new
 * data` after a change to data the user had confirmed, which the click confirms and plots like
 * any other. The thread names a plot turn the same. `boxData` as for `plotButtonKind`.
 */
export function plotButtonLabel(state: AgentSessionState, boxData = false): string {
  const kind = plotButtonKind(state, false, boxData);
  return kind === 'new_data'
    ? NEW_DATA_PLOT
    : kind === 'update'
      ? '.update_plot()'
      : '.create_plot()';
}

/**
 * The live data card's version in the session (`DataSnapshot.n`, the `3` of `data v3` on its
 * label), the number every line of the page names the data by: the server's, which the
 * assistant's session block lists too; null for a thread built by hand, whose card carries no
 * snapshot.
 */
export function liveDataVersion(state: AgentSessionState): number | null {
  for (let index = state.items.length - 1; index >= 0; index -= 1) {
    const item = state.items[index];
    if (item.kind === 'data') return item.snapshot?.n ?? null;
  }
  return null;
}

/** Step 2's line for the confirmed data: `data v3 fits · 48 rows · 4 columns`. */
function dataFits(state: AgentSessionState, dataset: NonNullable<AgentSessionState['dataset']>) {
  const { profile } = dataset.parsed;
  const version = liveDataVersion(state);
  const name = version === null ? 'data' : `data v${version}`;
  return `${name} fits · ${countOf(profile.rows, 'row')} · ${countOf(profile.columns.length, 'column')}`;
}

/**
 * Step 1's part of the status line, which the plot button at the composer's end names as its
 * description: the click takes the data and the bindings as the card shows them. It says what
 * the button waits for first (a table read from text to decide on, a required role without a
 * column), else what to check, the data and the bindings (one wording at every width: a phone's
 * card shows no preview table), and after a lost confirmation what lost it, which no thread
 * notice repeats. `action` is the button the line leads to: `.plot_all()` while `all` is pressed,
 * where no `.create_plot()` shows, else the button's own name (`plotButtonLabel`). `null` without
 * data or in step 2.
 */
export function stepOneLine(
  state: AgentSessionState,
  action = plotButtonLabel(state)
): string | null {
  if (!state.dataset || inStep2(state)) return null;
  if (state.transcription) return 'decide on the table first: .use() or .discard()';
  if (state.missingRoles.length > 0) {
    return `pick a column for ${state.missingRoles.join(', ')}, then ${action}`;
  }
  return state.confirmLoss
    ? CONFIRM_LOST_STEP_TEXT[state.confirmLoss](action)
    : `check the data and the bindings above, then ${action}`;
}

/** What the status line needs besides the session state: the page's own parts of it. */
export interface StatusLineOptions {
  /** The plot button the line leads to: `plotButtonLabel`, or `.plot_all()` while `all` is pressed. */
  action: string;
  /** The line of a table or a file waiting in the message box (`attachmentWaitLine`), else null. */
  attachmentLine: string | null;
  /**
   * While the plot button's one click reads the box's data before it plots (`plotChain.ts`), its
   * line (`CHAIN_READING_TEXT`), in place of everything else; null otherwise.
   */
  readingLine?: string | null;
  /**
   * After that click stopped at the data card, what to look at (`chainStopText`), in place of
   * step 1's own line; null otherwise, and once anything changed since the stop.
   */
  stopLine?: string | null;
  /**
   * A switch's offer to plot with the remembered decisions (`carryDecisions`): the library and
   * how many decisions the plot button's next plot keeps there; null without an offer.
   */
  carry: { library: string; decisions: number } | null;
  /**
   * `all` holds the message box in step 2: the libraries `.plot_all()` plots in, which the line
   * names together with the way back to the chat; null otherwise.
   */
  lockedLibraries: number | null;
}

/** The status line's step and its words, after the `>>>` the line starts with. */
export interface StatusLineText {
  step: AgentStep;
  /** `step 2 of 2`, `back to step 1 of 2`: the line's start, before its first `·`. */
  head: string;
  /**
   * The whole line as the plot button's description reads it (`step 2 of 2 · drawing your plot ·
   * usually 1–3 min`): never the clock, which only the eye reads.
   */
  text: string;
  /** While a plot is drawn, the run's part, which the line shows with its clock; else null. */
  run: RunLine | null;
}

/**
 * The status line at the chat frame's foot, `step 1 of 2 · …` (`back to step 1 of 2 · …` after a
 * lost confirmation), which took the step header's place and the step lines above the message
 * box in the v4 frame (2026-11-06), and since the v4 composer row is the plot button's
 * description. After the step it names, in this order: the plot button's one click reading the
 * box's data, the attachment that waits, the plot that runs (with its clock, which the
 * description leaves out), where that click stopped, step 1's line, while `all` holds the box
 * what `.plot_all()` does, before the library's first plot in step 2 what the plot button does,
 * else the confirmed data's shape.
 */
export function statusLine(state: AgentSessionState, options: StatusLineOptions): StatusLineText {
  const step: AgentStep = inStep2(state) ? 2 : 1;
  const head = step === 1 && state.confirmLoss ? 'back to step 1 of 2' : `step ${step} of 2`;
  const before = options.readingLine ?? options.attachmentLine ?? null;
  const run = before === null ? runLine(state) : null;
  const detail =
    before ??
    (run ? [run.words, run.tail].filter(Boolean).join(' · ') : null) ??
    (step === 1 ? options.stopLine : null) ??
    stepOneLine(state, options.action) ??
    stepTwoLine(state, options);
  return { step, head, text: `${head} · ${detail}`, run };
}

/**
 * Step 2's part of the status line, and step 1's while the session has no data yet: a table read
 * from text before any data was stored waits for its decision, else `your data`. After a switch
 * that offered it, the line names the decisions the plot button's next plot keeps in the new
 * library, since the button keeps its own name.
 */
function stepTwoLine(state: AgentSessionState, options: StatusLineOptions): string {
  if (!state.dataset && state.transcription)
    return 'decide on the table first: .use() or .discard()';
  if (!state.dataset || !inStep2(state)) return 'your data';
  if (options.lockedLibraries !== null) {
    return `plot the table as it is in all ${options.lockedLibraries} libraries at once · turn all off to chat`;
  }
  const carry = options.carry;
  const kept =
    carry && carry.decisions > 0
      ? `${countOf(carry.decisions, 'decision')} kept in ${carry.library} · `
      : '';
  if (!hasPlotHere(state)) {
    return `${kept}create the plot as it is, or say first what it should do differently`;
  }
  if (kept) return `${kept}${options.action} brings them in, or ask for a change`;
  return dataFits(state, state.dataset);
}

/**
 * What the hidden polite region beside the status line reads out: the step, when it changes,
 * and that a paste is being read. It stays mounted, so a screen reader hears each change, while
 * the status line itself says more and changes more often.
 */
export function stepAnnouncement(state: AgentSessionState): string {
  if (state.parsing) return 'parsing your data';
  if (inStep2(state)) return 'step 2: the data is confirmed; create the plot below';
  return state.dataset ? 'step 1: check the data, then create the plot' : '';
}

/**
 * What the working line says for a turn without plot work (`pendingReply`): the turn's kind, that
 * it stops, that it reconnects, or, once a run's card is in, that the reply is on its way.
 */
export type PendingReply =
  'summarize_data' | 'example_data' | 'message' | 'stopping' | 'reconnecting' | 'writing';

/**
 * Whether a run's card is in (a plot, or the card of a run that failed) and the reply to it is on
 * its way: the root writes the reply after the plot, seconds later, and until then nothing would
 * say that the turn still works. Notices between the card and the reply do not end the wait.
 */
export function awaitsReply(state: AgentSessionState): boolean {
  if (!state.run) return false;
  for (let index = state.items.length - 1; index >= 0; index -= 1) {
    const kind = state.items[index].kind;
    if (kind === 'plot' || kind === 'plot_failed') return true;
    if (kind !== 'notice') return false;
  }
  return false;
}

/**
 * What the working line says while a turn without plot work waits for its reply: the summary of
 * the data, example data, a question, a data request. It shows exactly while the turn's own
 * prompt is the last item, so the first reply (a message, a refusal, an error, a plot) takes its
 * place. A plot run (`create_plot`, `carry_plot`) gets none here, and neither does a turn that
 * reached a pipeline step: that is plot work (`plotWork`), which the working line words itself.
 * A wait in the run queue keeps the line (`workingLine` says where the turn waits). Once a run's
 * card is in, the line stands below the card until the reply takes its place (`awaitsReply`).
 */
export function pendingReply(state: AgentSessionState): PendingReply | null {
  const run = state.run;
  if (run && awaitsReply(state)) {
    if (run.reconnecting && !run.stopping) return 'reconnecting';
    return run.stopping ? 'stopping' : 'writing';
  }
  if (!run || run.kind === 'create_plot' || run.kind === 'carry_plot') return null;
  if (run.steps.some(entry => entry.step !== 'queued')) return null;
  // A cut stream the page reads again: the turn's only indicator, also after its reply arrived.
  if (run.reconnecting && !run.stopping) return 'reconnecting';
  const last = state.items[state.items.length - 1];
  if (!last || (last.kind !== 'user' && last.kind !== 'action')) return null;
  return run.stopping ? 'stopping' : run.kind;
}

/**
 * Plot work: a plot run, which draws from the queue on, or any turn that reached a pipeline step.
 * The working line says `drawing your plot` for it, with its clock and its try, and the status
 * line at the frame's foot the same with how long a plot usually takes. A turn without steps that
 * waits in the queue keeps its own words (`pendingReply`), so its wait has one line, not two.
 */
export function plotWork(state: AgentSessionState): boolean {
  const run = state.run;
  return !!run && (isPlotAction(run.kind) || run.steps.some(entry => entry.step !== 'queued'));
}

/** The run waits in the run queue: its last step is the wait. */
function inQueue(run: RunState): boolean {
  return run.steps[run.steps.length - 1]?.step === 'queued';
}

/** A run's part of the status line while a plot is drawn (`runLine`). */
export interface RunLine {
  /** `drawing your plot`, or `stopping…` once `.stop()` was pressed. */
  words: string;
  /** The words on a phone: `drawing`. */
  short: string;
  /** When the clock after the words started (`RunState.startedAt`); null for no clock. */
  clockFrom: number | null;
  /** After the clock: `usually 1–3 min`; empty while the run stops. */
  tail: string;
}

/**
 * The status line's part while a plot is drawn (`runView`): it takes the step's part, which would
 * still invite the click that started the run, and says how long it runs and how long a plot
 * usually takes, `drawing your plot · 0:42 · usually 1–3 min` (on a phone `drawing · 0:42 · …`),
 * the clock counting on past the usual time unchanged; `.stop()` stands at the line's end. No
 * clock while the run waits in the queue or was not timed. `null` while no plot is drawn, and
 * once the run's card is in.
 */
export function runLine(state: AgentSessionState): RunLine | null {
  const run = state.run;
  if (!run || !runView(state).drawing) return null;
  if (run.stopping) return { words: 'stopping…', short: 'stopping…', clockFrom: null, tail: '' };
  return {
    words: DRAWING_TEXT,
    short: DRAWING_SHORT,
    clockFrom: !inQueue(run) && run.startedAt !== undefined ? run.startedAt : null,
    tail: USUAL_PLOT_TIME,
  };
}

/** Items that end a turn's plot work in the thread: its card, or the error or refusal that ended it. */
const ENDS_DRAWING: ReadonlySet<ChatItem['kind']> = new Set([
  'plot',
  'plot_failed',
  'error',
  'refusal',
]);

/**
 * The thread of a run, as the page shows it: every item the reducer keeps, a version per data
 * item and a line per library switch (`threadModel.ts` puts them in chapters). While a plot is
 * drawn (`drawing`), an item the run sends in (a reply, a note) would land above the working line
 * and push it and the composer down: it waits, and the user's own message or action stays in
 * view. The run's result card (a plot, or the card of a run that failed) ends the drawing, and the
 * waiting items come with it; so does an error or a refusal that ends the turn, which takes the
 * working line's place; a run that ends without any shows them as it ends. Returns `state.items`
 * itself while nothing waits.
 *
 * The data versions never wait: the live card moves with every new version, and held back it
 * would unmount and lose its own state, while the stub it left says it holds the latest data.
 * Today a version arrives only with a turn's `done`, which ends the run, or from the card's own
 * controls, which wait while a run lasts, so none lands under a plot being drawn.
 */
export function runView(state: AgentSessionState): { items: ChatItem[]; drawing: boolean } {
  const items = state.items;
  if (!plotWork(state)) return { items, drawing: false };
  let ask = items.length - 1;
  while (ask >= 0 && items[ask].kind !== 'user' && items[ask].kind !== 'action') ask -= 1;
  if (ask < 0) return { items, drawing: true };
  const since = items.slice(ask + 1);
  if (since.some(item => ENDS_DRAWING.has(item.kind))) return { items, drawing: false };
  if (!since.length) return { items, drawing: true };
  const versions = since.filter(item => item.kind === 'data' || item.kind === 'data_stub');
  return { items: [...items.slice(0, ask + 1), ...versions], drawing: true };
}

/** What the working line says, at the thread's foot (`WorkingLine.tsx`). */
export interface WorkingLineText {
  /** `drawing` while a plot is drawn, else the line's own kind. */
  kind: PendingReply | 'drawing' | 'waiting';
  /** The words on a wide screen. */
  text: string;
  /** The words on a phone (`drawing`, `drawing · second try`); the same where nothing is shorter. */
  short: string;
  /** When the clock after the words started (`RunState.startedAt`); null for no clock. */
  clockFrom: number | null;
}

/** The working line's words of a turn without plot work, beside the site's loader. */
const PENDING_TEXT: Record<'summarize_data' | 'example_data' | 'message' | 'writing', string> = {
  summarize_data: 'summarizing your data',
  example_data: 'making example data',
  message: 'working on your message',
  writing: 'writing the reply',
};

/** The words of a run that stops: it leaves the queue, ends at its next step, or just stops. */
function stoppingText(run: RunState): string {
  if (inQueue(run)) return 'leaving the queue…';
  return run.steps.some(entry => entry.step !== 'queued')
    ? 'stopping after this step…'
    : 'stopping…';
}

/**
 * The try a plot is on, for the working line: none on the first try (owner, 2026-11-09: the
 * common line stays short); from the second on `try 2 of 2` with the server's round cap
 * (`max_attempts`), else `second try`, never a cap the page assumes.
 */
export function trySegment(run: RunState): string | null {
  let attempt = 1;
  for (let index = run.steps.length - 1; index >= 0; index -= 1) {
    const entry = run.steps[index];
    if (entry.step === 'queued') continue;
    attempt = entry.attempt ?? 1;
    break;
  }
  if (attempt < 2) return null;
  return run.maxAttempts
    ? `try ${attempt} of ${Math.max(run.maxAttempts, attempt)}`
    : roundLabel(attempt);
}

/**
 * The one working line at the thread's foot, for every turn and both lanes (the v4 design): what
 * the turn in flight does now, beside the site's loader. It took the place of the thread's
 * in-progress line, the progress timeline below the thread and the queue counter.
 *
 * - While a plot is drawn: `drawing your plot · second try · 0:42` (on a phone `drawing · 0:42`,
 *   from the second try on `drawing · second try · 0:42`),
 *   the try from the second on (`trySegment`), the clock from `RunState.startedAt`.
 * - While the own turn waits in the run queue: `waiting · you are 3rd`, without a clock (owner,
 *   2026-11-09: the line in view says where, the frame's tab only `busy`).
 * - A turn without plot work keeps its words (`summarizing your data`, `working on your message`),
 *   and below a run's card `writing the reply`, while the reply is on its way.
 * - `leaving the queue…`, `stopping after this step…` or `stopping…` once `.stop()` was pressed,
 *   and `connection lost · reconnecting…` while the page reads a cut turn again.
 *
 * `null` while nothing is in flight, once the first reply of a turn without plot work took the
 * line's place, and once an error or a refusal ended the turn.
 */
export function workingLine(state: AgentSessionState): WorkingLineText | null {
  const run = state.run;
  if (!run) return null;
  const words = (kind: WorkingLineText['kind'], text: string, short = text): WorkingLineText => ({
    kind,
    text,
    short,
    clockFrom: null,
  });
  const waiting = () =>
    words('waiting', run.queue ? `waiting · you are ${queuePlace(run.queue.position)}` : 'waiting');
  if (!runView(state).drawing) {
    const pending = pendingReply(state);
    if (pending === null) return null;
    // Below the run's card no step is left to finish: the reply is what stops.
    if (pending === 'stopping') {
      return words('stopping', awaitsReply(state) ? 'stopping…' : stoppingText(run));
    }
    if (pending === 'reconnecting') return words('reconnecting', RECONNECTING_TEXT);
    if (pending === 'writing') return words('writing', PENDING_TEXT.writing);
    return inQueue(run) ? waiting() : words(pending, PENDING_TEXT[pending]);
  }
  if (run.stopping) return words('stopping', stoppingText(run));
  if (run.reconnecting) return words('reconnecting', RECONNECTING_TEXT);
  if (inQueue(run)) return waiting();
  const tries = trySegment(run);
  return {
    kind: 'drawing',
    text: tries ? `${DRAWING_TEXT} · ${tries}` : DRAWING_TEXT,
    short: tries ? `${DRAWING_SHORT} · ${tries}` : DRAWING_SHORT,
    clockFrom: run.startedAt ?? null,
  };
}
