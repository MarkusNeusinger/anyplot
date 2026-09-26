### Changed

- **Search results for a plot now name its languages and its other
  libraries.** A hub's title and H1 read `{title} in Python, R, Julia and
  JavaScript`; an implementation page's read `{title} in plotnine (Python)`,
  and its meta description adds "also in 14 other libraries". A lead
  paragraph under each H1 names the libraries by language and, on an
  implementation page, links the hub with the hub's own title. A searcher
  reported that "manhattan plot python" returned "Manhattan Plot for GWAS -
  plotnine" with nothing to say that seven other Python libraries had the same
  plot: the hub's title never named a language, so a single implementation
  page outranked it. Languages now follow the registry order (Python first)
  everywhere on both page types. `TEMPLATE_LAST_CHANGED` moves to 2026-09-26,
  which also signals the library-first meta descriptions of 2026-09-02 that
  shipped without a bump.

### Fixed

- **Google had no clean image to show as a result's thumbnail.** The only
  preferred-image signal was `og:image`, the text-heavy branded card. Both page
  types now carry a `WebPage` node (`CollectionPage` on the hub) whose
  `primaryImageOfPage` is the exact URL of the render in the body, and the
  implementation's `SoftwareSourceCode` node is marked as the page's main
  entity. `og:image` stays the card for link previews.
