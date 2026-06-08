import { useCallback } from 'react';
import { API_URL } from '../constants';
import { useAnalytics } from './useAnalytics';
import { useLocalStorage } from './useLocalStorage';
import { specIdFromPath } from '../utils/paths';
import {
  FEEDBACK_SESSION_KEY,
  newFeedbackSessionId,
  type QuickReaction,
} from '../utils/feedback';

/**
 * Submit a reaction-only feedback entry (👍 / 👎) to the `/feedback` endpoint.
 *
 * This is the headless counterpart to the FeedbackWidget's quick-stack: it
 * carries the same payload shape (path, spec id, viewport, correlation session)
 * and fires the same `feedback_submitted` analytics event, but leaves all UI to
 * the caller so it can live directly on a plot overlay.
 *
 * @param mode - Value recorded as the analytics `mode` so the originating
 *   surface (e.g. `'plot_overlay'`) can be told apart from the FAB widget.
 * @returns An async `submit(reaction)` that resolves to `true` when the server
 *   accepted the entry, `false` on any non-OK response or network error.
 */
export function useQuickReaction(mode: string) {
  const { trackEvent } = useAnalytics();
  const [sessionId, setSessionId] = useLocalStorage<string>(FEEDBACK_SESSION_KEY, '');

  return useCallback(
    async (reaction: QuickReaction): Promise<boolean> => {
      const session = sessionId || newFeedbackSessionId();
      if (!sessionId) setSessionId(session);

      const path = window.location.pathname + window.location.search;
      const specId = specIdFromPath(window.location.pathname);

      try {
        const response = await fetch(`${API_URL}/feedback`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: null,
            reaction,
            contact: null,
            path,
            spec_id: specId,
            viewport: `${window.innerWidth}x${window.innerHeight}`,
            session_id: session,
            website: '',
          }),
        });
        if (!response.ok) return false;
        trackEvent('feedback_submitted', {
          path: path || undefined,
          reaction,
          has_contact: 'false',
          spec_id: specId,
          mode,
        });
        return true;
      } catch {
        // Network failure — surface as an unsuccessful submit so the caller can
        // roll back any optimistic UI. No retry: a quick reaction is low-stakes.
        return false;
      }
    },
    [sessionId, setSessionId, trackEvent, mode],
  );
}
