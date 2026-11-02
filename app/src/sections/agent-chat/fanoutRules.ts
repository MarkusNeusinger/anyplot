/**
 * The admin fan-out's rules (`FanOut.tsx`): which library may start its plot,
 * how the panel backs off when the server's per-user cap answers `run_limit`,
 * and the one status line each library's card shows.
 */

import type { AgentSessionState, Failure } from 'src/hooks/useAgentSession';
import { ERROR_TEXT, PLOT_FAILED_TEXT } from 'src/sections/agent-chat/messages';

/**
 * The public cap (`AGENT_USER_MAX_RUNS`), for a server whose `/status` does not name the caller's own: an
 * older server has no admin lane, so the public cap is what it holds an admin to.
 */
export const DEFAULT_USER_MAX_RUNS = 3;

/** Where a library is: storing its data, waiting for a free place, running its plot, or finished. */
export type FanOutSlot = 'data' | 'waiting' | 'running' | 'done';

/** How long a panel held back by `run_limit` waits before it tries one library again. */
export const RUN_LIMIT_RETRY_MS = 15_000;
/** How long a library may keep getting `run_limit` before it gives up and its card says so. */
export const RUN_LIMIT_GIVE_UP_MS = 30 * 60_000;

/**
 * One panel's places. The server's cap (`user_max_runs`) counts the admin's runs in every window, while
 * `grantSlots` counts only this panel's: with three panels open, the server takes five runs in all and
 * answers the rest with `run_limit` (owner question of 2026-11-01). A `run_limit` is therefore no failure:
 * the library goes back to waiting and `cap` shrinks to the runs the server took from this panel, so the
 * panel starts nothing more until one of its own runs ends (a freed place) or `RUN_LIMIT_RETRY_MS` passes
 * (`retry`, one library more). A library gives up only after `RUN_LIMIT_GIVE_UP_MS` of `run_limit`.
 */
export interface FanOutState {
  slots: Record<string, FanOutSlot>;
  /** How many runs the panel starts at once after a `run_limit`; null is the server's `maxRuns`. */
  cap: number | null;
  /** Per library: when its first `run_limit` came (ms) and how many it got. */
  limited: Record<string, { since: number; count: number }>;
  /** The libraries that gave up after `RUN_LIMIT_GIVE_UP_MS` of `run_limit`. */
  gaveUp: string[];
}

export type FanOutEvent =
  | { type: 'ready'; library: string }
  | { type: 'ended'; library: string }
  | { type: 'run_limit'; library: string; now: number }
  | { type: 'retry' };

export function initialFanOut(libraries: readonly string[]): FanOutState {
  return {
    slots: Object.fromEntries(libraries.map(library => [library, 'data' as FanOutSlot])),
    cap: null,
    limited: {},
    gaveUp: [],
  };
}

/** The panel after `event`, its free places granted in the page's order (`grantSlots`). */
export function nextFanOut(
  state: FanOutState,
  event: FanOutEvent,
  order: readonly string[],
  maxRuns: number
): FanOutState {
  if (event.type !== 'retry' && state.slots[event.library] === 'done') return state;
  const running = order.filter(library => state.slots[library] === 'running').length;
  let { slots, cap, limited, gaveUp } = state;
  if (event.type === 'ready') {
    slots = { ...slots, [event.library]: 'waiting' };
  } else if (event.type === 'ended') {
    slots = { ...slots, [event.library]: 'done' };
  } else if (event.type === 'run_limit') {
    const before = limited[event.library];
    const entry = { since: before?.since ?? event.now, count: (before?.count ?? 0) + 1 };
    limited = { ...limited, [event.library]: entry };
    const giveUp = event.now - entry.since >= RUN_LIMIT_GIVE_UP_MS;
    slots = { ...slots, [event.library]: giveUp ? 'done' : 'waiting' };
    if (giveUp) gaveUp = [...gaveUp, event.library];
    // The server took the runs still running here and no more: start nothing past them for now.
    cap = Math.min(maxRuns, running - 1);
  } else if (cap !== null) {
    cap = Math.min(maxRuns, running + 1); // one library more, the server may have room again
  }
  if (cap !== null && cap >= maxRuns) cap = null;
  return { slots: grantSlots(slots, order, cap ?? maxRuns), cap, limited, gaveUp };
}

/** Whether the panel waits for a retry: it is held back by `run_limit` and a library waits. */
export function awaitsRetry(state: FanOutState): boolean {
  return state.cap !== null && Object.values(state.slots).includes('waiting');
}

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

/** A library's `run_limit` answers so far (`FanOutState.limited`), and whether it gave up. */
export interface RunLimitInfo {
  count: number;
  gaveUp: boolean;
}

/** One line for a library's card, from its session and its place in the fan-out. */
export function runStatus(
  state: AgentSessionState,
  slot: FanOutSlot,
  dataFailure: Failure | null,
  limit: RunLimitInfo | null = null
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
  // Your runs in other windows held every place: no failure, the library waits and tries again.
  if (limit?.gaveUp) {
    return {
      text: 'gave up · run_limit',
      tone: 'error',
      detail: `your runs in other windows held every place for ${RUN_LIMIT_GIVE_UP_MS / 60_000} minutes; close the panel and .plot_all() again`,
    };
  }
  if (limit && slot === 'waiting') {
    return {
      text: `waiting · run_limit ×${limit.count}`,
      tone: 'muted',
      detail: 'your runs in other windows hold every place; this one starts when a place frees',
    };
  }
  for (const item of [...state.items].reverse()) {
    if (item.kind === 'plot_failed') {
      return {
        text: `failed · ${item.result.reason ?? item.result.status}`,
        tone: 'error',
        detail: PLOT_FAILED_TEXT[item.result.reason ?? ''],
      };
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
