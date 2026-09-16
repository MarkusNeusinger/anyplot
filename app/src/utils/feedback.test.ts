import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  FEEDBACK_SESSION_KEY,
  newFeedbackSessionId,
  PLOT_VOTES_KEY,
  QUICK_REACTIONS,
  voteKey,
} from 'src/utils/feedback';

describe('feedback constants', () => {
  it('exposes stable storage keys and the two quick reactions', () => {
    expect(FEEDBACK_SESSION_KEY).toBe('anyplot_feedback_session');
    expect(PLOT_VOTES_KEY).toBe('anyplot_plot_votes');
    expect(QUICK_REACTIONS).toEqual(['thumbs_up', 'thumbs_down']);
  });
});

describe('voteKey', () => {
  it('keys a vote by spec, language and library', () => {
    expect(voteKey({ specId: 'scatter-basic', language: 'python', libraryId: 'matplotlib' })).toBe(
      'scatter-basic/python/matplotlib'
    );
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
    const original = crypto.randomUUID;
    Object.defineProperty(crypto, 'randomUUID', { value: undefined, configurable: true });
    try {
      expect(newFeedbackSessionId()).toMatch(/^s-[0-9a-f]{32}$/);
    } finally {
      Object.defineProperty(crypto, 'randomUUID', { value: original, configurable: true });
    }
  });

  it('degrades to a timestamp id when Web Crypto is entirely absent', () => {
    const original = globalThis.crypto;
    Object.defineProperty(globalThis, 'crypto', { value: undefined, configurable: true });
    try {
      expect(newFeedbackSessionId()).toMatch(/^s-[0-9a-z]+$/);
    } finally {
      Object.defineProperty(globalThis, 'crypto', { value: original, configurable: true });
    }
  });
});
