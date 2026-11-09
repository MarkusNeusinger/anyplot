"""Aggregates of the machine-read telemetry: the public tile on `/stats` and the owner's section on `/debug`.

Both writers (`api/machine_reads.py`, `app/nginx.conf`) put one content-free line per machine read into the
`machine-reads` log bucket, which BigQuery reads through the linked dataset `<dataset>_logs`
(`docs/reference/machine-readers.md`). This module runs two queries over it and answers counts only: per day,
per audience, per vendor and purpose, and per route name or catalogue id. Every key is a value of a closed set
or a validated catalogue id, so nothing here can carry an IP address, a user agent, a query string or a raw path.

- `public_sql` and `read_public` feed `GET /insights/machine-readers`: the last `PUBLIC_DAYS` UTC days of live
  reads that Cloudflare verified, on the content surfaces (`CONTENT_SURFACES`) and served (2xx or 304), split
  into the three audiences the tile shows (`PUBLIC_AUDIENCES`). Two counts sit beside them: the MCP requests of
  every client, verified or not (an MCP client other than Claude is never a verified bot), and the unverified
  requests of a named vendor (`assistant != 'other'`) in the same audiences, which the tile names as not counted.
  `read_public` raises on a failed query, so the endpoint decides what is kept (`api/routers/insights.py`).
- `detail_sql` and `read_detail` feed `GET /debug/machine-readers`: the last 7 or 30 UTC days of every line,
  verified or not, with every status: the totals, one row per vendor and purpose with its five most requested
  routes, and one row per day. `read_detail` answers `not_configured` or `unavailable` with zeros, like
  `api/agent_usage.py`, and keeps an `ok` answer for `DETAIL_CACHE_TTL_S` in the process.

Cost. Both queries read `_AllLogs` of the linked log dataset, not the `reads` view: the view deduplicates over
the whole bucket, which no time filter can prune. The `timestamp` filter comes first and the deduplication on
`line_id` reads only the window's partitions. BigQuery's result cache does not answer a repeat, because the
linked `_AllLogs` view changes with every line that arrives; the process caches bound how often a query runs
(the tile's `get_or_set_cache` refreshes hourly, the owner's answer is kept ten minutes). Each window starts at
00:00 UTC, so a day's answers cover the same days.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from api.agent_usage import DATASET_PATTERN, LOGS_SUFFIX, UsageItem, UsageQuery, UsageStatus
from api.machine_reads import AUDIENCE_SQL


logger = logging.getLogger(__name__)

PUBLIC_DAYS = 28
"""The tile's window: today and the 27 UTC days before it, as the visitors strip beside it."""
DETAIL_WINDOWS = (7, 30)
"""The windows of the owner's section, in days."""
TOP_PATHS = 5
"""The routes kept per vendor row."""
DETAIL_CACHE_TTL_S = 600.0
"""How long an `ok` answer of the owner's section is kept in the process."""
CONTENT_SURFACES = ("page", "shell", "code", "spec", "mcp")
"""What the tile counts as a read of the catalogue: a page (prerendered or the shell), a code or spec answer, an
MCP request. og images, the machine files and the rest of the JSON API are left out."""
PUBLIC_AUDIENCES = ("for_person", "index_training", "search")
"""The audiences the tile shows, from `AUDIENCE_SQL`; `seo`, `preview` and `other` are the owner's to see."""
SERVED = "(status BETWEEN 200 AND 299 OR status = 304)"
"""A served answer, the same rule as the daily view's `served`."""


class MachineReadsUnavailable(Exception):
    """The dataset is configured, but the BigQuery client could not start (no credentials)."""


# --- Answers ------------------------------------------------------------------------------


class MachineReaderPoint(BaseModel):
    """One UTC day of the tile: verified, served reads on the content surfaces, by audience."""

    date: str
    for_person: int = Field(default=0, ge=0)
    index_training: int = Field(default=0, ge=0)
    search: int = Field(default=0, ge=0)
    mcp: int = Field(default=0, ge=0)
    """MCP requests of every client, verified or not."""


