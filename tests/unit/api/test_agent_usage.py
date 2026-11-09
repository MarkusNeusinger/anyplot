"""
Tests for GET /debug/agent-usage, GET /debug/agent-usage/daily and api/agent_usage.py — the agent usage
highlights and the per-day table read from BigQuery.

No test reaches BigQuery: `get_usage_query` is overridden with a fake that records the SQL and answers rows.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import agent_usage
from api.agent_usage import (
    CACHE_TTL_S,
    DATASET_PATTERN,
    LIMIT_CODES,
    clear_usage_cache,
    daily_sql,
    daily_start,
    decode_rows,
    read_daily,
    read_usage,
    usage_query,
    usage_sql,
    window_start,
)
from api.main import app, fastapi_app
from api.routers.debug import get_usage_query, require_admin
from core.config import settings


DATASET = "anyplot.agent_telemetry"
ROW: dict[str, Any] = {
    "sessions": 12,
    "plots_shipped": 30,
    "kept_rate": 0.4166666,
    "kept_sessions": 5,
    "shipped_sessions": 12,
    "repair_rate": 0.3125,
    "repaired_runs": 5,
    "runs": 16,
    "top_specs": [{"key": "scatter-basic", "count": 5}, {"key": "bar-basic", "count": 3}],
    "top_formats": [{"key": "csv", "count": 9}],
    "top_refusals": [{"key": "unparseable", "count": 3}, {"key": None, "count": 1}],
}


class FakeQuery:
    def __init__(self, rows: list[dict[str, Any]] | None = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, datetime]] = []
        self._rows = rows if rows is not None else [ROW]
        self._error = error

    def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
        self.calls.append((sql, since))
        if self._error is not None:
            raise self._error
        return self._rows


@pytest.fixture(autouse=True)
def fresh_cache() -> Iterator[None]:
    clear_usage_cache()
    yield
    clear_usage_cache()


@pytest.fixture
def fake() -> FakeQuery:
    return FakeQuery()


@pytest.fixture
def client(fake: FakeQuery):
    fastapi_app.dependency_overrides[require_admin] = lambda: None
    fastapi_app.dependency_overrides[get_usage_query] = lambda: fake
    with patch.object(settings, "agent_telemetry_dataset", DATASET):
        yield TestClient(app)
    fastapi_app.dependency_overrides.clear()


class TestEndpoint:
    def test_answers_the_aggregates(self, client, fake) -> None:
        response = client.get("/debug/agent-usage?days=30")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok" and body["days"] == 30
        assert (body["sessions"], body["plots_shipped"]) == (12, 30)
        assert body["kept_rate"] == 0.4167 and body["repair_rate"] == 0.3125
        # The counts behind both rates, for the card's "5 of 12".
        assert (body["kept_sessions"], body["shipped_sessions"]) == (5, 12)
        assert (body["repaired_runs"], body["runs"]) == (5, 16)
        assert body["top_specs"] == [{"key": "scatter-basic", "count": 5}, {"key": "bar-basic", "count": 3}]
        assert body["top_refusals"] == [{"key": "unparseable", "count": 3}]  # a null key is dropped
        assert body["generated_at"].endswith("Z")
        sql, since = fake.calls[0]
        assert f"`{DATASET}_logs._AllLogs`" in sql
        assert timedelta(days=30) <= datetime.now(UTC) - since < timedelta(days=30, minutes=11)

    def test_defaults_to_seven_days(self, client, fake) -> None:
        assert client.get("/debug/agent-usage").json()["days"] == 7
        assert datetime.now(UTC) - fake.calls[0][1] < timedelta(days=7, minutes=11)

    def test_a_second_load_runs_no_query(self, client, fake) -> None:
        client.get("/debug/agent-usage")
        client.get("/debug/agent-usage")
        client.get("/debug/agent-usage?days=30")
        assert len(fake.calls) == 2  # one per window

    @pytest.mark.parametrize("days", ["8", "0", "365", "seven"])
    def test_other_windows_are_refused(self, client, fake, days) -> None:
        assert client.get(f"/debug/agent-usage?days={days}").status_code in (400, 422)
        assert fake.calls == []

    def test_not_configured_is_an_empty_state(self, client, fake) -> None:
        with patch.object(settings, "agent_telemetry_dataset", None):
            body = client.get("/debug/agent-usage").json()
        assert body["status"] == "not_configured" and body["sessions"] == 0 and body["top_specs"] == []
        assert fake.calls == []

    def test_a_failed_query_is_unavailable(self, client) -> None:
        fastapi_app.dependency_overrides[get_usage_query] = lambda: FakeQuery(error=RuntimeError("403 Access Denied"))
        body = client.get("/debug/agent-usage").json()
        assert body["status"] == "unavailable" and body["kept_rate"] is None and body["top_formats"] == []

    def test_no_client_is_unavailable(self, client) -> None:
        fastapi_app.dependency_overrides[get_usage_query] = lambda: None
        assert client.get("/debug/agent-usage").json()["status"] == "unavailable"

    def test_needs_the_admin_gate(self) -> None:
        fastapi_app.dependency_overrides[get_usage_query] = lambda: FakeQuery()
        try:
            with patch.object(settings, "admin_token", "supersecret"):
                response = TestClient(app).get("/debug/agent-usage")
        finally:
            fastapi_app.dependency_overrides.clear()
        assert response.status_code == 401


class TestCache:
    def test_an_answer_is_kept_for_the_ttl(self) -> None:
        fake, now = FakeQuery(), [100.0]
        read_usage(fake, DATASET, 7, clock=lambda: now[0])
        now[0] += CACHE_TTL_S - 1
        read_usage(fake, DATASET, 7, clock=lambda: now[0])
        assert len(fake.calls) == 1
        now[0] += 2
        read_usage(fake, DATASET, 7, clock=lambda: now[0])
        assert len(fake.calls) == 2

    def test_a_failure_is_never_kept(self) -> None:
        failing = FakeQuery(error=RuntimeError("timeout"))
        assert read_usage(failing, DATASET, 7).status == "unavailable"
        working = FakeQuery()
        assert read_usage(working, DATASET, 7).status == "ok" and len(working.calls) == 1

    def test_the_window_start_moves_in_ten_minute_steps(self) -> None:
        a = window_start(7, datetime(2026, 10, 16, 12, 1, 5, tzinfo=UTC))
        b = window_start(7, datetime(2026, 10, 16, 12, 9, 59, tzinfo=UTC))
        c = window_start(7, datetime(2026, 10, 16, 12, 10, 0, tzinfo=UTC))
        assert a == b == datetime(2026, 10, 9, 12, 0, tzinfo=UTC)
        assert c == datetime(2026, 10, 9, 12, 10, tzinfo=UTC)

    def test_a_client_that_failed_to_start_is_tried_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        attempts: list[str] = []

        class Flaky:
            def __init__(self, project: str) -> None:
                attempts.append(project)
                if len(attempts) == 1:
                    raise RuntimeError("no credentials yet")

            def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
                return []

        monkeypatch.setattr(agent_usage, "BigQueryUsage", Flaky)
        monkeypatch.setattr(agent_usage, "_CLIENTS", {})
        assert usage_query(DATASET) is None
        first = usage_query(DATASET)
        assert first is not None and usage_query(DATASET) is first
        assert attempts == ["anyplot", "anyplot"]


class TestRestAnswer:
    """`decode_rows` reads BigQuery's `jobs.query` REST answer, where every scalar is a string."""

    ANSWER: dict[str, Any] = {
        "jobComplete": True,
        "schema": {
            "fields": [
                {"name": "sessions", "type": "INTEGER", "mode": "NULLABLE"},
                {"name": "kept_rate", "type": "FLOAT", "mode": "NULLABLE"},
                {"name": "repair_rate", "type": "FLOAT", "mode": "NULLABLE"},
                {
                    "name": "top_specs",
                    "type": "RECORD",
                    "mode": "REPEATED",
                    "fields": [
                        {"name": "key", "type": "STRING", "mode": "NULLABLE"},
                        {"name": "count", "type": "INTEGER", "mode": "NULLABLE"},
                    ],
                },
            ]
        },
        "rows": [
            {
                "f": [
                    {"v": "12"},
                    {"v": "0.25"},
                    {"v": None},
                    {"v": [{"v": {"f": [{"v": "scatter-basic"}, {"v": "5"}]}}]},
                ]
            }
        ],
    }

    def test_types_the_cells_by_the_schema(self) -> None:
        assert decode_rows(self.ANSWER) == [
            {
                "sessions": 12,
                "kept_rate": 0.25,
                "repair_rate": None,
                "top_specs": [{"key": "scatter-basic", "count": 5}],
            }
        ]

    def test_feeds_the_card(self) -> None:
        class Rest:
            def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
                return decode_rows(TestRestAnswer.ANSWER)

        usage = read_usage(Rest(), DATASET, 7)
        assert (usage.status, usage.sessions, usage.kept_rate) == ("ok", 12, 0.25)
        assert usage.top_specs[0].key == "scatter-basic" and usage.top_specs[0].count == 5

    def test_an_incomplete_job_is_unavailable(self) -> None:
        class Slow:
            def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
                return decode_rows({"jobComplete": False})

        assert read_usage(Slow(), DATASET, 7).status == "unavailable"

    def test_no_rows_is_empty(self) -> None:
        assert decode_rows({"jobComplete": True, "schema": {"fields": []}}) == []


