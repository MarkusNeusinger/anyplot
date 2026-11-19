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
  stays as it was.
