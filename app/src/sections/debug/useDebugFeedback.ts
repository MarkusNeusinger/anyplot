import { useEffect, useState } from 'react';

import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';

export interface FeedbackTopPage {
  path: string;
  count: number;
  last_seen: string | null;
}

export type FeedbackStatus = 'new' | 'in_progress' | 'done' | 'wont_solve';
export type FeedbackMessageFilter = '' | 'open' | FeedbackStatus;

export interface FeedbackMessageItem {
  id: string;
  timestamp: string;
  path: string | null;
  message: string;
  reaction: string | null;
  session_id: string;
  resolved: boolean;
  status: FeedbackStatus;
}

export const DEFAULT_MESSAGE_FILTER: FeedbackMessageFilter = 'open';

export function useDebugFeedback(adminToken: string, authRequired: boolean, reloadCounter: number) {
  const [topThumbsUp, setTopThumbsUp] = useState<FeedbackTopPage[]>([]);
  const [topThumbsDown, setTopThumbsDown] = useState<FeedbackTopPage[]>([]);
  const [feedbackMessages, setFeedbackMessages] = useState<FeedbackMessageItem[]>([]);
  const [feedbackStatusFilter, setFeedbackStatusFilter] =
    useState<FeedbackMessageFilter>(DEFAULT_MESSAGE_FILTER);

  useEffect(() => {
    if (authRequired) return;
    let cancelled = false;
    const qs = feedbackStatusFilter ? `?status=${feedbackStatusFilter}&limit=50` : '?limit=50';
    Promise.all([
      fetchWithAuth(
        `${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_up&limit=15`,
        adminToken
      ).then(r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])),
      fetchWithAuth(
        `${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_down&limit=15`,
        adminToken
      ).then(r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])),
      fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/messages${qs}`, adminToken).then(r =>
        r.ok ? (r.json() as Promise<FeedbackMessageItem[]>) : []
      ),
    ])
      .then(([up, down, msgs]) => {
        if (cancelled) return;
        setTopThumbsUp(Array.isArray(up) ? up : []);
        setTopThumbsDown(Array.isArray(down) ? down : []);
        setFeedbackMessages(Array.isArray(msgs) ? msgs : []);
      })
      .catch(() => {
        /* /debug/status useEffect already surfaces auth/network errors */
      });
    return () => {
      cancelled = true;
    };
  }, [adminToken, authRequired, reloadCounter, feedbackStatusFilter]);

  const updateFeedbackStatus = async (id: string, newStatus: FeedbackStatus) => {
    // Optimistic update — revert on failure so the dropdown stays truthful.
    const prev = feedbackMessages;
    setFeedbackMessages(prev.map(m => (m.id === id ? { ...m, status: newStatus } : m)));
    try {
      const r = await fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/${id}`, adminToken, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
    } catch {
      setFeedbackMessages(prev);
    }
  };

  return {
    topThumbsUp,
    topThumbsDown,
    feedbackMessages,
    feedbackStatusFilter,
    setFeedbackStatusFilter,
    updateFeedbackStatus,
  };
}
