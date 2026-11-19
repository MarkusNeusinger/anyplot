# The visitors tile counts a visitor who stayed ten seconds and did something, in either order

- Date: 2026-11-19
- Proposed: after a week of measuring `stayed_10s`, what the visitors tile on `/stats` counts. Any
  visit of ten seconds; ten seconds with an action within them; or ten seconds with an action or an
  interaction such as copying code within them. And whether the tile counts visits or unique
  visitors.
- Decided: a visitor counts when they were on the site for ten seconds and did something (a pointer
  move, a click, the wheel, a finger, or a key), no matter whether the action came before or after
  the ten seconds. His reason was his own example: someone opens the page, fetches a coffee, then
  clicks around, and counts. There is no exception below ten seconds: copying code in five seconds
  and leaving does not count. The tile counts unique visitors per day, from 2026-11-15, the first
  full day of the event, so it switches on 2026-12-12 instead of 2026-12-07; he accepted that the
  days before the deploy know no action after the ten seconds. Plausible's own bounce rule stays as
  it is.
- Where: `docs/reference/plausible.md`
