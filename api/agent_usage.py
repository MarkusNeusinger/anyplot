"""Aggregates of the agent usage telemetry for the admin debug page (`GET /debug/agent-usage`).

The agents service writes content-free telemetry lines (`agents/anyplot/telemetry.py`); a
Cloud Logging sink routes them into a log bucket that BigQuery reads through a linked dataset
(`docs/reference/agent-telemetry.md`). This module runs one query and answers aggregates only:
counts, two rates and the five most frequent specs, input formats and refusal codes, every key
an id or a code from a closed set. Live sessions only (`source = 'live'`): the eval harnesses
tag theirs `harness`, and the sessions the admin's "plot in all libraries" opens tag theirs `fanout`.

Cost. The query reads the linked log dataset `<dataset>_logs` (`agent_telemetry_logs` for
`AGENT_TELEMETRY_DATASET=anyplot.agent_telemetry`) directly, not the `events` view: the view
deduplicates over the whole bucket with a window function, which no time filter can prune. The
query filters `timestamp` (the log view's partition column) to the window first and
deduplicates only those rows, so a load scans the window, never the whole 180 days. The window
starts at `since`, the current time floored to `WINDOW_STEP_S` minus the days, passed as a
query parameter: within one step the query text and its parameters stay byte-identical, so
BigQuery may answer from its result cache, and on top of that this module keeps each answer for
`CACHE_TTL_S` in the process (`_CACHE`), so reloading `/debug` runs no query at all.

`AGENT_TELEMETRY_DATASET` unset answers `not_configured`; a query that fails (no table yet, no
permission, a timeout) answers `unavailable`, logged with the exception class only. Both carry
zeros, so the page shows its empty state and never an error. Neither is cached.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

UsageStatus = Literal["ok", "not_configured", "unavailable"]
USAGE_WINDOWS = (7, 30)
TOP_ITEMS = 5
QUERY_TIMEOUT_S = 20.0
WINDOW_STEP_S = 600
"""The window's start moves in steps of ten minutes, so repeated loads send the same query."""
CACHE_TTL_S = 600.0
"""How long an `ok` answer is kept in the process."""
DATASET_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]\.[A-Za-z_][A-Za-z0-9_]{0,1018}$")
"""`<project>.<dataset>`, checked before it goes into the SQL text: a dataset name cannot be a query parameter.
The dataset leaves room for the `_logs` suffix of the linked log dataset (1,024 characters at most)."""
LOGS_SUFFIX = "_logs"
"""The linked log dataset is the views dataset's name plus this suffix (`docs/reference/agent-telemetry.md`)."""

KEEP_ACTIONS = (
    "copied_code",
    "copied_image",
    "downloaded_png",
    "downloaded_code",
    "downloaded_page",
    "downloaded_data",
)
"""The outcomes that keep a result; never `saved_session`, which users also send to report a plot they did not like.
`downloaded_page` (a JavaScript plot's `plot.html`, since JS-4b) keeps one like the code download."""
REJECT_REACTIONS = ("thumbs_down", "bug")
"""Feedback reactions that make a session not kept, whatever else the user did."""
REJECT_LOOKBACK_DAYS = 2
"""How far before the window a session's rejections and runs are still read (reviews of #12207): a session that
straddles the window's start keeps a thumbs_down sent before it, and a plot shipped before it and kept inside it
counts as shipped and kept. Sessions live in memory on one instance, so two days covers them; the extra range is
a pruned partition scan, and the window's own counts (plots shipped, the repair rate) never reach into it."""


class UsageItem(BaseModel):
    key: str
    count: int = Field(ge=0)


class AgentUsage(BaseModel):
    status: UsageStatus
    days: int
    sessions: int = 0
    plots_shipped: int = 0
    kept_rate: float | None = None
    """Kept sessions among the sessions with a shipped plot (`kept_sessions` of `shipped_sessions`)."""
    kept_sessions: int = 0
    """Sessions with a copy or a download after their last run and no thumbs_down or bug feedback; a saved session
    alone is no keep (owner rule of 2026-10-16, the `sessions` view's `kept`)."""
    shipped_sessions: int = 0
    repair_rate: float | None = None
    """Pipeline runs that needed more than one round among the runs that started (`repaired_runs` of `runs`)."""
    repaired_runs: int = 0
    runs: int = 0
    """Pipeline runs that started (not the `not_ready` ones)."""
    top_specs: list[UsageItem] = Field(default_factory=list)
    top_formats: list[UsageItem] = Field(default_factory=list)
    top_refusals: list[UsageItem] = Field(default_factory=list)
    generated_at: str


