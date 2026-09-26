### Changed

- **The scheduled regen runs once a day instead of ten times.** `daily-regen.yml`
  now ticks at 02:17 UTC only (it ticked every 2 hours outside the 18–21 UTC quiet
  window), so it regenerates one spec per night and leaves the Claude rate limit
  to interactive work during the day. The workflow had been paused since
  2026-08-18 for the gap backfill and is re-enabled with this cadence. The
  watchdog's cron-liveness rescue moves from >10 h to >26 h of silence: at 10 h
  it would have re-dispatched a second run every day, while 26 h first fires at
  the 06:00 UTC scan after a dropped night tick, which replaces the missed run
  rather than adding one. The rescue's clock also starts at the workflow's
  last enable instead of only its newest run, so re-enabling after a pause no
  longer reads the weeks of deliberate silence as starvation and dispatches a
  run hours before the first scheduled tick. (#11848)
