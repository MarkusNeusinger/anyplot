/**
 * The agent chat's two steps, data first, as the page, the step header and the
 * data card read them from the session state.
 */

import type { AgentSessionState } from 'src/hooks/useAgentSession';

/**
 * Step 2: the stored data and its bindings are confirmed, and no table read
 * from text waits for its decision. The hook drops its flag for a
 * transcription, but a turn's sync can set it again from the server, which
 * keeps its confirmation until `.use()` stores the table; the page stays in
 * step 1 until the user decided.
 */
export function inStep2(state: AgentSessionState): boolean {
  return state.dataConfirmed && !!state.dataset && !state.transcription;
}
