/**
 * The addresses that only lead to another one. Each is a redirect in its route's loader, so the
 * address never becomes a page of its own: no render, no history entry, and no pageview, since
 * the layout records one for every address that does become a page (`RootLayout`). The page
 * being left also stays on screen until the destination is there, which the scroll depth
 * Plausible reports for it depends on.
 *
 * Keeping the old address out of the history takes one of two redirects. A link inside the app
 * has written no entry yet when the loader runs, so the destination is pushed and becomes the
 * link's own entry (`redirect`). A fresh load, and Back or Forward onto the old address, have
 * written theirs: the browser shows the old address before the loader runs, so the destination
 * takes that entry over (`replace`). Pushed on top of it instead, it would leave the old address
 * one step back, and Back would land there and be sent forward again.
 */

import { type LoaderFunctionArgs, redirect, replace } from 'react-router-dom';

import { AGENT_CHAT_PARAMS, paths, specPath } from 'src/routes/paths';
import { setAdminHint } from 'src/utils/adminAuth';

/**
 * The redirect to `to` that leaves no history entry of the address being opened. The address bar
 * tells the two cases apart: it shows that address only once the browser has written it, while a
 * link inside the app runs the loader with the bar still on the page being left, whose entry stays.
 */
function redirectWithoutEntry(request: Request, to: string) {
  const opened = new URL(request.url);
  const { pathname, search } = window.location;
  return opened.pathname === pathname && opened.search === search ? replace(to) : redirect(to);
}

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
  return redirectWithoutEntry(request, query ? `${paths.agent}?${query}` : paths.agent);
}

/** The legal page's old section that moved to the about page: stack, source and running costs. */
export const MOVED_TO_ABOUT = '#transparency';

/**
 * `/legal#transparency` is `/about#transparency` since that section moved. A loader's request
 * carries no fragment, so this reads the address bar, which names the address being opened only on
 * a fresh load: an in-app navigation runs the loader while the bar still shows the page being left,
 * hence the path check. A fresh load of the old address so never becomes a legal page or a
 * pageview, and since the bar already shows the old address, the about page takes over its
 * history entry. An in-app link to it is caught by the page itself (`LegalPage`).
 */
export function legalMovedSectionRedirect() {
  const { pathname, hash } = window.location;
  if (pathname.replace(/\/$/, '') === paths.legal && hash === MOVED_TO_ABOUT) {
    return replace(`${paths.about}${MOVED_TO_ABOUT}`);
  }
  return null;
}

/** `/{spec}/{language}` is the spec hub scoped to one language: `/{spec}?language={language}`. */
export function specLanguageRedirect({ request, params }: LoaderFunctionArgs) {
  const { specId = '', language = '' } = params;
  return redirectWithoutEntry(
    request,
    `${specPath(specId)}?language=${encodeURIComponent(language)}`
  );
}
