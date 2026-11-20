### Changed

- **The visitors tile will count the visitors who stayed ten seconds and did
  something, from 2026-12-12.** This replaces the visits with a second page
  or an interaction that it was to draw from 2026-12-07. A visitor counts
  when they had the site in front of them for ten seconds of a visit and used
  a pointer, a finger, or a key in it, before the ten seconds or after them:
  someone who opens a page, fetches a coffee, and then clicks around counts;
  someone who copies code in five seconds and leaves doesn't. `stayed_10s`
  now goes out once more, with `input` `yes`, at the first input after ten
  seconds without one, and `GET /insights/visitors` counts the unique
  visitors with `input=yes` per day from 2026-11-15, the event's first full
  day, in a second Plausible query. On 2026-11-15 to 2026-11-19 the
  crawler-farm pattern stayed ten seconds in 14 of 679 visits, all without
  input; Google visitors stayed in 181 of 256, 176 of them with input. The
  line under the strip shows all unique visitors, and Plausible's bounce rate
  stays as it was. A click or a mousedown counts as input, for screen
  readers and voice control that send no pointer events, and a pointer move
  only once the pointer has travelled 4 px. The clock checks that the page is
  still in front of the visitor before the ten seconds count, and an input
  brings it up to date. The query filters by the event's name instead of
  its goal, so renaming the goal can't break the tile, and its days are the
  Plausible site's (Europe/Zurich) instead of UTC days, so the last bar is
  today also just after midnight. `docs/reference/plausible.md` names the
  early warnings with their baselines and the readers the rule misses.
