### Changed

- **The canvas gate checks the dark render too.** "Canvas dimension gate" in
  `impl-review.yml` measured only `plot-light.png`, so a dark render that was
  missing, didn't open, or sat on another canvas passed unseen. It now
  requires both theme renders on a canonical canvas and on the same one. A
  miss writes one VQ-05 defect line per render that missed, tagged `(light)`
  or `(dark)` (`(both)` when the two drifted alike, the line of before), with
  the actual size, the signed delta, and the likely cause, including a size
  set inside a theme branch. A first generation goes to repair, and a
  regeneration is kept as `canvas_failed`. A missing or unreadable dark render
  fails the gate without failing the job. The notice line keeps its fields and
  adds the dark render's after `attempt=`, and `canvas_gate_report.py` reads
  them. On 2026-11-20 no live pair had a light render on the canvas and a dark
  render off it, so no pair that passes today fails the new check.
