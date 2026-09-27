### Added

- **Review provenance in the metadata.** `impl-review.yml` now stores which
  model and which rules produced a review: `review.model` (the resolved model
  ID from the session's execution file, for example `claude-sonnet-5`, not the
  alias that moves between releases), `review.criteria_version` (the git blob
  IDs of `prompts/quality-criteria.md`, `ai-quality-review.md`,
  `default-style-guide.md` and the library prompt, hashed after the prompt
  overlay, so exactly what the reviewer read), and `review.rendered_at` (the
  staging render's creation time). A new standard-library helper,
  `automation/scripts/review_provenance.py`, computes both. A value the run
  can't determine is left out, never filled with the alias, and a repair
  review drops what the previous review wrote for it. The keys aren't synced
  to the database, and every new step is non-gating. (#11950)
- **Regen gate records.** Every regen gate decision now carries a reason code
  (`merge`, `below_tolerance`, `no_visible_improvement`, `regression`,
  `regen_json_invalid`, …) and leaves a one-line JSON record in the PR comment
  as an invisible `<!-- regen-gate-record:v1 {...} -->` marker: scores,
  improvement and regression counts, the code, and the model and rules version
  of both the new review and the stored one. It holds no model-written text.
  The `::notice::regen_gate` line gains `code=`, `model=` and `criteria=`, and
  each regeneration's before/after pair (both renders, both sources, the
  previous review, the review files, the record) is kept as a 60-day
  `regen-pair-<pr>-<attempt>` artifact — the predecessor's production renders
  are overwritten on the next merge, so it is the only copy. Run logs expire;
  PR comments don't, so the gate can now be monitored after the fact. (#11950)

### Changed

- **A replaced implementation now gets a PR comment too.** Until now only a
  kept regeneration explained itself; the merge path posted nothing. The
  replace path now posts the same summary (stored, re-scored and new score,
  improvements, regressions, reason) and the gate record before it dispatches
  the merge. A failed comment only logs a warning and never holds up the merge.
  (#11950)

### Fixed

- **A regeneration no longer shows the review its predecessor's score.** A
  regeneration edits the live file, so its header still read
  `Quality: 92/100` — the stored score, in plain sight of the review that is
  meant to score the new version blind (seen on #11926). `impl-generate.yml`
  now resets it to `Quality: pending` before the PR opens, the state a fresh
  file starts in (`regen_gate.py sanitize-source --pending`); impl-review
  writes the new score afterwards. (#11950)