class MachineReaderTotals(BaseModel):
    """The window's sums of the points, plus the unverified requests the tile names as not counted."""

    for_person: int = Field(default=0, ge=0)
    index_training: int = Field(default=0, ge=0)
    search: int = Field(default=0, ge=0)
    mcp: int = Field(default=0, ge=0)
    unverified: int = Field(default=0, ge=0)
    """Served reads in the tile's audiences by a named vendor that Cloudflare did not verify."""


class MachineReadersResponse(BaseModel):
    """The answer of `GET /insights/machine-readers`."""

    status: UsageStatus
    days: int = PUBLIC_DAYS
    points: list[MachineReaderPoint] = Field(default_factory=list)
    """Every day of the window, oldest first, a day without reads with zeros; empty unless `status` is `ok`."""
    totals: MachineReaderTotals = Field(default_factory=MachineReaderTotals)
    generated_at: str


class MachineReadsVendor(BaseModel):
    """One vendor and purpose of the owner's matrix, every status and surface counted."""

    assistant: str
    kind: str
    category: str | None = None
    """Cloudflare's category on most of the row's verified lines; None when none was verified."""
    requests: int = Field(default=0, ge=0)
    verified: int = Field(default=0, ge=0)
    unverified: int = Field(default=0, ge=0)
    pages: int = Field(default=0, ge=0)
    """Page reads, prerendered or the shell."""
    code: int = Field(default=0, ge=0)
    og: int = Field(default=0, ge=0)
    mcp: int = Field(default=0, ge=0)
    not_found: int = Field(default=0, ge=0)
    top_paths: list[UsageItem] = Field(default_factory=list)
    """The most requested routes: the route name, then the catalogue ids of a served answer."""


class MachineReadsDay(BaseModel):
    """One UTC day of the owner's table: live lines, verified by audience, the unverified apart."""

    date: str
    for_person: int = Field(default=0, ge=0)
    index_training: int = Field(default=0, ge=0)
    search: int = Field(default=0, ge=0)
    seo: int = Field(default=0, ge=0)
    other: int = Field(default=0, ge=0)
    """Verified lines of the `preview` and `other` audiences."""
    unverified: int = Field(default=0, ge=0)
    mcp: int = Field(default=0, ge=0)


class MachineReadsDetail(BaseModel):
    """The answer of `GET /debug/machine-readers?days=N`."""

    status: UsageStatus
    days: int
    generated_at: str
    requests: int = Field(default=0, ge=0)
    """Live lines of the window."""
    verified: int = Field(default=0, ge=0)
    unverified: int = Field(default=0, ge=0)
    mcp_calls: int = Field(default=0, ge=0)
    synthetic: int = Field(default=0, ge=0)
    """Lines of the smoke checks and anyone else at a raw `*.run.app` origin, outside every other count."""
    vendors: list[MachineReadsVendor] = Field(default_factory=list)
    """One row per vendor and purpose, most requests first."""
    daily: list[MachineReadsDay] = Field(default_factory=list)
    """Every day of the window, newest first; empty unless `status` is `ok`."""


# --- Windows ------------------------------------------------------------------------------


def _midnight(now: datetime | None, days_back: int) -> datetime:
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return datetime.combine(current.date() - timedelta(days=days_back), datetime.min.time(), UTC)


def public_start(now: datetime | None = None) -> datetime:
    """The tile's start: 00:00 UTC `PUBLIC_DAYS - 1` days before today, the same for the whole day."""
    return _midnight(now, PUBLIC_DAYS - 1)


def detail_start(days: int, now: datetime | None = None) -> datetime:
    """The owner's window start: 00:00 UTC `days - 1` days before today, the same for the whole day."""
    return _midnight(now, days - 1)


