### Added

- **An admin lane in the agents service's run queue.** The admin's runs,
  `.plot_all()` above all, may hold five places per admin (public users two),
  with no per-user day caps or message minute (owner decisions of
  2026-11-01). The BFF asserts the tier with `X-Anyplot-Tier: admin` from the
  identity its admin gate verified; a missing or other value is the public
  tier, so the two services deploy in either order. `GET /status` reports the
  caller's own cap, and the fan-out panel follows it (#12507).
- **Anonymous limit telemetry on `pipeline_run`.** `lane`, `queue_wait_ms`,
  `queue_position`, `user_runs_today` and `user_tokens_today` show whether
  anyone waits long or comes close to a limit, as closed sets and bounded
  numbers with no user id and no hash; the views SQL reads them, and applying
  it in BigQuery waits for the owner after the merge (#12507).

### Changed

- **The run queue runs five plots at once and starts one every 10 seconds.**
  `AGENT_RUN_CONCURRENCY` 5 for the whole instance and `AGENT_RUNS_PER_MINUTE`
  6 with the starts spaced 10 s apart (1 and 1 before), so the queue holds 60
  and a 15-library fan-out no longer takes about 20 minutes. A public user's
  day is 50 runs and 10,000,000 weighted tokens (about $1), and the global
  day budget is 100,000,000 (about $10), admins included. Claude calls retry
  four times instead of two; a 429 or 529 that outlasts them ends the run as
  `busy`. The render gates run in a worker thread (#12507).
- **The fan-out panel waits out `run_limit` instead of failing.** With
  `.plot_all()` open in several windows the admin's cap counts them all: a
  library the cap refused goes back to waiting, and the panel tries again
  when one of its runs ends or after 15 s, giving up only after 30 minutes.
  The fan-out's data copies no longer count against an admin's copy limits
  (30 a minute, 150 a day), so three windows can copy their 45 datasets at
  once (#12507).
