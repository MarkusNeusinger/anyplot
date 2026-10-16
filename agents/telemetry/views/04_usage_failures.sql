-- Usage by spec, library and input format, and the failures by kind and code. Run after 03_sessions.sql.

-- One row per day, spec, library and input format: what was pasted, what ran, what shipped, what was kept.
-- `format` is the format of the session's stored data inputs on that day (`(none)` for sessions without one,
-- such as data computed in the chat from a formula or code).
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.usage` AS
WITH formats AS (
  SELECT DISTINCT DATE(ts) AS day, session, source, format
  FROM `anyplot.agent_telemetry.data_inputs`
  WHERE outcome = 'ok'
),
daily AS (
  SELECT
    DATE(ts) AS day,
    session,
    source,
    ANY_VALUE(spec_id) AS spec_id,
    ANY_VALUE(library) AS library,
    COUNTIF(event = 'data_input') AS data_inputs,
    COUNTIF(event = 'chat_turn') AS turns,
    COUNTIF(event = 'pipeline_run') AS runs,
    COUNTIF(event = 'pipeline_run' AND JSON_VALUE(payload.status) IN ('ok', 'needs_attention')) AS plots_shipped,
    COUNTIF(
      event = 'outcome'
      AND JSON_VALUE(payload.action) IN (
        'copied_code', 'copied_image', 'downloaded_png', 'downloaded_code', 'downloaded_data', 'saved_session'
      )
    ) AS keeps
  FROM `anyplot.agent_telemetry.events`
  GROUP BY day, session, source
)
SELECT
  daily.day,
  daily.source,
  daily.spec_id,
  daily.library,
  IFNULL(formats.format, '(none)') AS format,
  COUNT(DISTINCT daily.session) AS sessions,
  SUM(daily.data_inputs) AS data_inputs,
  SUM(daily.turns) AS turns,
  SUM(daily.runs) AS runs,
  SUM(daily.plots_shipped) AS plots_shipped,
  COUNT(DISTINCT IF(daily.keeps > 0, daily.session, NULL)) AS sessions_kept
FROM daily
LEFT JOIN formats USING (day, session, source)
GROUP BY day, source, spec_id, library, format;

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
