-- One row per shipped plot version: the run that made it (spec, library, its review score, its rounds and the stage
-- that ended each attempt) beside what the user did with exactly that version, and when. Run after 03_sessions.sql.
--
-- The join is exact: `pipeline_runs.version` is the session's number of the version the run shipped (since
-- 2026-10-30), and `outcomes.version` is the number the page sends with every beacon about that version. The numbers
-- count every plot the session shipped, across its libraries, so `versions_before` (the number minus one) is how many
-- plots the session shipped before this one: its refinement rounds so far. A run written before 2026-10-30 carries no
-- version and is left out.
--
-- `taken` is true when the user copied or downloaded this version (`copied_code`, `copied_image`, `downloaded_png`,
-- `downloaded_code`, `downloaded_data`); `rejected` when a feedback on this version reacted `thumbs_down` or `bug`;
-- `kept` is taken and not rejected. Unlike the session's `kept` (03_sessions.sql), it judges one version: a copy of
-- version 1 counts for version 1 even when the session went on to version 2. A saved session and a feedback on the
-- chat carry version 0 and belong to no version. `reaction` is the latest reaction on this version. The seconds run
-- to the first take-away (and the first feedback) from this version's run and from the session's first shipped plot.
-- The view leaves out sessions whose state is `active` (03_sessions.sql: a line in the last 30 minutes), whose
-- versions may still be taken: a version shows up once its session ended. `session_state` is how it ended.
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.score_outcomes` AS
WITH firsts AS (
  SELECT session, source, MIN(ts) AS first_shipped_at
  FROM `anyplot.agent_telemetry.pipeline_runs`
  WHERE shipped
  GROUP BY session, source
),
shipped AS (
  SELECT
    ts, source, session, spec_id, library, version, base, status, shipped_score, round_scores, stages, rounds,
    shipped_round, attempts, reviewer_mode, plot_language
  FROM `anyplot.agent_telemetry.pipeline_runs`
  WHERE shipped AND version IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY session, source, version ORDER BY ts) = 1
),
acted AS (
  SELECT
    session,
    source,
    version,
    COUNTIF(action IN ('copied_code', 'copied_image')) AS copies,
    COUNTIF(action IN ('downloaded_png', 'downloaded_code', 'downloaded_data')) AS downloads,
    COUNTIF(action = 'feedback') AS feedback,
    COUNTIF(action = 'feedback' AND reaction IN ('thumbs_down', 'bug')) AS rejections,
    ARRAY_AGG(reaction IGNORE NULLS ORDER BY ts DESC LIMIT 1)[SAFE_OFFSET(0)] AS reaction,
    MIN(IF(keeps AND action != 'saved_session', ts, NULL)) AS first_taken_at,
    MIN(IF(action = 'feedback', ts, NULL)) AS first_feedback_at
  FROM `anyplot.agent_telemetry.outcomes`
  WHERE version > 0
  GROUP BY session, source, version
)
SELECT
  shipped.ts,
  shipped.source,
  shipped.session,
  shipped.spec_id,
  shipped.library,
  shipped.version,
  shipped.version - 1 AS versions_before,
  shipped.base,
  shipped.status,
  shipped.shipped_score,
  shipped.round_scores,
  shipped.stages,
  shipped.rounds,
  shipped.shipped_round,
  shipped.attempts,
  shipped.reviewer_mode,
  shipped.plot_language,
  IFNULL(acted.copies, 0) AS copies,
  IFNULL(acted.downloads, 0) AS downloads,
  IFNULL(acted.feedback, 0) AS feedback,
  acted.reaction,
  IFNULL(acted.copies, 0) + IFNULL(acted.downloads, 0) > 0 AS taken,
  IFNULL(acted.rejections, 0) > 0 AS rejected,
  IFNULL(acted.copies, 0) + IFNULL(acted.downloads, 0) > 0 AND IFNULL(acted.rejections, 0) = 0 AS kept,
  TIMESTAMP_DIFF(acted.first_taken_at, shipped.ts, SECOND) AS s_plot_to_take,
  TIMESTAMP_DIFF(acted.first_taken_at, firsts.first_shipped_at, SECOND) AS s_first_plot_to_take,
  TIMESTAMP_DIFF(acted.first_feedback_at, firsts.first_shipped_at, SECOND) AS s_first_plot_to_feedback,
  sessions.state AS session_state
FROM shipped
JOIN firsts
  ON firsts.session = shipped.session AND firsts.source = shipped.source
LEFT JOIN acted
  ON acted.session = shipped.session AND acted.source = shipped.source AND acted.version = shipped.version
JOIN `anyplot.agent_telemetry.sessions` AS sessions
  ON sessions.session = shipped.session AND sessions.source = shipped.source
WHERE sessions.state != 'active';
