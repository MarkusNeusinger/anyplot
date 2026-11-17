import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import searchQueryCases from 'src/hooks/searchQuery.cases.json';
import {
  forgetSentMisses,
  MIN_MISS_LENGTH,
  MISS_PAUSE_MS,
  sendSearchMiss,
} from 'src/lib/searchMiss';

it('counts a text as finished after two seconds without a keystroke', () => {
  expect(MISS_PAUSE_MS).toBe(2000);
});

describe('sendSearchMiss', () => {
  const originalLocation = window.location;
  let fetchMock: ReturnType<typeof vi.fn>;

  /** The browser on a host: the live site unless told otherwise. */
  function at(hostname = 'anyplot.ai') {
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, hostname },
      writable: true,
      configurable: true,
    });
  }

  /** Lets the promise chain of a sent miss run to its end. */
  async function settle() {
    for (let round = 0; round < 5; round++) await Promise.resolve();
  }

  beforeEach(() => {
    forgetSentMisses();
    fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204 });
    vi.stubGlobal('fetch', fetchMock);
    at();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    setAnalyticsMuted(false);
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
      configurable: true,
    });
  });

  it('posts the text in a JSON body to /search/miss, never in the URL', () => {
    sendSearchMiss('spider chart');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/search\/miss$/);
    expect(url).not.toContain('spider');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
    expect(JSON.parse(String(init.body))).toEqual({ query: 'spider chart' });
    expect(init.keepalive).toBe(true);
    // No cookie travels with it: nothing but the text.
    expect(init.credentials).toBeUndefined();
  });

  it.each(['localhost', 'preview.anyplot.ai', 'www.anyplot.ai.example'])(
    'sends nothing from %s',
    hostname => {
      at(hostname);
      sendSearchMiss('spider');
      expect(fetchMock).not.toHaveBeenCalled();
    }
  );

  it("sends nothing while the admin's own use is muted", () => {
    setAnalyticsMuted(true);
    sendSearchMiss('spider');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sends a text once per page load', () => {
    sendSearchMiss('spider');
    sendSearchMiss('spider');
    sendSearchMiss('splom');
    expect(fetchMock).toHaveBeenCalledTimes(2);

    forgetSentMisses(); // a new page load
    sendSearchMiss('spider');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('sends nothing shorter than two characters, counted as characters', () => {
    expect(MIN_MISS_LENGTH).toBe(searchQueryCases.min_length);
    sendSearchMiss('s');
    sendSearchMiss('');
    sendSearchMiss('😀'); // one character, two UTF-16 units
    expect(fetchMock).not.toHaveBeenCalled();

    sendSearchMiss('sp');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('stays silent when the call fails or the route is not there yet', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    fetchMock.mockResolvedValueOnce({ ok: false, status: 404 });

    expect(() => sendSearchMiss('spider')).not.toThrow();
    expect(() => sendSearchMiss('splom')).not.toThrow();
    await settle();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(consoleError).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
    // No retry: a failed text counts as sent for this page load.
    sendSearchMiss('spider');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
