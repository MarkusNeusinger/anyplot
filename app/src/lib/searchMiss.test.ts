import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import searchQueryCases from 'src/hooks/searchQuery.cases.json';
import { normalizeQuery } from 'src/hooks/useAnalytics';
import {
  claimSearchMiss,
  forgetSentMisses,
  isCountableMiss,
  keptMissText,
  MAX_MISS_DIGITS,
  MIN_MISS_LENGTH,
  MISS_MARKS,
  MISS_PAUSE_MS,
  reportSearchMiss,
  sendSearchMiss,
} from 'src/lib/searchMiss';

// The docs and the privacy page say "two seconds"; the timer itself is tested in FilterSearch.test.tsx.
it('keeps the pause that makes a text finished at the two seconds the docs state', () => {
  expect(MISS_PAUSE_MS).toBe(2000);
});

describe('isCountableMiss', () => {
  // The API's `kept_query` reads the same cases (tests/unit/api/test_search_misses.py): the
  // verdict is on the whole typed text, and a kept text is its first 40 characters.
  it.each(searchQueryCases.cases.map(item => [item.rule, item] as const))(
    'keeps the rule, judged whole before the cut: %s',
    (_rule, item) => {
      expect(keptMissText(item.typed)).toBe(item.countable ? item.sent : null);
    }
  );

  it('folds the same text again to itself, over thousands of texts', () => {
    // The pool holds what folds or is dropped beside letters and the marks they carry, so a mark
    // that a dropped character kept apart is among them; a seeded generator keeps the run fixed.
    const pool = [
      ..."aAzZ09 .-,'",
      ...[0x00e9, 0x0301, 0x0308, 0x030c, 0x0130, 0x1e9e, 0x03a3, 0x0915, 0x094d],
      ...[0x00ad, 0x00a0, 0x2010, 0x2011, 0x2212, 0x2013, 0x2019, 0x3000, 0xfeff, 0x2028],
      ...[0xff41, 0xff21, 0xfb01, 0x00b2, 0x3392, 0xff08, 0x200c, 0x200d],
    ].map(char => (typeof char === 'number' ? String.fromCodePoint(char) : char));
    // mulberry32: 32-bit arithmetic throughout (`Math.imul`), so no product outgrows a double's
    // 53 bits and the low bits stay random.
    let seed = 20261118;
    const next = (bound: number) => {
      seed = (seed + 0x6d2b79f5) | 0;
      let mixed = Math.imul(seed ^ (seed >>> 15), seed | 1);
      mixed ^= mixed + Math.imul(mixed ^ (mixed >>> 7), mixed | 61);
      return ((mixed ^ (mixed >>> 14)) >>> 0) % bound;
    };
    const unstable: string[] = [];
    for (let round = 0; round < 3000; round++) {
      const length = 1 + next(60);
      const text = Array.from({ length }, () => pool[next(pool.length)]).join('');
      const once = normalizeQuery(text);
      if (normalizeQuery(once) !== once) unstable.push(text);
      const kept = keptMissText(text);
      if (kept !== null && keptMissText(kept) !== kept) unstable.push(text);
    }
    expect(unstable).toEqual([]);
  });

  it('has the bounds the API has', () => {
    expect(MIN_MISS_LENGTH).toBe(searchQueryCases.min_length);
    expect(MAX_MISS_DIGITS).toBe(searchQueryCases.max_digits);
    expect(MISS_MARKS).toBe(searchQueryCases.marks);
  });

  it('lets every listed sign through and no other', () => {
    for (const mark of MISS_MARKS) expect(isCountableMiss(`a${mark}b`)).toBe(true);
    for (const sign of '@:;!?*=$~<>"|\\`^[]{}') expect(isCountableMiss(`a${sign}b`)).toBe(false);
  });

  it("holds the API's ignorable ranges to Unicode's own property, over every code point", () => {
    const property = /^\p{Default_Ignorable_Code_Point}$/u;
    const ranges: [string, string][] = [];
    let start = -1;
    for (let code = 0; code <= 0x110000; code++) {
      const hit =
        code <= 0x10ffff &&
        !(code >= 0xd800 && code <= 0xdfff) &&
        property.test(String.fromCodePoint(code));
      if (hit && start < 0) start = code;
      if (!hit && start >= 0) {
        ranges.push([
          start.toString(16).padStart(4, '0'),
          (code - 1).toString(16).padStart(4, '0'),
        ]);
        start = -1;
      }
    }
    expect(ranges).toEqual(searchQueryCases.ignorable);
  });

  it('refuses every ignorable code point but a joiner between two letters', () => {
    const kept: string[] = [];
    for (const [low, high] of searchQueryCases.ignorable) {
      for (let code = parseInt(low, 16); code <= parseInt(high, 16); code++) {
        if (isCountableMiss(`ab${String.fromCodePoint(code)}cd`)) kept.push(code.toString(16));
      }
    }
    expect(kept).toEqual(['200c', '200d']);
  });
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
    // Nothing but the text travels, whatever the API's address becomes: no cookie, no page address.
    expect(init.credentials).toBe('omit');
    expect(init.referrerPolicy).toBe('no-referrer');
  });

  it.each(['jane.doe@example.org', '+41 79 123 45 67', 'https://example.org/plots'])(
    'never sends %s: it is no search for a plot',
    text => {
      sendSearchMiss(text);
      expect(fetchMock).not.toHaveBeenCalled();
    }
  );

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

  it('reports a text once per page load: one count at Plausible and one send, together', () => {
    const count = vi.fn();
    reportSearchMiss('spider', count);
    reportSearchMiss('spider', count);
    reportSearchMiss('splom', count);
    expect(count).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    forgetSentMisses(); // a new page load
    reportSearchMiss('spider', count);
    expect(count).toHaveBeenCalledTimes(3);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it.each(['s', 'jane.doe@example.org', 'https://example.org/plots'])(
    'reports %j neither at Plausible nor to the list: the claim refuses it',
    text => {
      const count = vi.fn();
      reportSearchMiss(text, count);
      expect(claimSearchMiss(text)).toBeNull();
      expect(count).not.toHaveBeenCalled();
      expect(fetchMock).not.toHaveBeenCalled();
    }
  );

  it('counts off the live site, where only the send keeps its own gate', () => {
    // The count's own gate is the analytics' (`trackEvent` sends nothing off the live site).
    at('localhost');
    const count = vi.fn();
    reportSearchMiss('spider', count);
    expect(count).toHaveBeenCalledTimes(1);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sends nothing shorter than two characters, counted as characters', () => {
    sendSearchMiss('s');
    sendSearchMiss('');
    sendSearchMiss('é'); // one character
    expect(fetchMock).not.toHaveBeenCalled();

    sendSearchMiss('sp');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('stays silent when the call fails or the route is not there yet', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'));
    fetchMock.mockResolvedValueOnce({ ok: false, status: 404 });

    expect(() => reportSearchMiss('spider', () => undefined)).not.toThrow();
    expect(() => reportSearchMiss('splom', () => undefined)).not.toThrow();
    await settle();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(consoleError).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
    // No retry: a failed text counts as reported for this page load.
    reportSearchMiss('spider', () => undefined);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
