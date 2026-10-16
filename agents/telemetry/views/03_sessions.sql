-- One row per chat session (salted session hash and source): its funnel, its plots and how it ended.
-- Run after 02_event_views.sql.
--
-- `kept` (owner rule of 2026-10-16) is true when the user took a result away and was content with it:
--   * after the session's last pipeline run (so after its last shipped plot, and with no plot turn after it),
--     at least one of copied_code, copied_image, downloaded_png, downloaded_code, downloaded_data, and
--   * no `feedback` outcome with the reaction thumbs_down or bug anywhere in the session.
-- Saving the session (`saved_session`) is never a keep: users also save a session to report a plot they did not
-- like. `saves` counts the saves on their own, and a session whose only take-away is a save ends `saved`.
--
-- Examples (the run and outcome lines of one session, in time order, and the session's `kept`):
--   shipped, copied_code                                   true
--   shipped, copied_code, shipped                          false  (a plot turn after the keep)
--   shipped, copied_code, shipped, downloaded_png          true
--   shipped, copied_image, feedback thumbs_down            false  (state `rejected`)
--   shipped, feedback bug, downloaded_code                 false  (state `rejected`)
--   shipped, saved_session                                 false  (state `saved`)
--   shipped, feedback thumbs_up, saved_session             false  (state `saved`)
--   copied_code without any shipped plot                   false
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
--   kept                   `kept` above
-- A session that never sent a data input, a turn or a beacon writes no line, so the funnel starts there.
-- A transcription writes two data_input rows (the offer, outcome `transcribed`, and the confirmed paste);
-- `data_inputs` counts the input once, without the offer.
--
-- `state` applies a 30-minute inactivity rule: a session whose last line is younger than 30 minutes is
-- `active`; any other session ended, as
--   rejected               a feedback with thumbs_down or bug (whatever else the user did)
--   kept                   `kept` above
--   saved                  a saved session and no keep (neutral: neither kept nor abandoned)
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
    COUNTIF(status != 'not_ready' AND rounds > 1) AS repaired_runs,
    MAX(IF(status != 'not_ready', ts, NULL)) AS last_run_at
  FROM `anyplot.agent_telemetry.pipeline_runs`
  GROUP BY session, source
),
outcomes AS (
  SELECT
    session,
    source,
    COUNTIF(keeps AND action != 'saved_session') AS keeps,
    MAX(IF(keeps AND action != 'saved_session', ts, NULL)) AS last_keep_at,
    COUNTIF(action = 'saved_session') AS saves,
    COUNTIF(action = 'feedback') AS feedback,
    COUNTIF(action = 'feedback' AND reaction IN ('thumbs_down', 'bug')) AS rejections
  FROM `anyplot.agent_telemetry.outcomes`
  GROUP BY session, source
),
joined AS (
  SELECT
    spans.*,
    IFNULL(inputs.data_inputs, 0) AS data_inputs,
    IFNULL(inputs.data_ok, 0) AS data_ok,
    IFNULL(inputs.transcriptions_offered, 0) AS transcriptions_offered,
    IFNULL(inputs.data_refused, 0) AS data_refused,
    IFNULL(turns.turns, 0) AS turns,
    IFNULL(runs.runs, 0) AS runs,
    IFNULL(runs.not_ready_runs, 0) AS not_ready_runs,
    IFNULL(runs.plots_shipped, 0) AS plots_shipped,
    IFNULL(runs.repaired_runs, 0) AS repaired_runs,
    runs.first_plot_turn,
    IFNULL(outcomes.keeps, 0) AS keeps,
    IFNULL(outcomes.saves, 0) AS saves,
    IFNULL(outcomes.feedback, 0) AS feedback,
    IFNULL(outcomes.rejections, 0) AS rejections,
    (
      IFNULL(runs.plots_shipped, 0) > 0
      AND IFNULL(outcomes.rejections, 0) = 0
      AND outcomes.last_keep_at IS NOT NULL
      AND outcomes.last_keep_at > runs.last_run_at
    ) AS kept
  FROM spans
  LEFT JOIN inputs USING (session, source)
  LEFT JOIN turns USING (session, source)
  LEFT JOIN runs USING (session, source)
  LEFT JOIN outcomes USING (session, source)
)
SELECT
  session,
  source,
  spec_id,
  first_library AS library,
  libraries,
  first_at,
  last_at,
  TIMESTAMP_DIFF(last_at, first_at, SECOND) AS duration_s,
  data_inputs,
  data_ok,
  transcriptions_offered,
  turns,
  runs,
  not_ready_runs,
  plots_shipped,
  repaired_runs,
  first_plot_turn AS turns_to_first_plot,
  keeps,
  saves,
  feedback,
  rejections,
  kept,
  CASE
    WHEN kept THEN 'kept'
    WHEN plots_shipped > 0 THEN 'plot_shipped'
    WHEN runs > 0 THEN 'plot_run'
    WHEN not_ready_runs > 0 THEN 'plot_not_ready'
    WHEN turns > 0 THEN 'chatted'
    WHEN data_ok > 0 THEN 'data_ok'
    WHEN transcriptions_offered > 0 THEN 'transcription_offered'
    WHEN data_refused > 0 THEN 'data_refused'
    ELSE 'outcome_only'
  END AS funnel_last_step,
  CASE
    WHEN last_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE) THEN 'active'
    WHEN rejections > 0 THEN 'rejected'
    WHEN kept THEN 'kept'
    WHEN saves > 0 THEN 'saved'
    WHEN plots_shipped >= 2 THEN 'refined'
    WHEN plots_shipped > 0 THEN 'abandoned_after_plot'
    ELSE 'abandoned_before_plot'
  END AS state
FROM joined;
