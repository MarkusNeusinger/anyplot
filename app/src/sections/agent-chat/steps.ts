/**
 * The agent chat's two steps, data first, as the page, the step header and the
 * data card read them from the session state, and the thread's in-progress
 * line of a turn the assistant is still working on.
 */

import type { AgentSessionState, ChatItem } from 'src/hooks/useAgentSession';
import { isPlotAction } from 'src/lib/agent';
import { CONFIRM_LOST_STEP_TEXT, NEW_DATA_PLOT } from 'src/sections/agent-chat/messages';

/**
 * The pinned header's line (`✓ data fits · ...`, `PinnedData.tsx`), which step 2's plot buttons
 * in the composer name as their description.
 */
export const DATA_SUMMARY_ID = 'agent-data-summary';

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

/**
 * The line above the composer in step 1, which the plot button at the composer's end names as
 * its description: the click takes the data and the bindings as the card shows them. It says
 * what the button waits for first (a table read from text to decide on, a required role without
 * a column), else what to check, and after a lost confirmation what lost it, which no thread
 * notice repeats. `action` is the button the line leads to: `.plot_all()` while `all` is pressed,
 * where no `.create_plot()` shows, else the button's own name (`plotButtonLabel`). `null` without
 * data or in step 2.
 */
export function stepOneLine(
  state: AgentSessionState,
  action = plotButtonLabel(state)
): string | null {
  if (!state.dataset || inStep2(state)) return null;
  const head = state.confirmLoss ? '# step 1 again — ' : '# step 1 — ';
  if (state.transcription) return `${head}decide on the table first: .use() or .discard()`;
  if (state.missingRoles.length > 0) {
    return `${head}pick a column for ${state.missingRoles.join(', ')}, then ${action}`;
  }
  return state.confirmLoss
    ? `${head}${CONFIRM_LOST_STEP_TEXT[state.confirmLoss](action)}`
    : `${head}check the preview and the bindings above, then ${action}`;
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
 * The line above the composer while a plot runs (the progress timeline stands below the thread,
 * `runView`): it takes the step's line, which would still invite the click that started the run,
 * and names the one action the run leaves, `.stop()`. `null` while no plot runs, and once the
 * run's card took the timeline's place.
 */
export function runLine(state: AgentSessionState): string | null {
  if (!runView(state).timeline) return null;
  return state.run?.stopping ? '# stopping…' : '# plotting… .stop() to cancel';
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