# --- Queries ------------------------------------------------------------------------------


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def _lines(dataset: str, columns: str) -> str:
    """The window's machine-read lines of the linked log dataset, deduplicated on `line_id`.

    The `timestamp` filter comes before the `QUALIFY`, so BigQuery prunes the log view's partitions to the window.
    nginx writes an empty `verified_category` for an unverified request; it reads as NULL, as in the `reads` view.
    """
    return f"""lines AS (
  SELECT
    timestamp AS ts,
    JSON_VALUE(json_payload.source) AS source,
    JSON_VALUE(json_payload.assistant) AS assistant,
    JSON_VALUE(json_payload.kind) AS kind,
    NULLIF(JSON_VALUE(json_payload.verified_category), '') AS verified_category,
    JSON_VALUE(json_payload.surface) AS surface,
    LAX_INT64(json_payload.status) AS status{columns}
  FROM `{dataset}{LOGS_SUFFIX}._AllLogs`
  WHERE timestamp >= @since
    AND JSON_VALUE(json_payload.log_type) = 'machine_read'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY JSON_VALUE(json_payload.line_id) ORDER BY timestamp) = 1
)"""


def public_sql(dataset: str) -> str:
    """The tile's query: one row per UTC day with reads, the three audiences, the MCP requests, the unverified.

    Live lines only, on the content surfaces and served. An audience counts a line Cloudflare verified
    (`verified_category IS NOT NULL`); the MCP count takes every client, and the unverified count only a named
    vendor, so a python or node MCP client or a crawler only Cloudflare could have named is never called a
    crawler that carried a name.
    """
    audiences = _quoted(PUBLIC_AUDIENCES)
    counts = ",\n  ".join(
        f"COUNTIF(verified_category IS NOT NULL AND audience = '{audience}') AS {audience}"
        for audience in PUBLIC_AUDIENCES
    )
    return f"""
WITH {_lines(dataset, "")},
reads AS (
  SELECT DATE(ts) AS day, assistant, verified_category, surface, {AUDIENCE_SQL} AS audience
  FROM lines
  WHERE source = 'live'
    AND surface IN ({_quoted(CONTENT_SURFACES)})
    AND {SERVED}
)
SELECT
  day,
  {counts},
  COUNTIF(surface = 'mcp') AS mcp,
  COUNTIF(verified_category IS NULL AND assistant != 'other' AND audience IN ({audiences})) AS unverified
FROM reads
GROUP BY day
ORDER BY day
"""


_PATH_KEY = (
    "CONCAT(route, IFNULL(CONCAT(' ', spec_id), ''), IFNULL(CONCAT('/', language), ''),"
    " IFNULL(CONCAT('/', library), ''))"
)
"""A route row's key: the route name, then the catalogue ids a served answer carries (`spec_detail
scatter-basic/python/matplotlib`). Every part is a closed name or a validated id."""


