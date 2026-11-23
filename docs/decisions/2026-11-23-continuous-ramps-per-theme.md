# The continuous colour ramps get their own stops per theme, for fields and for marks

- Date: 2026-11-23
- Proposed: `imprint_seq` was one ramp for both themes, brand green to blue, so close in lightness
  that high and low values barely separated in heatmaps. Five candidates were rendered on four
  catalogue plots in both themes: the ramp as it was, the same ramp widened, two per-theme ramps in
  the brand hues, and viridis. Two smaller cards went with it: the midpoint of `imprint_div` where
  coloured marks sit on the page, and the style guide's contrast sentence, whose numbers came from
  other surfaces.
- Decided: for filled fields (heatmaps, spectrograms, filled contours, maps, tiles) a per-theme ramp
  with a wide lightness range, pale mint to navy on the light page and deep green to pale blue on
  the dark one; for lines and markers a per-theme ramp whose every colour keeps 3:1 against its
  page. In both themes high values stand out from the page and low values recede into it. He chose
  the stops from the renders. For marks, `imprint_div` takes the `muted` anchor as its midpoint, the
  rule ordered categories already follow. The categorical hues stay as they are, and the contrast
  sentence now carries numbers measured on the two plot surfaces, which say that matte red and rose
  stay below 3:1 on the dark page.
- Where: `core/palette.py`, `prompts/default-style-guide.md`
