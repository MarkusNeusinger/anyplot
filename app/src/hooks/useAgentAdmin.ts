/**
 * Whether the chat at `/agent` runs for an admin, and so on the admin lane (`/debug/agent/*`).
 *
 * Only a browser that claims it asks: local development, or the admin hint that `DebugPage` sets
 * after `/debug/status` answered 200 (`src/utils/adminAuth.ts`). Every other browser, a visitor's,
 * sends no request to the debug API: the answer is `none` at once. A claiming browser asks the
 * admin lane's `GET /status` once per mount, with the tab's admin token or the Cloudflare Access
 * cookie, and the answer decides:
 *
 * - `admin`: the admin gate let the call through. That includes `404 not_enabled`, which the BFF
 *   answers only after its admin gate (`AGENT_ENABLED` off): the session's open then fails with
 *   the same code, and the admin menu names the switch.
 * - `expired`: the gate refused (401, or 403 for an account off the allow-list), no answer came
 *   (an expired Access session turns the call into a cross-origin redirect, which `fetch` reports
 *   as a network error), or the call failed otherwise. The page falls back to the public lane,
 *   and the admin menu says the admin session expired and links to `/debug`. A refusal clears the
 *   hint, as `DebugPage` does, so the next visit asks nothing; a missing answer keeps it. Local
 *   development without the hint claimed no admin, so a failed check there is `none`.
 * - `checking` until the answer: the page waits, since the answer picks the lane.
 *
 * `refused()` is for a refusal later on (a 401 on any admin call of the session): the hint goes
 * and the answer becomes `expired`. The server's admin gate decides every call either way; the
 * answer only picks which API the page calls, and grants nothing.
 *
 * The check's answer is the admin lane's status, which the chat needs too (its libraries, the
 * run cap, the day's pause): `takeStatus()` hands it over once, so the first admin chat of the
 * page asks no second time, and a later one (after "view as visitor" and back) asks afresh. For
 * `not_enabled` it hands over `{libraries: [], enabled: false}`, so the chat does not ask the
 * switched-off service again either.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { CONFIG } from 'src/global-config';
import { agentApi, AgentApiError, type AgentStatus } from 'src/lib/agent';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';

export type AgentAdmin = 'none' | 'checking' | 'admin' | 'expired';

export interface AgentAdminCheck {
  admin: AgentAdmin;
  /** The code of the failed check (`unauthorized`, `forbidden`, `unreachable`, ...), else null. */
  failure: string | null;
  /** An admin call refused later: the hint goes, and the answer becomes `expired`. */
  refused: () => void;
  /** The check's status answer, once; null after that, or when the check had none. */
  takeStatus: () => AgentStatus | null;
}

export function useAgentAdmin(): AgentAdminCheck {
  // Read once per mount: a hint set or cleared in another tab changes nothing on this page.
  const [claim] = useState(() => {
    const hinted = readAdminHint();
    return { claimed: CONFIG.features.agentChat && (CONFIG.isDev || hinted), hinted };
  });
  const [answer, setAnswer] = useState<{ admin: AgentAdmin; failure: string | null }>(() => ({
    admin: claim.claimed ? 'checking' : 'none',
    failure: null,
  }));
  const checked = useRef<AgentStatus | null>(null);

  useEffect(() => {
    if (!claim.claimed) return;
    let active = true;
    agentApi.status(readAdminToken()).then(
      answered => {
        if (!active) return;
        checked.current = answered;
        setAnswer({ admin: 'admin', failure: null });
      },
      (err: unknown) => {
        if (!active) return;
        const status = err instanceof AgentApiError ? err.status : 0;
        if (err instanceof AgentApiError && err.code === 'not_enabled') {
          // The chat's own `/status` would meet the same switch: it takes this answer instead,
          // a service without libraries, which changes nothing it shows, as a failed call would.
          checked.current = { libraries: [], enabled: false };
          setAnswer({ admin: 'admin', failure: null });
          return;
        }
        // A `GET` meets no CSRF guard, so a 401 or 403 here is the admin gate's own refusal. Its
        // detail is a sentence (with the account's address for a 403), so the menu names the
        // status's code instead.
        const refused = status === 401 || status === 403;
        if (refused) setAdminHint(false);
        const code = refused
          ? status === 401
            ? 'unauthorized'
            : 'forbidden'
          : err instanceof AgentApiError
            ? err.code
            : 'unreachable';
        setAnswer({ admin: claim.hinted ? 'expired' : 'none', failure: code });
      }
    );
    return () => {
      active = false;
    };
  }, [claim]);

  const refused = useCallback(() => {
    setAdminHint(false);
    checked.current = null;
    setAnswer({ admin: 'expired', failure: 'unauthorized' });
  }, []);

  const takeStatus = useCallback(() => {
    const answered = checked.current;
    checked.current = null;
    return answered;
  }, []);

  return { ...answer, refused, takeStatus };
}
