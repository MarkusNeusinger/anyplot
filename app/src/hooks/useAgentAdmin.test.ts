import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAgentAdmin } from 'src/hooks/useAgentAdmin';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

const flags = vi.hoisted(() => ({ isDev: false }));
vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    CONFIG: {
      ...actual.CONFIG,
      get isDev() {
        return flags.isDev;
      },
      features: { agentChat: true },
    },
  };
});

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

let answer: () => Promise<Response>;
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  flags.isDev = false;
  localStorage.clear();
  sessionStorage.clear();
  answer = async () => json(200, { libraries: ['matplotlib'], enabled: true });
  fetchMock = vi.fn((input: string) => {
    expect(new URL(input).pathname).toBe('/debug/agent/status');
    return answer();
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAgentAdmin', () => {
  it("asks nothing in a visitor's browser", () => {
    const { result } = renderHook(() => useAgentAdmin());
    expect(result.current.admin).toBe('none');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("checks a hinted browser on the admin lane's /status, once", async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result, rerender } = renderHook(() => useAgentAdmin());
    expect(result.current.admin).toBe('checking');
    await waitFor(() => expect(result.current.admin).toBe('admin'));
    rerender();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(result.current.failure).toBeNull();
  });

  it.each([
    [401, 'unauthorized'],
    [403, 'forbidden'],
  ])('reads a %i as expired and clears the hint', async (status, code) => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    // The gate's detail is a sentence, with the address for a 403: the code stands for it.
    answer = async () => json(status, { detail: 'User someone@example.com not authorized' });
    const { result } = renderHook(() => useAgentAdmin());
    await waitFor(() => expect(result.current.admin).toBe('expired'));
    expect(result.current.failure).toBe(code);
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull();
  });

  it('reads no answer (an expired Access session) as expired and keeps the hint', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    answer = () => Promise.reject(new TypeError('Failed to fetch'));
    const { result } = renderHook(() => useAgentAdmin());
    await waitFor(() => expect(result.current.admin).toBe('expired'));
    expect(result.current.failure).toBe('unreachable');
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBe('1');
  });

  it('reads not_enabled as an admin: the gate answers before the kill switch', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    answer = async () => json(404, { detail: 'not_enabled' });
    const { result } = renderHook(() => useAgentAdmin());
    await waitFor(() => expect(result.current.admin).toBe('admin'));
  });

  it('checks local development without the hint, and falls back silently there', async () => {
    flags.isDev = true;
    answer = async () => json(401, { detail: 'Invalid admin token' });
    const { result } = renderHook(() => useAgentAdmin());
    expect(result.current.admin).toBe('checking');
    // No admin was claimed: a visitor's page, without the expired line.
    await waitFor(() => expect(result.current.admin).toBe('none'));
  });

  it('turns expired on a refusal later in the session, and clears the hint', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result } = renderHook(() => useAgentAdmin());
    await waitFor(() => expect(result.current.admin).toBe('admin'));
    act(() => result.current.refused());
    expect(result.current.admin).toBe('expired');
    expect(result.current.failure).toBe('unauthorized');
    expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull();
  });
});
