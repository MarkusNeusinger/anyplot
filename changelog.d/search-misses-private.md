### Added

- **A private list of the gallery searches that found nothing.** A search
  that finds nothing in the whole catalogue (not in the filtered plots, not
  in all of them, in no category) goes to the new `search_misses` table, and
  the "search misses" section on `/debug` lists the texts of the last 180 days,
  most searched or most recently searched first and in pages, with a
  `.delete()` per text; it names the days that reached the day's cap and
  deletes such a day whole. The gallery sends only the finished text: after
  two seconds without a keystroke, or when the search loses focus, once per
  text and page load, so a fragment typed on within two seconds is never
  kept; the clear cross, Escape and "← back" throw a pending text away, and
  leaving the gallery within the two seconds drops it too. Both the app and
  the API fold the text (compatibility forms,
  typographic apostrophes, hyphens and dashes, soft hyphens) and keep it only
  when it reads as a search for a plot and shows something (letters and marks
  of any script, at most six digits, spaces and a few signs, among them those
  some scripts spell words with, no character that shows as nothing), so an
  e-mail address, a phone number or a link with its scheme
  never leaves the browser. A row is the text, the UTC day and a count, with
  no address, no user agent, no time of day and no session; it is
  pseudonymous, since the 30-day request log could match it by its day. The
  text travels in the body of `POST /search/miss`, which reads at most 1 KiB
  before it parses anything, answers `204` whatever happened, never logs the
  text, and gives a validation error without the body; the API normalises it
  again with the app's rule, held to it by shared test cases. A network (an
  address, or its /64 for IPv6) may send 20 requests a minute, a day takes at
  most 1,000 new texts, and rows are deleted after 180 days, every text alike,
  also when no miss comes in. It is a best-effort counter, and the list shows
  what the catalogue lacks and which words the search doesn't know. The
  privacy policy names the list in a row of its own, with its 180 days, and
  says that search texts sent to the public dashboard before the change still
  show there. The row says what the rule keeps out, that anything else typed
  may be kept, and asks for no personal data; the crawler copy of the page
  carries it too. A hand-made database snapshot leaves the table's rows out
  (`pg_dump --exclude-table-data=search_misses`, now part of the snapshot
  rule), so a text cannot outlive its period in a file that is never deleted.

### Changed

- **The search events no longer carry what a visitor typed.** `search` and
  `search_no_results` sent the search text as `query` to Plausible, whose
  dashboard is public. `search` now carries only the `category` of the pick
  and `search_no_results` no property at all; the texts that found nothing
  are in the private list instead. `search_no_results` also fires only for a
  finished search that finds nothing in the whole catalogue, at the moment
  and from the same decision as its report to the list, never for a fragment
  or a thrown-away text, so its count is smaller from then on and not
  comparable with earlier months.
