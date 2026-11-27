# The sequential ramps turn in hue from end to end and keep their low end visible on a dark map

- Date: 2026-11-27
- Proposed: the blind check of the regeneration batch of 2026-11-26 found heatmaps and maps whose
  neighbouring levels read as one colour (blue to navy over the upper part of the light ramps, deep
  green to brand green in the dark ones) and thin low-value lines on dark maps that sank into the
  land. New stops were built and shown on the palette page and on comparison sheets with simulated
  colour-vision deficiencies: on the light page brand green → deep blue `#024582` → dark violet
  `#351E45`, on the dark page olive (`#404C02` for fields, `#6F7E20` for marks) → brand green →
  pale blue, plus a style guide rule that ramp colours are opaque and map lines and points take the
  marks ramp. Three other light and two other dark variants were on the sheets.
- Decided: he picked "Farbrampen nachbessern" from the batch check on 2026-11-26 and, after looking
  at the page and the sheets on 2026-11-27, took the stops as built for both themes. The 38 live
  implementations that carry the old stops are regenerated afterwards.
- Where: #14724
