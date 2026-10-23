### Added

- **The adaptable-code convention in all 15 library prompts.** A new
  implementation keeps one replaceable `# Data` block that ends in a tidy
  DataFrame `df` (or a `tibble`, a Julia `DataFrame`, or JavaScript records),
  names each spec role once as a column constant with a `# role:` comment, lists
  all eight Imprint hues and uses the first `n`, and derives labels, callout
  targets, and limits from the data below the block. People who copy the code
  and the "Use with my data" agent replace the block and the constants, and
  nothing below them. Regenerations of R, Julia, and JavaScript pairs keep
  their regeneration rules, because only Python has a checker so far.
- **A Python self-check before every generation commits (Step 3c).**
  `python -m core.smoke_run selfcheck` runs the static adaptability check and
  the perturbation smoke run on the new file, up to three attempts. It never
  blocks the commit, and the commit body records the result, so a first
  generation that still fails merges and converts on its next regeneration.
- **A record-only smoke run and a predecessor render in `impl-generate.yml`.**
  The step "Adaptability smoke run (record-only)" runs the smoke run on the
  generated file and, on a regeneration, on the predecessor too. It renders both
  sources in the same runner and stages the results and the raw renders under a
  private `adapt/` prefix in GCS staging, which `impl-merge.yml` never promotes.
  `impl-repair.yml` reruns the smoke run after every repair. Identity is measured
  on the raw renders, before the PNGs are quantized.
- **A record-only adaptability step in `impl-review.yml`.** The step
  "Adaptability check (record-only)" runs the checker mirror on both sources
  and reads the staged smoke results. It writes one record per source and an
  `adapt_check` notice per side, and it never fails the run. The reviewer never
  sees it, and the review prompt and the rubric are unchanged.
- **The adapt route and the adapt regression in the regen gate.** A
  regeneration that converts a Python implementation to the convention now
  merges on render identity, without a visible improvement, when all of these
  hold: the predecessor fails the check and the new source passes it, the two
  renders differ in at most 0.5 % of their pixels in both themes at equal size,
  the new source stays within max(1.25 × prev, prev + 15) lines, and the review
  keeps every technical item at or above its re-score. The reason code is
  `adapt_identity`, and the gate record gains an `adapt` block. A conversion
  that breaks the check (the predecessor passes, the new source fails) is kept
  as `adapt_regression`, on every spec, so converted code stays converted.
  `regen_gate.py adapt-route` evaluates the route before the review. The
  repository variable `ADAPT_REVIEW_FREE` lets identical conversions merge
  without a review. It is off until the owner turns it on, and the label
  `regen:adapt` counts these merges.

### Changed

- **`impl-review.yml` runs on the pinned Python.** A setup step reads
  `.python-version` before the first regen tool runs, because the regen gate,
  the provenance script, and the checker mirror use PEP 758 `except A, B:`
  since the move to Python 3.14, and the runner image's own Python is not
  pinned. `impl-merge.yml` now promotes only the `plot-*` files from staging,
  so the private `adapt/` artifacts never reach production.
