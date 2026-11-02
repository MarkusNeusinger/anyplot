-- Typed views of the four telemetry events, one column per field of `agents/anyplot/telemetry.py`.
-- Run after 01_events.sql. Each statement is its own view; `bq query` runs the script as one job.
--
-- A field added to a line later (schema 1 grows by optional fields only) reads NULL on the lines written before it:
-- unknown, not "none" or false. Only a field whose absence has one meaning gets a default here (`drift_restored`:
-- no restore). The fields of 2026-10-30 (`plot_language`, `stages`, `round_scores`, `version`, `shipped_score`,
-- `readiness`, `loader_notes`, `edit_failures`, `validator_rules`, `adaptation_rules`, the pipeline configuration and
-- prompt hashes, and `thoughts` in `steps`) are NULL before that day, and so are the fields of 2026-11-01 (`lane`,
-- `queue_wait_ms`, `queue_position`, `user_runs_today`, `user_tokens_today` in `pipeline_runs`).

CREATE OR REPLACE VIEW `anyplot.agent_telemetry.data_inputs` AS
SELECT
  ts, source, session, spec_id, library, turn, idempotency_key, revision,
  JSON_VALUE(payload.format) AS format,
  JSON_VALUE(payload.entry) AS entry,
  JSON_VALUE(payload.outcome) AS outcome,
  JSON_VALUE(payload.cause) AS cause,
  JSON_VALUE(payload.size_bucket) AS size_bucket,
  JSON_VALUE(payload.rows_bucket) AS rows_bucket,
  JSON_VALUE(payload.cols_bucket) AS cols_bucket,
  LAX_INT64(payload.numeric_cols) AS numeric_cols,
  LAX_INT64(payload.integer_cols) AS integer_cols,
  LAX_INT64(payload.datetime_cols) AS datetime_cols,
  LAX_INT64(payload.text_cols) AS text_cols,
  LAX_INT64(payload.boolean_cols) AS boolean_cols,
  JSON_VALUE(payload.max_categories_bucket) AS max_categories_bucket,
  JSON_VALUE(payload.missing_bucket) AS missing_bucket,
  JSON_VALUE_ARRAY(payload.warnings) AS warnings,
  LAX_INT64(payload.tables) AS tables,
  LAX_INT64(payload.sheets) AS sheets,
  LAX_BOOL(payload.notes) AS notes,
  LAX_BOOL(payload.file_name) AS has_file_name,
  JSON_VALUE(payload.spec_fit) AS spec_fit,
  LAX_INT64(payload.judge_input) AS judge_input,
  LAX_INT64(payload.judge_output) AS judge_output,
  JSON_VALUE(payload.judge_model) AS judge_model,
  LAX_INT64(payload.latency_ms) AS latency_ms
FROM `anyplot.agent_telemetry.events`
WHERE event = 'data_input';

CREATE OR REPLACE VIEW `anyplot.agent_telemetry.chat_turns` AS
SELECT
  ts, source, session, spec_id, library, turn, idempotency_key, revision,
  JSON_VALUE(payload.kind) AS kind,
  JSON_VALUE(payload.action) AS action,
  LAX_BOOL(payload.asked_question) AS asked_question,
  JSON_VALUE_ARRAY(payload.tools) AS tools,
  JSON_VALUE_ARRAY(payload.prep_ops) AS prep_ops,
  LAX_INT64(payload.prep_calls) AS prep_calls,
  LAX_BOOL(payload.undo) AS undo,
  LAX_BOOL(payload.to_long) AS to_long,
  LAX_BOOL(payload.manual_binding_changed) AS manual_binding_changed,
  JSON_VALUE_ARRAY(payload.binding_warnings) AS binding_warnings,
  JSON_VALUE(payload.refusal) AS refusal,
  JSON_VALUE(payload.error) AS error,
  LAX_BOOL(payload.reply_reasked) AS reply_reasked,
  JSON_VALUE(payload.language_source) AS language_source,
  JSON_VALUE(payload.plot_language) AS plot_language,
  LAX_INT64(payload.llm_calls) AS llm_calls,
  payload.steps AS steps,
  LAX_INT64(payload.latency_ms) AS latency_ms
FROM `anyplot.agent_telemetry.events`
WHERE event = 'chat_turn';

