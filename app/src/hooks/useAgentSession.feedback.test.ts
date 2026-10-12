/**
 * `sendFeedback` (`.send()` on a result card): the stored case is recorded on
 * the version and reported. In a file of its own, like the `.save()` tests; the
 * fetch mock is the same shape.
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  agentReducer,
  initialAgentState,
  type PlotVersion,
  useAgentSession,
  type UseAgentSessionOptions,
} from 'src/hooks/useAgentSession';
import { AgentApiError } from 'src/lib/agent';

const trackEvent = vi.fn();
vi.mock('src/hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
}));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

function sse(events: [string, unknown][]) {
  return new Response(
    events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join(''),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
  );
}

const PLOT = {
  status: 'ok',
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};

interface Call {
  method: string;
  path: string;
  body: unknown;
}

let calls: Call[];
let feedback: (call: Call) => Response | Promise<Response>;
let turn: () => Response | Promise<Response>;

function mockFetch() {
  calls = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const call = {
        method: init.method ?? 'GET',
        path: url.pathname.replace(/^.*\/debug\/agent/, ''),
        body: init.body ? JSON.parse(String(init.body)) : null,
      };
      calls.push(call);
      if (call.method === 'POST' && call.path === '/sessions') {
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      if (call.method === 'POST' && call.path === '/sessions/S1/messages') return turn();
      if (call.method === 'POST' && call.path === '/sessions/S1/feedback') return feedback(call);
      if (call.method === 'GET' && call.path.startsWith('/sessions/S1/artifacts/')) {
        return new Response('png', { status: 200 });
      }
      if (call.method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found', ref: 'ref-404' });
    })
  );
}

const options: UseAgentSessionOptions = {
  specId: 'scatter-basic',
  library: 'matplotlib',
  locale: 'en',
  token: '',
};

/** An open session with version 1 on screen. */
async function withVersion() {
  mockFetch();
  const hook = renderHook(() => useAgentSession(options));
  await waitFor(() => expect(hook.result.current.state.phase).toBe('ready'));
  await act(() => hook.result.current.createPlot());
  await waitFor(() => expect(hook.result.current.state.versions[1]).toBeDefined());
  return hook;
}

const feedbackCalls = () => calls.filter(call => call.path.endsWith('/feedback'));

