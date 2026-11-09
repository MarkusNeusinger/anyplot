/**
 * One admin GET of a debug section, read by `read`: the agent usage day views
 * (`AgentDailyUsage.tsx`) and the machine readers section use it.
 */

import { useEffect, useState } from 'react';

import { fetchWithAuth } from 'src/lib/api';

interface Answer<T> {
  key: string;
  value: T | null;
}

/**
 * The answer of `url` for this token and reload count: `undefined` while it is
 * out, `null` when the request failed or `read` refused the body. Pass a stable
 * `read` (a module-level function), or every render fetches again.
 */
export function useAnswer<T>(
  url: string,
  token: string,
  reloadCounter: number,
  read: (body: unknown) => T | null
): T | null | undefined {
  const key = `${url}\n${token}\n${reloadCounter}`;
  const [answer, setAnswer] = useState<Answer<T> | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetchWithAuth(url, token)
      .then(async response => (response.ok ? read(await response.json()) : null))
      .catch(() => null)
      .then(value => {
        if (!cancelled) setAnswer({ key, value });
      });
    return () => {
      cancelled = true;
    };
  }, [url, token, key, read]);
  return answer && answer.key === key ? answer.value : undefined;
}
