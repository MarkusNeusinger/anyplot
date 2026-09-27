### Changed

- **Regenerations only replace a live implementation when they are visibly
  better.** A regeneration (an implementation PR for a pair that already has an
  implementation on main, such as every `daily-regen` pick) now gets one review
  and no repair loop. The review scores the new render blind, re-scores the
  predecessor's production renders against the same criteria, and writes a
  before/after judgement to `review_regen.json`; `automation/scripts/regen_gate.py`
  merges only when the new score is at least the re-scored predecessor minus one,
  at least one improvement is visible, and nothing regressed (a replaced data
  scenario or added encodings on a `*-basic` spec count as regressions).
  Otherwise the PR is closed as `regen:kept` and main, GCS production and the
  database stay untouched. Anything missing fails closed to keep. The
  bubble-basic regen experiment showed why: five rounds kept scores flat at
  89–92 while code grew 35 %, three libraries swapped their data scenario, and
  two moved data marks off their values. `regen_gate=false` on `impl-generate.yml`
  and `bulk-generate.yml` forces the old path (`regen:forced`); `daily-regen`
  now counts kept attempts when picking the oldest spec; the watchdog re-closes
  open `regen:kept` PRs and never rescues a regeneration into repair; a failed
  regeneration no longer marks the pair `impl:<lib>:failed`; and the local
  `/regen` withholds `ai-approved` when the new score falls more than one point
  below the stored one. (#11945)
