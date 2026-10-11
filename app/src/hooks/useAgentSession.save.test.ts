/**
 * `saveSession` (`.save()`): the bundle download. In a file of its own so the
 * main hook tests stay as they are; the fetch mock is the same shape.
 */

import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAgentSession, type UseAgentSessionOptions } from 'src/hooks/useAgentSession';
import { AgentApiError, attachmentFilename, bundleFilename } from 'src/lib/agent';

const trackEvent = vi.fn();
vi.mock('src/hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
}));

const json = (status: number, body: unknown, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });

const BUNDLE = { session: { spec_id: 'scatter-basic' }, transcript: [], versions: [] };

interface Call {
  method: string;
  path: string;
  search: string;
}

let calls: Call[];
let bundle: (call: Call) => Response | Promise<Response>;
let dataset: (call: Call) => Response | Promise<Response>;

function mockFetch() {
  calls = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const call = {
        method: init.method ?? 'GET',
        path: url.pathname.replace(/^.*\/debug\/agent/, ''),
        search: url.search,
      };
      calls.push(call);
      if (call.method === 'POST' && call.path === '/sessions') {
        return json(200, {
          session_id: 'S1abcdefgh',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      if (call.method === 'GET' && call.path === '/sessions/S1abcdefgh/bundle') return bundle(call);
      if (call.method === 'POST' && call.path === '/sessions/S1abcdefgh/dataset') {
        return dataset(call);
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

async function openSession() {
  mockFetch();
  const hook = renderHook(() => useAgentSession(options));
  await waitFor(() => expect(hook.result.current.state.phase).toBe('ready'));
  return hook;
}

let downloads: { href: string; download: string }[];

beforeEach(() => {
  trackEvent.mockClear();
  downloads = [];
  bundle = () =>
    json(200, BUNDLE, {
      'Content-Disposition': 'attachment; filename="anyplot-session-S1abcdef.json"',
    });
  dataset = () => json(422, { detail: 'unparseable', ref: 'ref-u' });
  URL.createObjectURL = vi.fn(() => 'blob:bundle');
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement
  ) {
    downloads.push({ href: this.href, download: this.download });
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('useAgentSession: .save()', () => {
  it('downloads the bundle with the data under the BFF file name and records it', async () => {
    const { result } = await openSession();
    await act(() => result.current.saveSession(true));

    const call = calls.find(item => item.path.endsWith('/bundle'));
    expect(call?.search).toBe('?include_data=true');
    expect(downloads).toEqual([{ href: 'blob:bundle', download: 'anyplot-session-S1abcdef.json' }]);
    expect(trackEvent).toHaveBeenCalledWith('agent_session_saved', { include_data: 'yes' });
  });

  it('asks without the data and names the file itself where the header is unreadable', async () => {
    bundle = () => json(200, BUNDLE);
    const { result } = await openSession();
    await act(() => result.current.saveSession(false));

    expect(calls.find(item => item.path.endsWith('/bundle'))?.search).toBe('?include_data=false');
    expect(downloads).toEqual([{ href: 'blob:bundle', download: 'anyplot-session-S1abcdef.json' }]);
    expect(trackEvent).toHaveBeenCalledWith('agent_session_saved', { include_data: 'no' });
  });

  it('rejects with the code and ref of a failed save, downloads nothing and records nothing', async () => {
    bundle = () => json(502, { detail: 'too_large', ref: 'ref-big' });
    const { result } = await openSession();

    let error: unknown;
    await act(async () => {
      await result.current.saveSession(true).catch((err: unknown) => {
        error = err;
      });
    });

    expect(error).toBeInstanceOf(AgentApiError);
    expect(error).toMatchObject({ status: 502, code: 'too_large', ref: 'ref-big' });
    expect(downloads).toEqual([]);
    expect(trackEvent).not.toHaveBeenCalledWith('agent_session_saved', expect.anything());
    expect(result.current.state.phase).toBe('ready');
  });

  it('shows the sign-in notice when the admin gate refuses the save', async () => {
    bundle = () => json(401, { status: 401, message: 'admin required' });
    const { result } = await openSession();
    await act(async () => {
      await result.current.saveSession(true).catch(() => undefined);
    });
    expect(result.current.state.phase).toBe('unauthorized');
  });

  it('starts one save at a time', async () => {
    let release!: () => void;
    bundle = () =>
      new Promise<Response>(resolve => {
        release = () => resolve(json(200, BUNDLE));
      });
    const { result } = await openSession();

    let first: Promise<void> = Promise.resolve();
    act(() => {
      first = result.current.saveSession(true);
    });
    await act(() => result.current.saveSession(false));
    expect(calls.filter(item => item.path.endsWith('/bundle'))).toHaveLength(1);

    release();
    await act(() => first);
    expect(downloads).toHaveLength(1);
  });

  it('starts no save while the data is parsed, and saves once the parse is over', async () => {
    let release!: () => void;
    dataset = () =>
      new Promise<Response>(resolve => {
        release = () => resolve(json(422, { detail: 'unparseable', ref: 'ref-u' }));
      });
    const { result } = await openSession();

    let parse: Promise<void> = Promise.resolve();
    act(() => {
      parse = result.current.parseData('hours,score\n1.5,52\n');
    });
    await waitFor(() => expect(calls.some(item => item.path.endsWith('/dataset'))).toBe(true));
    await act(() => result.current.saveSession(true));
    expect(calls.filter(item => item.path.endsWith('/bundle'))).toHaveLength(0);
    expect(downloads).toEqual([]);
    expect(trackEvent).not.toHaveBeenCalledWith('agent_session_saved', expect.anything());

    release();
    await act(() => parse);
    await act(() => result.current.saveSession(true));
    expect(calls.filter(item => item.path.endsWith('/bundle'))).toHaveLength(1);
    expect(downloads).toHaveLength(1);
  });

  it('lets go of the blob URL a second after the download starts', async () => {
    const { result } = await openSession();
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
    try {
      await act(() => result.current.saveSession(true));
      expect(downloads).toHaveLength(1);
      expect(URL.revokeObjectURL).not.toHaveBeenCalled();
      vi.advanceTimersByTime(1000);
      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:bundle');
    } finally {
      vi.useRealTimers();
    }
  });
});

describe('bundle file names', () => {
  it("builds the BFF's name from the session id's first eight safe characters", () => {
    expect(bundleFilename('S1abcdefghij')).toBe('anyplot-session-S1abcdef.json');
    expect(bundleFilename('a_-b')).toBe('anyplot-session-a_-b.json');
    expect(bundleFilename('../..')).toBe('anyplot-session-session.json');
  });

  it('takes only a plain .json attachment name from the header', () => {
    expect(attachmentFilename('attachment; filename="anyplot-session-ab.json"')).toBe(
      'anyplot-session-ab.json'
    );
    expect(attachmentFilename(null)).toBeNull();
    expect(attachmentFilename('inline; filename="a.json"')).toBeNull();
    expect(attachmentFilename('attachment; filename="../a.json"')).toBeNull();
    expect(attachmentFilename('attachment; filename="a.html"')).toBeNull();
  });
});
