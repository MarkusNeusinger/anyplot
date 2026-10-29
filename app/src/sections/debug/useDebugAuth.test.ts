import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as adminAuth from 'src/utils/adminAuth';

import { useDebugAuth } from './useDebugAuth';

vi.mock('src/utils/adminAuth', () => ({
  clearAdminToken: vi.fn(),
  readAdminToken: vi.fn(),
  writeAdminToken: vi.fn(),
}));

describe('useDebugAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with token from readAdminToken', () => {
    vi.mocked(adminAuth.readAdminToken).mockReturnValue('initial-token');
    const { result } = renderHook(() => useDebugAuth());

    expect(result.current.adminToken).toBe('initial-token');
    expect(result.current.authRequired).toBe(false);
    expect(result.current.tokenInput).toBe('');
    expect(result.current.reloadCounter).toBe(0);
  });

  it('handles token submit', () => {
    vi.mocked(adminAuth.readAdminToken).mockReturnValue('');
    const { result } = renderHook(() => useDebugAuth());

    act(() => {
      result.current.setTokenInput('  new-token  ');
    });

    const preventDefault = vi.fn();
    act(() => {
      result.current.handleTokenSubmit({ preventDefault } as unknown as React.FormEvent);
    });

    expect(preventDefault).toHaveBeenCalled();
    expect(adminAuth.writeAdminToken).toHaveBeenCalledWith('new-token');
    expect(result.current.adminToken).toBe('new-token');
    expect(result.current.tokenInput).toBe('');
  });

  it('ignores empty token submit', () => {
    vi.mocked(adminAuth.readAdminToken).mockReturnValue('');
    const { result } = renderHook(() => useDebugAuth());

    act(() => {
      result.current.setTokenInput('    ');
    });

    const preventDefault = vi.fn();
    act(() => {
      result.current.handleTokenSubmit({ preventDefault } as unknown as React.FormEvent);
    });

    expect(preventDefault).toHaveBeenCalled();
    expect(adminAuth.writeAdminToken).not.toHaveBeenCalled();
    expect(result.current.adminToken).toBe('');
  });

  it('handles token clear', () => {
    vi.mocked(adminAuth.readAdminToken).mockReturnValue('initial-token');
    const { result } = renderHook(() => useDebugAuth());

    act(() => {
      result.current.handleTokenClear();
    });

    expect(adminAuth.clearAdminToken).toHaveBeenCalled();
    expect(result.current.adminToken).toBe('');
    expect(result.current.reloadCounter).toBe(1);
  });
});
