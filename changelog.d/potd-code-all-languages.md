### Fixed

- **The plot of the day returns its code for every language.** When the day's
  pick was one of the seven R, Julia, or JavaScript libraries,
  `GET /insights/plot-of-the-day` answered `code`, `image_description`,
  `library_version`, and `language_version` as null, because the
  implementation was looked up under Python. The implementation repository
  now requires the language when it looks up or upserts one implementation,
  with no default, so a call that leaves it out fails instead of looking
  under Python; the plot of the day passes its pick's own language. The
  agent case detail on the debug page had the same gap and now finds the
  catalogue code of a non-Python case. Its diff therefore runs on R, Julia,
  and JavaScript code for the first time: it drops the `//` attribution
  header of a JavaScript export as it drops the `#` header, and both diff
  labels carry the library's file extension instead of `.py`. A JavaScript
  case whose version names no library is now filed under the library its
  exported code names, as the other languages' cases already were, and the
  regression importer (`agents/evals/import_case.py`) reads the header the
  same way, so it replays such a case under that library. (#13123)
