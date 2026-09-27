### Added

- **CI checks every spec's "What a good version looks like" section.** The
  required "Run Tests" job now runs `automation/scripts/spec_characteristics_lint.py`
  on every PR and push, even when no Python changed: `contract` checks every
  spec against the shape the regen gate parses (exact heading, last section,
  column-0 `- ` bullets with a kind prefix, 2-8 of them, no duplicates) and
  blocks the merge; `style` warns about house style in the changed specs
  (3-6 one-line bullets, no thresholds, generic ideals or library names, the
  `-basic` variant bullet, possible contradictions with Notes). Before, a
  spec-only PR skipped pytest, so a section the gate would misread could merge
  unchecked. spec-create runs both checks before it commits, and `--strict`
  makes the style rules blocking for the planned backfill.

### Changed

- **Each characteristic bullet states its kind.** Every bullet now opens with
  `A good version shows:` (an affirmative property; missing it deducts, and
  only these can be cited as an improvement) or `Expected, not a defect:`
  (a permission; never penalized, never a target), one kind per bullet. The
  template and both spec-create prompts ask for 3-6 bullets with at least one
  of each, and the eight hand-seeded specs are split accordingly
  (heatmap-basic gains its missing basic-variant bullet). The regen gate no
  longer counts an improvement that cites a permission, and the review and
  generation prompts follow suit: a permission is never a weakness, never a
  DQ-01 aspect and never shaped into the data. The review also scores a
  related but different form (a donut for a pie) as a partial SC-01 on any
  spec, deducts spline overshoot under SC-03, and names missed Notes or
  `A good version shows:` bullets under SC-02.

### Fixed

- **The regen gate reads wrapped characteristic bullets whole.** An indented
  continuation line was dropped, so the gate cited a truncated bullet; it is
  now joined to the bullet above it. The regeneration comparison in the review
  prompt also exempts what SC-03 exempts (categorical jitter, layout-positioned
  types, offsets the spec asks for) from its "marks moved" regression, and no
  longer counts an element the spec requires as an added encoding.
