/**
 * The agent chat's one reader of the lane's `GET /status` (`agentApi.status`), and the load mood
 * the frame's tab shows from it (`LoadMood.tsx`, kit 5 option C).
 *
 * - The first read, at mount, gives the page the enabled libraries (which gate the admin's `all`
 *   through `settled`) and the caller's run cap (`user_max_runs`). The admin lane's first read is
 *   the admin check's answer (`takeAdminStatus`), so it asks no second time. A failed first read
 *   leaves both to the page's defaults, and no mood: never a guessed `quiet`.
 * - It reads again after each run ends, when the tab becomes visible again (`visibilitychange`),
 *   and every 60 s while the tab is visible (`STATUS_POLL_MS`; PLAN question 6, option a). No
 *   poll reads while a turn is in flight (`running`); a read that would start while another is
 *   out is skipped. A poll changes only the load (`waiting`, `in_flight`, `paused`, `resets_at`);
 *   the libraries and the run cap stay the first read's. A failed read keeps the last answer.
 * - The admin menu's read as it opens (`refresh`) goes also during a run, through the same
 *   guard: during a run its answer feeds the admin meters' count only (`inFlight`), never the
 *   mood, so an admin's tab shows what a visitor's shows.
 * - A `service_paused` refusal rests the mood at once (`markPaused`), and the pause ends at the
 *   reset by itself, without a reload.
 *
 * The answer holds counts and times only. Unmounting clears the timer and the listener, and an
 * answer that comes after it is dropped.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { agentApi, type AgentLane, type AgentStatus } from 'src/lib/agent';
import { localClock } from 'src/sections/agent-chat/messages';

/** How often the mood reads `/status` while the tab is visible and no turn is in flight. */
export const STATUS_POLL_MS = 60_000;

/** The longest wait a browser timer takes (about 24.8 days); a later reset is waited for in steps. */
const MAX_TIMER_MS = 2 ** 31 - 1;

/** What the mood reads of an answer. */
export interface AgentLoad {
  /** Turns waiting in the run queue. */
  waiting: number;
  /** Runs in flight. */
  inFlight: number;
  /** While the service's day budget is spent, its reset (ISO, still ahead); else null. */
  pausedUntil: string | null;
}

/** The mood on the frame's tab: one word and a dot (`LoadMood.tsx`). */
export type Mood =
  | { kind: 'quiet' }
  | { kind: 'busy' }
  /** `until`: the reset on the visitor's clock (`01:00`), null where it does not parse. */
  | { kind: 'resting'; until: string | null };

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