beforeEach(() => {
  trackEvent.mockClear();
  feedback = () => json(201, { case_id: '20261012T143005Z-1a2b3c4d', stored: ['manifest.json'] });
  turn = () =>
    sse([
      ['plot', PLOT],
      ['done', { llm_calls: 2 }],
    ]);
  URL.createObjectURL = vi.fn(() => 'blob:png');
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('useAgentSession: quick feedback', () => {
  it('stores the case, records it on the version and reports it', async () => {
    const { result } = await withVersion();

    await act(() =>
      result.current.sendFeedback(1, {
        reaction: 'thumbs_down',
        message: '  the legend hides the points  ',
        includeData: true,
      })
    );

    expect(feedbackCalls()).toEqual([
      {
        method: 'POST',
        path: '/sessions/S1/feedback',
        body: {
          reaction: 'thumbs_down',
          message: 'the legend hides the points',
          include_data: true,
          result_version: 1,
        },
      },
    ]);
    expect(result.current.state.versions[1].feedback).toEqual({
      reaction: 'thumbs_down',
      message: 'the legend hides the points',
      includeData: true,
      caseId: '20261012T143005Z-1a2b3c4d',
    });
    expect(trackEvent).toHaveBeenCalledWith('agent_result_feedback', {
      reaction: 'thumbs_down',
      include_data: 'yes',
    });
  });

  it('sends no text as null, and a later send names and replaces the record', async () => {
    const { result } = await withVersion();
    await act(() =>
      result.current.sendFeedback(1, { reaction: 'bug', message: 'x', includeData: true })
    );
    expect(feedbackCalls()[0].body).not.toHaveProperty('replaces');

    feedback = () => json(201, { case_id: '20261012T143100Z-99999999', stored: ['manifest.json'] });
    await act(() =>
      result.current.sendFeedback(1, { reaction: 'thumbs_up', message: '   ', includeData: false })
    );

    expect(feedbackCalls()[1].body).toEqual({
      reaction: 'thumbs_up',
      message: null,
      include_data: false,
      result_version: 1,
      replaces: '20261012T143005Z-1a2b3c4d',
    });
    expect(result.current.state.versions[1].feedback).toEqual({
      reaction: 'thumbs_up',
      message: null,
      includeData: false,
      caseId: '20261012T143100Z-99999999',
    });
    expect(trackEvent).toHaveBeenLastCalledWith('agent_result_feedback', {
      reaction: 'thumbs_up',
      include_data: 'no',
    });
  });

  it('rejects with the code and ref of a failed send and records nothing', async () => {
    feedback = () => json(502, { detail: 'storage', ref: 'ref-st' });
    const { result } = await withVersion();

    let error: unknown;
    await act(async () => {
      await result.current
        .sendFeedback(1, { reaction: 'idea', message: '', includeData: true })
        .catch((err: unknown) => {
          error = err;
        });
    });

    expect(error).toBeInstanceOf(AgentApiError);
    expect(error).toMatchObject({ status: 502, code: 'storage', ref: 'ref-st' });
    expect(result.current.state.versions[1].feedback).toBeUndefined();
    expect(trackEvent).not.toHaveBeenCalledWith('agent_result_feedback', expect.anything());
    expect(result.current.state.phase).toBe('ready');
  });

  it('shows the sign-in notice when the admin gate refuses the send', async () => {
    feedback = () => json(401, { status: 401, message: 'admin required' });
    const { result } = await withVersion();
    await act(async () => {
      await result.current
        .sendFeedback(1, { reaction: 'idea', message: '', includeData: true })
        .catch(() => undefined);
    });
    expect(result.current.state.phase).toBe('unauthorized');
  });

  it('runs while a turn is in flight, and the turn never waits for it', async () => {
    const { result } = await withVersion();
    let release!: () => void;
    turn = () =>
      new Promise<Response>(resolve => {
        release = () => resolve(sse([['done', { llm_calls: 1 }]]));
      });

    let running: Promise<void> = Promise.resolve();
    act(() => {
      running = result.current.sendMessage('bigger markers');
    });
    await waitFor(() => expect(result.current.state.run).not.toBeNull());

    await act(() =>
      result.current.sendFeedback(1, { reaction: 'thumbs_up', message: '', includeData: true })
    );
    expect(result.current.state.versions[1].feedback?.reaction).toBe('thumbs_up');
    expect(result.current.state.run).not.toBeNull();

    release();
    await act(() => running);
    expect(result.current.state.run).toBeNull();
  });

  it('joins a second send for the same version while the first runs', async () => {
    let release!: () => void;
    feedback = () =>
      new Promise<Response>(resolve => {
        release = () => resolve(json(201, { case_id: 'c1', stored: ['manifest.json'] }));
      });
    const { result } = await withVersion();

    let first: Promise<void> = Promise.resolve();
    let second: Promise<void> = Promise.resolve();
    act(() => {
      first = result.current.sendFeedback(1, { reaction: 'bug', message: '', includeData: true });
      second = result.current.sendFeedback(1, { reaction: 'bug', message: '', includeData: true });
    });
    expect(second).toBe(first);
    release();
    await act(() => first);
    expect(feedbackCalls()).toHaveLength(1);
  });

  it('refuses a version the session does not hold, and a text over 500 characters', async () => {
    const { result } = await withVersion();
    await expect(
      result.current.sendFeedback(7, { reaction: 'bug', message: '', includeData: true })
    ).rejects.toMatchObject({ code: 'no_session' });
    await expect(
      result.current.sendFeedback(1, {
        reaction: 'bug',
        message: 'x'.repeat(501),
        includeData: true,
      })
    ).rejects.toMatchObject({ code: 'too_long' });
    expect(feedbackCalls()).toHaveLength(0);
  });
});

describe('agentReducer: version_feedback', () => {
  it('records the case on the version and ignores an unknown version', () => {
    const version: PlotVersion = {
      number: 2,
      library: 'matplotlib',
      result: { ...PLOT, status: 'ok', version: 2, artifacts: ['plot-light.png'] },
      theme: 'light',
      images: {},
      code: { state: 'loading' },
    };
    const state = { ...initialAgentState('matplotlib'), versions: { 2: version } };
    const record = { reaction: 'idea' as const, message: null, includeData: false, caseId: 'c9' };

    const next = agentReducer(state, { type: 'version_feedback', number: 2, feedback: record });
    expect(next.versions[2].feedback).toEqual(record);
    expect(agentReducer(state, { type: 'version_feedback', number: 5, feedback: record })).toBe(
      state
    );
  });
});