def detail_sql(dataset: str) -> str:
    """The owner's query: one row with the window's totals, the vendor matrix and the per-day counts.

    Every live line counts, whatever its surface, status or verdict; `synthetic` counts the rest. A vendor row is
    a vendor and purpose (`claude` reads as a person's assistant, an index and a training crawler) with the
    category Cloudflare gave most of its verified lines and its `TOP_PATHS` most requested routes.
    """
    columns = """,
    JSON_VALUE(json_payload.route) AS route,
    JSON_VALUE(json_payload.spec_id) AS spec_id,
    JSON_VALUE(json_payload.language) AS language,
    JSON_VALUE(json_payload.library) AS library"""
    return f"""
WITH {_lines(dataset, columns)},
live AS (
  SELECT *, {AUDIENCE_SQL} AS audience FROM lines WHERE source = 'live'
),
categories AS (
  SELECT assistant, kind, verified_category AS category
  FROM live
  WHERE verified_category IS NOT NULL
  GROUP BY assistant, kind, verified_category
  QUALIFY ROW_NUMBER() OVER (PARTITION BY assistant, kind ORDER BY COUNT(*) DESC, verified_category) = 1
),
paths AS (
  SELECT assistant, kind, ARRAY_AGG(STRUCT(key, count) ORDER BY count DESC, key) AS top_paths
  FROM (
    SELECT assistant, kind, {_PATH_KEY} AS key, COUNT(*) AS count
    FROM live
    GROUP BY assistant, kind, key
    QUALIFY ROW_NUMBER() OVER (PARTITION BY assistant, kind ORDER BY COUNT(*) DESC, key) <= {TOP_PATHS}
  )
  GROUP BY assistant, kind
),
vendors AS (
  SELECT
    assistant,
    kind,
    COUNT(*) AS requests,
    COUNTIF(verified_category IS NOT NULL) AS verified,
    COUNTIF(verified_category IS NULL) AS unverified,
    COUNTIF(surface IN ('page', 'shell')) AS pages,
    COUNTIF(surface = 'code') AS code,
    COUNTIF(surface = 'og') AS og,
    COUNTIF(surface = 'mcp') AS mcp,
    COUNTIF(status = 404) AS not_found
  FROM live
  GROUP BY assistant, kind
),
days AS (
  SELECT
    DATE(ts) AS day,
    COUNTIF(verified_category IS NOT NULL AND audience = 'for_person') AS for_person,
    COUNTIF(verified_category IS NOT NULL AND audience = 'index_training') AS index_training,
    COUNTIF(verified_category IS NOT NULL AND audience = 'search') AS search,
    COUNTIF(verified_category IS NOT NULL AND audience = 'seo') AS seo,
    COUNTIF(verified_category IS NOT NULL AND audience IN ('preview', 'other')) AS other,
    COUNTIF(verified_category IS NULL) AS unverified,
    COUNTIF(surface = 'mcp') AS mcp
  FROM live
  GROUP BY day
)
SELECT
  (SELECT COUNT(*) FROM live) AS requests,
  (SELECT COUNTIF(verified_category IS NOT NULL) FROM live) AS verified,
  (SELECT COUNTIF(verified_category IS NULL) FROM live) AS unverified,
  (SELECT COUNTIF(surface = 'mcp') FROM live) AS mcp_calls,
  (SELECT COUNTIF(source = 'synthetic') FROM lines) AS synthetic,
  ARRAY(
    SELECT AS STRUCT vendors.*, categories.category, paths.top_paths
    FROM vendors
    LEFT JOIN categories USING (assistant, kind)
    LEFT JOIN paths USING (assistant, kind)
    ORDER BY requests DESC, assistant, kind
  ) AS vendors,
  ARRAY(SELECT AS STRUCT * FROM days ORDER BY day DESC) AS daily
"""


# --- Reading ------------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _day(value: Any) -> str | None:
    """A row's day as `YYYY-MM-DD`: the REST answer sends a DATE as that string."""
    return value[:10] if isinstance(value, str) and len(value) >= 10 else None


def empty_public(status: UsageStatus) -> MachineReadersResponse:
    """The tile's answer without numbers: `not_configured` or `unavailable`."""
    return MachineReadersResponse(status=status, generated_at=_now())


def read_public(query: UsageQuery | None, dataset: str, *, now: datetime | None = None) -> MachineReadersResponse:
    """The tile's 28 days, oldest first and zero-filled, and their totals.

    Raises when the dataset name is not one, when the client could not start and when the query fails: the
    endpoint keeps only an answer, so the tile recovers on the next load once BigQuery answers.
    """
    if not DATASET_PATTERN.fullmatch(dataset):
        raise ValueError("not a dataset name")
    if query is None:
        raise MachineReadsUnavailable
    since = public_start(now)
    rows = query.rows(public_sql(dataset), since)
    by_day = {day: row for row in rows if (day := _day(row.get("day")))}
    points = []
    for offset in range(PUBLIC_DAYS):
        date = (since + timedelta(days=offset)).date().isoformat()
        row = by_day.get(date, {})
        points.append(
            MachineReaderPoint(
                date=date,
                for_person=_count(row.get("for_person")),
                index_training=_count(row.get("index_training")),
                search=_count(row.get("search")),
                mcp=_count(row.get("mcp")),
            )
        )
    totals = MachineReaderTotals(
        for_person=sum(point.for_person for point in points),
        index_training=sum(point.index_training for point in points),
        search=sum(point.search for point in points),
        mcp=sum(point.mcp for point in points),
        unverified=sum(_count(by_day.get(point.date, {}).get("unverified")) for point in points),
    )
    return MachineReadersResponse(status="ok", points=points, totals=totals, generated_at=_now())


