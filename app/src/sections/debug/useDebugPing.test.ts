import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from 'src/lib/api';

import { useDebugPing } from './useDebugPing';

vi.mock('src/lib/api', () => ({
  fetchWithAuth: vi.fn(),
}));

describe('useDebugPing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('polls ping endpoint successfully', async () => {
    vi.mocked(api.fetchWithAuth).mockResolvedValue(
      new Response(JSON.stringify({ database_connected: true }), { status: 200 })
    );

    const { result } = renderHook(() => useDebugPing('token', false));

    await waitFor(() => {
      expect(result.current.pings.length).toBeGreaterThan(0);
    });

    expect(result.current.pings[0].ok).toBe(true);
  });

  it('handles authRequired correctly', () => {
    renderHook(() => useDebugPing('token', true));
    expect(api.fetchWithAuth).not.toHaveBeenCalled();
  });

  it('handles ping failure', async () => {
    vi.mocked(api.fetchWithAuth).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useDebugPing('token', false));

    await waitFor(() => {
      expect(result.current.pings.length).toBeGreaterThan(0);
    });

    expect(result.current.pings[0].ok).toBe(false);
  });
});
