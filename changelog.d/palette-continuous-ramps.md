### Changed

- **The continuous colour ramps have their own stops per theme, for fields and for marks.**
  `imprint_seq` was one green-to-blue ramp for both themes, so narrow in lightness that high and low
  values barely separated in a heatmap. It now has four ramps in the brand hues, as positioned stops:
  a wide one for filled fields (pale mint to navy on the light page, deep green to pale blue on the
  dark one) and one for points, lines, outlines and bars whose every colour keeps 3:1 against its
  page. In both themes high values stand out from the page. `imprint_div` keeps the page as its
  midpoint for fields; for marks it takes a grey that keeps at least 3:1 against the page, the
  `muted` anchor `#6B6A63` on the light page and `#686762` on the dark one, where the brighter
  `muted` ink would outshine the poles, so a mark at the midpoint no longer vanishes and the
  extremes lead. A label on a coloured fill (a bar segment, a heatmap cell) now takes the light or
  dark ink that reads on that fill, or a halo carries it, and the ramp helpers (`ramp_color` in
  Python, `rampAt` in JavaScript) give a missing value no colour instead of the low end.
  `core/palette.py` (`sequential_stops`, `diverging_stops`, `sequential`, `diverging`,
  `ramp_color`), the style guide, the review rubric, the fifteen library prompts, the JavaScript
  harness's tokens (`seqFields`, `seqMarks`, `divFields`, `divMarks`; `seq` and `div` stay for
  existing files) and the palette page carry the new stops. (#14243)

### Fixed

- **The style guide's palette claims match the plot surfaces.** The contrast sentence now gives the
  WCAG ratios measured on `#FAF8F1` and `#1A1A17`: lavender, cyan, lime and amber below 3:1 on the
  light page, matte red and rose below it on the dark page. The continuous ramps are no longer
  called perceptually uniform in CAM02-UCS, because they are straight sRGB blends between their
  stops, and "identical across themes" now covers the categorical colours only. (#14243)
