-- Usage by spec and library, the inputs by format, and the failures by kind and code. Run after 03_sessions.sql.

-- One row per day, spec and library: what was pasted, what ran, what shipped, what was kept. Every line carries
-- the library it was written under, so a session that switched from matplotlib to seaborn counts each library's
-- runs under that library (and is one session under each). `sessions_kept` counts each session the `sessions`
-- view calls `kept` (a copy or a download after the last run, no thumbs_down or bug; a saved session alone is no
-- keep) exactly once, under the day, spec and library of its LAST shipped run: the keep comes after that run, so
-- it is the plot the user took away (review of #12207: a superseded matplotlib copy and the final seaborn download
-- had counted the session under both libraries).
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.usage` AS
WITH base AS (
  SELECT
    DATE(ts) AS day,
    source,
    spec_id,
    library,
    COUNT(DISTINCT session) AS sessions,
    COUNTIF(event = 'data_input' AND JSON_VALUE(payload.outcome) != 'transcribed') AS data_inputs,
    COUNTIF(event = 'chat_turn') AS turns,
    COUNTIF(event = 'pipeline_run' AND JSON_VALUE(payload.status) != 'not_ready') AS runs,
    COUNTIF(event = 'pipeline_run' AND JSON_VALUE(payload.status) IN ('ok', 'needs_attention')) AS plots_shipped
  FROM `anyplot.agent_telemetry.events`
  GROUP BY day, source, spec_id, library
),
last_shipped AS (
  SELECT session, source, DATE(ts) AS day, spec_id, library
  FROM `anyplot.agent_telemetry.pipeline_runs`
  WHERE shipped
  QUALIFY ROW_NUMBER() OVER (PARTITION BY session, source ORDER BY ts DESC, idempotency_key DESC) = 1
),
kept AS (
  SELECT last_shipped.day, last_shipped.source, last_shipped.spec_id, last_shipped.library, COUNT(*) AS sessions_kept
  FROM last_shipped
  JOIN `anyplot.agent_telemetry.sessions` AS sessions
    ON sessions.session = last_shipped.session AND sessions.source = last_shipped.source
  WHERE sessions.kept
  GROUP BY 1, 2, 3, 4
)
SELECT base.*, IFNULL(kept.sessions_kept, 0) AS sessions_kept
FROM base
LEFT JOIN kept
  ON kept.day = base.day
  AND kept.source = base.source
  AND kept.spec_id IS NOT DISTINCT FROM base.spec_id
  AND kept.library IS NOT DISTINCT FROM base.library;

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
