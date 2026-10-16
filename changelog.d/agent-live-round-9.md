### Fixed

- **A plot request made before the confirmation reaches the first plot.** A title asked for before
  `.confirm()` now goes through `plot_pipeline`, which keeps it for the next `.create_plot()`, and
  the result says `request_kept`, so the assistant only says a request is kept when the server
  kept it.
- **The progress grid shows the repair round.** Rounds are named `first try`, `second try`, and a
  running repair round says what it repairs in words (`repairing text size, layout`, from the
  rubric ids the round before passed on). The result card names the round that shipped when an
  earlier one won (`first try shipped of 2`).
- **Review fixes for `.to_long()` and the readiness scan.** `.to_long()` keeps the user's bindings
  on the columns it keeps; weekday headers must all come from one language (Portuguese and Dutch
  names added, and two-letter codes such as `FR, SA, SO` need five distinct days); a line with
  several color-scale literals names all of them once; `center` counts only on seaborn's heatmap
  and clustermap and `levels` only on contours; and the dataset judge reads at most five full
  values per 40-character display copy and 8,000 characters per column.

### Changed

- **`.to_long()` names its new columns in the session language.** German sessions get `Wochentag`
  and `Wert` instead of `Weekday` and `Value` (French, Spanish, Italian, Portuguese, Dutch and
  Polish too; English otherwise). The language route and every turn's `done` return the
  recomputed offer, so the data panel's card always names what `.to_long()` applies.
- **A session is kept only when the user took a result away and was content.** The `sessions` view
  and the `/debug` card count a copy or a download after the last run without a `thumbs_down` or
  `bug` feedback; a saved session alone is no keep (new states `rejected` and `saved`). The card
  shows the counts behind the kept and repair rates (`5 of 12`).
