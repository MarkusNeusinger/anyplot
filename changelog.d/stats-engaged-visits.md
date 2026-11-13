### Changed

- **The visitors tile draws the visits with a second page or an
  interaction.** Its bars were Plausible's unique visitors, and on 2026-11-13
  a crawler farm made up 488 of the day's 598. A farm loads one page per
  visit, so the bars now show the visits Plausible doesn't count as bounced
  (61 to 80 a day from 2026-11-10 to 2026-11-13), and the number of all
  visits of the same days stands under the strip, with a hint on the word
  "all" that says what else is in it. `GET /insights/visitors` gives each day
  its `visits` and `engaged` visits. The count starts on 2026-11-10: before
  it, web-vitals events kept every visit from bouncing, so those days draw
  the floor and are named "not counted", and the header says "since
  2026-11-10" until the 28-day window has moved past them.

### Added

- **Zooming into a plot counts as a use (`ui_feature`, `plot_zoom`).** The
  zoom opens no page and sent nothing, so a visitor who landed on a plot,
  looked closer, and left counted as one who did nothing.
