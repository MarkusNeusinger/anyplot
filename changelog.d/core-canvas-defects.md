### Added

- **Shared canvas gate in `core/canvas.py`.** The canvas check that
  `impl-review.yml` runs inline (3200×1800 or 2400×2400 within ±16 px, the
  nearer target, the signed delta and the per-library likely cause) is now a
  pure function, `check_canvas`, plus a PNG reader that refuses files without
  the PNG signature and a `python -m core.canvas <png>` CLI that prints the
  workflow's lines and exits non-zero on drift. The module also holds the PNG
  auto-reject checks AR-04 (blank) and AR-07 (format), ported from
  `scripts/evaluate-plot.py`. AR-04 counts the most common color instead of
  that script's near-white and near-black thresholds: the near-white rule
  can never flag a blank render on the light `#FAF8F1` page, and the
  near-black rule flagged 6 of 24 sampled dark catalogue renders, while the
  one-color rule flags none of 48. A parity test runs the workflow's own
  script on the same PNGs and requires identical output, so the workflow can
  switch to the module later without changing a byte of the repair feedback.
  (#12102)
- **Review feedback grammar in `core/defects.py`.** The defect-line and
  suggestion-line grammar, the criterion IDs, `nothing_to_repair` and the spec
  characteristics parser now have a canonical, stdlib-only home that the
  planned agents service can import, plus a `format_defect` builder whose
  lines read back through the same parser. `regen_gate.py` keeps its own copy
  for now, because the workflows run it as a single-file copy where `core` is
  not importable; a parity test checks both copies against the catalogue's
  stored weaknesses and every spec. (#12102)
