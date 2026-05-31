/**
 * Shared helpers for the lightweight feedback channel (issue #5662).
 *
 * Both the floating FeedbackWidget and the in-plot quick-vote buttons submit to
 * the same `/feedback` endpoint and correlate a visitor across submissions with
 * an opaque, locally-stored session id. Keeping the key and id generator here
 * means the two entry points stay in lock-step.
 */

export const FEEDBACK_SESSION_KEY = 'anyplot_feedback_session';

export const QUICK_REACTIONS = ['thumbs_up', 'thumbs_down'] as const;
export type QuickReaction = (typeof QUICK_REACTIONS)[number];

/**
 * Generate an opaque session id used purely as a correlation handle (never a
 * credential), preferring Web Crypto and degrading gracefully on browsers
 * without it. We never fall back to `Math.random()`.
 */
export function newFeedbackSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return `s-${Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')}`;
  }
  // Browser without Web Crypto support (e.g. very old, or insecure context).
  return `s-${Date.now().toString(36)}`;
}
