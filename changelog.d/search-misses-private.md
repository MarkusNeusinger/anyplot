### Added

- **A private list of the gallery searches that found nothing.** A search
  that finds nothing in the whole catalogue (not in the filtered plots, not
  in all of them, in no category) goes to the new `search_misses` table, and
  the "search misses" section on `/debug` lists the texts of the last 90 days,
  most searched first, with a `.delete()` per text. The gallery sends only the
  finished text: after two seconds without a keystroke, or when the search
  loses focus or closes, once per text and page load, so a typing fragment is
  never kept. A row is the text, the UTC day and a count, with no address, no
  user agent, no time of day and no session. The text travels in the body of
  `POST /search/miss`, which answers `204` whatever happened, never logs the
  text, and gives a validation error without the body; the API normalises it
  again with the app's rule, held to it by shared test cases. A network may
  send 20 requests a minute, a day takes at most 1,000 new texts, and rows
  are deleted after 90 days. The list shows what the catalogue lacks and
  which words the search doesn't know.

### Changed

- **The search events no longer carry what a visitor typed.** `search` and
  `search_no_results` sent the search text as `query` to Plausible, whose
  dashboard is public. `search` now carries only the `category` of the pick
  and `search_no_results` no property at all; the texts that found nothing
  are in the private list instead.
