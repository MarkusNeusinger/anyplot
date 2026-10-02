### Changed

- **A later review starts blind.** After a repair, the pull request branch
  carries the previous review in two places: the `Quality: N/100` header and
  the metadata file with the score and the whole review. The second review of
  an unchanged file scored four points higher than the first (#12028), all of
  them on design and library items. `impl-review.yml` now resets the header to
  `Quality: pending` and moves the metadata file out of the workspace while
  the reviewer runs at attempt 2 or later, and puts both back before it stores
  the new review. A regeneration's re-score already hid its predecessor's
  review this way.
- **The workflow owns the stored verdict.** `review.verdict` used to be what
  the reviewer wrote in `review_verdict.txt`, which needed the approval bar in
  the reviewer's prompt and was wrong at times (`APPROVED` on a review the
  workflow sent to repair). The metadata step now stores what the workflow
  decided, and a kept regeneration's write-back stores `APPROVED`, because
  the kept implementation stays live; `review_prev.json` no longer needs a
  `verdict`.
- **A review with nothing to repair is approved as it stands.** A first
  review below 90 used to go to repair even when it named no defect. A
  repair fixes defect lines, so that cycle bought only a second, noisier
  score. A review at 80 or more whose every technical criterion (VQ, SC, DQ,
  CQ) is at its maximum is now approved, with a comment that says why. The
  workflow reads the condition from the review's checklist, not from the
  absence of defect lines, so a deduction without a defect line still gets
  its repair.
