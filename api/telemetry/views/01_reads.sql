-- Base view of the machine-read telemetry: one row per machine read, deduplicated by its line id.
--
-- Reads the Log Analytics linked dataset `machine_reads_logs` (the `machine-reads` log bucket, which the sink
-- fills with `jsonPayload.log_type="machine_read"` lines of `anyplot-api` and `anyplot-app`). Cloud Logging may
-- deliver a line twice; both copies carry the line's `line_id` (api/machine_reads.py, nginx's `$request_id`),
-- so the earliest row per id counts.
--
-- The lines are content-free by construction: closed sets, a status and validated catalogue ids only, never an
-- IP address, a user agent, a query string or a raw path (docs/reference/machine-readers.md). nginx writes an
-- empty `verified_category` for an unverified request, which NULLIF folds into the same NULL the API's omitted
-- field reads as; nginx never writes `spec_id`, `language`, `library`, `client`, `rpc` or `tool`.
--
-- The deduplication spans the whole bucket, which defeats partition pruning: filter a large query on
-- `_AllLogs.timestamp` before the QUALIFY instead of reading through this view.
CREATE OR REPLACE VIEW `anyplot.machine_reads.reads` AS
SELECT
  timestamp AS ts,
  LAX_INT64(json_payload.schema) AS schema_version,
  JSON_VALUE(json_payload.writer) AS writer,
  JSON_VALUE(json_payload.service) AS service,
  JSON_VALUE(json_payload.revision) AS revision,
  JSON_VALUE(json_payload.source) AS source,
  JSON_VALUE(json_payload.line_id) AS line_id,
  JSON_VALUE(json_payload.assistant) AS assistant,
  JSON_VALUE(json_payload.kind) AS kind,
  NULLIF(JSON_VALUE(json_payload.verified_category), '') AS verified_category,
  JSON_VALUE(json_payload.client) AS client,
  JSON_VALUE(json_payload.surface) AS surface,
  JSON_VALUE(json_payload.route) AS route,
  JSON_VALUE(json_payload.spec_id) AS spec_id,
  JSON_VALUE(json_payload.language) AS language,
  JSON_VALUE(json_payload.library) AS library,
  JSON_VALUE(json_payload.host) AS host,
  JSON_VALUE(json_payload.method) AS method,
  LAX_INT64(json_payload.status) AS status,
  JSON_VALUE(json_payload.rpc) AS rpc,
  JSON_VALUE(json_payload.tool) AS tool
FROM `anyplot.machine_reads_logs._AllLogs`
WHERE JSON_VALUE(json_payload.log_type) = 'machine_read'
QUALIFY ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(json_payload.line_id) ORDER BY timestamp) = 1;
