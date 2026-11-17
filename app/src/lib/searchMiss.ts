/**
 * The gallery's private list of searches that found nothing: the search box hands a finished
 * text that matched no plot in the whole catalogue to `sendSearchMiss`, which posts it to the API
 * (`POST /search/miss`, `api/search_misses.py`). The owner reads the list on /debug to see what
 * the catalogue lacks and which words the search does not know. Plausible never sees the text.
 *
 * - The text travels in the JSON body, never in the URL: request URLs stand in the server logs.
 * - Only from the live site, and not while the admin's own use is muted: a local build, a
 *   preview and a test send nothing, the same rule as the analytics (`inProduction`).
 * - Once per distinct text and page load, and nothing shorter than `MIN_MISS_LENGTH`
 *   characters, which the API would drop anyway.
 * - Fire and forget: the app and the API deploy apart, so the route may answer 404 for a while.
 *   No retry, nothing in the console, no effect on the search.
 */

import { analyticsMuted } from 'src/analytics/mute';
import { inProduction } from 'src/hooks/useAnalytics';
import { apiUrl, endpoints } from 'src/lib/api';

/** How long the search box waits after the last keystroke before a text counts as finished. */
export const MISS_PAUSE_MS = 2000;

/** The shortest text that is sent, in characters: one character is the start of a search. */
export const MIN_MISS_LENGTH = 2;

// The texts this page load already sent; a full reload starts over.
const sent = new Set<string>();

/** Forgets the texts already sent. For tests: the set is the module's and outlives one. */
export function forgetSentMisses(): void {
  sent.clear();
}

/**
 * Sends one normalised search text (`normalizeQuery`) that found nothing in the whole catalogue.
 * `keepalive` lets a miss sent as the visitor leaves outlive the page.
 */
export function sendSearchMiss(query: string): void {
  if (!inProduction() || analyticsMuted()) return;
  if (Array.from(query).length < MIN_MISS_LENGTH || sent.has(query)) return;
  sent.add(query);
  fetch(apiUrl(endpoints.searchMiss), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    keepalive: true,
  }).catch(() => undefined);
}
