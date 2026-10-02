### Added

- **Check values.** A spec's Notes may carry a `Check values:` bullet: one
  to three numbers a correct implementation reproduces from its own
  computation. The review verifies each one that applies in the render and
  in the data code, where it must fall out of the computation; a missed
  value is a DQ-03 defect with the expected value, the observed value and
  the delta. Without check values a reviewer can't tell a wrong matrix from
  a right one: a swapped diagonal in `line-tanabe-sugano` scored DQ-03 at
  4 of 4. The spec template names the bullet.

### Changed

- **A deduction names its defect.** The 15 first reviews of
  `line-tanabe-sugano` deducted 27 technical items and wrote a defect line for
  20 of them; the same gap was a lost point on one library and a
  `Suggestion:` on another. The 19 technical criteria (VQ, SC, DQ, CQ) now
  start at their maximum, and every point below it is carried by a defect
  line; the five judgment criteria (DE, LM) start at their default and rise
  on named evidence. The review lists defects first, then scores, then adds
  up: it never picks a total, and the "median 72-78" anchor describes where
  written-down defects land a typical plot instead of naming a target.
  `regen_gate.py check-feedback` reports a technical item below its maximum
  that no defect line names, and the workflow's format notice counts them
  (`silent=N`).
- **The same gap costs the same criterion on every library.** Each library
  of a spec is reviewed without seeing the others, so `quality-criteria.md`
  gains a routing table ("Which criterion a gap belongs to"): a missed Notes
  bullet is SC-02 when the fix is in the plotting code and DQ-01 when it is
  in the data, a departure from a Data range, an example or a stated
  preference costs nothing unless the Notes require it, a conditional
  requirement whose condition the data doesn't meet costs nothing, and a
  wrong domain value is DQ-03. It routes; it sets no threshold.
- **The reviewer scores without the approval bar in view.** The cascade
  (90, 80, 70, 60, 50), what follows from a score, and the expected score
  distribution left `quality-criteria.md`, `ai-quality-review.md`, and
  `quality-evaluator.md`; they stay documented for people in
  `docs/workflows/overview.md`. The reviewer writes no verdict any more (the
  `### Verdict` line, `review_verdict.txt`, and `review_prev.json`'s
  `verdict` are gone; the workflow sets it), and is told not to open earlier
  reviews of the pull request.
- **Compliance is not excellence.** A first review used to credit what the
  spec or the style guide already requires as design excellence: "spines
  removed, grid at 15%" raised DE-02 on 15 of 15 reviews. Evidence that
  raises a DE or LM item is now something beyond what the spec's Notes and
  the style guide require, and the DE-01 and DE-02 ladders no longer name the
  style-guide baseline or a forbidden custom palette. The complete baseline
  earns exactly the defaults (DE-01 = 4, DE-02 = 2), so the 75 cap can't fire
  on a compliant implementation. Scores move down by this change; a score
  under these rules isn't comparable with one stored before them.
- **CQ-04's hand-roll list is marked as examples.** The score row read as a
  whitelist ("a KDE, binning, quantiles, ACF/PACF, a fit, a linkage"), and
  "a fit" still named the closed-form slope and intercept the scoring notes
  exempt. The row now says the examples aren't a list to match against and
  narrows the fit to one that takes an iteration or a matrix solve.
