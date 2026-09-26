### Added

- **The gallery links a spec's own page when it is filtered to that spec.**
  `/plots?spec=manhattan-gwas` shows the same implementations as
  `/manhattan-gwas` but never linked to it; getting there meant opening an
  implementation page first. A `{spec_id}.compare() →` link in the style
  guide's explicit-subject form now sits above the grid whenever exactly one
  known spec is filtered. Its click saves the scroll position like a card click
  does and is tracked as `nav_click` with `source: gallery_spec_hub`; its
  accessible name leads with the visible words, without the `.()` a screen
  reader would spell out. (#11845)

### Fixed

- **`docs/reference/plausible.md` describes the recorded gallery paths again.**
  Filter pageviews have been recorded under `/plots/...` since 2026-07-10, but
  the doc still showed the old root paths and missed the `lang` and `language`
  categories. `docs/reference/seo.md` also still said the `/{spec_id}/{language}`
  crawler redirect pointed at a `/seo-proxy/` path. (#11845)
