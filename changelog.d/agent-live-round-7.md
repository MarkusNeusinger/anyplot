### Fixed

- **A wide heatmap matrix is offered in long form instead of plotting nonsense.** A paste such as
  `Stunde;Mo;...;So` on a heatmap or grouped box now gets the `.to_long()` offer (row labels kept),
  and no role that wants labels is bound to one of the side-by-side number columns by default; bound
  so by hand, the data panel and the session block warn and point to `.to_long()`. (#12204)
- **A visible defect the review names gets the repair round.** A review that names clipped text
  (AR-09), overlap (VQ-02) or a cut or crammed layout (VQ-05) sends the round to the repair even
  when its points pass the review bar; the ship bar is unchanged. (#12204)
- **Replies no longer claim data changes the plot never made.** A shipped plot result tells the
  assistant `data_changed: false`, and the prompts keep data-change claims to the data tools'
  change lines. (#12204)
- **Months and quarters are dates at the paste.** A column of `2025-01` or `2025-Q1` is read as the
  first day of each month or quarter, with a warning that names the reading. (#12204)
- **The repair-exhaustion comment of `impl-review` no longer shares a fixed `/tmp` path**, which made
  its test race under parallel runs; it is written under `$RUNNER_TEMP`. (#12204)
