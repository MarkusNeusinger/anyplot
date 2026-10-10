import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  agentApi,
  agentFetch,
  browserLocale,
  parseAgentEvent,
  renderedThemes,
  sizeBucket,
  toAgentApiError,
} from 'src/lib/agent';
import { ACCESS_RELOAD_KEY } from 'src/utils/adminAuth';

const raw = (event: string, data: unknown) => ({
  event,
  data: typeof data === 'string' ? data : JSON.stringify(data),
});

describe('parseAgentEvent', () => {
  it('types the queued status and the pipeline steps', () => {
    expect(parseAgentEvent(raw('status', { step: 'queued', position: 2, waiting: 3 }))).toEqual({
      type: 'queued',
      position: 2,
      waiting: 3,
    });
    expect(parseAgentEvent(raw('status', { step: 'repairing', attempt: 2 }))).toEqual({
      type: 'step',
      step: 'repairing',
      attempt: 2,
    });
  });

  it('keeps only the documented plot fields and artifact names', () => {
    const event = parseAgentEvent(
      raw('plot', {
        status: 'needs_attention',
        attempts: 2,
        artifacts: ['plot-light.png', 'plot.py', 'data.csv', '../etc/passwd'],
        changes: ['bigger markers', 3],
        residual_defects: ['VQ-03 light: overlap'],
        error_details: 'Traceback …',
      })
    );
    expect(event).toEqual({
      type: 'plot',
      result: {
        status: 'needs_attention',
        reason: null,
        attempts: 2,
        artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
        changes: ['bigger markers'],
        residual_defects: ['VQ-03 light: overlap'],
        version: null,
      },
    });
  });

  it("keeps the server's version number and drops one that is not a positive integer", () => {
    const plot = (version: unknown) =>
      parseAgentEvent(raw('plot', { status: 'ok', attempts: 1, artifacts: [], version }));
    expect(plot(3)).toMatchObject({ type: 'plot', result: { version: 3 } });
    expect(plot(0)).toMatchObject({ result: { version: null } });
    expect(plot('3')).toMatchObject({ result: { version: null } });
    expect(plot(1.5)).toMatchObject({ result: { version: null } });
  });

  it('reads an unknown error code as internal and keeps the ref', () => {
    expect(parseAgentEvent(raw('error', { code: 'kaboom', ref: 'abc' }))).toEqual({
      type: 'error',
      code: 'internal',
      ref: 'abc',
    });
  });

  it('drops unknown types, non-object data, malformed JSON and bad statuses', () => {
    expect(parseAgentEvent(raw('debug', { a: 1 }))).toBeNull();
    expect(parseAgentEvent(raw('message', '[1,2]'))).toBeNull();
    expect(parseAgentEvent(raw('message', '{not json'))).toBeNull();
    expect(parseAgentEvent(raw('status', { step: 'thinking' }))).toBeNull();
    expect(parseAgentEvent(raw('status', { step: 'queued', position: -1, waiting: 2 }))).toBeNull();
    expect(parseAgentEvent(raw('plot', { status: 'great' }))).toBeNull();
  });

  it('types ready, message, refusal and done', () => {
    expect(parseAgentEvent(raw('ready', { v: 'anyplot/1', run_id: 'r' }))).toEqual({
      type: 'ready',
      runId: 'r',
    });
    expect(parseAgentEvent(raw('message', { text: 'hi' }))).toEqual({
      type: 'message',
      text: 'hi',
    });
    expect(parseAgentEvent(raw('refusal', { code: 'budget', text: 'later' }))).toEqual({
      type: 'refusal',
      code: 'budget',
      text: 'later',
    });
    expect(parseAgentEvent(raw('done', {}))).toEqual({
      type: 'done',
      llmCalls: null,
      tokens: null,
    });
  });
});

describe('toAgentApiError', () => {
  it('reads the BFF code and ref', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'run_active', ref: 'r-1' }), { status: 409 })
    );
    expect(error).toMatchObject({ status: 409, code: 'run_active', ref: 'r-1' });
    expect(error.unauthorized).toBe(false);
  });

  it('falls back to a code for the status when the body has none', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ status: 401, message: 'no' }), { status: 401 })
    );
    expect(error).toMatchObject({ status: 401, code: 'unauthorized', ref: null });
    expect(error.unauthorized).toBe(true);
  });

  it('maps the kill switch message to not_enabled', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'agent chat is not enabled' }), { status: 404 })
    );
    expect(error.code).toBe('not_enabled');
  });

  it("keeps the binding check's lines of a refused binding set", async () => {
    const error = await toAgentApiError(
      new Response(
        JSON.stringify({ detail: 'invalid', ref: 'r', errors: ["role 'y' takes y1", 7] }),
        { status: 422 }
      )
    );
    expect(error).toMatchObject({ code: 'invalid', errors: ["role 'y' takes y1"] });
  });
});

describe('agentFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('reports a request without a readable answer as unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    );
    await expect(agentFetch('/status', '')).rejects.toMatchObject({
      status: 0,
      code: 'unreachable',
    });
  });

  it('clears the Access reload guard once an answer arrives', async () => {
    sessionStorage.setItem(ACCESS_RELOAD_KEY, '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 200 }))
    );
    await agentFetch('/status', '');
    expect(sessionStorage.getItem(ACCESS_RELOAD_KEY)).toBeNull();
  });

  it('sends the delete with keepalive when the page goes away', async () => {
    const fetchMock = vi.fn(async () => new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);
    await agentApi.deleteSession('', 'S1', { keepalive: true });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init).toMatchObject({ method: 'DELETE', keepalive: true });
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
  });
});

describe('helpers', () => {
  it('buckets sizes without exposing them', () => {
    expect(sizeBucket(10)).toBe('lt_1kb');
    expect(sizeBucket(5 * 1024)).toBe('1_10kb');
    expect(sizeBucket(20 * 1024)).toBe('10_50kb');
    expect(sizeBucket(200 * 1024)).toBe('50_200kb');
    expect(sizeBucket(200 * 1024 + 1)).toBe('over_200kb');
  });

  it('names the rendered themes from the artifacts', () => {
    expect(renderedThemes(['plot-dark.png', 'plot.py'])).toEqual(['dark']);
    expect(renderedThemes(['plot.py'])).toEqual([]);
  });

  it('sends a locale the BFF accepts', () => {
    expect(browserLocale()).toMatch(/^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$/);
  });
});
