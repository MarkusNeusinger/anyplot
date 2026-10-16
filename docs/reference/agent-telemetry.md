# Agent usage telemetry

> **Status (2026-10-16):** the agents service writes the four events, the BFF forwards the page's outcome
> beacon, the views and the `/debug` card are in the repository. The log bucket, the sink, the linked dataset,
> the views dataset and the IAM grants are not created yet: run [Set up the BigQuery side](#set-up-the-bigquery-side)
> once. Until then the card shows `not configured`.

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
| `chat_turn` | A `/messages` turn ends, refused ones included; `manual_binding_changed` counts only a `PUT /bindings` whose bindings differ from the ones the session held, because the page echoes the parse's defaults after every paste | `kind` (`plot`, `prep`, `formula`, `code`, `talk`, `refused`, `error`), `action`, `asked_question`, `tools`, `prep_ops`, `undo`, `to_long`, `manual_binding_changed`, `binding_warnings`, `refusal`, `error`, `reply_reasked`, `language_source`, `steps` (calls, tokens and model per agent), `latency_ms` |
| `pipeline_run` | A `plot_pipeline` run ends, or the root asked for one before the data was ready (`status: not_ready` with its reason) | `run_index` (1 is the session's first plot), `base`, `status`, `reason`, `stage`, `attempts`, `rounds`, `score_round1`, `score_round2` (buckets), `shipped_attempt`, `forced_repair`, `gates_failed`, `reviewer_defects`, `residual_defects`, `sandbox_failures` (`syntax`, `name`, `key`, `value`, `type`, `timeout`, `memory`, `other`), time per stage, `steps` |
| `outcome` | The page's beacon after a copy, a download, a session save, or a feedback send | `action` (`copied_code`, `copied_image`, `downloaded_png`, `downloaded_code`, `downloaded_data`, `saved_session`, `feedback`), `version`, `reaction` |

Every line carries the same envelope:

| Field | Meaning |
|---|---|
| `log_type` | Always `agent_telemetry`: the sink selects on it |
| `schema` | The line format's version, `1`. A renamed or removed field is a new schema; an added field is not |
| `event` | One of the four events |
| `service`, `revision` | Cloud Run's `K_SERVICE` and `K_REVISION` |
| `source` | `live`, or `harness` for the eval harnesses (`agents/evals/matrix.py`, `agents/evals/prep.py`); the card counts `live` only |
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
| `02_event_views.sql` | `data_inputs`, `chat_turns`, `pipeline_runs`, `outcomes` | One typed column per field |
| `03_sessions.sql` | `sessions` | One row per session: data inputs, transcription offers, turns, runs, `not_ready` asks, shipped plots, `turns_to_first_plot`, keeps (copies and downloads), saves, feedback, rejections (feedback with `thumbs_down` or `bug`), `kept`, `funnel_last_step` (from `outcome_only` and `data_refused` through `transcription_offered`, `data_ok`, `chatted`, `plot_not_ready`, `plot_run` and `plot_shipped` to `kept`), and `state` under a 30-minute inactivity rule (`active`, `rejected`, `kept`, `saved`, `refined`, `abandoned_after_plot`, `abandoned_before_plot`). A session is `kept` when, after its last pipeline run, the user copied or downloaded a result (`copied_code`, `copied_image`, `downloaded_png`, `downloaded_code`, `downloaded_data`) and sent no feedback with `thumbs_down` or `bug`. A saved session is never a keep, because users also save a session to report a plot they did not like: a session whose only take-away is a save ends `saved`, and one with a `thumbs_down` or `bug` ends `rejected`. The view's header lists example sessions and how each is classified. A transcription writes two `data_input` rows, the offer (outcome `transcribed`) and the confirmed paste; every view counts the input once and the offers apart. `not_ready` runs are never counted as runs or in the repair rate |
| `04_usage_failures.sql` | `usage`, `input_formats`, `failures` | Usage by day, spec and library (each line under the library it was written under, so a library switch splits a session's runs correctly; `sessions_kept` counts the sessions the `sessions` view calls `kept`, so run it after `03_sessions.sql`); data inputs by format and entry, each input under its own format; one row per failure with its kind and closed code |
| `05_prices_cost.sql` | `model_prices`, `cost` | The `eu` list prices of `agents/evals/pricing.py` (a test keeps both equal) and the cost of every turn step and data-input judge call |

The cost view prices the `chat_turn` and `data_input` lines only: `pipeline_run.steps` repeats the adapter's
and the reviewer's share of its turn for per-run analysis.

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

## Before the chat opens to the public

The telemetry is content-free and keyed by a salted, per-instance session hash, but it is still a record of
use. Before real users reach the chat, the legal page (`app/src/pages/LegalPage.tsx`) needs an entry for it:
purpose (improving the chat), the fields in plain words, the 180-day retention, the EU location, and that
no content is recorded. The chat is admin-only on 2026-10-16, so the page stays unchanged for now.