class TestQuery:
    def test_prunes_to_the_window_before_it_deduplicates(self) -> None:
        sql = usage_sql(DATASET)
        assert sql.index("timestamp >= @since") < sql.index("QUALIFY ROW_NUMBER()")
        assert "CURRENT_TIMESTAMP" not in sql  # the window comes from `@since`, so the process cache keys hold
        assert "'live'" in sql and "LIMIT 5" in sql

    def test_a_save_is_no_keep_and_a_rejection_or_a_later_run_undoes_one(self) -> None:
        """Owner rule of 2026-10-16: users save a session to report a plot they did not like."""
        sql = usage_sql(DATASET)
        keeps = (
            "'copied_code', 'copied_image', 'downloaded_png', 'downloaded_code', 'downloaded_page', 'downloaded_data'"
        )
        assert f"IN ({keeps}), ts, NULL)) AS last_keep_at" in sql and "saved_session" not in sql
        assert "IN ('thumbs_down', 'bug')" in sql
        assert "outcomes.last_keep_at > per_session.last_run_at" in sql
        # Review of #12207: a thumbs_down sent just before the window still rejects a session that straddles it.
        assert "timestamp >= TIMESTAMP_SUB(@since, INTERVAL 2 DAY)" in sql
        assert "NOT IN (SELECT session FROM rejections" in sql
        # A plot shipped just before the window and kept inside it counts as shipped and kept.
        runs = sql[sql.index("per_session AS") : sql.index("outcomes AS")]
        assert "INTERVAL 2 DAY" in runs and "IN (SELECT session FROM ev)" in runs

    def test_counts_an_input_once_and_leaves_not_ready_runs_out(self) -> None:
        sql = usage_sql(DATASET)
        assert "JSON_VALUE(payload.outcome) != 'transcribed'" in sql
        assert "JSON_VALUE(payload.status) != 'not_ready'" in sql

    @pytest.mark.parametrize("dataset", ["anyplot.agent_telemetry", "my-project-1.usage_views"])
    def test_accepts_a_dataset_name(self, dataset) -> None:
        assert DATASET_PATTERN.fullmatch(dataset)

    @pytest.mark.parametrize(
        "dataset", ["agent_telemetry", "anyplot.agent`; DROP TABLE x; --", "anyplot.agent telemetry", "Anyplot.x"]
    )
    def test_a_dataset_that_could_break_the_sql_is_not_configured(self, dataset) -> None:
        fake = FakeQuery()
        assert read_usage(fake, dataset, 7).status == "not_configured"
        assert fake.calls == []

    def test_an_empty_answer_is_zero(self) -> None:
        usage = read_usage(FakeQuery(rows=[]), DATASET, 7)
        assert usage.status == "ok" and usage.sessions == 0 and usage.kept_rate is None


