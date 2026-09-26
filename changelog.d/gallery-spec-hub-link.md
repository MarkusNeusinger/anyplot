### Added

- **The gallery links a spec's own page when it is filtered to that spec.**
  `/plots?spec=manhattan-gwas` shows the same implementations as
  `/manhattan-gwas` but never linked to it: the spec page was reachable only
  through an implementation's `.compare()`. A `{spec_id}.compare() →` link now
  sits above the grid whenever exactly one known spec is filtered, and its
  click is tracked as `nav_click` with `source: gallery_spec_hub`. It is set in
  one tone rather than the two-tone `subject.verb()` style, whose dimmed
  subject measures about 3.7:1 on the light background, below WCAG AA.
  (#11845)

### Fixed

- **`docs/reference/plausible.md` describes the recorded gallery paths again.**
  Filter pageviews have been recorded under `/plots/...` since 2026-07-10, but
  the doc still showed the old root paths and missed the `lang` and `language`
  categories. `docs/reference/seo.md` also still said the `/{spec_id}/{language}`
  crawler redirect pointed at a `/seo-proxy/` path. (#11845)
