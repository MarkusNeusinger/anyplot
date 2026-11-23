### Added

- **One follow-up regeneration after a gated regeneration, behind two
  switches.** When the regen gate replaces a live implementation and the
  new review still names a defect, `impl-merge.yml` can dispatch one more
  regeneration of the pair after the merge (`REGEN_REPAIR_ROUND`). When the
  gate keeps the live implementation for a regression, `impl-review.yml` can
  dispatch one with that regression as a note (`REGEN_RETRY`). The same gate
  judges each follow-up against the file that is live by then, so the winner
  merges exactly as it would have, and an implementation still never gets
  worse. A follow-up is never followed up: the PR body line `**Follow-up
  of:**`, a marker comment on the predecessor and a seven-day check of the
  pair's pull requests bound it, with no label involved, and anything
  unreadable means no dispatch. A kept repair round writes no re-score back. The
  gate record gains `defect_lines`, `follow_up_trigger`, `follow_up_of` and
  `follow_up_kind`, and the weekly collector and `gate-report` pair each
  follow-up with its predecessor. Both switches are off until the owner sets
  them.
