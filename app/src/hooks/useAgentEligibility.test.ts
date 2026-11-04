import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAgentEligibility } from 'src/hooks/useAgentEligibility';
import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

const flags = vi.hoisted(() => ({ built: true, isDev: false }));

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    get AGENT_CHAT_ENABLED() {
      return flags.built;
    },
    CONFIG: {
      ...actual.CONFIG,
      get isDev() {
        return flags.isDev;
      },
      features: {
        get agentChat() {
          return flags.built;
        },
      },
    },
  };
});

let fetchMock: ReturnType<typeof vi.fn>;
/** What the API answers: the public lane's door, and the eligibility route of either lane. */
const server = {
  laneOpen: false,
  status: 200,
  body: { eligible: true, status: 'clean', reasons: [] } as unknown,
};

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function stubEligibility(status: number, body: unknown) {
  server.status = status;
  server.body = body;
}

/** The URLs the hook fetched, in order. */
const urls = () => fetchMock.mock.calls.map(([url]) => String(url));

beforeEach(() => {
  flags.built = true;
  flags.isDev = false;
  localStorage.clear();
  sessionStorage.clear();
  resetAgentLaneProbe();
  server.laneOpen = false;
  stubEligibility(200, { eligible: true, status: 'clean', reasons: [] });
  fetchMock = vi.fn(async (url: string) =>
    String(url).endsWith('/agent/lane')
      ? server.laneOpen
        ? json(200, { open: true })
        : json(404, { detail: 'agent chat is not enabled' })
      : json(server.status, server.body)
  );
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAgentEligibility', () => {
  it('never probes the debug API for a visitor without the admin hint', async () => {
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(urls()).toHaveLength(1));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBeNull();
    // Only the public door is asked, and it is closed: no eligibility, no debug route.
    expect(urls()[0]).toMatch(/\/agent\/lane$/);
    expect(urls().some(url => url.includes('/debug/'))).toBe(false);
  });

  it('never probes when the build has no agent chat, even for an admin', async () => {
    flags.built = false;
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('leads an admin to the admin chat only while the public lane is closed', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(result.current).toBe('admin'));
    // The door first: nothing is asked of either lane before it answers.
    expect(urls()[0]).toMatch(/\/agent\/lane$/);
    expect(
      urls().some(url =>
        url.includes('/debug/agent/eligibility?spec=scatter-basic&library=matplotlib')
      )
    ).toBe(true);
  });

  it('leads an admin to the public chat while the public lane is open, as a visitor', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    server.laneOpen = true;
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(result.current).toBe('public'));
    const eligibility = fetchMock.mock.calls.filter(([url]) =>
      String(url).includes('/eligibility')
    ) as [string, RequestInit][];
    // One probe, on the public route, without the admin token: the debug API is never asked.
    expect(eligibility).toHaveLength(1);
    expect(eligibility[0][0]).not.toContain('/debug/');
    expect((eligibility[0][1].headers as Record<string, string>)['X-Admin-Token']).toBeUndefined();
    expect(urls().some(url => url.includes('/debug/'))).toBe(false);
  });

  it('opens local development on the public lane too while it is open', async () => {
    flags.isDev = true;
    server.laneOpen = true;
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(result.current).toBe('public'));
    expect(urls().some(url => url.includes('/debug/'))).toBe(false);
  });

  it('asks the public lane for everyone else while it is open', async () => {
    server.laneOpen = true;
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(result.current).toBe('public'));
    const call = fetchMock.mock.calls.find(([url]) =>
      String(url).includes('/agent/eligibility?spec=scatter-basic')
    ) as [string, RequestInit];
    expect(call[0]).not.toContain('/debug/');
    // Anonymous: the tab's random id, never a cookie or an admin token.
    const headers = call[1].headers as Record<string, string>;
    expect(headers['X-Anyplot-Anon']).toMatch(/^[A-Za-z0-9_-]{22,64}$/);
    expect(headers['X-Admin-Token']).toBeUndefined();
    expect(call[1].credentials).toBe('omit');
  });

  it('hides the entry for a blocked pair', async () => {
    flags.isDev = true;
    stubEligibility(200, { eligible: false, status: 'blocked', reasons: ['map-spec'] });
    const { result } = renderHook(() => useAgentEligibility('map-choropleth', 'matplotlib'));
    await waitFor(() => expect(urls().some(url => url.includes('/eligibility'))).toBe(true));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBeNull();
  });

  it('clears a stale admin hint on 401', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubEligibility(401, { status: 401, message: 'admin required' });
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull());
    expect(result.current).toBeNull();
  });

  it('does nothing without a library (the hub page)', async () => {
    flags.isDev = true;
    renderHook(() => useAgentEligibility('scatter-basic', null));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(urls().some(url => url.includes('/eligibility'))).toBe(false);
  });
});
