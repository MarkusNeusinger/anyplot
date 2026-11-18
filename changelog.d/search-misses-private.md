### Added

- **A private list of the gallery searches that found nothing.** A search
  that finds nothing in the whole catalogue (not in the filtered plots, not
  in all of them, in no category) goes to the new `search_misses` table, and
  the "search misses" section on `/debug` lists the texts of the last 90 days,
  most searched or most recently searched first and in pages, with a
  `.delete()` per text; it names the days that reached the day's cap and
  deletes such a day whole. The gallery sends only the finished text: after
  two seconds without a keystroke, or when the search loses focus or the page
  is left, once per text and page load, so a fragment typed on within two
  seconds is never kept; the clear cross, Escape and "← back" throw a pending
  text away. Both the app and the API fold the text (compatibility forms,
  typographic apostrophes and dashes) and keep it only when it reads as a
  search for a plot and shows something (letters and marks of any script, at
  most six digits, spaces and a few signs, no character that shows as
  nothing), so an e-mail address, a phone number or a link with its scheme
  never leaves the browser. A row is the text, the UTC day and a count, with
  no address, no user agent, no time of day and no session; it is
  pseudonymous, since the 30-day request log could match it by its day. The
  text travels in the body of `POST /search/miss`, which reads at most 1 KiB
  before it parses anything, answers `204` whatever happened, never logs the
  text, and gives a validation error without the body; the API normalises it
  again with the app's rule, held to it by shared test cases. A network (an
  address, or its /64 for IPv6) may send 20 requests a minute, a day takes at
  most 1,000 new texts, and rows are deleted after 90 days, also when no miss
  comes in. It is a best-effort counter, and the list shows what the
  catalogue lacks and which words the search doesn't know.

### Changed

- **The search events no longer carry what a visitor typed.** `search` and
  `search_no_results` sent the search text as `query` to Plausible, whose
  dashboard is public. `search` now carries only the `category` of the pick
  and `search_no_results` no property at all; the texts that found nothing
  are in the private list instead.
