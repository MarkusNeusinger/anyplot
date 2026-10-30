### Added

- **Agent telemetry: why a run needed its attempts, and with which configuration.** Each `pipeline_run` line
  now lists the stage that ended every attempt (`stages`, so adapter answers cut off at the output limit can
  be counted), the score bucket of every round, the readiness of the catalogue file, the kinds of cells the
  runtime's loader changed (`inexact`, `submillisecond`, `offset`, asked from the runtime), the edit-failure
  kinds and validator rule ids of its checks, the reviewer mode, ship-best and self-review settings, and the
  hashes of the adapter and reviewer prompts. Every token entry gains `thoughts`, the thinking part of
  `output`, which stays inclusive so the cost view and the older rows keep their meaning. All values come from
  closed sets pinned to their sources by tests; an unknown id is `other`, never a dropped line. The views get a
  typed column per field, an `attempts` view and `edit` and `validator` failure kinds.
- **Agent telemetry: the plot language, as a code.** `chat_turn` and `pipeline_run` record the session
  language as one of twelve codes or `other`, never the free-text value; the legal page names it.
- **Agent telemetry: the admin's fan-out sessions are filed apart.** The sessions "plot in all libraries"
  opens carry `source = "fanout"` on every line, so the live numbers and the `/debug` card no longer count the
  owner's test sessions, none of which ever kept a plot.

### Fixed

- **Agent telemetry: a turn records the language it set.** `language_source` was read before the turn ran, so
  the turn whose message the language was detected from, or that called `set_language`, recorded the value from
  before; the line now reads the session after the run.
