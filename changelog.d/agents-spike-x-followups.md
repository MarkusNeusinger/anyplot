### Changed

- **The eval run record says where each run stopped.** Report schema 2 of
  `agents/evals/matrix.py` records the stage that ended each attempt and the
  run (`adapter_truncated`, `edit_apply`, `validator`, `gates`,
  `reviewer_defects` and so on) instead of the bare `failed (validation)`, the
  shipped and the reviewed attempt, an attempt log with the adapter's outcome,
  finish reason, output tokens and plan shape, every model call's finish
  reason and tokens, and the edit-failure kinds (`zero_match`, `multi_match`,
  `protected:*`, `drift:*`). All of it is content-free, read from the
  pipeline's attribution lines. A schema-1 baseline still loads and diffs.
  An unparseable file now counts as one `syntax` rejection instead of two, so
  `validator_rejections.syntax` reads lower than in older reports. (#12118)
- **More than eight groups have a palette rule.** The adapter keeps the Imprint
  palette one literal list and, past eight groups, draws all but the seven
  largest in the theme's muted ink as one "Other" group, which the reviewer
  accepts under VQ-07. The style guide's small-multiples advice contradicted
  the adapter's "keep the plot" rule. (#12118)

### Fixed

- **The Gemini adapter's first answer is no longer cut off.** Gemini counts
  thinking tokens toward the output cap, and the 2,048-token edit cap ended
  every first adapter call of the spike-X Gemini arm with `MAX_TOKENS`, so no
  run had a repair round. The Gemini edit cap is now 8,192 tokens, which holds
  101 of the run's 112 plans and still lets a first answer cut off at the cap
  leave the repair its time, and the full-file repair runs at 12,288 tokens
  with LOW thinking. Claude stays at 2,048 tokens with thinking disabled. The
  repair also no longer reserves the whole 60 s render timeout, so the first
  attempt keeps 65 s of the 140 s soft deadline instead of 35 s. (#12118)
- **A cut-off adapter answer gets its own repair line.** The repair now hears
  that the previous answer ran out of output tokens instead of a generic
  schema miss, and a cut-off answer is never used as a plan, even when a
  truncated Claude tool input still validates. The schema-miss and
  refused-full-file lines no longer tell the repair to send edits when it may
  send a full file. (#12118)
- **The palette repair target matches the palette rule.** Every soft
  ADAPTATION finding asked the repair to "derive it from df and the Imprint
  palette", while the validator wants a literal list; that finding decided 10
  of Claude Haiku 5.5's 20 non-passes in spike X. Each rule now has its own
  target. (#12118)
- **The G3 probe gate measures only drawn text.** The render probe counted
  tick labels that matplotlib never draws (the locator's edge ticks outside
  the view, labels of hidden axes), so G3 (text beyond the canvas) fired on
  every line plot of spike X and spent the repair before the review. It now
  measures the texts its own draw renders, for G3 and the tick-overlap gate
  G7. Remote renders pick it up when the renderer image is rebuilt. (#12118)
