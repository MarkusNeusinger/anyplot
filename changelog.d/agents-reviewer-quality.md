### Changed

- **The agent pipeline reviews a repaired render once more.** After a
  rejected first review, the render that the repair produced used to ship
  unreviewed (stage `not_rereviewed`, 39 of 244 runs in the rerun of spike X),
  so a repaired run could never end `ok`. The pipeline now makes up to two
  reviewer calls (`MAX_REVIEWS`), and the second verdict decides the shipped
  render; the `pipeline_result` line counts the calls as `reviews`. (#12122)
- **Output caps with ample headroom above the measured answers.** On Claude
  Haiku 5.5 the adapter's edit-only call may now write 8,192 tokens (23 of 244
  first calls were cut off at 2,048), a full-file repair 16,384, the reviewer
  and the root 4,096, and the judges 256. Gemini keeps 8,192 and 12,288 for
  the adapter, which its soft-deadline arithmetic bounds. An answer that
  finishes costs the same under any cap, and a Claude call that uses its whole
  cap still fits the time the deadline check reserves for it. (#12122)
- **The agent token budgets count cost-weighted tokens.** The request,
  user-day and global-day budgets weigh each token by its list price relative
  to an uncached input token (cache read 0.1, cache write 1.25, output 5;
  `BUDGET_WEIGHTS`), the judges included. With a warm prompt cache the median
  run books about 37,000 instead of 70,000 tokens. A cold cache weighs more
  (a reviewed run books about 78,000), so the request budget rises from
  80,000 to 160,000, about 36 % above the costliest reviewed run simulated
  cold with a second review (about 115,000, or 117,300 with three attempts),
  and the user-day and global-day budgets double to 2,000,000 and 6,000,000:
  about 26 cold runs per user, so the 40-run cap binds first. A review starts
  only while 35,000 are left for it and the root's closing reply, so a tight
  budget skips the review instead of answering a shipped plot with the
  usage-limit refusal. The `done` event keeps the plain count. (#12122)
- **The Claude eval baseline is the spike-X rerun on main.**
  `agents/evals/baselines/claude-haiku-5-5.json` now holds the 244 runs of the
  evening of 2026-10-10 (report schema 2, the drawn-text G3 probe, 90.6 %
  passed the gates, 23.4 % ended `ok`) instead of the first spike-X run. Of
  the 50 G3 lines it still reports, the 48 on heatmap-basic seaborn and
  matplotlib and scatter-basic seaborn are real clips that the catalogue
  originals already carry; the 2 on adapted renders were not examined.
  (#12122)

### Fixed

- **Reviewer and adapter answers that miss only a formal rule are mended.**
  The rerun of spike X could not read 44 of 218 reviewer answers, none of them
  cut off. `schema_guard` now clips over-long texts, keeps the first five
  defects and derives `ok` from them, drops defects whose id is outside the
  checklist (a pass that names only such ids stays a pass, a rejection that
  names only such ids stays unread), and mends change notes and a blank
  `full_code` in adapter plans, then validates the result against the same
  strict schema; the edit contract is never repaired. Each failed answer writes a content-free `answer_schema` line with
  the broken rules, which the eval report counts. (#12122)
- **The agent reviewer judges sizes and colors by the style guide's own
  table.** It called the prescribed sizes (axis titles 10 pt, ticks 8 pt at
  dpi 400) too small in 50 of 56 VQ-01 lines and flagged Imprint colors by
  their look in the render, so repairs enlarged fonts against the house style.
  `reviewer.md` now quotes the table, judges colors from the code, lists what
  is never a defect, and treats a gate note as a measurement to confirm.
  (#12122)
