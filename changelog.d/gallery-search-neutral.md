### Changed

- **The gallery search ignores generic words and accents.** On `/plots`, the search drops words that
  only say "a chart" or join two terms (chart, plot, graph, diagram, and, with, and their German,
  French, Spanish, Italian, Portuguese, Dutch and Polish forms, such as Diagramm, graphique or
  wykres) before it matches. A query of nothing but such words still searches as typed. `bar chart`
  now ranks `type:bar` first where it ranked the spec "Bar Chart with Error Bars" first, and `line
  chart` finds the line specs where it found three bar and indicator specs. Fuse folds accents and ß
  on both sides, so `scätter` finds `scatter`. The rule works in any language and needs no word list
  per language: the catalogue's words stay English.
- **The gallery counter names its units.** It reads `37% · 8 specs · 120 plots` instead of
  `37% · 120`, at both widths. A tag on 8 specs in 15 libraries showed 120 without saying that the
  number counts plots.

### Fixed

- **Search after Back finds spec titles again.** Back to `/plots` restores the gallery from the
  layout's saved state without a fetch, and that state did not hold the spec titles. The search then
  matched spec IDs only: `bar chart`, `pie chart` and `line chart` found nothing, and the spec
  tooltips in the dropdown were empty.
- **An empty search inside the filters says why.** When a search finds nothing because the active
  filters hide every match, the dropdown offers `.search_all()` under `results.empty()`, with the
  number of matches in all plots. It removes the filters and keeps the query; a bare Enter never
  picks it.
