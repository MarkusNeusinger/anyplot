### Added

- **Review retest set v2: the regen pairs of verification round 1.**
  `automation/retest/set-v2.yaml` freezes the 12 regenerations the gate
  merged on 2026-09-27 (#11951 to #11963 without #11955), each predecessor at
  `0ccb3fec1` and each new version at `28df16aed`, with the spec pinned at
  `0ccb3fec1`. Set v1 has no pair that a suggestion alone could carry, so it
  can't show whether a gate change stops such merges; set v2 can. The
  workflow's new `set` input (`v1` by default, or `v2`) hands the chosen
  manifest and lock to `plan`, `bundle` and `report`. Its 48 renders are
  frozen under `gs://anyplot-images/retest/sets/v2/`, and its labels stay
  drafts until the owner confirms them. (#11966)
- **Forward merges without a labeled carrier.** Regen items can carry a
  `fixes` label: the predecessor defects the forward new version fixes, on
  carrier criteria only (VQ, SC, DQ, CQ), each with a pattern for the
  improvement's `what` text. The report and the PR snippet show the share of
  forward merges in which no counted visible improvement matches such a
  label or cites an affirmative characteristic of the spec
  (`merges_without_carrier`). It reads only fields every rules version
  writes, so a baseline and a candidate arm mean the same by it. Round 1
  replayed through it gives 6 of 12, the number the P3 gate change is
  measured against. (#11966)

### Changed

- **An off-canvas predecessor may be frozen for a forward-only pair.**
  `impl-review.yml` shows the reviewer the predecessor's render as
  production stores it, and round 1 had two off-canvas ones (4766 × 2670 and
  4800 × 2700). A regen pair marked `orders: forward` now runs in the forward
  order only, and its `prev` render may be off-canvas; every render a
  session reviews still has to be on a canonical canvas, as the production
  canvas gate requires. Regen cells also record the spec's characteristic
  count and permissions (`spec_characteristics`), which the carrier metric
  reads. (#11966)
