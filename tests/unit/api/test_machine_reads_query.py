"""
Tests for api/machine_reads_query.py and GET /debug/machine-readers: the machine-read telemetry's public tile
and the owner's section, read from BigQuery.

No test reaches BigQuery: the queries go to a fake that records the SQL and the window start and answers rows.
The public endpoint's tests live with the insights router (tests/unit/api/test_routers.py).
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import machine_reads_query
from api.agent_usage import decode_rows
from api.machine_reads import AUDIENCE_SQL
from api.machine_reads_query import (
    CONTENT_SURFACES,
    DETAIL_CACHE_TTL_S,
    PUBLIC_DAYS,
    MachineReadsUnavailable,
    clear_detail_cache,
    detail_sql,
    detail_start,
    public_sql,
    public_start,
    read_detail,
    read_public,
)
from api.main import app, fastapi_app
from api.routers.debug import get_machine_reads_query, require_admin
from core.config import settings


DATASET = "anyplot.machine_reads"
NOW = datetime(2026, 11, 9, 13, 50, tzinfo=UTC)

DETAIL_ROW: dict[str, Any] = {
    "requests": 81,
    "verified": 50,
    "unverified": 31,
    "mcp_calls": 4,
    "synthetic": 10,
    "vendors": [
        {
            "assistant": "perplexity",
            "kind": "index",
            "category": None,
            "requests": 27,
            "verified": 0,
            "unverified": 27,
            "pages": 14,
            "code": 8,
            "og": 5,
            "mcp": 0,
            "not_found": 0,
            "top_paths": [{"key": "code icicle-basic/altair", "count": 1}, {"key": "", "count": 1}],
        },
        {
            "assistant": "ahrefs",
            "kind": "seo",
            "category": "Search Engine Optimization",
            "requests": 25,
            "verified": 25,
            "unverified": 0,
            "pages": 3,
            "code": 0,
            "og": 2,
            "mcp": 0,
            "not_found": 1,
            "top_paths": [{"key": "other", "count": 6}],
        },
        {"assistant": None, "kind": "index", "requests": 3},
    ],
    "daily": [
        {
            "day": "2026-11-09",
            "for_person": 0,
            "index_training": 16,
            "search": 4,
            "seo": 30,
            "other": 0,
            "unverified": 31,
            "mcp": 4,
        }
    ],
}


class FakeQuery:
    def __init__(self, rows: list[dict[str, Any]] | None = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, datetime]] = []
        self._rows = rows if rows is not None else [DETAIL_ROW]
        self._error = error

    def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
        self.calls.append((sql, since))
        if self._error is not None:
            raise self._error
        return self._rows


@pytest.fixture(autouse=True)
def fresh_cache() -> Iterator[None]:
    clear_detail_cache()
    yield
    clear_detail_cache()


@pytest.fixture
def fake() -> FakeQuery:
    return FakeQuery()


@pytest.fixture
def client(fake: FakeQuery):
    fastapi_app.dependency_overrides[require_admin] = lambda: None
    fastapi_app.dependency_overrides[get_machine_reads_query] = lambda: fake
    with patch.object(settings, "machine_reads_dataset", DATASET):
        yield TestClient(app)
    fastapi_app.dependency_overrides.clear()


class TestQueries:
    @pytest.mark.parametrize("build", [public_sql, detail_sql])
    def test_prune_to_the_window_before_they_deduplicate(self, build) -> None:
        sql = build(DATASET)
        assert f"`{DATASET}_logs._AllLogs`" in sql
        assert sql.index("timestamp >= @since") < sql.index("QUALIFY ROW_NUMBER()")
        assert "PARTITION BY JSON_VALUE(json_payload.line_id)" in sql
        assert "JSON_VALUE(json_payload.log_type) = 'machine_read'" in sql
        assert "CURRENT_TIMESTAMP" not in sql and "CURRENT_DATE" not in sql
        # nginx writes an empty verdict for an unverified request; it reads as NULL, as in the `reads` view.
        assert "NULLIF(JSON_VALUE(json_payload.verified_category), '')" in sql
        assert AUDIENCE_SQL in sql

    def test_the_tile_counts_verified_served_live_reads_on_the_content_surfaces(self) -> None:
        sql = public_sql(DATASET)
        assert "source = 'live'" in sql
        assert "(status BETWEEN 200 AND 299 OR status = 304)" in sql
        assert f"surface IN ({', '.join(repr(surface) for surface in CONTENT_SURFACES)})" in sql
        for audience in ("for_person", "index_training", "search"):
            assert f"COUNTIF(verified_category IS NOT NULL AND audience = '{audience}') AS {audience}" in sql

    def test_the_tile_counts_mcp_over_every_client_and_unverified_only_for_a_named_vendor(self) -> None:
        sql = public_sql(DATASET)
        assert "COUNTIF(surface = 'mcp') AS mcp" in sql
        assert "verified_category IS NULL AND assistant != 'other'" in sql

    def test_the_owner_query_counts_every_live_line_and_the_synthetic_apart(self) -> None:
        sql = detail_sql(DATASET)
        assert "verified_category IS NOT NULL" in sql
        assert "status BETWEEN" not in sql  # every status: the matrix has a 404 column
        assert "COUNTIF(source = 'synthetic') FROM lines" in sql
        assert "PARTITION BY assistant, kind ORDER BY COUNT(*) DESC, key) <= 5" in sql

    def test_the_owner_query_keeps_every_surface(self) -> None:
        assert "surface IN ('page', 'shell', 'code', 'spec', 'mcp')" not in detail_sql(DATASET)


class TestWindows:
    def test_the_tile_starts_at_utc_midnight_27_days_back_all_day(self) -> None:
        early = public_start(datetime(2026, 11, 9, 0, 0, 1, tzinfo=UTC))
        late = public_start(datetime(2026, 11, 9, 23, 59, 59, tzinfo=UTC))
        assert early == late == datetime(2026, 10, 13, tzinfo=UTC)

    def test_the_owner_window_starts_at_utc_midnight_days_minus_one_back(self) -> None:
        assert detail_start(7, NOW) == datetime(2026, 11, 3, tzinfo=UTC)
        assert detail_start(30, NOW) == datetime(2026, 10, 11, tzinfo=UTC)
        assert detail_start(7, datetime(2026, 11, 9, 23, 59, tzinfo=UTC)) == detail_start(7, NOW)


class TestReadPublic:
    ROWS: list[dict[str, Any]] = [
        {"day": "2026-11-09", "for_person": 2, "index_training": 16, "search": 3, "mcp": 4, "unverified": 26},
        {"day": "2026-10-13", "for_person": 1, "index_training": 0, "search": 5, "mcp": 0, "unverified": 1},
    ]

    def test_zero_fills_28_days_oldest_first_and_sums_them(self) -> None:
        fake = FakeQuery(rows=self.ROWS)
        answer = read_public(fake, DATASET, now=NOW)
        assert answer.status == "ok" and answer.days == PUBLIC_DAYS
        assert [point.date for point in answer.points][:2] == ["2026-10-13", "2026-10-14"]
        assert answer.points[-1].date == "2026-11-09" and len(answer.points) == 28
        assert answer.points[1].model_dump() == {
            "date": "2026-10-14",
            "for_person": 0,
            "index_training": 0,
            "search": 0,
            "mcp": 0,
        }
        assert answer.totals.model_dump() == {
            "for_person": 3,
            "index_training": 16,
            "search": 8,
            "mcp": 4,
            "unverified": 27,
        }
        assert fake.calls[0][1] == datetime(2026, 10, 13, tzinfo=UTC)

    def test_an_empty_answer_is_28_zero_days(self) -> None:
        answer = read_public(FakeQuery(rows=[]), DATASET, now=NOW)
        assert answer.status == "ok" and len(answer.points) == 28
        assert answer.totals.model_dump() == dict.fromkeys(
            ("for_person", "index_training", "search", "mcp", "unverified"), 0
        )

    def test_raises_so_the_endpoint_keeps_nothing(self) -> None:
        with pytest.raises(RuntimeError):
            read_public(FakeQuery(error=RuntimeError("403 Access Denied")), DATASET)
        with pytest.raises(MachineReadsUnavailable):
            read_public(None, DATASET)
        with pytest.raises(ValueError):
            read_public(FakeQuery(), "anyplot.x`; DROP")


class TestReadDetail:
    def test_reads_the_totals_the_vendors_and_every_day_newest_first(self, fake) -> None:
        detail = read_detail(fake, DATASET, 7, now=NOW)
        assert detail.status == "ok" and detail.days == 7
        assert (detail.requests, detail.verified, detail.unverified, detail.mcp_calls, detail.synthetic) == (
            81,
            50,
            31,
            4,
            10,
        )
        # A row without a vendor is dropped; a path without a key too.
        assert [(vendor.assistant, vendor.kind) for vendor in detail.vendors] == [
            ("perplexity", "index"),
            ("ahrefs", "seo"),
        ]
        assert detail.vendors[0].category is None
        assert [path.key for path in detail.vendors[0].top_paths] == ["code icicle-basic/altair"]
        assert detail.vendors[1].not_found == 1
        assert [day.date for day in detail.daily] == [f"2026-11-0{n}" for n in range(9, 2, -1)]
        assert detail.daily[0].seo == 30 and detail.daily[1].model_dump()["unverified"] == 0
        assert fake.calls[0][1] == datetime(2026, 11, 3, tzinfo=UTC)

    def test_an_answer_is_kept_for_the_ttl_and_a_new_day_queries_anew(self, fake) -> None:
        now = [100.0]
        read_detail(fake, DATASET, 7, now=NOW, clock=lambda: now[0])
        now[0] += DETAIL_CACHE_TTL_S - 1
        read_detail(fake, DATASET, 7, now=NOW, clock=lambda: now[0])
        assert len(fake.calls) == 1
        read_detail(fake, DATASET, 30, now=NOW, clock=lambda: now[0])
        read_detail(fake, DATASET, 7, now=datetime(2026, 11, 10, 0, 1, tzinfo=UTC), clock=lambda: now[0])
        assert len(fake.calls) == 3
        now[0] += 2
        read_detail(fake, DATASET, 7, now=NOW, clock=lambda: now[0])
        assert len(fake.calls) == 4

    def test_expired_answers_are_dropped_on_the_next_write(self, fake) -> None:
        now = [100.0]
        read_detail(fake, DATASET, 7, now=NOW, clock=lambda: now[0])
        read_detail(fake, DATASET, 30, now=NOW, clock=lambda: now[0])
        assert len(machine_reads_query._DETAIL_CACHE) == 2
        now[0] += DETAIL_CACHE_TTL_S + 1
        read_detail(fake, DATASET, 7, now=datetime(2026, 11, 10, 9, 0, tzinfo=UTC), clock=lambda: now[0])
        assert list(machine_reads_query._DETAIL_CACHE) == [(DATASET, 7, "2026-11-04")]

    def test_a_failure_is_never_kept(self) -> None:
        failing = FakeQuery(error=RuntimeError("timeout"))
        detail = read_detail(failing, DATASET, 7, now=NOW)
        assert detail.status == "unavailable" and detail.requests == 0 and detail.daily == []
        working = FakeQuery()
        assert read_detail(working, DATASET, 7, now=NOW).status == "ok" and len(working.calls) == 1

    @pytest.mark.parametrize("dataset", [None, "", "machine_reads", "anyplot.x`; DROP TABLE y; --"])
    def test_an_unset_or_malformed_dataset_is_not_configured(self, fake, dataset) -> None:
        assert read_detail(fake, dataset, 7).status == "not_configured"
        assert fake.calls == []

    def test_no_client_is_unavailable(self) -> None:
        assert read_detail(None, DATASET, 7).status == "unavailable"


class TestRestAnswer:
    """`decode_rows` reads the owner's one row: REPEATED STRUCT vendors with a nested REPEATED STRUCT."""

    PATH_FIELDS = [
        {"name": "key", "type": "STRING", "mode": "NULLABLE"},
        {"name": "count", "type": "INTEGER", "mode": "NULLABLE"},
    ]
    ANSWER: dict[str, Any] = {
        "jobComplete": True,
        "schema": {
            "fields": [
                {"name": "requests", "type": "INTEGER", "mode": "NULLABLE"},
                {
                    "name": "vendors",
                    "type": "RECORD",
                    "mode": "REPEATED",
                    "fields": [
                        {"name": "assistant", "type": "STRING", "mode": "NULLABLE"},
                        {"name": "kind", "type": "STRING", "mode": "NULLABLE"},
                        {"name": "requests", "type": "INTEGER", "mode": "NULLABLE"},
                        {"name": "category", "type": "STRING", "mode": "NULLABLE"},
                        {"name": "top_paths", "type": "RECORD", "mode": "REPEATED", "fields": PATH_FIELDS},
                    ],
                },
                {
                    "name": "daily",
                    "type": "RECORD",
                    "mode": "REPEATED",
                    "fields": [
                        {"name": "day", "type": "DATE", "mode": "NULLABLE"},
                        {"name": "search", "type": "INTEGER", "mode": "NULLABLE"},
                    ],
                },
            ]
        },
        "rows": [
            {
                "f": [
                    {"v": "25"},
                    {
                        "v": [
                            {
                                "v": {
                                    "f": [
                                        {"v": "ahrefs"},
                                        {"v": "seo"},
                                        {"v": "25"},
                                        {"v": "Search Engine Optimization"},
                                        {"v": [{"v": {"f": [{"v": "plots_filter"}, {"v": "3"}]}}]},
                                    ]
                                }
                            }
                        ]
                    },
                    {"v": [{"v": {"f": [{"v": "2026-11-09"}, {"v": "4"}]}}]},
                ]
            }
        ],
    }

    def test_types_the_nested_cells(self) -> None:
        assert decode_rows(self.ANSWER) == [
            {
                "requests": 25,
                "vendors": [
                    {
                        "assistant": "ahrefs",
                        "kind": "seo",
                        "requests": 25,
                        "category": "Search Engine Optimization",
                        "top_paths": [{"key": "plots_filter", "count": 3}],
                    }
                ],
                "daily": [{"day": "2026-11-09", "search": 4}],
            }
        ]

    def test_feeds_the_section(self) -> None:
        class Rest:
            def rows(self, sql: str, since: datetime) -> list[dict[str, Any]]:
                return decode_rows(TestRestAnswer.ANSWER)

        detail = read_detail(Rest(), DATASET, 7, now=NOW)
        assert detail.status == "ok" and detail.requests == 25
        assert detail.vendors[0].top_paths[0].key == "plots_filter" and detail.vendors[0].top_paths[0].count == 3
        assert detail.daily[0].date == "2026-11-09" and detail.daily[0].search == 4


