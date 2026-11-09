import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, type MockInstance, vi } from 'vitest';

import {
  type AgentLoad,
  loadMood,
  moodText,
  STATUS_POLL_MS,
  useAgentStatus,
  type UseAgentStatusOptions,
} from 'src/hooks/useAgentStatus';
import { agentApi, type AgentStatus, PUBLIC_LANE } from 'src/lib/agent';
import { localClock } from 'src/sections/agent-chat/messages';

const T0 = Date.UTC(2026, 10, 9, 12, 0, 0);
const answer = (extra: Partial<AgentStatus> = {}): AgentStatus => ({
  libraries: ['matplotlib', 'seaborn'],
  enabled: true,
  user_max_runs: 2,
  waiting: 0,
  in_flight: 1,
  ...extra,
});

let status: MockInstance<typeof agentApi.status>;
let visibility: DocumentVisibilityState;

beforeEach(() => {
  // Fake timers in every test that answers `/status`: the 60 s poll must not leak.
  vi.useFakeTimers({ now: T0 });
  status = vi.spyOn(agentApi, 'status').mockResolvedValue(answer());
  visibility = 'visible';
  vi.spyOn(document, 'visibilityState', 'get').mockImplementation(() => visibility);
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

/** Let the answers in flight land. */
const settle = () => act(async () => vi.advanceTimersByTimeAsync(0));

function mount(overrides: Partial<UseAgentStatusOptions> = {}) {
  return renderHook((props: UseAgentStatusOptions) => useAgentStatus(props), {
    initialProps: {
      token: PUBLIC_LANE,
      lane: 'public',
      takeAdminStatus: () => null,
      running: false,
      ...overrides,
    },
  });
}

describe('loadMood', () => {
  const load = (extra: Partial<AgentLoad> = {}): AgentLoad => ({
    waiting: 0,
    inFlight: 0,
    pausedUntil: null,
    ...extra,
  });

  it('is quiet, busy with a queue or the own turn in it, and resting until the reset ahead', () => {
    expect(loadMood(null, true)).toBeNull();
    expect(loadMood(load(), false)).toEqual({ kind: 'quiet' });
    expect(loadMood(load({ waiting: 2 }), false)).toEqual({ kind: 'busy' });
    expect(loadMood(load(), true)).toEqual({ kind: 'busy' });
    const reset = new Date(T0 + 3_600_000).toISOString();
    const resting = loadMood(load({ pausedUntil: reset, waiting: 4 }), true);
    expect(resting).toEqual({ kind: 'resting', until: localClock(reset) });
    expect(moodText(resting!)).toBe(`resting until ${localClock(reset)}`);
    // A phone's tab is too narrow for it: the short form.
    expect(moodText(resting!, true)).toBe(`back at ${localClock(reset)}`);
    expect(moodText({ kind: 'busy' }, true)).toBe('busy');
    // A reset already past rests no more.
    expect(loadMood(load({ pausedUntil: new Date(T0 - 1).toISOString() }), false)).toEqual({
      kind: 'quiet',
    });
  });
});

describe('useAgentStatus', () => {
  it('reads once at mount, the admin lane from the admin check, and settles after a failure', async () => {
    const { result, unmount } = mount();
    expect(result.current.settled).toBe(false);
    expect(result.current.load).toBeNull();
    await settle();
    expect(status).toHaveBeenCalledTimes(1);
    expect(result.current).toMatchObject({
      libraries: ['matplotlib', 'seaborn'],
      userMaxRuns: 2,
      settled: true,
      load: { waiting: 0, inFlight: 1, pausedUntil: null },
      inFlight: 1,
    });
    unmount();

    // The admin check asked a moment ago: its answer is the first read.
    status.mockClear();
    const admin = mount({
      token: 'tok',
      lane: 'admin',
      takeAdminStatus: () => answer({ libraries: ['plotly'] }),
    });
    await settle();
    expect(status).not.toHaveBeenCalled();
    expect(admin.result.current.libraries).toEqual(['plotly']);
    admin.unmount();

    // No answer: the page's defaults stay, and no mood is guessed.
    status.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    const failed = mount();
    await settle();
    expect(failed.result.current).toMatchObject({
      libraries: null,
      userMaxRuns: null,
      settled: true,
      load: null,
    });
  });

  it('reads every 60 s while the tab is visible, and as it becomes visible again', async () => {
    const { result } = mount();
    await settle();
    status.mockResolvedValue(answer({ waiting: 3 }));
    await act(async () => vi.advanceTimersByTimeAsync(STATUS_POLL_MS));
    expect(status).toHaveBeenCalledTimes(2);
    expect(result.current.load?.waiting).toBe(3);

    // A hidden tab reads nothing.
    visibility = 'hidden';
    await act(async () => vi.advanceTimersByTimeAsync(3 * STATUS_POLL_MS));
    expect(status).toHaveBeenCalledTimes(2);
    visibility = 'visible';
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(status).toHaveBeenCalledTimes(3);
  });

  it('keeps the libraries and the run cap of the first read, and the last answer after a failure', async () => {
    const { result } = mount();
    await settle();
    status.mockResolvedValueOnce(
      answer({ libraries: ['plotly'], user_max_runs: 9, waiting: 1, in_flight: 4 })
    );
    await act(async () => vi.advanceTimersByTimeAsync(STATUS_POLL_MS));
    expect(result.current.libraries).toEqual(['matplotlib', 'seaborn']);
    expect(result.current.userMaxRuns).toBe(2);
    expect(result.current.load).toEqual({ waiting: 1, inFlight: 4, pausedUntil: null });

    status.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await act(async () => vi.advanceTimersByTimeAsync(STATUS_POLL_MS));
    expect(status).toHaveBeenCalledTimes(3);
    expect(result.current.load).toEqual({ waiting: 1, inFlight: 4, pausedUntil: null });
  });

  it('skips the poll during a run, reads after it, and never reads twice at once', async () => {
    const { result, rerender } = mount();
    await settle();
    rerender({ token: PUBLIC_LANE, lane: 'public', takeAdminStatus: () => null, running: true });
    await act(async () => vi.advanceTimersByTimeAsync(2 * STATUS_POLL_MS));
    expect(status).toHaveBeenCalledTimes(1);

    // The admin menu's read goes during the run: the meters' count, never the mood.
    status.mockResolvedValueOnce(answer({ waiting: 5, in_flight: 3 }));
    await act(async () => {
      await result.current.refresh();
    });
    expect(status).toHaveBeenCalledTimes(2);
    expect(result.current.inFlight).toBe(3);
    expect(result.current.load).toEqual({ waiting: 0, inFlight: 1, pausedUntil: null });

    // The run ends: one read, whose answer is the mood's again.
    let release: (value: AgentStatus) => void = () => undefined;
    status.mockImplementationOnce(() => new Promise(resolve => (release = resolve)));
    rerender({ token: PUBLIC_LANE, lane: 'public', takeAdminStatus: () => null, running: false });
    expect(status).toHaveBeenCalledTimes(3);
    // A read while one is out never runs beside it: the menu's is dropped, a poll waits for it.
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
      await result.current.refresh();
    });
    expect(status).toHaveBeenCalledTimes(3);
    status.mockResolvedValueOnce(answer({ waiting: 4 }));
    await act(async () => release(answer({ waiting: 2 })));
    await settle();
    expect(status).toHaveBeenCalledTimes(4);
    expect(result.current.load?.waiting).toBe(4);
  });

  it('never makes the mood of an answer asked for during a run, and still reads after it', async () => {
    const { result, rerender } = mount();
    await settle();
    rerender({ token: PUBLIC_LANE, lane: 'public', takeAdminStatus: () => null, running: true });
    // The admin menu opens during the run; the run ends before its answer comes.
    let release: (value: AgentStatus) => void = () => undefined;
    status.mockImplementationOnce(() => new Promise(resolve => (release = resolve)));
    let menuRead: Promise<void> = Promise.resolve();
    act(() => {
      menuRead = result.current.refresh();
    });
    rerender({ token: PUBLIC_LANE, lane: 'public', takeAdminStatus: () => null, running: false });
    expect(status).toHaveBeenCalledTimes(2);
    status.mockResolvedValueOnce(answer({ waiting: 1, in_flight: 0 }));
    await act(async () => {
      release(answer({ waiting: 9, in_flight: 3 }));
      await menuRead;
    });
    await settle();
    // The in-run snapshot fed the meters only; the read after the run, which waited for it, the mood.
    expect(status).toHaveBeenCalledTimes(3);
    expect(result.current.load).toEqual({ waiting: 1, inFlight: 0, pausedUntil: null });
    expect(result.current.inFlight).toBe(0);
  });

  it('rests at a pause until its reset, and at once on a refusal', async () => {
    const reset = new Date(T0 + 90_000).toISOString();
    status.mockResolvedValue(answer({ paused: true, resets_at: reset }));
    const { result } = mount();
    await settle();
    expect(result.current.load?.pausedUntil).toBe(reset);
    // The new day comes without a reload (no poll needed: the tab is hidden).
    visibility = 'hidden';
    await act(async () => vi.advanceTimersByTimeAsync(90_000));
    expect(result.current.load?.pausedUntil).toBeNull();

    // A `service_paused` refusal rests at once, a reset in the past never.
    const later = new Date(T0 + 7_200_000).toISOString();
    act(() => result.current.markPaused(later));
    expect(result.current.load?.pausedUntil).toBe(later);
    act(() => result.current.markPaused(new Date(T0 - 5).toISOString()));
    expect(result.current.load?.pausedUntil).toBe(later);
  });

  it('waits for a reset past what one browser timer takes, in steps', async () => {
    const far = new Date(T0 + 30 * 86_400_000).toISOString();
    status.mockResolvedValue(answer({ paused: true, resets_at: far }));
    visibility = 'hidden';
    const { result } = mount();
    await settle();
    // A timer past 2^31 ms would fire at once: the pause holds until its day.
    await act(async () => vi.advanceTimersByTimeAsync(25 * 86_400_000));
    expect(result.current.load?.pausedUntil).toBe(far);
    await act(async () => vi.advanceTimersByTimeAsync(5 * 86_400_000));
    expect(result.current.load?.pausedUntil).toBeNull();
  });

  it('clears its timer and its listener when it goes, and drops a late answer', async () => {
    let release: (value: AgentStatus) => void = () => undefined;
    status.mockImplementationOnce(() => new Promise(resolve => (release = resolve)));
    const { result, unmount } = mount();
    unmount();
    await act(async () => release(answer({ waiting: 7 })));
    expect(result.current.load).toBeNull();
    await act(async () => vi.advanceTimersByTimeAsync(5 * STATUS_POLL_MS));
    document.dispatchEvent(new Event('visibilitychange'));
    expect(status).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
  });
});
