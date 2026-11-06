/**
 * The old admin address of the agent chat, `/debug/agent?spec=&library=&language=`, for links
 * and bookmarks from before 2026-11-06: one chat page at `/agent` serves visitors and admins
 * since then, and detects the admin itself (`AgentChatPage`). A client-side redirect, replacing
 * the history entry, that keeps the parameters the page reads (`AGENT_CHAT_PARAMS`) and drops
 * the rest, such as the fan-out's old `&all=1`. No sign-in door of its own: the admin signs in
 * on `/debug`.
 */

import { Navigate, useLocation } from 'react-router-dom';

import { AGENT_CHAT_PARAMS, paths } from 'src/routes/paths';

export function AgentChatRedirect() {
  const { search } = useLocation();
  const old = new URLSearchParams(search);
  const kept = new URLSearchParams();
  for (const name of AGENT_CHAT_PARAMS) {
    const value = old.get(name);
    if (value !== null) kept.set(name, value);
  }
  const query = kept.toString();
  return <Navigate to={{ pathname: paths.agent, search: query ? `?${query}` : '' }} replace />;
}