def _paths(value: Any) -> list[UsageItem]:
    if not isinstance(value, list):
        return []
    items = []
    for entry in value[:TOP_PATHS]:
        key, count = (entry.get("key"), entry.get("count")) if isinstance(entry, dict) else (None, None)
        if isinstance(key, str) and key and isinstance(count, int):
            items.append(UsageItem(key=key, count=_count(count)))
    return items


def _vendor(row: dict[str, Any]) -> MachineReadsVendor | None:
    assistant, kind = _text(row.get("assistant")), _text(row.get("kind"))
    if assistant is None or kind is None:
        return None
    return MachineReadsVendor(
        assistant=assistant,
        kind=kind,
        category=_text(row.get("category")),
        requests=_count(row.get("requests")),
        verified=_count(row.get("verified")),
        unverified=_count(row.get("unverified")),
        pages=_count(row.get("pages")),
        code=_count(row.get("code")),
        og=_count(row.get("og")),
        mcp=_count(row.get("mcp")),
        not_found=_count(row.get("not_found")),
        top_paths=_paths(row.get("top_paths")),
    )


def _detail_day(date: str, row: dict[str, Any]) -> MachineReadsDay:
    return MachineReadsDay(
        date=date,
        for_person=_count(row.get("for_person")),
        index_training=_count(row.get("index_training")),
        search=_count(row.get("search")),
        seo=_count(row.get("seo")),
        other=_count(row.get("other")),
        unverified=_count(row.get("unverified")),
        mcp=_count(row.get("mcp")),
    )


_DETAIL_CACHE: dict[tuple[str, int, str], tuple[float, MachineReadsDetail]] = {}
_CACHE_LOCK = threading.Lock()


def clear_detail_cache() -> None:
    """Forget every kept answer of the owner's section (tests, and a dataset change at runtime)."""
    with _CACHE_LOCK:
        _DETAIL_CACHE.clear()


def read_detail(
    query: UsageQuery | None,
    dataset: str | None,
    days: int,
    *,
    now: datetime | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> MachineReadsDetail:
    """The owner's section for the last `days` UTC days; `not_configured` or `unavailable` with zeros otherwise.

    An `ok` answer is kept for `DETAIL_CACHE_TTL_S` per dataset, window and window start, so a new UTC day queries
    anew; a failure is never kept.
    """
    if not dataset or not DATASET_PATTERN.fullmatch(dataset):
        return MachineReadsDetail(status="not_configured", days=days, generated_at=_now())
    since = detail_start(days, now)
    key = (dataset, days, since.date().isoformat())
    with _CACHE_LOCK:
        kept = _DETAIL_CACHE.get(key)
    if kept is not None and clock() < kept[0]:
        return kept[1]
    if query is None:  # configured, but the client could not start (no credentials)
        return MachineReadsDetail(status="unavailable", days=days, generated_at=_now())
    try:
        rows = query.rows(detail_sql(dataset), since)
    except Exception as exc:  # no table yet, no permission, a timeout: the section shows its empty state
        logger.warning("machine reads query failed: %s", type(exc).__name__)
        return MachineReadsDetail(status="unavailable", days=days, generated_at=_now())
    row = rows[0] if rows else {}
    entries = [entry for entry in row.get("daily") or [] if isinstance(entry, dict)]
    by_day = {day: entry for entry in entries if (day := _day(entry.get("day")))}
    vendors = [vendor for entry in row.get("vendors") or [] if isinstance(entry, dict) and (vendor := _vendor(entry))]
    dates = [(since + timedelta(days=offset)).date().isoformat() for offset in reversed(range(days))]
    detail = MachineReadsDetail(
        status="ok",
        days=days,
        generated_at=_now(),
        requests=_count(row.get("requests")),
        verified=_count(row.get("verified")),
        unverified=_count(row.get("unverified")),
        mcp_calls=_count(row.get("mcp_calls")),
        synthetic=_count(row.get("synthetic")),
        vendors=vendors,
        daily=[_detail_day(date, by_day.get(date, {})) for date in dates],
    )
    with _CACHE_LOCK:
        _DETAIL_CACHE[key] = (clock() + DETAIL_CACHE_TTL_S, detail)
    return detail