NOW = datetime(2026, 11, 2, 14, 5, 30, tzinfo=UTC)
DAY_ROWS: list[dict[str, Any]] = [
    {
        "day": "2026-11-02",
        "sessions": 4,
        "plots_shipped": 3,
        "hits_service_paused": 2,
        "hits_capacity": 1,
        "queue_wait_p95_ms": 12_400,
        "queue_waits": 3,
        "cost_usd": 0.022837133,
        "fanout_cost_usd": 0.1210845185,
        "unpriced_calls": 0,
    },
    # A day with lines but no shipped plot and a run before the queue-wait field: no percentile.
    {"day": "2026-10-28", "sessions": 11, "cost_usd": 0.17469341, "queue_wait_p95_ms": None, "queue_waits": 0},
    {"day": None, "sessions": 99},  # never a row without its day
]


class TestDaily:
    def test_answers_every_day_of_the_window_newest_first(self, client, fake) -> None:
        fake._rows = DAY_ROWS
        body = client.get("/debug/agent-usage/daily").json()

        assert body["status"] == "ok" and body["days"] == 14 and len(body["rows"]) == 14
        dates = [row["date"] for row in body["rows"]]
        assert dates == sorted(dates, reverse=True) and dates[0] == datetime.now(UTC).date().isoformat()
        sql, since = fake.calls[0]
        assert f"`{DATASET}_logs._AllLogs`" in sql and f"`{DATASET}.model_prices`" in sql
        assert since == datetime.combine(datetime.now(UTC).date() - timedelta(days=13), datetime.min.time(), UTC)

    def test_reads_a_day_and_fills_the_days_without_lines(self) -> None:
        daily = read_daily(FakeQuery(rows=DAY_ROWS), DATASET, now=NOW)
        today, quiet, busy = daily.rows[0], daily.rows[1], daily.rows[5]

        assert (today.date, today.sessions, today.plots_shipped) == ("2026-11-02", 4, 3)
        assert (today.cost_usd, today.fanout_cost_usd, today.unpriced_calls) == (0.0228, 0.1211, 0)
        assert today.limit_hits == {
            "service_paused": 2,
            "budget": 0,
            "daily_limit": 0,
            "rate_limited": 0,
            "run_limit": 0,
            "capacity": 1,
        }
        assert (today.queue_wait_p95_ms, today.queue_waits) == (12_400, 3)
        # A day without a line is zeros, and its percentile is unknown, not 0.
        assert quiet.date == "2026-11-01" and quiet.sessions == 0 and quiet.cost_usd == 0.0
        assert quiet.queue_wait_p95_ms is None and set(quiet.limit_hits.values()) == {0}
        assert (busy.date, busy.sessions, busy.cost_usd, busy.queue_wait_p95_ms) == ("2026-10-28", 11, 0.1747, None)
        assert daily.rows[-1].date == "2026-10-20" and 99 not in [row.sessions for row in daily.rows]

    def test_the_window_starts_at_midnight_and_stays_for_the_day(self) -> None:
        morning = daily_start(datetime(2026, 11, 2, 0, 0, 1, tzinfo=UTC))
        night = daily_start(datetime(2026, 11, 2, 23, 59, 59, tzinfo=UTC))
        assert morning == night == datetime(2026, 10, 20, tzinfo=UTC)
        assert daily_start(datetime(2026, 11, 3, tzinfo=UTC)) == datetime(2026, 10, 21, tzinfo=UTC)

    def test_an_answer_is_kept_and_a_new_day_queries_anew(self) -> None:
        fake, now = FakeQuery(rows=DAY_ROWS), [100.0]
        read_daily(fake, DATASET, now=NOW, clock=lambda: now[0])
        now[0] += CACHE_TTL_S - 1
        read_daily(fake, DATASET, now=NOW, clock=lambda: now[0])
        assert len(fake.calls) == 1
        read_daily(fake, DATASET, now=NOW + timedelta(days=1), clock=lambda: now[0])
        assert len(fake.calls) == 2  # the window moved: another key

    def test_the_statuses_carry_no_rows(self) -> None:
        assert read_daily(FakeQuery(), None).status == "not_configured"
        assert read_daily(None, DATASET).status == "unavailable"
        failing = FakeQuery(error=RuntimeError("403 Access Denied"))
        failed = read_daily(failing, DATASET, now=NOW)
        assert failed.status == "unavailable" and failed.rows == []
        # A failure is never kept.
        assert read_daily(FakeQuery(rows=[]), DATASET, now=NOW).status == "ok"

    def test_needs_the_admin_gate(self) -> None:
        fastapi_app.dependency_overrides[get_usage_query] = lambda: FakeQuery()
        try:
            with patch.object(settings, "admin_token", "supersecret"):
                response = TestClient(app).get("/debug/agent-usage/daily")
        finally:
            fastapi_app.dependency_overrides.clear()
        assert response.status_code == 401