class UsageQuery(Protocol):
    """Runs one standard-SQL query with a TIMESTAMP `@since` parameter and returns its rows as dicts."""

    def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]: ...


BIGQUERY_SCOPE = "https://www.googleapis.com/auth/bigquery"
QUERY_URL = "https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries"


class QueryIncomplete(Exception):
    """BigQuery did not finish the query within `QUERY_TIMEOUT_S` (`jobComplete: false`)."""


class BigQueryUsage:
    """`UsageQuery` on BigQuery's REST API (`jobs.query`), billed to the dataset's project.

    It runs through google-auth's `AuthorizedSession`, which the API already ships for the
    agent BFF's ID tokens, so the API image carries no BigQuery client library (and no gRPC).
    One synchronous call: the query is small, and an answer that is not complete within
    `QUERY_TIMEOUT_S` counts as a failure (`QueryIncomplete`), never a poll.
    """

    def __init__(self, project: str) -> None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession

        credentials, _ = google.auth.default(scopes=[BIGQUERY_SCOPE])
        self._session = AuthorizedSession(credentials)
        self._url = QUERY_URL.format(project=project)

    def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
        body = {
            "query": sql,
            "useLegacySql": False,
            "useQueryCache": True,
            "timeoutMs": int(QUERY_TIMEOUT_S * 1000),
            "parameterMode": "NAMED",
            "queryParameters": [
                {
                    "name": "since",
                    "parameterType": {"type": "TIMESTAMP"},
                    "parameterValue": {"value": since.strftime("%Y-%m-%d %H:%M:%S+00:00")},
                }
            ],
        }
        response = self._session.post(self._url, json=body, timeout=QUERY_TIMEOUT_S + 10)
        response.raise_for_status()
        return decode_rows(response.json())


def decode_rows(answer: dict[str, Any]) -> list[dict[str, Any]]:
    """The rows of a `jobs.query` answer as dicts, typed by its schema (REST sends every scalar as a string)."""
    if not answer.get("jobComplete", False):
        raise QueryIncomplete
    fields = (answer.get("schema") or {}).get("fields") or []
    return [
        {field["name"]: _cell(field, cell) for field, cell in zip(fields, row.get("f") or [], strict=False)}
        for row in answer.get("rows") or []
    ]


def _cell(field: dict[str, Any], cell: dict[str, Any] | None) -> Any:
    value = (cell or {}).get("v")
    if field.get("mode") == "REPEATED":
        return [_scalar(field, item.get("v") if isinstance(item, dict) else None) for item in value or []]
    return _scalar(field, value)


def _scalar(field: dict[str, Any], value: Any) -> Any:
    if value is None:
        return None
    kind = field.get("type")
    if kind in ("RECORD", "STRUCT"):
        subfields = field.get("fields") or []
        return {sub["name"]: _cell(sub, cell) for sub, cell in zip(subfields, value.get("f") or [], strict=False)}
    if kind in ("INTEGER", "INT64"):
        return int(value)
    if kind in ("FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC"):
        return float(value)
    if kind in ("BOOLEAN", "BOOL"):
        return value == "true"
    return value


