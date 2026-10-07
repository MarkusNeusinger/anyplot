# Lessons for the weekly regen review

These are the durable lessons from the scoring and regen-gate work of
September and October 2026 (P3 to P10). Read them before you judge a
week of regenerations: most of what looks odd in the numbers is
expected, and a few things that look fine are not. The mechanisms are
documented in `docs/workflows/overview.md` (regen gate, write-back)
and `docs/workflows/review-retest.md` (retest, gate-report,
first-reviews); this file says what they mean in practice.

## The gate

- **Only a verified defect carries a merge.** A regeneration replaces
  the live implementation when it fixes a visual, spec, data or code
  defect that scores higher in the new review than in the re-score of
  the predecessor, or an `A good version shows:` property, and the
  review names the kind `fix` or `removal`. Nothing else carries:
  suggestions, design (DE) and library-mastery (LM) points, feature
  coverage (DQ-01), additions, polish, items without a kind, and
  weaknesses the re-score classed obsolete.
- **Keep is the default.** Anything missing or malformed keeps the
  live implementation. A kept regen is a normal outcome, and its
  write-back still replaces the stored review with the Opus re-score,
  so the next regeneration starts from current problems.
- **The code path is narrow.** With no visual carrier, a regen still
  merges when it fixes a `CQ-04 (code): … → \`call\`` defect from the
  previous review, calls that function more often, is shorter, and
  keeps the data scenario and encodings. Production verification:
  acf-pacf plotly and seaborn (#12011, #12012), carriers 0, code 1,
  renders unchanged.
- **The score rule is relative.** New must be at least the re-scored
  predecessor minus 1. There is no absolute floor on regen merges
  (owner decision, 2026-09-30): bubble-basic/ggplot2 merged at 76
  because its predecessor re-scored at 71.
- **`P` carriers deserve a read.** A `P` item is a predecessor defect
  the re-score found itself. In round 2 (2026-09-30) 7 of 10 merges
  carried only on `P` items, all genuine `-basic` scope-creep
  removals. The risk is a review that classifies to justify the new
  render; the set v2 labels are the standing check on it.

## Regression or defect

A review can describe something that got worse as a defect of the new
render instead of a regression. The gate then sees no regression and
merges. In the P10 C1 arm the gate met its target at 40 of 42; the
pair the baseline got right and the candidate missed was d3's hollow
legend rings, written as a defect of the new render instead of a
regression. When you read a merge's renders, ask
for every defect line of the new review whether the predecessor had
the same problem. If it didn't, it is a regression the gate missed.

## Scores and the review model

- **Every review runs on Opus since P9 (2026-09-28).** On identical
  renders Opus scores about 8 points below Sonnet. Against stored
  Sonnet-era scores Opus landed −13 on the set v1 retest and −9.4 on
  the round-2 production re-scores (median −10, SD 6.2). That drop is
  the model, not the plot. Never compare or rank scores across review
  models; `review.model` is in the metadata but not in Postgres.
- **90 and above must be rare and earned** (owner, 2026-09-28). Never
  propose lowering a line or relaxing a rule to restore an old pass
  or merge rate. Justify a threshold by what the score should mean.
- **Why first reviews piled up at 90.** The modal review was "every
  technical item at its maximum, design called good", which adds up
  to exactly 90: the bar sat where "no defect found" lands. Between
  15 libraries of one spec the spread was smaller than one reviewer's
  run-to-run noise (SD 1.6 against 2.0), and three libraries got the
  identical 24-item vector.
- **What P10 changed (#12045 on 2026-10-02, #12046 on 2026-10-04):**
  - *No silent deductions:* every technical point below its maximum
    needs a defect line naming the criterion, so a repair has
    something to fix. The run log prints `weakness_format … silent=N`.
  - *Compliance is not excellence:* DE and LM rise above their
    defaults only for evidence beyond the spec's Notes, its
    characteristic section and the style guide. Removed spines and a
    subtle grid earn the default, nothing more. A compliant plot that
    adds nothing lands near 82.
  - *Blind reviews:* the reviewer doesn't see the threshold, the
    stored score, or an earlier review; the workflow, not the
    reviewer, owns the verdict. Only the working-tree copies are
    hidden: branch history, `gh` and earlier PR comments stay
    reachable and only the prompt forbids them, so a leak would come
    from there.
  - *Check values:* a domain spec states one to three numbers a
    correct implementation reproduces (Notes bullet starting with
    `Check values:`). The reviewer checks them in the render and in
    the code. Without them, physics went unchecked: tanabe matplotlib
    had a swapped matrix diagonal and scored 90 with data quality
    15/15. With them, its regen (#12052) reproduced 34.92 against 34.9.
- **Second reviews used to gain on judgment items** that no repair
  touched (14 of 18 points across eight tanabe repairs, one of them
  with no repair commit at all). `first-reviews` reports this split;
  a return of that pattern means the blind review leaks.
- **Identical scores across libraries are a red flag.** Two libraries
  of one spec with the same category vector, or totals within two
  points on visibly different renders, mean anchoring. Read the two
  reviews side by side.

## Specs

- **Notes and Data win.** A characteristic bullet may never be
  stricter than, or contradict, the spec's Notes or Data section. A
  fix that lands only in the appended section while a Notes line says
  the opposite is wrong; change both or neither.
- **`-basic` means basic.** The scope bullets of a `-basic` spec are
  complete: mean lines, trend lines, callouts, highlight rings and
  extra encodings are scope creep. Expect a wave of merges that
  remove creep after the backfill; it should taper off.
- **A spec that wants its distinctive feature shown must say so.**
  The tanabe Data example pointed at a configuration without the
  crossover, so 13 of 15 libraries drew none. Steering the example
  (#12042) fixed it.
- **Research domain conventions before writing domain specs**
  (Tanabe–Sugano, Smith chart, skew-T, Kaplan–Meier): standards and
  textbooks first, sources cited, and research never overrides a
  Notes line.
- **Political plots use invented parties and data.** No real party,
  parliament, country or election; colors that don't mimic real
  parties. DQ-02 targets real politics only, so a clearly fictional
  parliament scores normally (parliament-basic/pygal, #12053).

## Implementations

- **Each library is an independent interpretation.** A regen reads
  its own predecessor, the spec and its library prompt, never another
  library's code or review. Different data scenarios are fine.
- **Similarity change requests are terse.** For an identical pair,
  flag only one library, in one sentence, naming what is identical
  and a direction; no interactive or library-feature pitches.

## Working habits

- **Read keyword hits by hand.** Counts by grep over renders or
  reviews were wrong in both directions during the spec-polish check
  (a comment said "Okabe-Ito orange" for a red). The retest's carrier
  metric matches words too: read the runs it flags before acting.
- **Use background watchers for anything that waits.** Agents that
  promised to check back went silent for hours while two items sat
  stuck (round 2). Run the wait as a background command that exits on
  the condition, and post status every ~10 minutes.
- **Recoveries the watchdog doesn't do.** A regen PR at
  `ai-review-failed` is only flagged; a `Merge: PR #N` run that fails
  after "Merge PR to main" leaves images in staging. The recipes are
  in the `babysit-pipeline` skill; each re-run needs the owner's go.
