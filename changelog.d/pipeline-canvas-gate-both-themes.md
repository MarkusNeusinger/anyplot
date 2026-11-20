### Changed

- **The canvas gate checks the dark render too.** "Canvas dimension gate" in
  `impl-review.yml` measured only `plot-light.png`, so a dark render that
  didn't open or sat on another canvas than the light one passed unseen. A
  missing one never got that far: "Verify both theme renders exist" stops the
  job first, as before. The gate now requires both theme renders on a
  canonical canvas and on the same one. A miss writes one VQ-05 defect line
  per render that missed, tagged `(light)` or `(dark)` (`(both)` when the two
  drifted alike, the line of before). A line for a drift names the actual
  size, the signed delta, and the likely cause, including a size set inside a
  theme branch; when the dark render sits on a canonical canvas, the light
  line aims at that canvas. A first generation goes to repair, and a
  regeneration is kept as `canvas_failed`. A dark render that doesn't open
  fails the gate without failing the job. The notice line keeps its fields and
  adds the light and dark verdicts and the dark render's size after
  `attempt=`, and `canvas_gate_report.py` reads them. The audit skill's local
  render check applies the same one-canvas rule. On 2026-11-20 no live pair
  had a light render on the canvas and a dark render off it, so no pair that
  passes today fails the new check. (#13241)
