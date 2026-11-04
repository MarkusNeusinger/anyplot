/**
 * The agent chat's two steps, data first, as the page, the step header and the
 * data card read them from the session state, and the thread's in-progress
 * line of a turn the assistant is still working on.
 */

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { isPlotAction } from 'src/lib/agent';
import { CONFIRM_LOST_TEXT } from 'src/sections/agent-chat/messages';

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

/**
 * The line above the composer in step 1, which `.confirm()` at the composer's end names as its
 * description: what the confirmation waits for first (a table read from text to decide on, a
 * required role without a column), else what to check, and after a lost confirmation what lost
 * it, as the thread's notice says. `null` without data or in step 2, where `.confirm()` is gone.
 */
export function confirmStepLine(state: AgentSessionState): string | null {
  if (!state.dataset || inStep2(state)) return null;
  const head = state.confirmLoss ? '# step 1 again — ' : '# step 1 — ';
  if (state.transcription) return `${head}decide on the table first: .use() or .discard()`;
  if (state.missingRoles.length > 0) {
    return `${head}pick a column for ${state.missingRoles.join(', ')}, then confirm`;
  }
  return state.confirmLoss
    ? `${head}${CONFIRM_LOST_TEXT[state.confirmLoss]}`
    : `${head}check the preview and the bindings, then confirm`;
}

/** What the thread's in-progress line says: the turn's kind, or that it stops. */
export type PendingReply = 'summarize_data' | 'example_data' | 'message' | 'stopping';

/**
 * The in-progress line in the assistant's slot of the thread, while a turn
 * without pipeline steps waits for its reply: the summary of the data, example
 * data, a question, a data request. It shows exactly while the turn's own prompt is the
 * last item, so the first reply (a message, a refusal, an error, a plot) takes
 * its place. A plot run (`create_plot`, `carry_plot`) gets none, and neither
 * does a turn that reached a pipeline step: the progress timeline below the
 * thread shows those, and two indicators would say the same thing. A wait in
 * the run queue keeps the line, since the queue counter says where, not what.
 */
export function pendingReply(state: AgentSessionState): PendingReply | null {
  const run = state.run;
  if (!run || run.kind === 'create_plot' || run.kind === 'carry_plot') return null;
  if (run.steps.some(entry => entry.step !== 'queued')) return null;
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
