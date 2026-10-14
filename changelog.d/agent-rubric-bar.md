### Changed

- **The agent's adapter works to the reviewer's rubric, and fewer plots go to a repair.** The adapter's
  instruction now holds the very rubric sections the reviewer scores with (scoring principles, anchors,
  the 5c and 5d checks) instead of thirteen one-line criteria rows, so the first try knows what will be
  judged. A render needs 95 % of the technical points instead of all of them to skip the repair round
  (`AGENT_REVIEW_BAR`, owner decision pending), measured gate findings such as clipped or overlapping
  text go to the self-review and the review before they start a repair (`AGENT_GATE_REPAIR`), and a
  repair round is no longer proofread before its review (`AGENT_REPAIR_SELF_REVIEW`).
- **The G9 plotted-points limit is 500,000.** Dense user data such as 20,000 rows of 24 series no
  longer draws a DQ-03 note; the stress cases' 610,000 and 1,000,000 computed points still do.

### Fixed

- **`ok` no longer hides a measured defect.** A shipped plot keeps every advisory gate line (clipping,
  overlapping text, annotations outside their axes) in its notes whatever its review score; until now
  only a missing glyph stayed above the ship bar. An optional review-score condition for `ok`
  (`AGENT_STATUS_SCORE`, off by default) waits for the owner's decision.
