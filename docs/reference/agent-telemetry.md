# Agent usage telemetry

> **Status (2026-10-30):** the agents service writes the four events, the BFF forwards the page's outcome
> beacon, and the BigQuery side is set up: the views hold lines since 2026-10-16. The fields added on 2026-10-30
> (see [Fields added on 2026-10-30](#fields-added-on-2026-10-30)) are written once the agents service is
> deployed, and reach the typed views after you create the views again (step 6 of
> [Set up the BigQuery side](#set-up-the-bigquery-side)).

The admin-only agent chat ("Use with my data") records how it is used, without recording what anyone
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
| `chat_turn` | A `/messages` turn ends, refused ones included; `manual_binding_changed` counts only a `PUT /bindings` whose bindings differ from the ones the session held, because the page echoes the parse's defaults after every paste | `kind` (`plot`, `prep`, `formula`, `code`, `talk`, `refused`, `error`), `action`, `asked_question`, `tools`, `prep_ops`, `undo`, `to_long`, `manual_binding_changed`, `binding_warnings`, `refusal`, `error`, `reply_reasked`, `language_source` and `plot_language` (both as the turn left them), `steps` (calls, tokens, thinking tokens and model per agent), `latency_ms` |
| `pipeline_run` | A `plot_pipeline` run ends, or the root asked for one before the data was ready (`status: not_ready` with its reason) | `run_index` (1 is the session's first plot), `base`, `status`, `reason`, `stage`, `stages`, `attempts`, `rounds`, `round_scores`, `score_round1`, `score_round2` (buckets), `shipped_attempt`, `version` (the shipped version's number, which `outcome.version` names), `shipped_score`, `forced_repair`, `gates_failed`, `reviewer_defects`, `residual_defects`, `sandbox_failures` (`syntax`, `name`, `key`, `value`, `type`, `timeout`, `memory`, `other`), `drift_restored` (true when a plan that only changed the protected theme statements had them restored after the round's check retry), `plot_language`, `readiness`, `loader_notes`, `edit_failures`, `validator_rules`, `adaptation_rules`, the pipeline configuration and prompt hashes, time per stage, `steps` |
| `outcome` | The page's beacon after a copy, a download, a session save, or a feedback send | `action` (`copied_code`, `copied_image`, `downloaded_png`, `downloaded_code`, `downloaded_data`, `saved_session`, `feedback`), `version`, `reaction` |

Every line carries the same envelope:

| Field | Meaning |
|---|---|
| `log_type` | Always `agent_telemetry`: the sink selects on it |
| `schema` | The line format's version, `1`. A renamed or removed field is a new schema; an added field is not |
| `event` | One of the four events |
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

### No user id

The attribution lines (one per plugin hook, for debugging) carry the HMAC user id for the rate limits and
the security review. The telemetry lines never do: they come from a different logger, and the sink filter
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
per library, replays the upload in each and runs `create_plot` in each. None of these sessions ever keeps a plot,
so counted as `live` they would multiply sessions and data inputs and push the kept rate down. The page marks each
session it opens for the fan-out (`useAgentSession` with `fanout`, `POST /debug/agent/sessions` with
`source: "fanout"`), the BFF forwards the value, and the agents service accepts `fanout` only (any other value is
`422`). The service keeps the mark in session state (`anyplot.telemetry_source`), and every line of the session,
whatever its event, carries `source = "fanout"` instead of `live`. Every existing `source = 'live'` filter (the
`/debug` card, `api/agent_usage.py`) leaves them out, and the views keep them apart by `source`.

Only an admin can open the chat today, so the value labels the owner's own test sessions. Once the chat is
public, a user who sends the mark by hand only files their own lines as tests.

### Fields added on 2026-10-30

Schema 1 grows by optional fields only: a line written before 2026-10-30 lacks these fields, and the views read
them as `NULL` (unknown), not as an empty list or `false`. Every value comes from a closed set; an id the set does
not know yet becomes `other`, so a new rule never drops a line.

| Event | Field | Meaning |
|---|---|---|
| `chat_turn` | `plot_language` | The session language as the turn left it, as a code: `en`, `de`, `fr`, `es`, `it`, `pt`, `nl`, `pl`, `zh`, `vi`, `ru`, `ja` (the languages `agents/anyplot/language.py` names in `ENGLISH_NAMES`), and `other` for every other language. The session language itself is free text (`Swedish`), and a rare language could single a user out, so it never reaches a line |
| `chat_turn` | `language_source` | Since 2026-10-30 read after the turn's run, like `plot_language`: the turn whose message the scope judge detected, or that called `set_language`, records the new value. Before, it recorded the value from before the turn |
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
| `02_event_views.sql` | `data_inputs`, `chat_turns`, `pipeline_runs`, `outcomes` | One typed column per field, `NULL` where a line predates the field; `pipeline_runs` also has `adapter_truncations`, the count of `adapter_truncated` in `stages` |
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
and its source. Runs written before 2026-10-30 carry no version and are left out.

| Column | Meaning |
|---|---|
| `ts`, `source`, `session`, `spec_id`, `library`, `version` | The run that shipped the version, and its envelope |
| `versions_before` | The plots the session shipped before this one, across its libraries: its refinement rounds so far (`version` minus 1, since only a shipped run stores a version) |
| `base`, `status`, `shipped_score`, `round_scores`, `stages`, `rounds`, `shipped_round`, `attempts`, `reviewer_mode`, `plot_language` | The run, as `pipeline_runs` has it |
| `copies`, `downloads`, `feedback`, `reaction` | What the user did with this version: copies of the code or the image, downloads of the PNG, the code or the data, feedback sent on it, and the latest reaction |
| `taken`, `rejected`, `kept` | `taken`: copied or downloaded. `rejected`: a feedback on this version reacted `thumbs_down` or `bug`. `kept`: taken and not rejected |
| `s_plot_to_take`, `s_first_plot_to_take`, `s_first_plot_to_feedback` | Seconds to the first copy or download of this version from its own run, and from the session's first shipped plot; seconds to the first feedback on it from the session's first shipped plot. `NULL` when the user never did it |
| `session_state` | The session's `state` from the `sessions` view |

A version's `kept` differs from the session's `kept` in the `sessions` view: it judges one version, so a copy of
version 1 counts for version 1 even when the session went on to version 2. A saved session and feedback on the chat
carry version 0 and belong to no version. Leave out sessions whose state is `active`: their versions may still be
taken.

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
  AND session_state != 'active'
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

   An empty answer means the Compute Engine default service account,
   `239660669828-compute@developer.gserviceaccount.com`.

8. Grant that identity `roles/bigquery.jobUser` on the project:

   ```bash
   gcloud projects add-iam-policy-binding anyplot \
     --member=serviceAccount:API_SERVICE_ACCOUNT --role=roles/bigquery.jobUser
   ```

9. Grant it `roles/bigquery.dataViewer` on both datasets: the views read the linked dataset with the
   caller's rights. In the console, open each dataset (`agent_telemetry`, `agent_telemetry_logs`) and choose
   **Sharing > Permissions > Add principal**, or use `bq add-iam-policy-binding`:

   ```bash
   bq add-iam-policy-binding --member=serviceAccount:API_SERVICE_ACCOUNT \
     --role=roles/bigquery.dataViewer anyplot:agent_telemetry
   bq add-iam-policy-binding --member=serviceAccount:API_SERVICE_ACCOUNT \
     --role=roles/bigquery.dataViewer anyplot:agent_telemetry_logs
   ```

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

## On the legal page

The telemetry is content-free and keyed by a salted, per-instance session hash, but it is still a record of
use. The privacy section of the legal page (`app/src/pages/LegalPage.tsx`, "data assistant (preview)")
describes it: the purpose, the fields in plain words, that no content is recorded, the 180-day retention,
the EU location, and that it is pseudonymous rather than anonymous. The section describes the chat as a
preview that only admins can open, so it stays true when the chat opens. If you change a field, the
retention or the location here, update that section too; `app/src/pages/LegalPage.test.tsx` pins its claims.
