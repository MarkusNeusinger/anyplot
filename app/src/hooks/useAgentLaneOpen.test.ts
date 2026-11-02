import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { resetAgentLaneProbe, useAgentLaneOpen } from 'src/hooks/useAgentLaneOpen';

const flags = vi.hoisted(() => ({ built: true }));

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    get AGENT_CHAT_ENABLED() {
      return flags.built;
    },
  };
});

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  flags.built = true;
  resetAgentLaneProbe();
  fetchMock = vi.fn(async () => new Response(JSON.stringify({ open: true }), { status: 200 }));
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAgentLaneOpen', () => {
  it('asks once per page load and answers later callers at once', async () => {
    const first = renderHook(() => useAgentLaneOpen());
    expect(first.result.current).toBeNull();
    await waitFor(() => expect(first.result.current).toBe(true));

    // A component mounted after the answer gets it on its first render: no flash of "closed".
    const second = renderHook(() => useAgentLaneOpen());
    expect(second.result.current).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('reads a closed lane as false', async () => {
    fetchMock.mockImplementation(async () => new Response('{}', { status: 404 }));
    const { result } = renderHook(() => useAgentLaneOpen());
    await waitFor(() => expect(result.current).toBe(false));
  });

  it('asks nothing without the chat in the build', async () => {
    flags.built = false;
    const { result } = renderHook(() => useAgentLaneOpen());
    expect(result.current).toBe(false);
    await new Promise(resolve => setTimeout(resolve, 10));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
