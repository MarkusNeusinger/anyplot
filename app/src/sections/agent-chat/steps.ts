/**
 * The agent chat's two steps, data first, as the page, the status line at the chat frame's foot
 * and the data card read them from the session state, and the thread's in-progress line of a
 * turn the assistant is still working on.
 */

import type { AgentSessionState, ChatItem } from 'src/hooks/useAgentSession';
import { isPlotAction } from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import { CONFIRM_LOST_STEP_TEXT, NEW_DATA_PLOT } from 'src/sections/agent-chat/messages';

/** The step the session is in: 1 the data, 2 the plot. */
export type AgentStep = 1 | 2;

/**
 * The status line at the chat frame's foot (`StatusLine`, `ChatFrame.tsx`), which the composer's
 * plot buttons name as their description, and `.send()` while an attachment waits. It holds the
 * id the pinned header's summary had, so a description that points at it stays valid while the
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

/**
 * The name of the composer's filled plot button, as the lines that lead to it say it:
 * `.create_plot()`, and `plot the new data` after a change to data the user had confirmed, which
 * the click confirms and plots like any other (`Composer.tsx` names the button the same).
 */
export function plotButtonLabel(state: AgentSessionState): string {
  return dataChanged(state) ? NEW_DATA_PLOT : '.create_plot()';
}

/** The server files a version under its (spec, library) pair: whether the library in use has one. */
export function hasPlotHere(state: AgentSessionState): boolean {
  return Object.values(state.versions).some(version => version.library === state.library);
}

/** The data's shape in one line: `2 rows · 2 columns · version 1`. */
export function dataShape(dataset: NonNullable<AgentSessionState['dataset']>): string {
  const { profile, version } = dataset.parsed;
  return `${countOf(profile.rows, 'row')} · ${countOf(profile.columns.length, 'column')} · version ${version ?? 1}`;
}

/**
 * Step 1's part of the status line, which the plot button at the composer's end names as its
 * description: the click takes the data and the bindings as the card shows them. It says what
 * the button waits for first (a table read from text to decide on, a required role without a
 * column), else what to check, and after a lost confirmation what lost it, which no thread
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
    : `check the preview and the bindings above, then ${action}`;
}

/** What the status line needs besides the session state: the page's own parts of it. */
export interface StatusLineOptions {
  /** The plot button the line leads to: `plotButtonLabel`, or `.plot_all()` while `all` is pressed. */
  action: string;
  /** The line of a table or a file waiting in the message box (`attachmentWaitLine`), else null. */
  attachmentLine: string | null;
  /** A switch's carry as its button reads (`carryActionText`); null without one shown. */
  carryText: string | null;
  /** `all` holds the message box in step 2: the composer's own line above the box says why. */
  chatLocked: boolean;
}

/** The status line's step and its words, after the `>>>` the line starts with. */
export interface StatusLineText {
  step: AgentStep;
  text: string;
}

/**
 * The status line at the chat frame's foot, `step 1 of 2 · …` (`back to step 1 of 2 · …` after a
 * lost confirmation), which took the step header's place and the step lines above the message
 * box in the v4 frame (2026-11-06). After the step it names, in this order: the attachment that
 * waits for Enter, the plot that runs and the `.stop()` it leaves, step 1's line, before the
 * library's first plot in step 2 what the plot button does, else the confirmed data's shape.
 */
export function statusLine(state: AgentSessionState, options: StatusLineOptions): StatusLineText {
  const step: AgentStep = inStep2(state) ? 2 : 1;
  const head = step === 1 && state.confirmLoss ? 'back to step 1 of 2' : `step ${step} of 2`;
  const detail =
    options.attachmentLine ??
    runLine(state) ??
    stepOneLine(state, options.action) ??
    stepTwoLine(state, options);
  return { step, text: `${head} · ${detail}` };
}

/**
 * Step 2's part of the status line, and step 1's while the session has no data yet: a table read
 * from text before any data was stored waits for its decision, else `your data`.
 */
function stepTwoLine(state: AgentSessionState, options: StatusLineOptions): string {
  if (!state.dataset && state.transcription)
    return 'decide on the table first: .use() or .discard()';
  if (!state.dataset || !inStep2(state)) return 'your data';
  if (!hasPlotHere(state) && !options.chatLocked) {
    const action = options.carryText ?? 'create the plot as it is';
    return `${action}, or say first what it should do differently`;
  }
  return `data fits · ${dataShape(state.dataset)}`;
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
 * What the thread's in-progress line says: the turn's kind, that it stops, that it reconnects, or,
 * once a run's card is in, that the reply is on its way.
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
 * The in-progress line in the assistant's slot of the thread, while a turn
 * without pipeline steps waits for its reply: the summary of the data, example
 * data, a question, a data request. It shows exactly while the turn's own prompt is the
 * last item, so the first reply (a message, a refusal, an error, a plot) takes
 * its place. A plot run (`create_plot`, `carry_plot`) gets none, and neither
 * does a turn that reached a pipeline step: the progress timeline below the
 * thread shows those, and two indicators would say the same thing. A wait in
 * the run queue keeps the line, since the queue counter says where, not what.
 * Once a run's card took the timeline's place, the line stands below the card
 * until the reply takes its place (`awaitsReply`).
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
 * Whether the progress timeline below the thread has something to say that
 * the in-progress line does not: a plot run, whose path shows up front from
 * the queue on, or any turn that reached a pipeline step. A turn without steps
 * that waits in the queue keeps the in-progress line and the queue counter
 * alone, so its wait has one loader and one queue position, not two.
 */
export function showsTimeline(state: AgentSessionState): boolean {
  const run = state.run;
  return !!run && (isPlotAction(run.kind) || run.steps.some(entry => entry.step !== 'queued'));
}

/**
 * The status line's part while a plot runs (the progress timeline stands below the thread,
 * `runView`): it takes the step's part, which would still invite the click that started the run,
 * and names the one action the run leaves, `.stop()`. `null` while no plot runs, and once the
 * run's card took the timeline's place.
 */
export function runLine(state: AgentSessionState): string | null {
  if (!runView(state).timeline) return null;
  return state.run?.stopping ? 'stopping…' : 'plotting… .stop() to cancel';
}

/**
 * The thread and the progress timeline of a run, as the page shows them. While the timeline
 * stands below the thread, an item the run sends in (a reply, a refusal, a note) would land
 * above it and push it and the composer down: it waits, and the user's own message or action
 * stays in view. The run's result card (a plot, or the card of a run that failed) takes the
 * timeline's place, and the waiting items come with it; a run that ends without one shows them
 * as it ends.
 */
export function runView(state: AgentSessionState): { items: ChatItem[]; timeline: boolean } {
  const items = state.items;
  if (!showsTimeline(state)) return { items, timeline: false };
  let ask = items.length - 1;
  while (ask >= 0 && items[ask].kind !== 'user' && items[ask].kind !== 'action') ask -= 1;
  if (ask < 0) return { items, timeline: true };
  const since = items.slice(ask + 1);
  if (since.some(item => item.kind === 'plot' || item.kind === 'plot_failed')) {
    return { items, timeline: false };
  }
  return { items: since.length ? items.slice(0, ask + 1) : items, timeline: true };
}
