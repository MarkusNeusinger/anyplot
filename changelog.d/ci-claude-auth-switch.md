### Added

- **The pipeline's Claude steps can run on API credits, by workload identity
  federation or an API key: the repository variable `CLAUDE_AUTH`.** Unset or
  `subscription`, all 13 Claude steps in the 8 workflows that run Claude use
  the `CLAUDE_CODE_OAUTH_TOKEN` secret as before. `oidc` exchanges the job's
  GitHub OIDC token for a short-lived token of the `ci-regen` workspace (the
  four `CLAUDE_WIF_*` variables; the Console rule accepts only runs on
  `main`), and `api` uses the `ANTHROPIC_API_KEY` secret. A new first step,
  "Resolve Claude credentials", stops the job on any other value or a missing
  credential instead of falling back to the subscription and the owner's
  interactive quota, and every Claude step reads its outputs, so each passes
  exactly one credential and a new mode changes one step.
  `docs/workflows/overview.md` has the Console setup, the switch commands and
  the runs federation refuses.
- **Every Claude session's cost in the job summary, and a clean stop at a
  spend or usage limit.** A step after each Claude step writes
  `total_cost_usd` (Claude Code's estimate at API list price), the model and
  the credential mode to the job summary and the log, and never fails the
  job. It also reads, from the error fields of a failed session, the API's
  spend-limit, spend-cap and credit messages and the subscription's
  usage-limit messages: the retry is skipped, `impl-generate.yml` parks the
  pair, `impl-review.yml` and `impl-repair.yml` hand the PR on without
  spending their automatic retry, and nothing counts as an attempt or marks
  `impl:<lib>:failed`, a first implementation included. Before, a
  subscription usage limit used up a pair's three attempts. The weekly regen
  review's `collect_week.py --costs` reads the line, now counts the
  `daily-regen.yml` pre-flight too, and names the part that ran on API
  credits.
- **Daily regeneration by implementation instead of by spec: the repository
  variable `REGEN_PAIRS_PER_DAY`.** Set to N, the scheduled `daily-regen.yml`
  run picks the N oldest (spec, library) pairs across the catalogue
  (`automation/scripts/regen_pick_pairs.py`), skips the spec polish, and
  dispatches each pair straight to `impl-generate.yml` with
  `bulk-generate.yml`'s arguments and pace, since that workflow's single
  concurrency group would cancel queued runs. A pair merged or really
  attempted (a closed PR, a kept regeneration, a failed generation) within
  the attempt window, 30 days unless `attempt_window_days` or
  `REGEN_ATTEMPT_WINDOW_DAYS` says otherwise, is not picked again, while an
  infrastructure failure or a stop at a spend or usage limit leaves it in the
  queue. Unset,
  the schedule regenerates whole specs as before; a manual run opts in with
  the new `pairs` input, and the watchdog's cron rescue forwards the
  variable.