def window_start(days: int, now: datetime | None = None) -> datetime:
    """The window's start: now, floored to `WINDOW_STEP_S`, minus `days`."""
    current = now or datetime.now(UTC)
    floored = datetime.fromtimestamp(int(current.timestamp()) // WINDOW_STEP_S * WINDOW_STEP_S, UTC)
    return floored - timedelta(days=days)


def usage_sql(dataset: str) -> str:
    """The one query behind the card: the window's lines of the linked log dataset, deduplicated, aggregated.

    The `timestamp` filter comes before the deduplication, so BigQuery prunes the log view's
    partitions to the window. Transcription offers (`outcome: transcribed`) are left out of the
    formats: the confirmed paste that follows carries the same format, so each input counts once.
    `not_ready` runs (a plot asked for before the data was confirmed) count neither as shipped
    nor in the repair rate's base. A session counts as kept as the `sessions` view's `kept` says
    (`agents/telemetry/views/03_sessions.sql`): a copy or a download after its last run, and no
    thumbs_down or bug feedback; a saved session alone is no keep. The counts behind both rates come along,
    so the card shows "1 of 3" beside the percentage.
    """
    keep = ", ".join(f"'{action}'" for action in KEEP_ACTIONS)
    reject = ", ".join(f"'{reaction}'" for reaction in REJECT_REACTIONS)
    return f"""
WITH ev AS (
  SELECT
    timestamp AS ts,
    JSON_VALUE(json_payload.event) AS event,
    JSON_VALUE(json_payload.session) AS session,
    JSON_VALUE(json_payload.spec_id) AS spec_id,
    json_payload AS payload
  FROM `{dataset}{LOGS_SUFFIX}._AllLogs`
  WHERE timestamp >= @since
    AND JSON_VALUE(json_payload.log_type) = 'agent_telemetry'
    AND JSON_VALUE(json_payload.source) = 'live'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(json_payload.idempotency_key) ORDER BY timestamp) = 1
),
runs AS (
  SELECT JSON_VALUE(payload.status) AS status, LAX_INT64(payload.rounds) AS rounds, session, ts
  FROM ev WHERE event = 'pipeline_run' AND JSON_VALUE(payload.status) != 'not_ready'
),
per_session AS (
  -- Every session of the window, its runs read from up to {REJECT_LOOKBACK_DAYS} days before it: a plot shipped
  -- just before the window and kept inside it counts as shipped and kept, as the session counts in `sessions`
  -- (review of #12207). The window's own run counts (plots shipped, the repair rate) stay in `runs`.
  SELECT
    JSON_VALUE(json_payload.session) AS session,
    MAX(timestamp) AS last_run_at,
    COUNTIF(JSON_VALUE(json_payload.status) IN ('ok', 'needs_attention')) AS shipped
  FROM `{dataset}{LOGS_SUFFIX}._AllLogs`
  WHERE timestamp >= TIMESTAMP_SUB(@since, INTERVAL {REJECT_LOOKBACK_DAYS} DAY)
    AND JSON_VALUE(json_payload.log_type) = 'agent_telemetry'
    AND JSON_VALUE(json_payload.source) = 'live'
    AND JSON_VALUE(json_payload.event) = 'pipeline_run'
    AND JSON_VALUE(json_payload.status) != 'not_ready'
    AND JSON_VALUE(json_payload.session) IN (SELECT session FROM ev)
  GROUP BY session
),
outcomes AS (
  SELECT session, MAX(IF(JSON_VALUE(payload.action) IN ({keep}), ts, NULL)) AS last_keep_at
  FROM ev WHERE event = 'outcome' GROUP BY session
),
rejections AS (
  -- A rejection counts from up to {REJECT_LOOKBACK_DAYS} days before the window, so a session that straddles the
  -- window's start keeps a thumbs_down or bug sent before it; still a pruned partition range.
  SELECT DISTINCT JSON_VALUE(json_payload.session) AS session
  FROM `{dataset}{LOGS_SUFFIX}._AllLogs`
  WHERE timestamp >= TIMESTAMP_SUB(@since, INTERVAL {REJECT_LOOKBACK_DAYS} DAY)
    AND JSON_VALUE(json_payload.log_type) = 'agent_telemetry'
    AND JSON_VALUE(json_payload.source) = 'live'
    AND JSON_VALUE(json_payload.event) = 'outcome'
    AND JSON_VALUE(json_payload.action) = 'feedback'
    AND JSON_VALUE(json_payload.reaction) IN ({reject})
),
shipped_sessions AS (
  SELECT per_session.session, (
    per_session.session NOT IN (SELECT session FROM rejections WHERE session IS NOT NULL)
    AND outcomes.last_keep_at IS NOT NULL
    AND outcomes.last_keep_at > per_session.last_run_at
  ) AS kept
  FROM per_session LEFT JOIN outcomes USING (session)
  WHERE per_session.shipped > 0
),
refusals AS (
  SELECT IFNULL(JSON_VALUE(payload.cause), JSON_VALUE(payload.outcome)) AS key
  FROM ev WHERE event = 'data_input' AND JSON_VALUE(payload.outcome) NOT IN ('ok', 'transcribed')
  UNION ALL
  SELECT JSON_VALUE(payload.refusal) FROM ev WHERE event = 'chat_turn' AND JSON_VALUE(payload.refusal) IS NOT NULL
)
SELECT
  (SELECT COUNT(DISTINCT session) FROM ev) AS sessions,
  (SELECT COUNTIF(status IN ('ok', 'needs_attention')) FROM runs) AS plots_shipped,
  (SELECT COUNTIF(kept) FROM shipped_sessions) AS kept_sessions,
  (SELECT COUNT(*) FROM shipped_sessions) AS shipped_sessions,
  (SELECT SAFE_DIVIDE(COUNTIF(kept), COUNT(*)) FROM shipped_sessions) AS kept_rate,
  (SELECT COUNTIF(rounds > 1) FROM runs) AS repaired_runs,
  (SELECT COUNT(*) FROM runs) AS runs,
  (SELECT SAFE_DIVIDE(COUNTIF(rounds > 1), COUNT(*)) FROM runs) AS repair_rate,
  ARRAY(
    SELECT AS STRUCT spec_id AS key, COUNT(DISTINCT session) AS count FROM ev
    WHERE spec_id IS NOT NULL GROUP BY spec_id ORDER BY count DESC, key LIMIT {TOP_ITEMS}
  ) AS top_specs,
  ARRAY(
    SELECT AS STRUCT JSON_VALUE(payload.format) AS key, COUNT(*) AS count FROM ev
    WHERE event = 'data_input' AND JSON_VALUE(payload.outcome) != 'transcribed'
    GROUP BY key ORDER BY count DESC, key LIMIT {TOP_ITEMS}
  ) AS top_formats,
  ARRAY(
    SELECT AS STRUCT key, COUNT(*) AS count FROM refusals
    WHERE key IS NOT NULL GROUP BY key ORDER BY count DESC, key LIMIT {TOP_ITEMS}
  ) AS top_refusals
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _items(value: Any) -> list[UsageItem]:
    if not isinstance(value, list):
        return []
    items = []
    for entry in value[:TOP_ITEMS]:
        key, count = (entry.get("key"), entry.get("count")) if isinstance(entry, dict) else (None, None)
        if isinstance(key, str) and isinstance(count, int):
            items.append(UsageItem(key=key, count=count))
    return items


def _count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _rate(value: Any) -> float | None:
    return round(float(value), 4) if isinstance(value, int | float) else None


_CACHE: dict[tuple[str, int], tuple[float, AgentUsage]] = {}
_CACHE_LOCK = threading.Lock()


def clear_usage_cache() -> None:
    """Forget every kept answer (tests, and a dataset change at runtime)."""
    with _CACHE_LOCK:
        _CACHE.clear()


def read_usage(
    query: UsageQuery | None, dataset: str | None, days: int, *, clock: Callable[[], float] = time.monotonic
) -> AgentUsage:
    """The card's aggregates for the last `days` days; `not_configured` or `unavailable` with zeros otherwise.

    An `ok` answer is kept for `CACHE_TTL_S` per dataset and window; a failure is never kept, so the card
    recovers on the next load once BigQuery answers.
    """
    if not dataset or not DATASET_PATTERN.fullmatch(dataset):
        return AgentUsage(status="not_configured", days=days, generated_at=_now())
    with _CACHE_LOCK:
        kept = _CACHE.get((dataset, days))
    if kept is not None and clock() < kept[0]:
        return kept[1]
    if query is None:  # configured, but the client could not start (no credentials)
        return AgentUsage(status="unavailable", days=days, generated_at=_now())
    try:
        rows = query.rows(usage_sql(dataset), window_start(days))
    except Exception as exc:  # no table yet, no permission, a timeout: the page shows its empty state
        logger.warning("agent usage query failed: %s", type(exc).__name__)
        return AgentUsage(status="unavailable", days=days, generated_at=_now())
    row = rows[0] if rows else {}
    usage = AgentUsage(
        status="ok",
        days=days,
        sessions=int(row.get("sessions") or 0),
        plots_shipped=int(row.get("plots_shipped") or 0),
        kept_rate=_rate(row.get("kept_rate")),
        kept_sessions=_count(row.get("kept_sessions")),
        shipped_sessions=_count(row.get("shipped_sessions")),
        repair_rate=_rate(row.get("repair_rate")),
        repaired_runs=_count(row.get("repaired_runs")),
        runs=_count(row.get("runs")),
        top_specs=_items(row.get("top_specs")),
        top_formats=_items(row.get("top_formats")),
        top_refusals=_items(row.get("top_refusals")),
        generated_at=_now(),
    )
    with _CACHE_LOCK:
        _CACHE[(dataset, days)] = (clock() + CACHE_TTL_S, usage)
    return usage


_CLIENTS: dict[str, UsageQuery] = {}
_CLIENTS_LOCK = threading.Lock()


def usage_query(dataset: str | None) -> UsageQuery | None:
    """The BigQuery client for `dataset`'s project, one per process once it started, or None when the dataset is
    unset or the client cannot start. A failure is never kept: the next request tries again (credentials that
    appear later, a transient metadata-server error)."""
    if not dataset or not DATASET_PATTERN.fullmatch(dataset):
        return None
    project = dataset.split(".", 1)[0]
    with _CLIENTS_LOCK:
        client = _CLIENTS.get(project)
    if client is not None:
        return client
    try:
        client = BigQueryUsage(project=project)
    except Exception as exc:  # no credentials (a local run): the card's `unavailable` state
        logger.warning("BigQuery client unavailable: %s", type(exc).__name__)
        return None
    with _CLIENTS_LOCK:
        _CLIENTS.setdefault(project, client)
    return client
