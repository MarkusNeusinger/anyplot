/**
 * Shared helpers for the lightweight feedback channel (issue #5662).
 *
 * Both the floating FeedbackWidget and the 👍/👎 buttons on a plot submit to
 * the same `/feedback` endpoint and correlate a visitor across submissions
 * with an opaque, locally stored session id. Keeping the key and the id
 * generator here keeps the two entry points in lock-step.
 */

export const FEEDBACK_SESSION_KEY = 'anyplot_feedback_session';

/** localStorage key for the visitor's own 👍/👎 per implementation. */
export const PLOT_VOTES_KEY = 'anyplot_plot_votes';

export const QUICK_REACTIONS = ['thumbs_up', 'thumbs_down'] as const;
export type QuickReaction = (typeof QUICK_REACTIONS)[number];

/** The implementation a plot vote is about. */
export interface VoteTarget {
  specId: string;
  language: string;
  libraryId: string;
}

/** Stable key for one implementation in the persisted votes map. */
export function voteKey({ specId, language, libraryId }: VoteTarget): string {
  return `${specId}/${language}/${libraryId}`;
}

/**
 * Generate an opaque session id used purely as a correlation handle (never a
 * credential), preferring Web Crypto and degrading gracefully on browsers
 * without it. Never falls back to `Math.random()`.
 */
export function newFeedbackSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return `s-${Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')}`;
  }
  // Browser without Web Crypto support (e.g. very old, or insecure context). The
  // session id is an opaque correlation handle, not a credential — a coarse
  // timestamp-derived id is acceptable here.
  return `s-${Date.now().toString(36)}`;
}
