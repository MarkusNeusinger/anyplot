import { useCallback } from 'react';

import { useAnalytics } from 'src/hooks/useAnalytics';
import { useLocalStorage } from 'src/hooks/useLocalStorage';
import { apiPost, endpoints } from 'src/lib/api';
import { turnstileHeaders } from 'src/lib/turnstile';
import {
  FEEDBACK_SESSION_KEY,
  newFeedbackSessionId,
  type QuickReaction,
  type VoteTarget,
} from 'src/utils/feedback';

/**
 * Submit a reaction-only feedback entry (👍 / 👎) for one implementation.
 *
 * Headless counterpart to the FeedbackWidget's quick-stack: same endpoint,
 * same session correlation and the same `feedback_submitted` analytics event
 * (with `source: "plot_vote"`), but it leaves all UI to the caller so the
 * buttons can sit directly on the plot. Unlike the widget it names the
 * implementation (`library_id`, `language`) so votes can be counted per image.
 * Each vote carries a fresh Turnstile token (`src/lib/turnstile.ts`): the
 * script loads on the first tap, not with the page, and the caller's
 * optimistic UI hides the check's second or so.
 *
 * @returns An async `submit(reaction, target)` resolving to `true` when the
 *   server accepted the entry, `false` on any non-OK response or network error.
 */
export function useQuickReaction() {
  const { trackEvent } = useAnalytics();
  const [sessionId, setSessionId] = useLocalStorage<string>(FEEDBACK_SESSION_KEY, '');

  return useCallback(
    async (reaction: QuickReaction, target: VoteTarget): Promise<boolean> => {
      const session = sessionId || newFeedbackSessionId();
      if (!sessionId) setSessionId(session);

      const path = window.location.pathname + window.location.search;

      try {
        await apiPost<unknown>(
          endpoints.feedback,
          {
            message: null,
            reaction,
            contact: null,
            path,
            spec_id: target.specId,
            library_id: target.libraryId,
            language: target.language,
            viewport: `${window.innerWidth}x${window.innerHeight}`,
            session_id: session,
            website: '',
          },
          { headers: await turnstileHeaders('site_feedback') }
        );
      } catch {
        // Non-2xx, a failed bot check or a network failure — report as
        // unsuccessful so the caller can roll back its optimistic UI. No retry:
        // a quick vote is low-stakes, and a second tap sends it again.
        return false;
      }
      trackEvent('feedback_submitted', {
        source: 'plot_vote',
        spec: target.specId,
        library: target.libraryId,
      });
      return true;
    },
    [sessionId, setSessionId, trackEvent]
  );
}
