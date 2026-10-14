import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ApiError, apiGet, apiPost, RETRY_AFTER_CAP_MS, RETRY_DELAYS_MS } from 'src/lib/api';

// The longest jittered backoff: base + 20 %.
const maxWait = (attempt: number) => Math.ceil(RETRY_DELAYS_MS[attempt] * 1.2);

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.useFakeTimers();
  fetchMock = vi.fn();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('apiGet retry', () => {
  it('retries a network TypeError and then succeeds', async () => {
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(json({ ok: 1 }));

    const result = apiGet<{ ok: number }>('/specs');
    await vi.advanceTimersByTimeAsync(maxWait(0));

    await expect(result).resolves.toEqual({ ok: 1 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('retries 503 twice with growing backoff and then succeeds', async () => {
    fetchMock
      .mockResolvedValueOnce(json({}, 503))
      .mockResolvedValueOnce(json({}, 503))
      .mockResolvedValueOnce(json({ ok: 2 }));

    const result = apiGet('/stats');
    await vi.advanceTimersByTimeAsync(RETRY_DELAYS_MS[0] - 1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(maxWait(0));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(maxWait(1));

    await expect(result).resolves.toEqual({ ok: 2 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('throws ApiError with the last status once the retries are spent', async () => {
    fetchMock.mockImplementation(() => Promise.resolve(json({}, 502)));

    const result = apiGet('/stats');
    const assertion = expect(result).rejects.toMatchObject({ name: 'ApiError', status: 502 });
    await vi.advanceTimersByTimeAsync(maxWait(0) + maxWait(1));

    await assertion;
    expect(fetchMock).toHaveBeenCalledTimes(1 + RETRY_DELAYS_MS.length);
  });

  it('rethrows the network error once the retries are spent', async () => {
    fetchMock.mockImplementation(() => Promise.reject(new TypeError('Failed to fetch')));

    const result = apiGet('/specs');
    const assertion = expect(result).rejects.toThrow('Failed to fetch');
    await vi.advanceTimersByTimeAsync(maxWait(0) + maxWait(1));

    await assertion;
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('does not retry a 404: "Spec not found" stays instant', async () => {
    fetchMock.mockResolvedValue(json({}, 404));

    await expect(apiGet('/specs/missing')).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('does not retry an error that is not a network TypeError', async () => {
    fetchMock.mockRejectedValue(new SyntaxError('bad'));

    await expect(apiGet('/specs')).rejects.toThrow('bad');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('does not retry an aborted request', async () => {
    const controller = new AbortController();
    controller.abort();
    fetchMock.mockRejectedValue(new TypeError('aborted'));

    await expect(apiGet('/specs', { signal: controller.signal })).rejects.toThrow('aborted');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('stops at once when aborted during the backoff wait', async () => {
    const controller = new AbortController();
    fetchMock.mockResolvedValue(json({}, 503));

    const result = apiGet('/specs', { signal: controller.signal });
    const assertion = expect(result).rejects.toMatchObject({ name: 'AbortError' });
    await vi.advanceTimersByTimeAsync(RETRY_DELAYS_MS[0] / 2);
    controller.abort();

    await assertion;
    await vi.advanceTimersByTimeAsync(maxWait(0) + maxWait(1));
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('honours Retry-After in seconds', async () => {
    fetchMock
      .mockResolvedValueOnce(json({}, 429, { 'Retry-After': '2' }))
      .mockResolvedValueOnce(json({ ok: 3 }));

    const result = apiGet('/specs');
    await vi.advanceTimersByTimeAsync(1999);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    await expect(result).resolves.toEqual({ ok: 3 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('caps a long Retry-After', async () => {
    fetchMock
      .mockResolvedValueOnce(json({}, 503, { 'Retry-After': '3600' }))
      .mockResolvedValueOnce(json({ ok: 4 }));

    const result = apiGet('/specs');
    await vi.advanceTimersByTimeAsync(RETRY_AFTER_CAP_MS);

    await expect(result).resolves.toEqual({ ok: 4 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('does not retry a GET overridden to another method', async () => {
    fetchMock.mockResolvedValue(json({}, 503));

    await expect(apiGet('/specs', { method: 'DELETE' })).rejects.toMatchObject({ status: 503 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe('apiPost', () => {
  it('never retries, neither a 503 nor a network error', async () => {
    fetchMock.mockResolvedValueOnce(json({}, 503));
    await expect(apiPost('/feedback', { a: 1 })).rejects.toMatchObject({ status: 503 });

    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    await expect(apiPost('/feedback', { a: 1 })).rejects.toThrow('Failed to fetch');

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
