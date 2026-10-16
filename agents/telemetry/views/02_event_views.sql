-- Typed views of the four telemetry events, one column per field of `agents/anyplot/telemetry.py`.
-- Run after 01_events.sql. Each statement is its own view; `bq query` runs the script as one job.

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
  JSON_VALUE_ARRAY(payload.forced_repair) AS forced_repair,
  JSON_VALUE_ARRAY(payload.gates_failed) AS gates_failed,
  JSON_VALUE_ARRAY(payload.reviewer_defects) AS reviewer_defects,
  JSON_VALUE_ARRAY(payload.residual_defects) AS residual_defects,
  JSON_VALUE_ARRAY(payload.sandbox_failures) AS sandbox_failures,
  IFNULL(LAX_BOOL(payload.drift_restored), FALSE) AS drift_restored,
  LAX_INT64(payload.adapt_ms) AS adapt_ms,
  LAX_INT64(payload.check_ms) AS check_ms,
  LAX_INT64(payload.render_ms) AS render_ms,
  LAX_INT64(payload.review_ms) AS review_ms,
  LAX_INT64(payload.total_ms) AS total_ms,
  payload.steps AS steps,
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
    'copied_code', 'copied_image', 'downloaded_png', 'downloaded_code', 'downloaded_data', 'saved_session'
  ) AS keeps
FROM `anyplot.agent_telemetry.events`
WHERE event = 'outcome';
