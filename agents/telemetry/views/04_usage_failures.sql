-- Usage by spec and library, the inputs by format, and the failures by kind and code. Run after 03_sessions.sql.

-- One row per day, spec and library: what was pasted, what ran, what shipped, what was kept. Every line carries
-- the library it was written under, so a session that switched from matplotlib to seaborn counts each library's
-- runs under that library (and is one session under each). `sessions_kept` counts the sessions of the row whose
-- keep line falls on it and that the `sessions` view calls `kept` (a copy or a download after the last run, no
-- thumbs_down or bug; a saved session alone is no keep).
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.usage` AS
SELECT
  DATE(events.ts) AS day,
  events.source AS source,
  events.spec_id AS spec_id,
  events.library AS library,
  COUNT(DISTINCT events.session) AS sessions,
  COUNTIF(events.event = 'data_input' AND JSON_VALUE(events.payload.outcome) != 'transcribed') AS data_inputs,
  COUNTIF(events.event = 'chat_turn') AS turns,
  COUNTIF(events.event = 'pipeline_run' AND JSON_VALUE(events.payload.status) != 'not_ready') AS runs,
  COUNTIF(
    events.event = 'pipeline_run' AND JSON_VALUE(events.payload.status) IN ('ok', 'needs_attention')
  ) AS plots_shipped,
  COUNT(DISTINCT IF(
    events.event = 'outcome'
    AND JSON_VALUE(events.payload.action) IN (
      'copied_code', 'copied_image', 'downloaded_png', 'downloaded_code', 'downloaded_data'
    )
    AND sessions.kept,
    events.session,
    NULL
  )) AS sessions_kept
FROM `anyplot.agent_telemetry.events` AS events
LEFT JOIN `anyplot.agent_telemetry.sessions` AS sessions
  ON sessions.session = events.session AND sessions.source = events.source
GROUP BY 1, 2, 3, 4;

-- One row per day, spec, library and input format: the data inputs of that format and how they ended. Each
-- input counts under its own format only; the session totals live in `usage`, never copied onto every format.
-- A transcription writes two rows (the offer, outcome `transcribed`, then the confirmed paste): `inputs`
-- counts it once, and `transcriptions_offered` counts the offers.
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.input_formats` AS
SELECT
  DATE(ts) AS day,
  source,
  spec_id,
  library,
  format,
  entry,
  COUNTIF(outcome != 'transcribed') AS inputs,
  COUNTIF(outcome = 'transcribed') AS transcriptions_offered,
  COUNTIF(outcome = 'ok') AS stored,
  COUNTIF(outcome NOT IN ('ok', 'transcribed')) AS refused,
  COUNT(DISTINCT session) AS sessions
FROM `anyplot.agent_telemetry.data_inputs`
GROUP BY day, source, spec_id, library, format, entry;

-- One row per failure: a refused or failed data input, a refused or failed turn, a failed pipeline run, and
-- every sandbox failure class and failed gate of a run. `kind` says which, `code` the closed code.
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.failures` AS
SELECT ts, source, session, spec_id, library, 'data_input' AS kind, outcome AS code, cause AS detail
FROM `anyplot.agent_telemetry.data_inputs`
WHERE outcome NOT IN ('ok', 'transcribed')
UNION ALL
SELECT ts, source, session, spec_id, library, 'turn_refused', refusal, NULL
FROM `anyplot.agent_telemetry.chat_turns`
WHERE refusal IS NOT NULL
UNION ALL
SELECT ts, source, session, spec_id, library, 'turn_error', error, NULL
FROM `anyplot.agent_telemetry.chat_turns`
WHERE error IS NOT NULL
UNION ALL
SELECT ts, source, session, spec_id, library, 'run_failed', IFNULL(reason, status), stage
FROM `anyplot.agent_telemetry.pipeline_runs`
WHERE status IN ('failed', 'not_ready')
UNION ALL
SELECT ts, source, session, spec_id, library, 'sandbox', failure, NULL
FROM `anyplot.agent_telemetry.pipeline_runs`, UNNEST(sandbox_failures) AS failure
UNION ALL
SELECT ts, source, session, spec_id, library, 'gate', gate, NULL
FROM `anyplot.agent_telemetry.pipeline_runs`, UNNEST(gates_failed) AS gate;
