/**
 * The addresses that only lead to another one. Each is a redirect in its route's loader, so the
 * address never becomes a page of its own: no render, no history entry, and no pageview, since
 * the layout records one for every address that does become a page (`RootLayout`). The page
 * being left also stays on screen until the destination is there, which the scroll depth
 * Plausible reports for it depends on.
 */

import { type LoaderFunctionArgs, redirect } from 'react-router-dom';

import { AGENT_CHAT_PARAMS, paths, specPath } from 'src/routes/paths';
import { setAdminHint } from 'src/utils/adminAuth';

/**
 * The old admin address of the agent chat, `/debug/agent?spec=&library=&language=`, for links
 * and bookmarks from before 2026-11-06: one chat page at `/agent` serves visitors and admins
 * since then, and detects the admin itself (`AgentChatPage`). It keeps the parameters the page
 * reads (`AGENT_CHAT_PARAMS`) and drops the rest, such as the fan-out's old `&all=1`.
 *
 * It sets the admin hint first. A full load of this address reaches the app only after
 * Cloudflare Access let the browser through `/debug*`, so the bookmark's user is an admin even
 * in a fresh browser, after cleared storage or after a refusal cleared the hint; without it the
 * page would treat them as a visitor and show no admin menu. The hint grants nothing: the page
 * still asks the admin lane's `/status`, and a refusal there clears it again (`useAgentAdmin`).
 * No sign-in door of its own: an expired admin session signs in again on `/debug`.
 */
export function agentChatRedirect({ request }: LoaderFunctionArgs) {
  const old = new URL(request.url).searchParams;
  const kept = new URLSearchParams();
  for (const name of AGENT_CHAT_PARAMS) {
    const value = old.get(name);
    if (value !== null) kept.set(name, value);
  }
  const query = kept.toString();
  // Before the navigation: the chat page reads the hint once, when it mounts.
  setAdminHint(true);
  return redirect(query ? `${paths.agent}?${query}` : paths.agent);
}

/** `/{spec}/{language}` is the spec hub scoped to one language: `/{spec}?language={language}`. */
export function specLanguageRedirect({ params }: LoaderFunctionArgs) {
  const { specId = '', language = '' } = params;
  return redirect(`${specPath(specId)}?language=${encodeURIComponent(language)}`);
}
