import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { usePlotOfTheDay } from 'src/hooks/usePlotOfTheDay';

const potd = {
  spec_id: 'scatter-basic',
  spec_title: 'Basic Scatter',
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  preview_url: 'https://cdn.example.com/plot.png',
};

describe('usePlotOfTheDay', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  const answer = (body: unknown) => ({ ok: true, json: () => Promise.resolve(body) });

  it('is loading until the answer, then ready with the plot', async () => {
    fetchMock.mockResolvedValueOnce(answer(potd));
    const { result } = renderHook(() => usePlotOfTheDay());
    expect(result.current.status).toBe('loading');
    expect(result.current.potd).toBeNull();

    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.potd).toEqual(potd);
  });

  it('is none when the API answers that there is no plot of the day', async () => {
    fetchMock.mockResolvedValueOnce(answer(null));
    const { result } = renderHook(() => usePlotOfTheDay());

    await waitFor(() => expect(result.current.status).toBe('none'));
    expect(result.current.potd).toBeNull();
  });

  it('is failed after a failed request, and a retry asks again', async () => {
    // A 404 is not retried by apiGet, so one mock answer is one attempt.
    fetchMock.mockResolvedValueOnce({ ok: false, status: 404, statusText: 'Not Found' });
    let resolveSecond: (value: unknown) => void = () => {};
    fetchMock.mockImplementationOnce(
      () =>
        new Promise(resolve => {
          resolveSecond = resolve;
        })
    );
    const { result } = renderHook(() => usePlotOfTheDay());
    await waitFor(() => expect(result.current.status).toBe('failed'));

    act(() => result.current.retry());
    expect(result.current.status).toBe('loading');
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    resolveSecond(answer(potd));
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.potd).toEqual(potd);
  });

  it('aborts the request when the page goes away, so apiGet stops retrying', () => {
    fetchMock.mockImplementationOnce(() => new Promise(() => {}));
    const { unmount } = renderHook(() => usePlotOfTheDay());
    const signal = (fetchMock.mock.calls[0][1] as RequestInit).signal!;
    expect(signal.aborted).toBe(false);

    unmount();
    expect(signal.aborted).toBe(true);
  });

  it('aborts the pending request when a retry asks again', async () => {
    fetchMock.mockResolvedValueOnce({ ok: false, status: 404, statusText: 'Not Found' });
    fetchMock.mockImplementation(() => new Promise(() => {}));
    const { result } = renderHook(() => usePlotOfTheDay());
    await waitFor(() => expect(result.current.status).toBe('failed'));

    act(() => result.current.retry());
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const second = (fetchMock.mock.calls[1][1] as RequestInit).signal!;
    act(() => result.current.retry());
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(second.aborted).toBe(true);
    expect(result.current.status).toBe('loading');
  });
});
