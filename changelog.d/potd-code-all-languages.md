### Fixed

- **The plot of the day returns its code for every language.** When the day's
  pick was one of the seven R, Julia, or JavaScript libraries,
  `GET /insights/plot-of-the-day` answered `code`, `image_description`,
  `library_version`, and `language_version` as null, because the
  implementation was looked up under Python. The implementation repository
  now requires the language for every lookup and write of one
  implementation, with no default, so a call that leaves it out fails
  instead of looking under Python; the plot of the day passes its pick's own
  language. The agent case detail on the debug page had the same gap and now
  finds the catalogue code of a non-Python case.
