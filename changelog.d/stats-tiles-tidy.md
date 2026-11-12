### Changed

- **The machine readers and shared links tiles on the stats page are plainer.**
  Both draw one bar per day in the green of the visitors strip: the day's sum
  of verified requests, and the day's sum of shares. The machine readers tile
  loses its three-colour split, its legend and its footnote sentence; under
  the bars it gives the 28-day sums in three lines: the verified requests by
  audience, the MCP requests, and the unverified requests. The shared links
  tile gives the platforms' 28-day sums in one line, without its explanatory
  paragraph, which the legal page it links holds. The shared links bars were
  a brighter green than the other strips. (#13071)
- **The shared links tile names the most shared specs and the most shared
  libraries, not single pages.** A spec's sum holds its hub and all of its
  implementation pages, a library's sum its implementation pages across
  specs; a spec links to its hub, a library to the gallery filtered by it.
  `GET /insights/shared-links` answers `top_specs` and `top_libraries` in
  place of `top`; the page-by-page list stays on the debug page. (#13071)
