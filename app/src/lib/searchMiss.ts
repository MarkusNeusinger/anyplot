/**
 * The gallery's private list of searches that found nothing: the search box hands a finished
 * text that matched no plot in the whole catalogue to `sendSearchMiss`, which posts it to the API
 * (`POST /search/miss`, `api/search_misses.py`). The owner reads the list on /debug to see what
 * the catalogue lacks and which words the search does not know. Plausible never sees the text.
 *
 * - Only a text that reads as a search for a plot leaves the browser (`isCountableMiss`, the
 *   API's rule): an address, a phone number or a link does not.
 * - The text travels in the JSON body, never in the URL: request URLs stand in the server logs.
 *   No cookie and no referrer go with it, whatever the API's address becomes.
 * - Only from the live site, and not while the admin's own use is muted: a local build, a
 *   preview and a test send nothing, the same rule as the analytics (`inProduction`).
 * - Once per distinct text and page load.
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

/** The most decimal digits a text may hold: enough for "ggplot2" or a year, too few for a phone. */
export const MAX_MISS_DIGITS = 6;

/**
 * The signs a text may hold besides letters, combining marks, decimal digits and spaces: those a
 * plot search uses, and those some scripts spell their words with. By code point: the middle dot
 * (U+00B7), the katakana middle dot (U+30FB), the Hebrew geresh (U+05F3), gershayim (U+05F4) and
 * maqaf (U+05BE), the Tibetan tsheg (U+0F0B) and the Ethiopic wordspace (U+1361).
 */
export const MISS_MARKS =
  " -_.+#/&'(),%" + String.fromCodePoint(0x00b7, 0x30fb, 0x05f3, 0x05f4, 0x05be, 0x0f0b, 0x1361);

// The zero width non-joiner and joiner: ignorable, but ordinary spelling between two letters or
// marks in several scripts, and allowed there and nowhere else.
const JOINERS = new Set([String.fromCodePoint(0x200c), String.fromCodePoint(0x200d)]);
// The code points made to show as nothing: fillers, variation selectors, format characters and
// their kind. The API holds the same set by range (`DEFAULT_IGNORABLE`).
const IGNORABLE = /^\p{Default_Ignorable_Code_Point}$/u;
const LETTER = /^\p{L}$/u;
const MARK = /^\p{M}$/u;
const DIGIT = /^\p{Nd}$/u;

const isLetterOrMark = (char: string | undefined): boolean =>
  char !== undefined && (LETTER.test(char) || MARK.test(char));

/**
 * Whether a normalised text (`normalizeQuery`) reads as a search for a plot that shows something,
 * in any script: two characters or more, each a letter, a combining mark on a letter or a mark, a
 * decimal digit (at most `MAX_MISS_DIGITS` in all), a space or one of `MISS_MARKS`, and at least
 * one letter or digit. A zero width non-joiner or joiner counts only between two letters or marks.
 * No `@` and no `:`, so no address and no link; no control, format, direction or other ignorable
 * character, so no row looks empty or reads backwards; no bare combining mark. A text has to show
 * something, but a joiner inside a word can still make a row that looks like another in a script
 * where it changes nothing that is seen; each such row is its own entry, which the owner can
 * delete. The API keeps only what passes the same rule (`is_countable` in
 * `api/search_misses.py`), and `searchQuery.cases.json` holds the two together.
 */
export function isCountableMiss(query: string): boolean {
  const chars = Array.from(query);
  if (chars.length < MIN_MISS_LENGTH) return false;
  let digits = 0;
  let shows = false;
  for (let index = 0; index < chars.length; index++) {
    const char = chars[index];
    if (JOINERS.has(char)) {
      const between =
        index > 0 &&
        index < chars.length - 1 &&
        isLetterOrMark(chars[index - 1]) &&
        isLetterOrMark(chars[index + 1]);
      if (!between) return false;
      continue;
    }
    if (IGNORABLE.test(char)) return false;
    if (DIGIT.test(char)) {
      digits += 1;
      shows = true;
    } else if (LETTER.test(char)) {
      shows = true;
    } else if (MARK.test(char)) {
      // A mark sits on the letter or mark before it; a joiner in between belongs to the spelling.
      let base = index - 1;
      while (base >= 0 && JOINERS.has(chars[base])) base -= 1;
      if (base < 0 || !isLetterOrMark(chars[base])) return false;
    } else if (!MISS_MARKS.includes(char)) {
      return false;
    }
  }
  return shows && digits <= MAX_MISS_DIGITS;
}

// The texts this page load already sent; a full reload starts over.
const sent = new Set<string>();

/** Forgets the texts already sent. For tests: the set is the module's and outlives one. */
export function forgetSentMisses(): void {
  sent.clear();
}

/**
 * Sends one normalised search text (`normalizeQuery`) that found nothing in the whole catalogue,
 * when it is countable. `keepalive` lets a miss sent as the visitor leaves outlive the page.
 */
export function sendSearchMiss(query: string): void {
  if (!inProduction() || analyticsMuted()) return;
  if (!isCountableMiss(query) || sent.has(query)) return;
  sent.add(query);
  fetch(apiUrl(endpoints.searchMiss), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    keepalive: true,
  }).catch(() => undefined);
}
