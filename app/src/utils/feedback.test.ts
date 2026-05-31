import { describe, it, expect, afterEach, vi } from 'vitest';
import { FEEDBACK_SESSION_KEY, QUICK_REACTIONS, newFeedbackSessionId } from './feedback';

describe('feedback constants', () => {
  it('exposes a stable session-storage key and the two quick reactions', () => {
    expect(FEEDBACK_SESSION_KEY).toBe('anyplot_feedback_session');
    expect(QUICK_REACTIONS).toEqual(['thumbs_up', 'thumbs_down']);
  });
});

describe('newFeedbackSessionId', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('prefers crypto.randomUUID when available', () => {
    vi.spyOn(crypto, 'randomUUID').mockReturnValue('11111111-1111-4111-8111-111111111111');
    expect(newFeedbackSessionId()).toBe('11111111-1111-4111-8111-111111111111');
  });

  it('falls back to getRandomValues when randomUUID is unavailable', () => {
    // @ts-expect-error — simulate a browser without crypto.randomUUID.
    vi.spyOn(crypto, 'randomUUID', 'get').mockReturnValue(undefined);
    const id = newFeedbackSessionId();
    expect(id).toMatch(/^s-[0-9a-f]{32}$/);
  });

  it('degrades to a timestamp id when Web Crypto is entirely absent', () => {
    const original = globalThis.crypto;
    // @ts-expect-error — simulate an insecure context with no Web Crypto.
    delete globalThis.crypto;
    try {
      expect(newFeedbackSessionId()).toMatch(/^s-[0-9a-z]+$/);
    } finally {
      Object.defineProperty(globalThis, 'crypto', { value: original, configurable: true });
    }
  });
});
