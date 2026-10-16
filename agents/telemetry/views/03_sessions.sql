-- One row per chat session (salted session hash and source): its funnel, its plots and how it ended.
-- Run after 02_event_views.sql.
--
-- `funnel_last_step` is the furthest step the session reached:
--   outcome_only           only outcome beacons (feedback on a chat, a save) and no input, turn or run
--   data_refused           every data input was refused or failed
--   transcription_offered  free text was read as a table, and the user never confirmed it
--   data_ok                a dataset was stored
--   chatted                a chat turn ran
--   plot_not_ready         a plot was asked for before the data was confirmed, and none started
--   plot_run               a pipeline run started (`not_ready` ones are not runs here)
--   plot_shipped           a pipeline run shipped a plot (status ok or needs_attention)
--   kept                   the user copied or downloaded a result or saved the session
-- A session that never sent a data input, a turn or a beacon writes no line, so the funnel starts there.
-- A transcription writes two data_input rows (the offer, outcome `transcribed`, and the confirmed paste);
-- `data_inputs` counts the input once, without the offer.
--
-- `state` applies a 30-minute inactivity rule: a session whose last line is younger than 30 minutes is
-- `active`; any other session ended, as
--   kept                   the user kept a result (copied, downloaded or saved)
--   refined                no keep, but two or more shipped plots (the user iterated on a result)
--   abandoned_after_plot   a shipped plot, no keep and no refinement
--   abandoned_before_plot  no shipped plot
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.sessions` AS
WITH lines AS (
  SELECT session, source, ts, spec_id, library FROM `anyplot.agent_telemetry.events`
),
spans AS (
  SELECT
    session,
    source,
    MIN(ts) AS first_at,
    MAX(ts) AS last_at,
    ARRAY_AGG(spec_id IGNORE NULLS ORDER BY ts LIMIT 1)[SAFE_OFFSET(0)] AS spec_id,
    ARRAY_AGG(library IGNORE NULLS ORDER BY ts LIMIT 1)[SAFE_OFFSET(0)] AS first_library,
    COUNT(DISTINCT library) AS libraries
  FROM lines
  GROUP BY session, source
),
inputs AS (
  SELECT
    session,
    source,
    COUNTIF(outcome != 'transcribed') AS data_inputs,
    COUNTIF(outcome = 'ok') AS data_ok,
    COUNTIF(outcome = 'transcribed') AS transcriptions_offered,
    COUNTIF(outcome NOT IN ('ok', 'transcribed')) AS data_refused
  FROM `anyplot.agent_telemetry.data_inputs`
  GROUP BY session, source
),
turns AS (
  SELECT session, source, COUNT(*) AS turns, MAX(turn) AS last_turn
  FROM `anyplot.agent_telemetry.chat_turns`
  GROUP BY session, source
),
runs AS (
  SELECT
    session,
    source,
    COUNTIF(status != 'not_ready') AS runs,
    COUNTIF(status = 'not_ready') AS not_ready_runs,
    COUNTIF(shipped) AS plots_shipped,
    MIN(IF(shipped, turn, NULL)) AS first_plot_turn,
    COUNTIF(status != 'not_ready' AND rounds > 1) AS repaired_runs
  FROM `anyplot.agent_telemetry.pipeline_runs`
  GROUP BY session, source
),
kept AS (
  SELECT session, source, COUNTIF(keeps) AS keeps, COUNTIF(action = 'feedback') AS feedback
  FROM `anyplot.agent_telemetry.outcomes`
  GROUP BY session, source
)
SELECT
  spans.session,
  spans.source,
  spans.spec_id,
  spans.first_library AS library,
  spans.libraries,
  spans.first_at,
  spans.last_at,
  TIMESTAMP_DIFF(spans.last_at, spans.first_at, SECOND) AS duration_s,
  IFNULL(inputs.data_inputs, 0) AS data_inputs,
  IFNULL(inputs.data_ok, 0) AS data_ok,
  IFNULL(inputs.transcriptions_offered, 0) AS transcriptions_offered,
  IFNULL(turns.turns, 0) AS turns,
  IFNULL(runs.runs, 0) AS runs,
  IFNULL(runs.not_ready_runs, 0) AS not_ready_runs,
  IFNULL(runs.plots_shipped, 0) AS plots_shipped,
  IFNULL(runs.repaired_runs, 0) AS repaired_runs,
  runs.first_plot_turn AS turns_to_first_plot,
  IFNULL(kept.keeps, 0) AS keeps,
  IFNULL(kept.feedback, 0) AS feedback,
  CASE
    WHEN IFNULL(kept.keeps, 0) > 0 THEN 'kept'
    WHEN IFNULL(runs.plots_shipped, 0) > 0 THEN 'plot_shipped'
    WHEN IFNULL(runs.runs, 0) > 0 THEN 'plot_run'
    WHEN IFNULL(runs.not_ready_runs, 0) > 0 THEN 'plot_not_ready'
    WHEN IFNULL(turns.turns, 0) > 0 THEN 'chatted'
    WHEN IFNULL(inputs.data_ok, 0) > 0 THEN 'data_ok'
    WHEN IFNULL(inputs.transcriptions_offered, 0) > 0 THEN 'transcription_offered'
    WHEN IFNULL(inputs.data_refused, 0) > 0 THEN 'data_refused'
    ELSE 'outcome_only'
  END AS funnel_last_step,
  CASE
    WHEN spans.last_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE) THEN 'active'
    WHEN IFNULL(kept.keeps, 0) > 0 THEN 'kept'
    WHEN IFNULL(runs.plots_shipped, 0) >= 2 THEN 'refined'
    WHEN IFNULL(runs.plots_shipped, 0) > 0 THEN 'abandoned_after_plot'
    ELSE 'abandoned_before_plot'
  END AS state
FROM spans
LEFT JOIN inputs USING (session, source)
LEFT JOIN turns USING (session, source)
LEFT JOIN runs USING (session, source)
LEFT JOIN kept USING (session, source);
