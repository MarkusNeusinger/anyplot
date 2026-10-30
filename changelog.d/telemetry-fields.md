### Added

- **Agent telemetry: why a run needed its attempts, and with which configuration.** Each `pipeline_run` line
  now lists the stage that ended every attempt (`stages`, so adapter answers cut off at the output limit can
  be counted), the score bucket of every round, the readiness of the catalogue file, the kinds of cells the
  runtime's loader changed (`inexact`, `submillisecond`, `offset`, asked from the runtime), the edit-failure
  kinds and validator rule ids of its checks, the reviewer mode, ship-best and self-review settings, and the
  hashes of the adapter and reviewer prompts. Every token entry gains `thoughts`, the thinking part of
  `output`, which stays inclusive so the cost view and the older rows keep their meaning. All values come from
  closed sets pinned to their sources by tests; an unknown id is `other`, never a dropped line. The views get a
  typed column per field, an `attempts` view and `edit` and `validator` failure kinds. (#12477)
- **Agent telemetry: the review score joins what users do with the plot.** `pipeline_run` names the version
  it shipped (`version`, the number the page sends back with every outcome) and the shipped render's own score
  bucket (`shipped_score`). The new `score_outcomes` view lists every shipped version with its score, rounds and
  attempt stages beside the copies, downloads and reaction on exactly that version, the plots the session shipped
  before it, and the seconds from the first plot to the take-away, so the keep rate can be read per score bucket
  and library. (#12477)
- **Feedback cases: the catalogue reviewer's prompt has its own hash.** The bundle's `prompt_hashes` gain
  `reviewer_catalogue`: `reviewer` hashed the checklist instruction only, so a change of the catalogue rubric the
  live reviewer runs changed no hash. Every case's combined `prompt_hash` shifts once with this release without any
  prompt changing; the cases before it are all admin test cases. The same deploy shifts three telemetry numbers a
  report sees: `language_source` reads the turn's own detection, `failures` gains the kinds `edit` and `validator`,
  and the fan-out's sessions leave `live` (`docs/reference/agent-telemetry.md`, "Shifts a report notices on
  2026-10-30"). (#12477)
- **Agent telemetry: the plot language, as a code.** `chat_turn` and `pipeline_run` record the session
  language as one of twelve codes or `other`, never the free-text value; the legal page names it. (#12477)
- **Agent telemetry: the admin's fan-out sessions are filed apart.** The sessions "plot in all libraries"
  opens carry `source = "fanout"` on every line, so the live numbers and the `/debug` card no longer count the
  owner's test sessions, none of which ever kept a plot. (#12477)

### Fixed

- **Agent telemetry: a turn records the language it set.** `language_source` was read before the turn ran, so
  the turn whose message the language was detected from, or that called `set_language`, recorded the value from
  before; the line now reads the session after the run. (#12477)