class TestDailyQuery:
    def test_prunes_to_the_window_before_it_deduplicates(self) -> None:
        sql = daily_sql(DATASET)
        assert sql.index("timestamp >= TIMESTAMP_SUB(@since, INTERVAL 2 DAY)") < sql.index("QUALIFY ROW_NUMBER()")
        assert "CURRENT_TIMESTAMP" not in sql and "CURRENT_DATE" not in sql
        # The lookback only dates the chats: every count of the window reads from its start.
        assert sql.count("WHERE ts >= @since") == 3 and "WHERE first_ts >= @since" in sql
        # As the card's `COUNT(DISTINCT session)`: a line without a session is no chat.
        assert "source = 'live' AND session IS NOT NULL GROUP BY session" in sql

    def test_counts_live_lines_and_the_fanout_cost_apart(self) -> None:
        sql = daily_sql(DATASET)
        assert "JSON_VALUE(json_payload.source) IN ('live', 'fanout')" in sql and "harness" not in sql
        lines = sql[sql.index("lines AS") : sql.index("steps AS")]
        assert "source = 'live'" in lines
        assert "SUM(IF(source = 'live', usd, 0)) AS cost_usd" in sql
        assert "SUM(IF(source = 'fanout', usd, 0)) AS fanout_cost_usd" in sql

    def test_prices_as_the_cost_view_does(self) -> None:
        """The same steps, the same model id clean-up and the same cache factors as `05_prices_cost.sql`."""
        view = (Path(__file__).parents[3] / "agents/telemetry/views/05_prices_cost.sql").read_text(encoding="utf-8")
        sql = daily_sql(DATASET)
        for fragment in (
            r"r'(@.*|-[0-9]{8})$'",
            "UNNEST(JSON_QUERY_ARRAY(",
            "* prices.input_usd_per_m * 0.1",
            "* prices.input_usd_per_m * 1.25",
            "* prices.output_usd_per_m",
            ") / 1e6",
        ):
            assert fragment in view and fragment in sql, fragment
        steps = sql[sql.index("steps AS") : sql.index("costs AS")]
        assert "event = 'chat_turn'" in steps and "event = 'data_input'" in steps and "pipeline_run" not in steps

    def test_counts_every_limit_code_where_a_line_records_it(self) -> None:
        sql = daily_sql(DATASET)
        for code in LIMIT_CODES:
            assert f"COUNTIF(code = '{code}') AS hits_{code}" in sql
        assert "IFNULL(JSON_VALUE(payload.refusal), JSON_VALUE(payload.error))" in sql
        assert "WHEN 'data_input' THEN JSON_VALUE(payload.outcome)" in sql
        assert "APPROX_QUANTILES(queue_wait_ms, 100 IGNORE NULLS)[SAFE_OFFSET(95)]" in sql
