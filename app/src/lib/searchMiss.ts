/**
 * The gallery's private list of searches that found nothing: the search box hands a finished
 * text that matched no plot in the whole catalogue to `reportSearchMiss`, which counts it at
 * Plausible without the text and posts the text to the API (`POST /search/miss`,
 * `api/search_misses.py`). The owner reads the list on /debug to see what the catalogue lacks and
 * which words the search does not know. Plausible never sees the text.
 *
 * - One decision in the browser (`claimSearchMiss`) makes a text a reported miss, and both reports
 *   follow from it.
 * - Only a text that reads as a search for a plot as a whole leaves the browser, cut to 40
 *   characters after it passed (`keptMissText`, the API's rule): an e-mail address, a phone
 *   number or a link with its scheme does not, also when it stands past the 40th character.
 * - The text travels in the JSON body, never in the URL: request URLs stand in the server logs.
 *   No cookie and no referrer go with it, whatever the API's address becomes.
 * - Only from the live site, and not while the admin's own use is muted: a local build, a
 *   preview and a test send nothing, the same rule as the analytics (`inProduction`).
 * - Once per distinct text and page load.
 * - Fire and forget: the app and the API deploy apart, so the route may answer 404 for a while.
 *   No retry, nothing in the console, no effect on the search.
 */

import { analyticsMuted } from 'src/analytics/mute';
import { cutQuery, foldQuery, inProduction } from 'src/hooks/useAnalytics';
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
 * Whether a folded text (`foldQuery`, or that text cut) reads as a search for a plot that shows
 * something, in any script: two characters or more, each a letter, a combining mark on a letter or a mark, a
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

/**
 * The text a row would keep of what was typed, or `null` when nothing of it is kept. Judged whole,
 * then cut, then judged again: the rule runs over the whole folded text first (`foldQuery`), so an
 * `@`, a `:` or a seventh digit past the 40th character refuses the text as it would within them,
 * and a long address or number is never kept in part. Only a text that passed is cut to 40
 * characters (`cutQuery`), and the cut text is judged once more, since a cut can end on a joiner.
 * The API decides the same way (`kept_query` in `api/search_misses.py`).
 */
export function keptMissText(typed: string): string | null {
  const folded = foldQuery(typed);
  if (!isCountableMiss(folded)) return null;
  const query = cutQuery(folded);
  return isCountableMiss(query) ? query : null;
}

// The texts this page load already reported; a full reload starts over.
const reported = new Set<string>();

/** Forgets the texts already reported. For tests: the set is the module's and outlives one. */
export function forgetSentMisses(): void {
  reported.clear();
}

/**
 * The one decision that a finished search text is a miss worth reporting: the text a row would
 * keep of it (`keptMissText`), when there is one and it was not reported yet in this page load.
 * Claims and returns that text, so it is never reported twice, or returns `null`. Both reports of
 * a miss follow from this one decision in the browser (`reportSearchMiss`). Afterwards they can
 * still part: the API's limits, the day's cap or a failed write can leave a counted miss without a
 * row, and a browser that blocks the analytics script can leave a row without a count.
 */
export function claimSearchMiss(typed: string): string | null {
  const query = keptMissText(typed);
  if (query === null || reported.has(query)) return null;
  reported.add(query);
  return query;
}

/**
 * Reports one finished search text, as typed, that found nothing in the whole catalogue, when
 * `claimSearchMiss` claims it: `count` counts it at Plausible without the text (the
 * `search_no_results` event), and the text a row keeps goes to the private list
 * (`sendSearchMiss`). Each keeps its own gate for the live site and the admin's mute.
 */
export function reportSearchMiss(typed: string, count: () => void): void {
  const query = claimSearchMiss(typed);
  if (query === null) return;
  count();
  sendSearchMiss(query);
}

/**
 * Sends one search text to the private list. Only `reportSearchMiss` calls it, after the claim;
 * the rule is checked once more here, so no other caller can send a text the API would refuse.
 * `keepalive` lets a miss sent as the visitor leaves outlive the page.
 */
export function sendSearchMiss(query: string): void {
  if (!inProduction() || analyticsMuted()) return;
  if (!isCountableMiss(query)) return;
  fetch(apiUrl(endpoints.searchMiss), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    keepalive: true,
  }).catch(() => undefined);
}
