import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAgentEligibility } from 'src/hooks/useAgentEligibility';
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

function stubEligibility(status: number, body: unknown) {
  fetchMock = vi.fn(
    async () =>
      new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' },
      })
  );
  vi.stubGlobal('fetch', fetchMock);
}

beforeEach(() => {
  flags.built = true;
  flags.isDev = false;
  localStorage.clear();
  stubEligibility(200, { eligible: true, status: 'clean', reasons: [] });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAgentEligibility', () => {
  it('never probes the debug API for a visitor without the admin hint', async () => {
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('never probes when the build has no agent chat, even for an admin', async () => {
    flags.built = false;
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('asks the eligibility route for an admin and shows the button when eligible', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(result.current).toBe(true));
    const [url] = fetchMock.mock.calls[0] as [string];
    expect(url).toContain('/debug/agent/eligibility?spec=scatter-basic&library=matplotlib');
  });

  it('hides the button for a blocked pair', async () => {
    flags.isDev = true;
    stubEligibility(200, { eligible: false, status: 'blocked', reasons: ['map-spec'] });
    const { result } = renderHook(() => useAgentEligibility('map-choropleth', 'matplotlib'));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(result.current).toBe(false);
  });

  it('clears a stale admin hint on 401', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubEligibility(401, { status: 401, message: 'admin required' });
    const { result } = renderHook(() => useAgentEligibility('scatter-basic', 'matplotlib'));
    await waitFor(() => expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull());
    expect(result.current).toBe(false);
  });

  it('does nothing without a library (the hub page)', async () => {
    flags.isDev = true;
    renderHook(() => useAgentEligibility('scatter-basic', null));
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