class TestEndpoint:
    def test_answers_the_detail(self, client, fake) -> None:
        response = client.get("/debug/machine-readers?days=30")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok" and body["days"] == 30 and len(body["daily"]) == 30
        assert body["vendors"][0]["assistant"] == "perplexity"
        assert body["generated_at"].endswith("Z")
        assert f"`{DATASET}_logs._AllLogs`" in fake.calls[0][0]

    def test_defaults_to_seven_days_and_a_second_load_runs_no_query(self, client, fake) -> None:
        assert client.get("/debug/machine-readers").json()["days"] == 7
        client.get("/debug/machine-readers?days=7")
        assert len(fake.calls) == 1

    @pytest.mark.parametrize("days", ["9", "0", "365"])
    def test_other_windows_are_a_400(self, client, fake, days) -> None:
        assert client.get(f"/debug/machine-readers?days={days}").status_code == 400
        assert fake.calls == []

    def test_a_window_that_is_no_number_is_refused(self, client, fake) -> None:
        assert client.get("/debug/machine-readers?days=seven").status_code in (400, 422)

    def test_not_configured_is_an_empty_state(self, client, fake) -> None:
        with patch.object(settings, "machine_reads_dataset", None):
            body = client.get("/debug/machine-readers").json()
        assert body["status"] == "not_configured" and body["vendors"] == [] and body["daily"] == []
        assert fake.calls == []

    def test_a_failed_query_is_unavailable(self, client) -> None:
        fastapi_app.dependency_overrides[get_machine_reads_query] = lambda: FakeQuery(error=RuntimeError("denied"))
        body = client.get("/debug/machine-readers").json()
        assert body["status"] == "unavailable" and body["requests"] == 0

    def test_needs_the_admin_gate(self) -> None:
        fastapi_app.dependency_overrides[get_machine_reads_query] = lambda: FakeQuery()
        try:
            with patch.object(settings, "admin_token", "supersecret"):
                response = TestClient(app).get("/debug/machine-readers")
        finally:
            fastapi_app.dependency_overrides.clear()
        assert response.status_code == 401
