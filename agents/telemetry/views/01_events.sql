-- Base view of the agent usage telemetry: one row per telemetry line, deduplicated by its idempotency key.
--
-- Reads the Log Analytics linked dataset `agent_telemetry_logs` (the `agent-telemetry` log bucket, which the
-- sink fills with `jsonPayload.log_type="agent_telemetry"` lines of `anyplot-agents`). Cloud Logging may deliver
-- a line twice, and ADK may re-run a pipeline node; both repeat the line's `idempotency_key`
-- (agents/anyplot/telemetry.py), so the earliest row per key counts.
--
-- The lines are content-free by construction: enums, buckets, counts and ids from closed sets only
-- (docs/reference/agent-telemetry.md). `payload` keeps the whole line for the event views below.
CREATE OR REPLACE VIEW `anyplot.agent_telemetry.events` AS
SELECT
  timestamp AS ts,
  JSON_VALUE(json_payload.event) AS event,
  LAX_INT64(json_payload.schema) AS schema_version,
  JSON_VALUE(json_payload.service) AS service,
  JSON_VALUE(json_payload.revision) AS revision,
  JSON_VALUE(json_payload.source) AS source,
  JSON_VALUE(json_payload.session) AS session,
  JSON_VALUE(json_payload.spec_id) AS spec_id,
  JSON_VALUE(json_payload.library) AS library,
  LAX_INT64(json_payload.turn) AS turn,
  JSON_VALUE(json_payload.idempotency_key) AS idempotency_key,
  json_payload AS payload
FROM `anyplot.agent_telemetry_logs._AllLogs`
WHERE JSON_VALUE(json_payload.log_type) = 'agent_telemetry'
QUALIFY ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(json_payload.idempotency_key) ORDER BY timestamp) = 1;
