import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCopyCode } from './useCopyCode';

describe('useCopyCode', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts with copied = false', () => {
    const { result } = renderHook(() => useCopyCode());
    expect(result.current.copied).toBe(false);
  });

  it('copies text to clipboard', async () => {
    const { result } = renderHook(() => useCopyCode());

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('hello');
    expect(result.current.copied).toBe(true);
  });

  it('resets copied after timeout', async () => {
    const { result } = renderHook(() => useCopyCode({ timeout: 1000 }));

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });
    expect(result.current.copied).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.copied).toBe(false);
  });

  it('calls onCopy callback', async () => {
    const onCopy = vi.fn();
    const { result } = renderHook(() => useCopyCode({ onCopy }));

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });

    expect(onCopy).toHaveBeenCalledOnce();
  });

  it('reset sets copied to false', async () => {
    const { result } = renderHook(() => useCopyCode());

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });
    expect(result.current.copied).toBe(true);

    act(() => {
      result.current.reset();
    });
    expect(result.current.copied).toBe(false);
  });

  it('handles clipboard failure gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('denied'));

    const { result } = renderHook(() => useCopyCode());

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });

    expect(result.current.copied).toBe(false);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