/** An answer the page can read: an object, whatever an older server leaves out. */
function isStatus(value: unknown): value is AgentStatus {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

/** The load an answer reports: a pause only while its reset is still ahead. */
export function loadOf(status: AgentStatus, now: number = Date.now()): AgentLoad {
  const resets = typeof status.resets_at === 'string' ? Date.parse(status.resets_at) : NaN;
  return {
    waiting: count(status.waiting),
    inFlight: count(status.in_flight),
    pausedUntil: status.paused === true && resets > now ? (status.resets_at ?? null) : null,
  };
}

/**
 * The mood from the last load and the own turn: resting while the day budget is spent and its
 * reset is ahead; busy while turns wait in the queue or the own turn waits there (PLAN, slice 9);
 * else quiet. `null` before the first answer.
 */
export function loadMood(
  load: AgentLoad | null,
  ownQueued: boolean,
  now = Date.now()
): Mood | null {
  if (!load) return null;
  if (load.pausedUntil && Date.parse(load.pausedUntil) > now) {
    return { kind: 'resting', until: localClock(load.pausedUntil) };
  }
  return load.waiting > 0 || ownQueued ? { kind: 'busy' } : { kind: 'quiet' };
}

/** The mood's word, as the frame's tab shows it: `quiet`, `busy`, `resting until 01:00`. */
export function moodText(mood: Mood): string {
  if (mood.kind !== 'resting') return mood.kind;
  return mood.until ? `resting until ${mood.until}` : 'resting';
}

export interface UseAgentStatusOptions {
  /** The admin token, or `PUBLIC_LANE`. */
  token: string;
  lane: AgentLane;
  /** The admin check's answer, once (`useAgentAdmin`): the admin lane's first read. */
  takeAdminStatus: () => AgentStatus | null;
  /** A turn is in flight (`state.run`): no poll reads, and an answer feeds no mood. */
  running: boolean;
}

export interface AgentStatusView {
  /** The first answer's enabled libraries; null before it, after it failed, or without any. */
  libraries: string[] | null;
  /** The first answer's run cap of the caller; null before it, after it failed, or without one. */
  userMaxRuns: number | null;
  /** The first read is in, or failed. */
  settled: boolean;
  /** The last load the mood reads; null before the first answer. */
  load: AgentLoad | null;
  /** The runs in flight of the latest answer, the menu's read during a run included. */
  inFlight: number | null;
  /** `/status` once more, also during a run (the admin menu's read as it opens). */
  refresh: () => Promise<void>;
  /** A `service_paused` refusal: rest until `until` (ISO) at once. */
  markPaused: (until: string) => void;
}

export function useAgentStatus({
  token,
  lane,
  takeAdminStatus,
  running,
}: UseAgentStatusOptions): AgentStatusView {
  const [first, setFirst] = useState<{
    libraries: string[] | null;
    userMaxRuns: number | null;
  } | null>(null);
  const [load, setLoad] = useState<AgentLoad | null>(null);
  const [inFlight, setInFlight] = useState<number | null>(null);
  const runningRef = useRef(running);
  runningRef.current = running;
  // One read at a time: a poll, the menu's read and the first read never overlap.
  const reading = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  /** An answer for the meters, and for the mood unless a turn is in flight. */
  const publish = useCallback((status: AgentStatus) => {
    if (typeof status.in_flight === 'number') setInFlight(count(status.in_flight));
    if (!runningRef.current) setLoad(loadOf(status));
  }, []);

  const read = useCallback(
    async (duringRun: boolean) => {
      if (reading.current || (!duringRun && runningRef.current)) return;
      reading.current = true;
      try {
        const status: unknown = await agentApi.status(token);
        if (mounted.current && isStatus(status)) publish(status);
      } catch {
        // No answer, or a refusal: the last answer stays.
      } finally {
        reading.current = false;
      }
    },
    [token, publish]
  );

  // The first read: the libraries and the run cap, and the first load. Once per lane: a new
  // `takeAdminStatus` alone reads nothing again.
  const takeChecked = useRef(takeAdminStatus);
  takeChecked.current = takeAdminStatus;
  useEffect(() => {
    let cancelled = false;
    const checked = lane === 'admin' ? takeChecked.current() : null;
    reading.current = true;
    (checked ? Promise.resolve(checked) : agentApi.status(token))
      .then((status: unknown) => {
        if (cancelled) return;
        if (!isStatus(status)) {
          setFirst({ libraries: null, userMaxRuns: null });
          return;
        }
        setFirst({
          libraries:
            Array.isArray(status.libraries) && status.libraries.length ? status.libraries : null,
          userMaxRuns:
            typeof status.user_max_runs === 'number' && status.user_max_runs > 0
              ? status.user_max_runs
              : null,
        });
        publish(status);
      })
      .catch(() => {
        if (!cancelled) setFirst({ libraries: null, userMaxRuns: null });
      })
      .finally(() => {
        // A read the effect dropped (a remount) leaves the guard to the read that replaced it.
        if (!cancelled) reading.current = false;
      });
    return () => {
      cancelled = true;
    };
  }, [token, lane, publish]);

  // Every 60 s while the tab is visible, and as it becomes visible again.
  useEffect(() => {
    const visible = () => document.visibilityState === 'visible';
    const timer = window.setInterval(() => {
      if (visible()) void read(false);
    }, STATUS_POLL_MS);
    const onVisibility = () => {
      if (visible()) void read(false);
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [read]);

  // After each run: the queue and the pause may have changed meanwhile.
  const wasRunning = useRef(running);
  useEffect(() => {
    const ended = wasRunning.current && !running;
    wasRunning.current = running;
    if (ended) void read(false);
  }, [running, read]);

  // The pause ends with the service's new day, without a reload.
  const pausedUntil = load?.pausedUntil ?? null;
  const [pauseTick, setPauseTick] = useState(0);
  useEffect(() => {
    if (!pausedUntil) return;
    const left = Date.parse(pausedUntil) - Date.now();
    const timer = window.setTimeout(
      () => {
        if (left > MAX_TIMER_MS) {
          setPauseTick(tick => tick + 1);
          return;
        }
        setLoad(current =>
          current && current.pausedUntil === pausedUntil
            ? { ...current, pausedUntil: null }
            : current
        );
      },
      Math.min(Math.max(0, left), MAX_TIMER_MS)
    );
    return () => window.clearTimeout(timer);
  }, [pausedUntil, pauseTick]);

  const refresh = useCallback(() => read(true), [read]);
  const markPaused = useCallback((until: string) => {
    if (!(Date.parse(until) > Date.now())) return;
    setLoad(current => ({
      waiting: current?.waiting ?? 0,
      inFlight: current?.inFlight ?? 0,
      pausedUntil: until,
    }));
  }, []);

  return {
    libraries: first?.libraries ?? null,
    userMaxRuns: first?.userMaxRuns ?? null,
    settled: first !== null,
    load,
    inFlight,
    refresh,
    markPaused,
  };
}
