# Agent usage telemetry

> **Status (2026-10-30):** the agents service writes the four events, the BFF forwards the page's outcome
> beacon, and the BigQuery side is set up: the views hold lines since 2026-10-16. The fields added on 2026-10-30
> (see [Fields added on 2026-10-30](#fields-added-on-2026-10-30)) are written once the agents service is
> deployed, and reach the typed views after you create the views again (step 6 of
> [Set up the BigQuery side](#set-up-the-bigquery-side)).

The agent chat ("Use with my data") records how it is used, without recording what anyone
used it for. This page lists what is recorded, where it goes, how long it stays, and how to read it.

## What is recorded, and what never is

Owner rule of 2026-10-16: no line holds a user input, a question, a reply, a data value, a column
name, a file or sheet name, or a cell. A line holds only enums, coarse buckets, counts, durations, and ids
from closed sets (spec ids, library ids, model ids, review defect ids such as `VQ-01`, gate ids such as
`G7`). Content reaches anyone only through the explicit feedback-case submission
([Feedback capture](../concepts/agent-network.md#feedback-capture)).

The guarantee is structural. Every event is a pydantic model in `agents/anyplot/telemetry.py` with
`extra="forbid"`, and every field is a `Literal` set, a bounded integer, a boolean, or an id that must match
a fixed pattern. A value outside its set fails validation, and the line is dropped with a warning that names
the event and the field, never the value. Warning sentences of the parser and the binding check are mapped
to closed codes before they reach a line (`agents/anyplot/data/warning_codes.py`), and a sentence no rule
knows becomes `other`. Tests run a whole session with distinctive column names, cells, notes, a file name and
a message, and fail if any of them reaches a telemetry line (`tests/unit/agents/runtime/test_telemetry.py`).

## Events

The agents service writes one wide JSON line per event to stdout on its own logger,
`anyplot.agents.telemetry` (`agents/main.py` `enable_attribution_log`). Cloud Run turns each line into a
`jsonPayload`.

| Event | When | Main fields |
|---|---|---|
| `data_input` | A paste or a dropped file reaches the dataset route, or the file conversion refuses a file | `format`, `entry` (`paste` or `file`), `outcome`, `cause`, `size_bucket`, `rows_bucket`, `cols_bucket`, column counts by type, `max_categories_bucket`, `missing_bucket`, `warnings` (codes), `tables`, `sheets`, `notes` and `file_name` (booleans), `spec_fit`, judge tokens, `latency_ms` |
| `chat_turn` | A `/messages` turn ends, refused ones included; `manual_binding_changed` counts only a `PUT /bindings` whose bindings differ from the ones the session held, because the page echoes the parse's defaults after every paste | `kind` (`plot`, `prep`, `formula`, `code`, `example`, `talk`, `refused`, `error`; a turn whose `plot_pipeline` call ToolSafety refused before the run is no `plot` turn since 2026-11-08, see [Meanings changed on 2026-11-08](#meanings-changed-on-2026-11-08)), `action`, `asked_question`, `tools`, `prep_ops`, `capability_gap` (since 2026-11-07, see [Fields added on 2026-11-07](#fields-added-on-2026-11-07)), `conversion` (what the turn did about a required role left open: `none` when the session block listed no conversion, `date`, `number` or `index` for the column `prepare_data` made, `asked` when one was listed and none was made; `asked_question` tells a question from a skip), `undo`, `to_long`, `manual_binding_changed`, `binding_warnings`, `refusal`, `error`, `reply_reasked`, `language_source` and `plot_language` (both as the turn left them), `steps` (calls, tokens, thinking tokens and model per agent), `latency_ms` |
| `pipeline_run` | A `plot_pipeline` run ends, or the root asked for one before the data was ready (`status: not_ready` with its reason, also when ToolSafety refused the call before the run) | `run_index` (1 is the session's first plot), `base`, `status`, `reason`, `stage`, `stages`, `attempts`, `rounds`, `round_scores`, `score_round1`, `score_round2` (buckets), `shipped_attempt`, `version` (the shipped version's number, which `outcome.version` names), `shipped_score`, `forced_repair`, `gates_failed`, `reviewer_defects`, `residual_defects`, `sandbox_failures` (`syntax`, `name`, `key`, `value`, `type`, `timeout`, `memory`, `other`), `drift_restored` (true when a plan that only changed the protected theme statements had them restored after the round's check retry), `plot_language`, `readiness`, `loader_notes`, `edit_failures`, `validator_rules`, `adaptation_rules`, the pipeline configuration and prompt hashes, time per stage, `steps`, and since 2026-11-01 `lane`, `queue_wait_ms`, `queue_position`, `user_runs_today`, `user_tokens_today` (see [Fields added on 2026-11-01](#fields-added-on-2026-11-01)) |
| `plot_switch` | The session switches its (spec, library) target, since 2026-11-02 | `switch_source`, `from_library`, `spec_changed`, `library_changed`, `carried_count`, `newer_count`, `target_has_plot`, `offered`, `memory_kinds` (see [Fields added on 2026-11-02](#fields-added-on-2026-11-02)) |
| `outcome` | The page's beacon after a copy, a download, a session save, or a feedback send | `action` (`copied_code`, `copied_image`, `downloaded_png`, `downloaded_code`, `downloaded_page`, `opened_preview`, `opened_data_view`, `downloaded_data`, `saved_session`, `feedback`; `downloaded_page` is a JavaScript plot's interactive `plot.html`, and `opened_preview` that page shown in the card, a look that keeps nothing, both since 2026-10-31; `opened_data_view` is the data panel's view of every row once it shows the rows, with version 0 because it looks at the session's data and not at a result, a look that keeps nothing either, since 2026-11-02), `version`, `reaction` |
| `language_offer` | Since 2026-11-08: the server sends the page the offer of a language it found in a typed message or a paste, the user takes such an offer with `.switch()`, or the user picks a language in the chat header's menu | `via` (`shown`, `offer`, `header`), `language` (the closed code of `plot_language` below) |

Every line carries the same envelope:

| Field | Meaning |
|---|---|
| `log_type` | Always `agent_telemetry`: the sink selects on it |
| `schema` | The line format's version, `1`. A renamed or removed field is a new schema; an added field is not |
| `event` | One of the six events (`plot_switch` since 2026-11-02, `language_offer` since 2026-11-08) |
| `service`, `revision` | Cloud Run's `K_SERVICE` and `K_REVISION` |
| `source` | `live`; `fanout` for every line of a session the admin's "plot in all libraries" fan-out opened; or `harness` for the eval harnesses (`agents/evals/matrix.py`, `agents/evals/prep.py`). The card and the `source = 'live'` filters count `live` only. See [Fan-out sessions](#fan-out-sessions) |
| `session` | An HMAC-SHA256 of the session id under a random per-process salt, 16 hex characters |
| `spec_id`, `library` | The session's spec and library, set once per request from session state |
| `turn` | The session's user turns so far; a `chat_turn` carries its own number |
| `idempotency_key` | A hash of session, turn, attempt and event: a line Cloud Logging delivers twice, or a pipeline node that ADK runs again, keeps its key, and the base view keeps one row per key |

### Session hash

Every `/v1` request URL that Cloud Run logs holds the session id, so a plain hash of it could be recomputed
and joined to the request log. The telemetry hash uses a salt that the process draws at start and never
logs. Sessions live in memory and end with the instance (`max-instances=1`), so the salt keeps one session's
lines together for exactly as long as the session exists. Since 2026-10-16 the attribution lines' `session`
is salted with the same per-process salt under another domain (`agents/anyplot/plugins/ledger.py` `salted`),
so it cannot be joined to the request log either, and the two hashes of one session differ: telemetry rows
cannot be joined to the attribution lines, which carry the user id.

The hash does not prevent a join by time. Cloud Run's request logs (the session id in the URL, the client IP
address) and the attribution lines (the HMAC user id) stay in the project's `_Default` log bucket for 30 days. For
those 30 days, someone with read access to both buckets can match a telemetry line to a request or an attribution
line by its timestamp and its kind of request (a paste, a turn, a beacon). After 30 days only the telemetry lines are left, and the join is gone. This
is why the lines stay pseudonymous rather than anonymous, and it holds for every field, not only the ones added
later.

For the public lane (since 2026-11-02) the API's request log no longer holds the session id: the page sends it
in the `X-Anyplot-Session` header, and anyplot-api's log lines leave it out. The agents service's request log
still holds it in its URLs, next to anyplot-api's address rather than the client's. The join by time stays
possible there for the same 30 days.

### No user id

The attribution lines (one per plugin hook, for debugging) carry the HMAC user id for the rate limits and
the security review; for a public caller that id is `pub_` and 16 hex digits of the browser tab's random id,
salted with the same per-process salt under its own domain, so it cannot be recomputed once the process ends. The telemetry lines never do: they come from a different logger, and the sink filter
takes only `log_type="agent_telemetry"`, so no attribution line reaches the telemetry bucket.

### Outcome beacon

The page posts `POST /debug/agent/sessions/{sid}/outcome` with `{action, version, reaction?}` after the
action succeeded. The BFF accepts only the closed fields and forwards them to
`POST /v1/sessions/{sid}/outcome`, which writes the line, so every line comes from one writer with one
session hash. The agents service limits the beacon to 30 per user per minute and 2,000 per day
(`OUTCOMES_PER_MINUTE`, `OUTCOMES_PER_DAY` in `agents/anyplot/plugins/ledger.py`); the page ignores every
error the beacon gets.

### Fan-out sessions

The admin's "plot in all libraries" (`.plot_all()`, `app/src/sections/agent-chat/FanOut.tsx`) opens one session
per library, has the agents service copy the page session's confirmed data into each
(`POST /v1/sessions/{sid}/dataset/copy`) and runs `create_plot` in each. Since 2026-11-01 a copy writes no
`data_input` line, because no input reaches the dataset route; its `dataset_copy` attribution log line carries the
outcome, the row and column counts, the version number and the source session's salted hash, never data. Before,
the page posted the paste again in each session, which wrote one `data_input` line per library, and it still does
against an agents service without the copy route. None of these sessions ever keeps a plot,
so counted as `live` they would multiply sessions and data inputs and push the kept rate down. The page marks each
session it opens for the fan-out (`useAgentSession` with `fanout`, `POST /debug/agent/sessions` with
`source: "fanout"`), the BFF forwards the value, and the agents service accepts `fanout` only (any other value is
`422`). The service keeps the mark in session state (`anyplot.telemetry_source`), and every line of the session,
whatever its event, carries `source = "fanout"` instead of `live`. Every existing `source = 'live'` filter (the
`/debug` card, `api/agent_usage.py`) leaves them out, and the views keep them apart by `source`. The one exception
is the per-day table's `fan-out` column ([The /debug card](#the-debug-card)): these sessions spend the same day
budget, so their cost is shown beside the live cost, never inside it.

Only an admin can open the chat today, so the value labels the owner's own test sessions. Once the chat is
public, a user who sends the mark by hand only files their own lines as tests.

### Fields added on 2026-10-30

Schema 1 grows by optional fields only: a line written before 2026-10-30 lacks these fields, and the views read
them as `NULL` (unknown), not as an empty list or `false`. Every value comes from a closed set; an id the set does
not know yet becomes `other`, so a new rule never drops a line.

| Event | Field | Meaning |
|---|---|---|
| `chat_turn` | `plot_language` | The session language as the turn left it, as a code: `en`, `de`, `fr`, `es`, `it`, `pt`, `nl`, `pl`, `zh`, `vi`, `ru`, `ja` (the languages `agents/anyplot/language.py` names in `ENGLISH_NAMES`), and `other` for every other language. The session language itself is free text (`Swedish`), and a rare language could single a user out, so it never reaches a line |
| `chat_turn` | `language_source` | Since 2026-10-30 read after the turn's run, like `plot_language`: the turn that called `set_language` records the new value (until 2026-11-08 also the turn whose message the scope judge detected). Before, it recorded the value from before the turn. The values since 2026-11-08 are in [Fields added on 2026-11-08](#fields-added-on-2026-11-08) |
| `chat_turn`, `pipeline_run` | `steps[].thoughts` | The thinking tokens among `output`. `output` stays candidates plus thoughts, as both providers bill them, so the cost view prices `output` as before; `thoughts` is a part of it, never added to it. `null` for the judges, which book a plain total |
| `pipeline_run` | `stages` | The stage that ended each attempt, in order (`pipeline.Run.stages`): retries after a failed check, proofreads, repairs and their causes. `adapter_truncated` counts the adapter answers cut off at the output limit. `stage` stays what stopped the run, also a limit before the next attempt. Both take the values of `pipeline.Stage` (pinned by a test), and `other` for a stage added there before the telemetry knows it |
| `pipeline_run` | `round_scores` | The bucket of each round's latest review score in round order, `unscored` for a round without one (a failed render, a checklist review). `score_round1` and `score_round2` repeat the first two |
| `pipeline_run` | `version` | The session's number of the version the run shipped (`PlotResult.version`): the number the `plot` event hands the page and the page sends back as `outcome.version`, counted per session across its libraries (`services.VersionStore`). `null` when the run shipped nothing. See [Score and outcome](#score-and-outcome) |
| `pipeline_run` | `shipped_score` | The bucket of the shipped render's own review score; `null` when it shipped unscored (a checklist review, no review left) |
| `pipeline_run` | `plot_language` | The run's plot language, as the closed code above |
| `pipeline_run` | `readiness` | `clean` or `coupled`: the readiness of the catalogue file the session adapts, as the session opened it for its library |
| `pipeline_run` | `loader_notes` | `inexact` (integers past ±2^53 read as the nearest double), `submillisecond` (timestamps cut to the millisecond), `offset` (timestamps with a UTC offset read in UTC): the kinds of cells the runtime's loader changed reading the run's data. The pipeline asks the runtime for each kind alone (`pipeline.loader_codes`): R reports `inexact` and `offset`, Julia `submillisecond` and `offset`, Python none. Never the note's sentence, which names columns and counts |
| `pipeline_run` | `edit_failures` | The distinct kinds (`agents/anyplot/code/edits.py` `FAILURE_KINDS`) of the edit failures that ended an attempt. A plan restored after drift is `drift_restored`, not here |
| `pipeline_run` | `validator_rules` | The distinct rule ids that rejected a plan's code in any check of the run: SECURITY findings, the blocking ADAPTATION rules and `literal-budget` |
| `pipeline_run` | `adaptation_rules` | The distinct soft ADAPTATION rule ids of any check of the run: defect lines, the code still rendered |
| `pipeline_run` | `reviewer_mode`, `ship_best`, `self_review`, `repair_self_review` | The pipeline configuration as set (`AGENT_REVIEWER_MODE`, `AGENT_SHIP_BEST`, `AGENT_SELF_REVIEW`, `AGENT_REPAIR_SELF_REVIEW`). `ship_best` takes effect with `reviewer_mode` `catalogue` only. `null` on a `not_ready` line |
| `pipeline_run` | `adapter_prompt`, `reviewer_prompt` | The first 16 hex characters of the SHA-256 of the run's adapter instruction and of the reviewer instruction in its mode (`policy.prompt_hash`, the hash of the feedback bundle's `prompt_hashes`). `adapter_prompt` equals the bundle's `adapter_<library>`, and `reviewer_prompt` the bundle's `reviewer_catalogue` in `catalogue` mode or its `reviewer` in `checklist` mode (a test pins both) |

Tests pin each closed set to its source: the language table, `FAILURE_KINDS`, the rule ids that the validators of
every language write (collected from their sources), `ColumnKinds`, the reviewer modes and the readiness statuses.
Another test pins `pipeline_run.version` to the number of the `plot` event, the version store and the
`outcome.version` the page sends back (`tests/unit/agents/runtime/test_telemetry.py`).

#### Shifts a report notices on 2026-10-30

The same deploy changes the meaning of a few existing numbers. A Looker Studio chart that spans the day shows a
step that is not a change in use:

- **`chat_turn.language_source`.** It is read after the turn's run now. The turn that detects the language, or
  sets it with `set_language`, records `detected` or `chosen`, where earlier lines recorded the value from before
  the turn (`default`, or `pasted`). Expect more `detected` and fewer `default` from that day.
- **`failures`.** The view gains the kinds `edit` and `validator`. A chart that counts all its rows without a filter
  on `kind` counts more from that day; filter on `kind` to compare with earlier weeks.
- **`source`.** The admin's fan-out sessions are `fanout` from that day. Before, they were `live`: one session per
  library, none of them kept (for example the fan-out of `scatter-basic` on 2026-10-28 at 23:41: 7 sessions in 6
  libraries within minutes, the page's own session included). Live sessions, data inputs and the kept rate before
  that day still include them.
- **The feedback case's `prompt_hash`.** The bundle's `prompt_hashes` gain `reviewer_catalogue`, the hash of the
  catalogue reviewer's instruction, which the live reviewer runs. The combined `prompt_hash` of every case shifts
  once on that day without any prompt changing; every case before it is an admin test case.

### Fields added on 2026-11-01

These fields show whether anyone waits long in the run queue or comes close to a limit, without saying who
(owner request of 2026-11-01). The owner's rule of 2026-10-30 holds for each of them: no user id, no hash of one,
no key that stays stable across sessions. Each field is a closed set or a bounded integer, so nothing that names a
user fits into it, and a test checks that the user id of the run appears nowhere in its line. They sit on
`pipeline_run` rather than `chat_turn`, because the per-user counts are counts of pipeline runs and the queue entry
is the run's. A `not_ready` run never enters the queue, so it carries `lane` only, and lines written before
2026-11-01 lack all five; the views read both as `NULL`.

| Event | Field | Meaning |
|---|---|---|
| `pipeline_run` | `lane` | `admin` or `public`: the tier the run was served in (`X-Anyplot-Tier`, which the BFF sets for an admin). It tells the admin's test runs, which skip the per-user day caps, from the runs the public limits bound |
| `pipeline_run` | `queue_wait_ms` | How long the turn's run-queue entry waited before the run could start, in milliseconds; `0` when it started at once. The queue starts at most one run every 10 seconds and holds at most 5 runs in flight, so a fan-out's later libraries wait by design |
| `pipeline_run` | `queue_position` | Where the entry stood when it was submitted: `0` when it started at once, `1` when it ran next, at most the queue's capacity (60 at the defaults) |
| `pipeline_run` | `user_runs_today` | A bucket of the run's ordinal among the same user's pipeline runs of the UTC day: `1`, `2_5`, `6_10`, `11_20`, `21_30`, `31_40`, `41_plus`. The count lives only in the service's memory (`UsageBook`), so a redeploy or a scale-to-zero starts it again; the public cap is 50 runs a day (`AGENT_DAILY_PIPELINE_RUNS`) |
| `pipeline_run` | `user_tokens_today` | A bucket of the share of the per-user daily token budget (`AGENT_DAILY_TOKEN_BUDGET`, 10,000,000 weighted tokens, about $1) the user had spent when the run was booked: `lt25`, `25_50`, `50_75`, `75_90`, `90_100`, `over`. An admin's share is measured against the same public budget, so the buckets stay comparable; `over` is a share past the budget, which only an admin, who is exempt from it, can reach |

The limit refusals were recorded before and stay where they were: `chat_turn.refusal` is `rate_limited` or
`daily_limit` for the message limits, and `chat_turn.error` is `capacity` (a full queue, a wait that ran out, or a
model service still refusing a call after its retries) or `run_limit` (the user's cap of runs in flight across
their windows). An admin's turns land there the same way. The `failures` view lists both.

The typed columns are in `agents/telemetry/views/02_event_views.sql` (`pipeline_runs`). Applying the changed view
in BigQuery is a write to the shared dataset: it waits for the owner's approval after the merge, and until then the
fields sit in `payload` of the `events` view. See [Set up the BigQuery side](#set-up-the-bigquery-side).

#### Shifts a report notices on 2026-11-01

Example data on request adds values to two closed sets:

- **`data_input.format` and `data_input.outcome` `data_request`.** A paste that asks for data instead of holding it
  ("Beispieldaten") goes to the chat. Its `cause` is `transcribed_data_request` when the free-text reader said so,
  and null when the fixed phrases of `data/classify.py` found it before any model. Like `formula` and `code`, the
  `sessions` and `input_formats` views count it among the refused inputs; the session's next `chat_turn` shows
  what the chat made of it.
- **`chat_turn.kind` `example`.** A turn whose `run_data_code` stored example data the user asked for
  (`source_language` `example`); such a turn was `code` before.

### Fields added on 2026-11-02

The library switch with the plot memory adds the `plot_switch` event and new fields and values on `pipeline_run`
and `chat_turn`, listed below. Like every other field, they hold counts, booleans and closed sets, never a decision's
text.

| Event | Field | Meaning |
|---|---|---|
| `plot_switch` | `switch_source` | `menu` for the page's library menu, `chat` for a switch the user asked for in the chat. Not `source`, which the envelope holds (`live`, `fanout`, `harness`) |
| `plot_switch` | `from_library`, `spec_changed`, `library_changed` | The library before the switch (the envelope's `library` is the one after it), and what the switch changed. Another spec is refused until the plot-type switch, so `spec_changed` is `false` for now |
| `plot_switch` | `carried_count`, `newer_count`, `target_has_plot`, `offered` | How many decisions a plot in the new library would take over, how many of them came after that library's own latest plot, whether it has one, and whether the answer offered the carry run |
| `plot_switch` | `memory_kinds` | The plot memory's entries counted by kind (`title`, `axis_label`, `reference_line`, `annotation`, `marker` and the other kinds of the closed set) |
| `pipeline_run` | `carried` | The run took a switch's carry: the first plot in a new library, from its catalogue plot with the user's decisions |
| `pipeline_run` | `fresh` | The run was the page's `.create_plot()` or `.start_over()`: the catalogue code again, without a switch's carry, with the memory's decisions; also "plot the new data" when it started from the catalogue plot |
| `pipeline_run` | `new_data` | Since 2026-11-08, only on the page's "plot the new data": `previous` when the run started from the library's latest version (the same paste, the same bindings), else why it started from the catalogue plot: `other_paste`, `other_data` (a computed table replaced the data), `bindings_changed`, `kept_note` (a first-plot request waited) or `no_plot`. It counts how often the latest version is the base |
| `pipeline_run` | `memory_entries`, `remembered`, `memory_full` | The plot memory's entries the run handed the adapter, the entries it stored once it shipped, and whether the memory had no room for them |
| `chat_turn` | `action` `carry_plot`, `tools` `forget` | The page's carry run after a switch, and the root removing a decision |
| `chat_turn` | `action` `plot_new_data` | Since 2026-11-08: the page's "plot the new data", after a data change or a paste |

The typed columns are in `agents/telemetry/views/02_event_views.sql` (`pipeline_runs` and the new `plot_switches`).
Applying the changed views waits for the owner's approval, as on 2026-11-01; until then the fields sit in `payload`
of the `events` view.

### Fields added on 2026-11-04

- **`chat_turn.action` `example_data`.** The page's `.example_data()`, the line above the composer while the session
  has no data: the example data a typed request asks for, in one click and as an action, so it sets no session
  language. Its `kind` is `example` when `run_data_code` stored the table, as for the typed request. The column is
  a string in the views, so they need no change.

### Fields added on 2026-11-07

- **`chat_turn.capability_gap`.** The data changes the root named in the turn as ones no `prepare_data` operation
  can make, by family: `fill_values`, `edit_cells`, `add_rows`, `combine_tables`, `text_pattern`, `time_window` or
  `other`, distinct and sorted. It is empty for every other turn. The family comes from the closed `unsupported`
  operation (`prepare.UnsupportedFamily`), never from the request's words. Count the turns where it is not empty to
  see what users ask the chat for that it cannot do, and group by family to see which operation to build next.
- **`chat_turn.prep_ops` `compute`, `diff`, `rolling`, `blank`.** The operations of the same date. `unsupported` is
  in the closed set too, but never appears: `prep_ops` lists only the calls that changed the data.

The typed column `capability_gap` is in `agents/telemetry/views/02_event_views.sql` (`chat_turns`). Applying the
changed view waits for the owner's approval, as on 2026-11-01; until then the field sits in `payload` of the
`events` view.

### Fields added on 2026-11-08

- **`language_offer`, a new event.** A typed message or a paste in another language no longer sets the session
  language: the page offers it once, and the user takes it or not. One line per offer the server sends to the page
  (`via: shown`, from the scope guard's offer for a typed message, in the turn's `done`, or from the dataset route's
  offer for the notes or column names of a paste), per offer the user takes (`via: offer`, `PUT .../language` with
  `via: offer`) and per pick in the chat header (`via: header`). `language` is the closed code, as `plot_language`.
  The share of offers taken is the `offer` lines over the `shown` ones. A request in the chat ("auf Deutsch bitte")
  writes no line: the turn's `chat_turn.language_source` records `chosen`. The event replaces a Plausible event the
  design proposed: most of the chat's sessions are the owner's own, and the Plausible dashboard is public.
- **`chat_turn.language_source`.** The closed set is `default`, `chosen` and `offer` now: `offer` is a session whose
  user took an offer. `pasted` and `detected` no longer appear, so expect more `default` from that day.

The typed columns of the new event are in the view `language_offers` in `agents/telemetry/views/02_event_views.sql`.
Applying the changed view waits for the owner's approval, as on 2026-11-01; until then the lines sit in `payload` of
the `events` view.

### Meanings changed on 2026-11-08

ToolSafety refuses `plot_pipeline` before the run in a turn that changed the data itself, and on the summary turn of
a paste while the data is unconfirmed (`data_changed_this_turn`, `summary_turn`; see the agent network's
[Two steps](../concepts/agent-network.md#two-steps-data-first-then-the-plot)). Before, such a call ran into the run's
own `not_ready`. No field is new, but three readings change from that date on:

- **`chat_turn.kind` and `chat_turn.tools`.** `tools` lists only the calls ToolSafety allowed, so the refused
  `plot_pipeline` is not in it, and the turn's `kind` is `prep`, `formula`, `code` or `talk` instead of `plot`.
- **`pipeline_run` `not_ready`.** The refusal writes the same line as the run's own `not_ready` would, with the run's
  reason, so the funnel still sees the ask. The Budget plugin counts no daily run for it, so `user_runs_today` is
  `null` on such a line.
- **`chat_turn.error` `no_reply`.** A summary turn whose reply is empty, or that the output sanitiser empties, ends as
  `no_reply` after such a refusal: no `plot` event went to the page. Before, the `not_ready` event counted as the
  turn's answer.

## Where the lines go

| Resource | Name | Notes |
|---|---|---|
| Log bucket | `agent-telemetry` in `europe-west4` | Retention 180 days (owner decision of 2026-10-16), Log Analytics on |
| Sink | `agent-telemetry` | Routes the filter below from `anyplot-agents` into the bucket |
| Linked dataset | `anyplot.agent_telemetry_logs` | Read-only view of the bucket in BigQuery (`_AllLogs`) |
| Views dataset | `anyplot.agent_telemetry` in `europe-west4` | The views of `agents/telemetry/views/*.sql`, for Looker Studio and the card |

The sink filter:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="anyplot-agents"
jsonPayload.log_type="agent_telemetry"
```

An exclusion on the `_Default` sink (step 3 below) keeps the same lines out of the project's `_Default`
bucket, so they live in one place with one retention.

## Views

Create them in file order. Each file is a script of `CREATE OR REPLACE VIEW` statements with the project
and dataset names written out.

| File | Views | Content |
|---|---|---|
| `01_events.sql` | `events` | One row per line, deduplicated by `idempotency_key` (`QUALIFY ROW_NUMBER()`), with the envelope as columns and the line as `payload` |
| `02_event_views.sql` | `data_inputs`, `chat_turns`, `pipeline_runs`, `plot_switches` (since 2026-11-02), `outcomes`, `language_offers` (since 2026-11-08) | One typed column per field, `NULL` where a line predates the field; `pipeline_runs` also has `adapter_truncations`, the count of `adapter_truncated` in `stages` |
| `03_sessions.sql` | `sessions` | One row per session: data inputs, transcription offers, turns, runs, `not_ready` asks, shipped plots, `turns_to_first_plot`, keeps (copies and downloads), saves, feedback, rejections (feedback with `thumbs_down` or `bug`), `kept`, `funnel_last_step` (from `outcome_only` and `data_refused` through `transcription_offered`, `data_ok`, `chatted`, `plot_not_ready`, `plot_run` and `plot_shipped` to `kept`), and `state` under a 30-minute inactivity rule (`active`, `rejected`, `kept`, `saved`, `refined`, `abandoned_after_plot`, `abandoned_before_plot`). A session is `kept` when, after its last pipeline run, the user copied or downloaded a result (`copied_code`, `copied_image`, `downloaded_png`, `downloaded_code`, `downloaded_data`) and sent no feedback with `thumbs_down` or `bug`. A saved session is never a keep, because users also save a session to report a plot they did not like: a session whose only take-away is a save ends `saved`, and one with a `thumbs_down` or `bug` ends `rejected`. The view's header lists example sessions and how each is classified. A transcription writes two `data_input` rows, the offer (outcome `transcribed`) and the confirmed paste; every view counts the input once and the offers apart. `not_ready` runs are never counted as runs or in the repair rate |
| `04_usage_failures.sql` | `usage`, `input_formats`, `failures`, `attempts` | Usage by day, spec and library (each line under the library it was written under, so a library switch splits a session's runs correctly; `sessions_kept` counts each session the `sessions` view calls `kept` once, under the day, spec and library of its last shipped run, so run it after `03_sessions.sql`); data inputs by format and entry, each input under its own format; one row per failure with its kind and closed code (since 2026-10-30 also the kinds `edit` and `validator`); one row per adapter attempt of a run with the stage that ended it |
| `05_prices_cost.sql` | `model_prices`, `cost` | The `eu` list prices of `agents/evals/pricing.py` (a test keeps both equal) and the cost of every turn step and data-input judge call, with `thoughts_tokens`, the thinking part of `output_tokens` |
| `06_score_outcomes.sql` | `score_outcomes` | One row per shipped plot version with its review score and what the user did with exactly that version; see [Score and outcome](#score-and-outcome). Run it after `03_sessions.sql` |

The cost view prices the `chat_turn` and `data_input` lines only: `pipeline_run.steps` repeats the adapter's
and the reviewer's share of its turn for per-run analysis.

### Score and outcome

The `score_outcomes` view answers whether the reviewer's score predicts what users do with a plot. Each shipped
`pipeline_run` names the version it shipped (`version`), and every outcome beacon names the version the user acted
on (`outcome.version`). Both are the session's version number, so the view joins them exactly, within the session
and its source. Runs written before 2026-10-30 carry no version and are left out, and so are the versions of
sessions whose state is `active` (a line in the last 30 minutes): they may still be taken, so a version appears
once its session ended.

| Column | Meaning |
|---|---|
| `ts`, `source`, `session`, `spec_id`, `library`, `version` | The run that shipped the version, and its envelope |
| `versions_before` | The plots the session shipped before this one, across its libraries: its refinement rounds so far (`version` minus 1, since only a shipped run stores a version) |
| `base`, `status`, `shipped_score`, `round_scores`, `stages`, `rounds`, `shipped_round`, `attempts`, `reviewer_mode`, `plot_language` | The run, as `pipeline_runs` has it |
| `copies`, `downloads`, `feedback`, `reaction` | What the user did with this version: copies of the code or the image, downloads of the PNG, the code or the data, feedback sent on it, and the latest reaction |
| `taken`, `rejected`, `kept` | `taken`: copied or downloaded. `rejected`: a feedback on this version reacted `thumbs_down` or `bug`. `kept`: taken and not rejected |
| `s_plot_to_take`, `s_first_plot_to_take`, `s_first_plot_to_feedback` | Seconds to the first copy or download of this version from its own run, and from the session's first shipped plot; seconds to the first feedback on it from the session's first shipped plot. `NULL` when the user never did it |
| `session_state` | How the session ended: its `state` from the `sessions` view, never `active` here |

A version's `kept` differs from the session's `kept` in the `sessions` view: it judges one version, so a copy of
version 1 counts for version 1 even when the session went on to version 2. A saved session and feedback on the chat
carry version 0 and belong to no version.

For example, to see the keep rate per score bucket and library over the last 30 days of live use:

```sql
SELECT
  library,
  IFNULL(shipped_score, 'unscored') AS score,
  COUNT(*) AS versions,
  COUNTIF(kept) AS kept,
  ROUND(SAFE_DIVIDE(COUNTIF(kept), COUNT(*)), 2) AS keep_rate,
  APPROX_QUANTILES(s_first_plot_to_take, 2)[OFFSET(1)] AS median_s_to_take,
  ROUND(AVG(versions_before), 1) AS avg_versions_before
FROM `anyplot.agent_telemetry.score_outcomes`
WHERE source = 'live'
  AND ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY library, score
ORDER BY library, score;
```

The counts stay small for months on live traffic. Read a rate with its count, and compare libraries on the eval
matrix rather than on a handful of sessions.

## Set up the BigQuery side

Run these steps once, as a project owner. They write nothing but the resources named.

1. Create the log bucket:

   ```bash
   gcloud logging buckets create agent-telemetry --project=anyplot --location=europe-west4 \
     --retention-days=180 --enable-analytics \
     --description="Content-free usage telemetry of the agent chat (docs/reference/agent-telemetry.md)"
   ```

2. Create the sink:

   ```bash
   gcloud logging sinks create agent-telemetry \
     logging.googleapis.com/projects/anyplot/locations/europe-west4/buckets/agent-telemetry \
     --project=anyplot \
     --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="anyplot-agents" AND jsonPayload.log_type="agent_telemetry"'
   ```

   A sink into a log bucket of the same project needs no grant for its writer identity.

3. Keep the lines out of the `_Default` bucket:

   ```bash
   gcloud logging sinks update _Default --project=anyplot \
     --add-exclusion=name=agent-telemetry,filter='resource.type="cloud_run_revision" AND resource.labels.service_name="anyplot-agents" AND jsonPayload.log_type="agent_telemetry"'
   ```

   Run it after step 2: an exclusion on `_Default` does not affect the `agent-telemetry` sink.

4. Link the bucket to BigQuery:

   ```bash
   gcloud logging links create agent_telemetry_logs --bucket=agent-telemetry \
     --location=europe-west4 --project=anyplot
   ```

5. Create the views dataset in the same location:

   ```bash
   bq --location=europe-west4 mk --dataset \
     --description="Views over the agent usage telemetry (agents/telemetry/views)" anyplot:agent_telemetry
   ```

6. Create the views, in file order, from the repository root:

   ```bash
   for file in agents/telemetry/views/0*.sql; do
     bq query --project_id=anyplot --location=europe-west4 --use_legacy_sql=false < "$file"
   done
   ```

   Run this step again after a change to the views merges: each statement replaces its view
   (`CREATE OR REPLACE VIEW`), and the lines in the bucket stay as they are.

7. Let the API read them. Find the API's runtime identity:

   ```bash
   gcloud run services describe anyplot-api --region=europe-west4 \
     --format='value(spec.template.spec.serviceAccountName)'
   ```

   Since 2026-11-02 that is `anyplot-api@anyplot.iam.gserviceaccount.com`, which already holds the grants of
   steps 8 and 9. An empty answer would mean the Compute Engine default service account,
   `239660669828-compute@developer.gserviceaccount.com`, the identity before that day.

8. Grant that identity `roles/bigquery.jobUser` on the project:

   ```bash
   gcloud projects add-iam-policy-binding anyplot \
     --member=serviceAccount:API_SERVICE_ACCOUNT --role=roles/bigquery.jobUser
   ```

9. Give it read access on both datasets: the views read the linked dataset with the caller's rights. In the
   console, open each dataset (`agent_telemetry`, `agent_telemetry_logs`) and choose **Sharing >
   Permissions > Add principal** with `roles/bigquery.dataViewer`. On the command line,
   `bq add-iam-policy-binding` answers "This feature requires allowlisting" for datasets (bq 2.1.39), so add
   a `READER` entry to each dataset's access list instead:

   1. Save the dataset's access list:

      ```bash
      bq show --format=prettyjson anyplot:agent_telemetry > agent_telemetry.json
      ```

   2. Append `{"role": "READER", "userByEmail": "API_SERVICE_ACCOUNT"}` to its `access` array and keep only
      that key: `{"access": [...]}`.
   3. Write it back:

      ```bash
      bq update --source agent_telemetry.json anyplot:agent_telemetry
      ```

   4. Repeat for `agent_telemetry_logs`.

10. Point the API at the views through the deploy pipeline, like `_AGENT_SERVICE_URL`: set the
    `_AGENT_TELEMETRY_DATASET` substitution on the `deploy-api` trigger. The pipeline writes the variable on
    every deploy, smoke-tests the new revision and moves the pinned traffic to it; a
    `gcloud run services update` would create a revision that serves no traffic and that the next deploy
    overwrites.

    ```bash
    gcloud builds triggers update github deploy-api --region=europe-west4 \
      --update-substitutions=_AGENT_TELEMETRY_DATASET=anyplot.agent_telemetry
    ```

    The setting takes effect with the next API deploy; run the trigger by hand if you want it at once
    (`gcloud builds triggers run deploy-api --region=europe-west4 --branch=main`).

11. Connect Looker Studio to the `anyplot.agent_telemetry` views with your own account, which needs the same
    two roles.

## The /debug card

The admin page `/debug` shows an "agent usage" card for the last 7 or 30 days: sessions, plots shipped,
the kept rate (`kept` sessions as the `sessions` view defines them, among the sessions with a shipped plot),
the repair rate (runs that needed more than one round), each with the counts behind it ("5 of 12"), and the
five most frequent specs, input formats and refusal codes.
It reads `GET /debug/agent-usage?days=7|30` (`api/agent_usage.py`). The API needs the linked log dataset to
be named like the views dataset plus `_logs` (`anyplot.agent_telemetry_logs` for
`AGENT_TELEMETRY_DATASET=anyplot.agent_telemetry`), because it queries the log view `_AllLogs` directly: it
filters `timestamp` to the window before it deduplicates, so a load scans the window's partitions only and
never the whole 180 days, which the `events` view, deduplicated over the whole bucket, cannot avoid. The
window starts at the current time floored to 10 minutes, passed as a query parameter, so repeated loads send
the same query and BigQuery may answer from its result cache; on top of that the API keeps each answer for 10
minutes, so reloading `/debug` runs no query at all. The answer holds aggregates only. `status` is
`not_configured` while the variable is unset, and `unavailable` when the query fails (no table yet, no
permission, a timeout); both come with zeros, the card shows its empty state, and a failure is never kept.

Below the tiles the card shows two views of the day that do not follow the 7 or 30 days toggle.

### Per day

A table of the last 14 UTC days, newest first, reads `GET /debug/agent-usage/daily` (`daily_sql` and `read_daily`
in `api/agent_usage.py`). A day without a line shows zeros.

| Column | What it counts |
|---|---|
| new chats | Live sessions whose first line falls on that day. A chat that was opened and never sent anything wrote no line and does not count. |
| plots | `pipeline_run` lines with the status `ok` or `needs_attention`. |
| cost | Live `chat_turn` steps and `data_input` judge calls, priced as `agents/telemetry/views/05_prices_cost.sql` prices them, from the views dataset's `model_prices`. `pipeline_run.steps` repeats its turn's tokens and is left out. A `+` means a step's model has no price row, so the sum is too low; the cell's tooltip says how many steps. |
| fan-out | The same cost for `source = 'fanout'` sessions. |
| limit hits | The counts of `service_paused`, `budget`, `daily_limit`, `rate_limited`, `run_limit` and `capacity`, from a `chat_turn`'s `refusal` or `error` and a `data_input`'s `outcome`. |
| p95 queue wait | The 95th percentile of `queue_wait_ms` on live `pipeline_run` lines, read from the line itself rather than the `pipeline_runs` view, so it fills from the deploy that writes the field. It reads `—` on a day whose runs do not carry the field. |

`locked_out` is a safety lockout, not a usage limit, so it stays in the card's refusal list and out of this column.
`service_paused` exists since 2026-11-02. Before that, a spent service budget read `budget` in a turn and
`daily_limit` in a paste, so those two columns hold both causes on older days.

Which lines count depends on their `source`:

- `live` lines fill every column.
- `fanout` lines fill the `fan-out` column only.
- `harness` lines are never read.

The query keeps the card's scan rules: it filters `timestamp` before it deduplicates, and the API keeps each answer
for 10 minutes. Its window is floored to the day instead of to 10 minutes, because the table's oldest row has to be
a whole day: it starts at 00:00 UTC 13 days ago, so the query text and its parameter stay the same all day. It also
reads the 2 days before the window, only to find each chat's first line, so a chat that began before the window is
not new on the window's first day. `model_prices` is a literal `UNNEST`, so the join reads no bytes.

### Today, live

The line above the table comes from the agents service's memory, not from BigQuery, through
`GET /debug/agent/budget`. It shows the service's spend against `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` and how many
users are at their own limits, counts only, never an id. An admin counts only at the limits that bind every tier:
the pastes, the conversions and the strikes. The line says since when it counts, because a redeploy or
a scale-to-zero starts the usage book again at zero: `since` is 00:00 UTC, or the instance's start if that came
later. A cold agents service also starts at the moment the page asks, so right after one the line reads zero.

The dollar amounts are the weighted tokens at the main model's uncached input list price in the service's location,
so they carry `eu`'s 10 %: 100 M weighted tokens of Claude Haiku 5.5 read `$11.00`, not `$10.00`. Both the spend and
the budget use the same price, so the share is exact. The per-day table's cost comes from the telemetry's model and
token counts instead, so the two can differ for today.

## On the legal page

The telemetry is content-free and keyed by a salted, per-instance session hash, but it is still a record of
use. The privacy section of the legal page (`app/src/pages/LegalPage.tsx`, "data assistant (preview)")
describes it: the purpose, the fields in plain words, that no content is recorded, the 180-day retention,
the EU location, and that it is pseudonymous rather than anonymous. The section describes the chat as a
preview that only admins can open, so it stays true when the chat opens. If you change a field, the
retention or the location here, update that section too; `app/src/pages/LegalPage.test.tsx` pins its claims.
