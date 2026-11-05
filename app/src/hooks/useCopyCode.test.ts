import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCopyCode } from 'src/hooks/useCopyCode';

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
    (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('denied')
    );

    const { result } = renderHook(() => useCopyCode());

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });

    expect(result.current.copied).toBe(false);
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('says for a while that the browser refused the copy, and calls onError', async () => {
    // A refused copy changed nothing on the page: it read as a dead button.
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('denied')
    );
    const onError = vi.fn();
    const { result } = renderHook(() => useCopyCode({ onError, timeout: 1000 }));

    await act(async () => {
      await result.current.copyToClipboard('hello');
    });
    expect(result.current.failed).toBe(true);
    expect(onError).toHaveBeenCalledOnce();

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.failed).toBe(false);
    consoleSpy.mockRestore();
  });

  it('gives a second click its full time, the earlier timer no longer counts', async () => {
    const { result } = renderHook(() => useCopyCode({ timeout: 1000 }));
    await act(async () => {
      await result.current.copyToClipboard('hello');
    });
    act(() => {
      vi.advanceTimersByTime(800);
    });
    await act(async () => {
      await result.current.copyToClipboard('hello');
    });
    act(() => {
      vi.advanceTimersByTime(800);
    });
    expect(result.current.copied).toBe(true);
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current.copied).toBe(false);
  });
});