CREATE OR REPLACE VIEW `anyplot.agent_telemetry.pipeline_runs` AS
SELECT
  ts, source, session, spec_id, library, turn, idempotency_key, revision,
  LAX_INT64(payload.run_index) AS run_index,
  JSON_VALUE(payload.base) AS base,
  JSON_VALUE(payload.status) AS status,
  JSON_VALUE(payload.reason) AS reason,
  JSON_VALUE(payload.stage) AS stage,
  LAX_INT64(payload.attempts) AS attempts,
  LAX_INT64(payload.rounds) AS rounds,
  LAX_INT64(payload.reviews) AS reviews,
  JSON_VALUE(payload.score_round1) AS score_round1,
  JSON_VALUE(payload.score_round2) AS score_round2,
  LAX_INT64(payload.shipped_attempt) AS shipped_attempt,
  LAX_INT64(payload.shipped_round) AS shipped_round,
  -- The session's number of the shipped version, the one `outcomes.version` names (`score_outcomes` joins them).
  LAX_INT64(payload.version) AS version,
  JSON_VALUE(payload.shipped_score) AS shipped_score,
  JSON_VALUE_ARRAY(payload.forced_repair) AS forced_repair,
  JSON_VALUE_ARRAY(payload.gates_failed) AS gates_failed,
  JSON_VALUE_ARRAY(payload.reviewer_defects) AS reviewer_defects,
  JSON_VALUE_ARRAY(payload.residual_defects) AS residual_defects,
  JSON_VALUE_ARRAY(payload.sandbox_failures) AS sandbox_failures,
  IFNULL(LAX_BOOL(payload.drift_restored), FALSE) AS drift_restored,
  -- The stage that ended each attempt, in order; `adapter_truncations` counts the answers cut off at the output limit.
  JSON_VALUE_ARRAY(payload.stages) AS stages,
  IF(
    payload.stages IS NULL,
    NULL,
    (SELECT COUNTIF(stage = 'adapter_truncated') FROM UNNEST(JSON_VALUE_ARRAY(payload.stages)) AS stage)
  ) AS adapter_truncations,
  -- Position n is round n; `unscored` for a round without a review score.
  JSON_VALUE_ARRAY(payload.round_scores) AS round_scores,
  JSON_VALUE(payload.plot_language) AS plot_language,
  JSON_VALUE(payload.readiness) AS readiness,
  JSON_VALUE_ARRAY(payload.loader_notes) AS loader_notes,
  JSON_VALUE_ARRAY(payload.edit_failures) AS edit_failures,
  JSON_VALUE_ARRAY(payload.validator_rules) AS validator_rules,
  JSON_VALUE_ARRAY(payload.adaptation_rules) AS adaptation_rules,
  JSON_VALUE(payload.reviewer_mode) AS reviewer_mode,
  LAX_BOOL(payload.ship_best) AS ship_best,
  LAX_BOOL(payload.self_review) AS self_review,
  LAX_BOOL(payload.repair_self_review) AS repair_self_review,
  JSON_VALUE(payload.adapter_prompt) AS adapter_prompt,
  JSON_VALUE(payload.reviewer_prompt) AS reviewer_prompt,
  LAX_INT64(payload.adapt_ms) AS adapt_ms,
  LAX_INT64(payload.check_ms) AS check_ms,
  LAX_INT64(payload.render_ms) AS render_ms,
  LAX_INT64(payload.review_ms) AS review_ms,
  LAX_INT64(payload.total_ms) AS total_ms,
  payload.steps AS steps,
  -- Whether anyone waits long or comes close to a limit, without saying who (2026-11-01): the tier, the run
  -- queue's wait and position at submit (0: it started at once), and buckets of the user's runs and spent token
  -- budget of the day. NULL for a `not_ready` run, which never enters the queue, and before that day.
  JSON_VALUE(payload.lane) AS lane,
  LAX_INT64(payload.queue_wait_ms) AS queue_wait_ms,
  LAX_INT64(payload.queue_position) AS queue_position,
  JSON_VALUE(payload.user_runs_today) AS user_runs_today,
  JSON_VALUE(payload.user_tokens_today) AS user_tokens_today,
  JSON_VALUE(payload.status) IN ('ok', 'needs_attention') AS shipped
FROM `anyplot.agent_telemetry.events`
WHERE event = 'pipeline_run';

CREATE OR REPLACE VIEW `anyplot.agent_telemetry.outcomes` AS
SELECT
  ts, source, session, spec_id, library, turn, idempotency_key, revision,
  JSON_VALUE(payload.action) AS action,
  LAX_INT64(payload.version) AS version,
  JSON_VALUE(payload.reaction) AS reaction,
  JSON_VALUE(payload.action) IN (
    'copied_code', 'copied_image', 'downloaded_png', 'downloaded_code', 'downloaded_page', 'downloaded_data',
    'saved_session'
  ) AS keeps
FROM `anyplot.agent_telemetry.events`
WHERE event = 'outcome';
