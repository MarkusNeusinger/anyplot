-- Model list prices and the cost of every turn and data input. Run after 04_usage_failures.sql.
--
-- `model_prices` holds USD per million tokens at the `eu` multi-region (the global list price plus 10 %), as
-- `agents/evals/pricing.py` records them (2026-10-10); `tests/unit/agents/evals/test_telemetry_prices.py` fails
-- when the two disagree, so a price change there names this file. List price, never a promotion; Vertex AI's
-- partner pricing for Claude may differ: re-check before a spend decision.
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.model_prices` AS
SELECT * FROM UNNEST([
  STRUCT('claude-haiku-5-5' AS model, 0.11 AS input_usd_per_m, 0.55 AS output_usd_per_m),
  STRUCT('claude-sonnet-5-5' AS model, 2.20 AS input_usd_per_m, 11.00 AS output_usd_per_m),
  STRUCT('claude-opus-5-5' AS model, 4.40 AS input_usd_per_m, 22.00 AS output_usd_per_m),
  STRUCT('gemini-3.8-flash' AS model, 1.65 AS input_usd_per_m, 8.25 AS output_usd_per_m),
  STRUCT('gemini-3.5-flash-lite' AS model, 0.33 AS input_usd_per_m, 2.75 AS output_usd_per_m)
]);

-- One row per step of a turn (root, adapter, reviewer, judge) and per data input's judge calls, priced.
-- `input` counts cached and cache-write tokens too (agents/anyplot/plugins/ledger.py `StepUsage`): cached ones
-- cost 0.1 and cache writes 1.25 of the input price, as `pricing.py` prices them. The cost comes from the
-- `chat_turn` and `data_input` lines only: `pipeline_run.steps` repeats the adapter's and the reviewer's share
-- of its turn for per-run analysis and is left out here, so no token is priced twice. A model without a price
-- row has a NULL cost (add the row above).
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.cost` AS
WITH steps AS (
  SELECT
    turns.ts, turns.source, turns.session, turns.spec_id, turns.library, 'chat_turn' AS origin,
    JSON_VALUE(step.step) AS step,
    REGEXP_REPLACE(JSON_VALUE(step.model), r'(@.*|-[0-9]{8})$', '') AS model,
    IFNULL(LAX_INT64(step.calls), 0) AS calls,
    IFNULL(LAX_INT64(step.input), 0) AS input_tokens,
    IFNULL(LAX_INT64(step.output), 0) AS output_tokens,
    IFNULL(LAX_INT64(step.cached), 0) AS cached_tokens,
    IFNULL(LAX_INT64(step.cache_write), 0) AS cache_write_tokens
  FROM `anyplot.agent_telemetry.chat_turns` AS turns, UNNEST(JSON_QUERY_ARRAY(turns.steps)) AS step
  UNION ALL
  SELECT
    ts, source, session, spec_id, library, 'data_input', 'judge',
    REGEXP_REPLACE(judge_model, r'(@.*|-[0-9]{8})$', ''),
    IF(judge_input + judge_output > 0, 1, 0),
    judge_input, judge_output, 0, 0
  FROM `anyplot.agent_telemetry.data_inputs`
  WHERE judge_input + judge_output > 0
)
SELECT
  steps.*,
  (
    GREATEST(steps.input_tokens - steps.cached_tokens - steps.cache_write_tokens, 0) * prices.input_usd_per_m
    + steps.cached_tokens * prices.input_usd_per_m * 0.1
    + steps.cache_write_tokens * prices.input_usd_per_m * 1.25
    + steps.output_tokens * prices.output_usd_per_m
  ) / 1e6 AS cost_usd
FROM steps
LEFT JOIN `anyplot.agent_telemetry.model_prices` AS prices USING (model);
