"""
Tests for GET /debug/agent-usage and api/agent_usage.py — the agent usage highlights read from BigQuery.

No test reaches BigQuery: `get_usage_query` is overridden with a fake that records the SQL and answers rows.
"""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.agent_usage import DATASET_PATTERN, decode_rows, read_usage, usage_sql
from api.main import app, fastapi_app
from api.routers.debug import get_usage_query, require_admin
from core.config import settings


DATASET = "anyplot.agent_telemetry"
ROW: dict[str, Any] = {
    "sessions": 12,
    "plots_shipped": 30,
    "kept_rate": 0.4166666,
    "repair_rate": 0.3125,
    "top_specs": [{"key": "scatter-basic", "count": 5}, {"key": "bar-basic", "count": 3}],
    "top_formats": [{"key": "csv", "count": 9}],
    "top_refusals": [{"key": "unparseable", "count": 3}, {"key": None, "count": 1}],
}


class FakeQuery:
    def __init__(self, rows: list[dict[str, Any]] | None = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, int]] = []
        self._rows = rows if rows is not None else [ROW]
        self._error = error

    def rows(self, sql: str, days: int) -> list[dict[str, Any]]:
        self.calls.append((sql, days))
        if self._error is not None:
            raise self._error
        return self._rows


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
        assert body["top_specs"] == [{"key": "scatter-basic", "count": 5}, {"key": "bar-basic", "count": 3}]
        assert body["top_refusals"] == [{"key": "unparseable", "count": 3}]  # a null key is dropped
        assert body["generated_at"].endswith("Z")
        assert fake.calls[0][1] == 30 and f"`{DATASET}.events`" in fake.calls[0][0]

    def test_defaults_to_seven_days(self, client, fake) -> None:
        assert client.get("/debug/agent-usage").json()["days"] == 7
        assert fake.calls[0][1] == 7

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
            def rows(self, sql: str, days: int) -> list[dict[str, Any]]:
                return decode_rows(TestRestAnswer.ANSWER)

        usage = read_usage(Rest(), DATASET, 7)
        assert (usage.status, usage.sessions, usage.kept_rate) == ("ok", 12, 0.25)
        assert usage.top_specs[0].key == "scatter-basic" and usage.top_specs[0].count == 5

    def test_an_incomplete_job_is_unavailable(self) -> None:
        class Slow:
            def rows(self, sql: str, days: int) -> list[dict[str, Any]]:
                return decode_rows({"jobComplete": False})

        assert read_usage(Slow(), DATASET, 7).status == "unavailable"

    def test_no_rows_is_empty(self) -> None:
        assert decode_rows({"jobComplete": True, "schema": {"fields": []}}) == []


class TestQuery:
    def test_counts_live_sessions_only_and_takes_days_as_a_parameter(self) -> None:
        sql = usage_sql(DATASET)
        assert "source = 'live'" in sql and "INTERVAL @days DAY" in sql
        assert "LIMIT 5" in sql

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
