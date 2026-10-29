import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as api from 'src/lib/api';
import * as adminAuth from 'src/utils/adminAuth';

import { useDebugStatus } from './useDebugStatus';

vi.mock('src/lib/api', () => ({
  fetchWithAuth: vi.fn(),
}));

vi.mock('src/utils/adminAuth', () => ({
  clearAccessReloadGuard: vi.fn(),
  reloadOnceForAccess: vi.fn(),
  setAdminHint: vi.fn(),
}));

const mockData = {
  total_specs: 100,
};

describe('useDebugStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches data successfully', async () => {
    vi.mocked(api.fetchWithAuth).mockResolvedValueOnce(
      new Response(JSON.stringify(mockData), { status: 200 })
    );

    const setAuthRequired = vi.fn();
    const { result } = renderHook(() => useDebugStatus('token', 0, setAuthRequired));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(adminAuth.clearAccessReloadGuard).toHaveBeenCalled();
    expect(adminAuth.setAdminHint).toHaveBeenCalledWith(true);
    expect(setAuthRequired).toHaveBeenCalledWith(false);
  });

  it('handles auth errors (401)', async () => {
    vi.mocked(api.fetchWithAuth).mockResolvedValueOnce(
      new Response('unauthorized', { status: 401 })
    );

    const setAuthRequired = vi.fn();
    const { result } = renderHook(() => useDebugStatus('token', 0, setAuthRequired));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('admin token required');
    expect(adminAuth.setAdminHint).toHaveBeenCalledWith(false);
    expect(setAuthRequired).toHaveBeenCalledWith(true);
  });

  it('handles 403 with message', async () => {
    vi.mocked(api.fetchWithAuth).mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'not allowed' }), { status: 403 })
    );

    const setAuthRequired = vi.fn();
    const { result } = renderHook(() => useDebugStatus('token', 0, setAuthRequired));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('not allowed');
    expect(adminAuth.setAdminHint).toHaveBeenCalledWith(false);
    expect(setAuthRequired).toHaveBeenCalledWith(true);
  });

  it('handles network error and triggers reload guard', async () => {
    vi.mocked(api.fetchWithAuth).mockRejectedValueOnce(new TypeError('Failed to fetch'));
    vi.mocked(adminAuth.reloadOnceForAccess).mockReturnValue(true);

    const setAuthRequired = vi.fn();
    const { result } = renderHook(() => useDebugStatus('token', 0, setAuthRequired));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should not set error if it reloaded
    expect(result.current.error).toBeNull();
  });
});
