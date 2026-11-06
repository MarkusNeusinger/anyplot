/**
 * The old admin address of the agent chat, `/debug/agent?spec=&library=&language=`, for links
 * and bookmarks from before 2026-11-06: one chat page at `/agent` serves visitors and admins
 * since then, and detects the admin itself (`AgentChatPage`). A client-side redirect, replacing
 * the history entry, that keeps the parameters the page reads (`AGENT_CHAT_PARAMS`) and drops
 * the rest, such as the fan-out's old `&all=1`.
 *
 * It sets the admin hint first. A full load of this address reaches the app only after
 * Cloudflare Access let the browser through `/debug*`, so the bookmark's user is an admin even
 * in a fresh browser, after cleared storage or after a refusal cleared the hint; without it the
 * page would treat them as a visitor and show no admin menu. The hint grants nothing: the page
 * still asks the admin lane's `/status`, and a refusal there clears it again (`useAgentAdmin`).
 * No sign-in door of its own: an expired admin session signs in again on `/debug`.
 */

import { useEffect } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import { AGENT_CHAT_PARAMS, paths } from 'src/routes/paths';
import { setAdminHint } from 'src/utils/adminAuth';

export function AgentChatRedirect() {
  const { search } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const old = new URLSearchParams(search);
    const kept = new URLSearchParams();
    for (const name of AGENT_CHAT_PARAMS) {
      const value = old.get(name);
      if (value !== null) kept.set(name, value);
    }
    const query = kept.toString();
    // Before the navigation: the chat page reads the hint once, when it mounts.
    setAdminHint(true);
    navigate({ pathname: paths.agent, search: query ? `?${query}` : '' }, { replace: true });
  }, [search, navigate]);

  return null;
}
