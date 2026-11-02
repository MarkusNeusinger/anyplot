### Added

- **Per-day agent numbers on `/debug`.** The usage card gains a table of the last
  14 UTC days, newest first: new chats, plots shipped, cost in dollars (the `cost`
  view's logic, the admin fan-out's beside it), limit hits by code and the 95th
  percentile of the run queue's wait, `—` on a day before the field. A new
  `GET /debug/agent-usage/daily` reads it from the telemetry under the card's own
  discipline: filtered on `timestamp` before it deduplicates, kept for ten minutes,
  aggregates only.
- **A live line for today on `/debug`.** `GET /debug/agent/budget` shows the service's
  spend against its day budget and how many users are at their own limits, counts
  only, from the agents service's memory. The line says since when it counts, because
  a redeploy or a scale-to-zero starts the counts again.

### Changed

- **A spent service budget has its own refusal.** When the service's day budget is
  spent, not the user's own, the chat now answers `service_paused` in every language,
  a paste or a file conversion `429 service_paused`, instead of the text for a user's
  own limit. It names the reset at 00:00 UTC, the page adds that time in the user's
  own time zone, and `GET /v1/status` answers `paused` and `resets_at`, so the chat
  shows the note before the user types.
