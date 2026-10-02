### Added

- **Review retest set v3: the 15 first generations of
  `line-tanabe-sugano`.** `automation/retest/set-v3.yaml` freezes the first
  spec whose first generations were all reviewed on Opus (#12019 to #12038),
  pinned at `cda962dc3` with the spec text their live reviews saw
  (`ec0619261`). Their live scores sat at 85 to 91, with less spread between
  the libraries than one reviewer shows between two runs, so the set probes
  what sets v1 and v2 can't: how a first review behaves where one point
  decides the verdict. Its 30 renders are frozen under
  `gs://anyplot-images/retest/sets/v3/`, the workflow's `set` input takes
  `v3`, and its labels stay drafts until the owner confirms them. A label may
  carry `spec_source: rules_ref`, which limits it to runs whose reviewer saw
  the spec text at `rules_ref`: a defect that only a later spec clause makes
  one doesn't count against an arm on the pinned text.
- **Silent deductions in the retest report.** A technical item (VQ, SC, DQ,
  or CQ) that a review scores below its maximum without a defect line that
  names it leaves a repair nothing to act on. The report and the pull request
  snippet now show the share of such items and the share of runs with at
  least one. It reads only the records' checklist and weaknesses, so a
  rebuilt report of an older arm shows it too: 52 of 266 and 45 of 261 on the
  two arms of the lean-code change.
- **A live report on first reviews.** `review_retest.py first-reviews --since
  <date>` reads the review comments of every first-generation pull request
  since a date, read-only and free: the attempt-1 histogram and the share at
  90 or 91, the spread between the libraries of a spec, the criteria no
  library differs on, silent deductions, and per repair the gain on technical
  against judgment items and whether the repair committed anything. The
  retest measures the reviewer on a frozen set; this shows what it did in
  production, batch after batch.
