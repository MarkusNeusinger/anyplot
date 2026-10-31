### Added

- **The pipeline's Claude steps can run on API credits: the repository
  variable `CLAUDE_AUTH`.** Unset or `subscription`, all 13 Claude steps in the
  8 workflows that run Claude use the `CLAUDE_CODE_OAUTH_TOKEN` secret as
  before; `api` switches them to the `ANTHROPIC_API_KEY` secret. Each step
  passes exactly one credential, because the action does not document which
  one wins when both are set. A new first step, "Check Claude credentials",
  stops the job on any other value and on `api` without the key, instead of
  falling back to the subscription and the owner's interactive quota.
  `docs/workflows/overview.md` has the switch, the spend limit and what the
  pipeline does when the limit is reached.
- **Every Claude session's cost in the job summary.** A step after each
  Claude step writes `total_cost_usd` (Claude Code's estimate at API list
  price), the model and the credential to the job summary and the log, and
  never fails the job. The weekly regen review's `collect_week.py --costs`
  reads it, now counts the `daily-regen.yml` pre-flight too, and names the
  part that ran on API credits.
- **Daily regeneration by implementation instead of by spec: the repository
  variable `REGEN_PAIRS_PER_DAY`.** Set to N, the scheduled `daily-regen.yml`
  run picks the N oldest (spec, library) pairs across the catalogue
  (`automation/scripts/regen_pick_pairs.py`), aged by their own metadata and
  their last regeneration attempt so a kept regeneration is not picked again,
  skips the spec polish, and dispatches each pair straight to
  `impl-generate.yml` with `bulk-generate.yml`'s arguments and pace, since
  that workflow's single concurrency group would cancel queued runs. Unset,
  the schedule regenerates whole specs as before; a manual run opts in with the
  new `pairs` input, and the watchdog's cron rescue forwards the variable.
