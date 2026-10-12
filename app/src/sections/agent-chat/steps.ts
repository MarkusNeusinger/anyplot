/**
 * The agent chat's two steps, data first, as the page, the step header and the
 * data card read them from the session state, and the thread's in-progress
 * line of a turn the assistant is still working on.
 */

import type { AgentSessionState } from 'src/hooks/useAgentSession';

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

/** What the thread's in-progress line says: the turn's kind, or that it stops. */
export type PendingReply = 'summarize_data' | 'message' | 'stopping';

/**
 * The in-progress line in the assistant's slot of the thread, while a turn
 * without pipeline steps waits for its reply: the summary of the data, a
 * question, a data request. It shows exactly while the turn's own prompt is the
 * last item, so the first reply (a message, a refusal, an error, a plot) takes
 * its place. A `create_plot` run gets none, and neither does a turn that
 * reached a pipeline step: the progress timeline below the thread shows those,
 * and two indicators would say the same thing. A wait in the run queue keeps
 * the line, since the queue counter says where, not what.
 */
export function pendingReply(state: AgentSessionState): PendingReply | null {
  const run = state.run;
  if (!run || run.kind === 'create_plot') return null;
  if (run.steps.some(entry => entry.step !== 'queued')) return null;
  const last = state.items[state.items.length - 1];
  if (!last || (last.kind !== 'user' && last.kind !== 'action')) return null;
  return run.stopping ? 'stopping' : run.kind;
}

/**
 * Whether the progress timeline below the thread has something to say that
 * the in-progress line does not: a `create_plot` run, whose path shows up front,
 * or any turn that waits in the queue or reached a pipeline step.
 */
export function showsTimeline(state: AgentSessionState): boolean {
  const run = state.run;
  return !!run && (run.kind === 'create_plot' || run.steps.length > 0);
}
