/**
 * The admin fan-out's rules (`FanOut.tsx`): which library may start its plot,
 * and the one status line each library's card shows.
 */

import type { AgentSessionState, Failure } from 'src/hooks/useAgentSession';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';

/** `AGENT_USER_MAX_RUNS`'s default, for a server whose `/status` does not name it. */
export const DEFAULT_USER_MAX_RUNS = 3;

/** Where a library is: storing its data, waiting for a free place, running its plot, or finished. */
export type FanOutSlot = 'data' | 'waiting' | 'running' | 'done';

/** Start the waiting libraries, in the page's order, while fewer than `max` run. */
export function grantSlots(
  slots: Record<string, FanOutSlot>,
  order: readonly string[],
  max: number
): Record<string, FanOutSlot> {
  let running = order.filter(library => slots[library] === 'running').length;
  const next = { ...slots };
  for (const library of order) {
    if (running >= max) break;
    if (next[library] === 'waiting') {
      next[library] = 'running';
      running += 1;
    }
  }
  return next;
}

const STATUS_LABEL: Record<string, string> = {
  ok: 'ok',
  needs_attention: 'needs attention',
};

export type Tone = 'ok' | 'warning' | 'error' | 'muted';

export interface RunStatus {
  text: string;
  tone: Tone;
  /** The error's sentence, where the chat has one. */
  detail?: string;
}

/** One line for a library's card, from its session and its place in the fan-out. */
export function runStatus(
  state: AgentSessionState,
  slot: FanOutSlot,
  dataFailure: Failure | null
): RunStatus {
  if (state.phase === 'opening') return { text: 'opening a session…', tone: 'muted' };
  if (state.phase === 'ineligible') return { text: 'not eligible', tone: 'error' };
  if (state.phase !== 'ready') {
    const code = state.failure?.code ?? state.phase;
    return { text: `error · ${code}`, tone: 'error', detail: ERROR_TEXT[code] };
  }
  if (dataFailure) {
    return {
      text: `data · ${dataFailure.code}`,
      tone: 'error',
      detail: ERROR_TEXT[dataFailure.code],
    };
  }
  const run = state.run;
  if (run) {
    if (run.stopping) return { text: 'stopping…', tone: 'muted' };
    if (run.queue) {
      return { text: `queued · ${run.queue.position} of ${run.queue.waiting}`, tone: 'muted' };
    }
    const step = run.steps[run.steps.length - 1]?.step;
    return { text: step && step !== 'queued' ? `${step}…` : 'starting…', tone: 'muted' };
  }
  const versions = Object.values(state.versions).filter(
    version => version.library === state.library
  );
  const latest = versions[versions.length - 1];
  if (latest) {
    const { status, attempts } = latest.result;
    return {
      text: `v${latest.number} · ${STATUS_LABEL[status] ?? status}${attempts > 1 ? ' · repaired' : ''}`,
      tone: status === 'ok' ? 'ok' : 'warning',
    };
  }
  for (const item of [...state.items].reverse()) {
    if (item.kind === 'plot_failed') {
      return { text: `failed · ${item.result.reason ?? item.result.status}`, tone: 'error' };
    }
    if (item.kind === 'error') {
      return { text: `error · ${item.code}`, tone: 'error', detail: ERROR_TEXT[item.code] };
    }
    if (item.kind === 'refusal') return { text: `refused · ${item.code}`, tone: 'error' };
    if (item.kind === 'notice' && item.text === 'stopped')
      return { text: 'stopped', tone: 'muted' };
  }
  if (slot === 'waiting') return { text: 'waiting for a free place…', tone: 'muted' };
  if (slot === 'done') return { text: 'no plot', tone: 'error' };
  return { text: 'storing the data…', tone: 'muted' };
}
