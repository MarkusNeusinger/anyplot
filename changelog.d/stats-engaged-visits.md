### Changed

- **The visitors tile will draw the visits with a second page or an
  interaction, from 2026-12-07.** Its bars are Plausible's unique visitors,
  and on 2026-11-13 a crawler farm made up 488 of the day's 598. A farm
  loads one page per visit, so the bars will show the visits Plausible
  doesn't count as bounced (61 to 80 a day from 2026-11-10 to 2026-11-13),
  with the number of all visits of the same days under the strip and a hint
  on the word "all" that says what else is in it. That count starts on
  2026-11-10: before it, web-vitals events kept every visit from bouncing.
  The owner didn't want a strip that is empty for most of its days, so the
  tile keeps drawing the unique visitors until every day of the 28-day
  window is counted, and switches by itself on 2026-12-07. `GET
  /insights/visitors` gives each day its `visits` and `engaged` visits from
  now on. (#13088)

### Added

- **Zooming into a plot counts as a use (`ui_feature`, `plot_zoom`).** The
  zoom opens no page and sent nothing, so a visitor who landed on a plot,
  looked closer, and left counted as one who did nothing. (#13088)
