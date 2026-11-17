"""Tests for the private list of gallery searches that found nothing (`api/search_misses.py`) and its routes.

What is under test: that the text is normalised by the app's rule, that only the production service
counts, that the answer is the same `204` whatever happened, that the limits hold, and that the text
goes nowhere but its row: not into a log, not into an error answer, never read from a URL or a header.
"""

import asyncio
import json
import logging
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError

from api import search_misses
from api.main import app, fastapi_app
from api.routers.debug import require_admin
from api.search_misses import (
    LIST_LIMIT,
    MAX_NEW_QUERIES_PER_DAY,
    MAX_QUERY_LENGTH,
    MIN_QUERY_LENGTH,
    RATE_LIMIT_MAX,
    RETENTION_DAYS,
    SearchMissesResponse,
    is_countable,
    normalize_query,
    read_misses,
    record_miss,
    retention_cutoff,
)
from core.config import settings
from core.database import get_db


ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "app" / "src" / "hooks" / "searchQuery.cases.json").read_text(encoding="utf-8"))
TODAY = date(2026, 11, 17)
# Stands for what a visitor typed: it must turn up in the row and nowhere else.
CANARY = "canary zq7x"


def _request(address: str = "203.0.113.7") -> MagicMock:
    """A request through the edge from *address*."""
    request = MagicMock()
    request.headers = {"cf-connecting-ip": address}
    return request


@pytest.fixture(autouse=True)
def _fresh_state() -> Iterator[None]:
    """Every test starts with an empty rate limit and a purge that has not run today."""
    with patch.object(search_misses, "_RATE_LIMIT", search_misses._RateLimit()):
        search_misses._Purge.day = None
        yield
        search_misses._Purge.day = None


@pytest.fixture
def counted() -> Iterator[AsyncMock]:
    """The background write, replaced: what it was called with is what would be counted."""
    with patch.object(search_misses, "_count", new_callable=AsyncMock) as write:
        yield write


async def _settle() -> None:
    for write in list(search_misses._WRITES):
        await write


def _logged(caplog: pytest.LogCaptureFixture) -> str:
    """Everything the test's log records hold: the messages, their arguments and any traceback."""
    return (
        "\n".join(f"{record.getMessage()} {record.args!r} {record.exc_text or ''}" for record in caplog.records)
        + caplog.text
    )


class FakeSession:
    """`get_db_context` without a database: yields a session the patched repository ignores."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def __aenter__(self) -> MagicMock:
        if self.error is not None:
            raise self.error
        return MagicMock()

    async def __aexit__(self, *exc: object) -> None:
        return None


class TestNormalizeQuery:
    """The server's rule is the app's `normalizeQuery`: both read the same cases."""

    @pytest.mark.parametrize("case", CASES["cases"], ids=[case["rule"] for case in CASES["cases"]])
    def test_gives_the_text_the_app_sends(self, case: dict[str, str]) -> None:
        assert normalize_query(case["typed"]) == case["sent"]

    def test_the_bounds_are_the_apps(self) -> None:
        assert MAX_QUERY_LENGTH == CASES["max_length"] == 40
        assert MIN_QUERY_LENGTH == CASES["min_length"] == 2

    def test_a_normalised_text_stays_as_it_is(self) -> None:
        """The app sends a normalised text, and the server's second pass changes nothing in it."""
        for case in CASES["cases"]:
            assert normalize_query(case["sent"]) == case["sent"]


class TestIsCountable:
    @pytest.mark.parametrize(
        ("query", "countable"),
        [
            ("sp", True),
            ("spider", True),
            ("s", False),
            ("", False),
            ("a\x00b", False),  # PostgreSQL holds no NUL
            ("ab\ud800", False),  # half of a surrogate pair, which UTF-8 cannot encode
        ],
        ids=["two", "word", "one", "empty", "nul", "lone-surrogate"],
    )
    def test_counts_two_characters_or_more_that_postgresql_can_hold(self, query: str, countable: bool) -> None:
        assert is_countable(query) is countable


class TestRateLimit:
    def test_a_network_gets_twenty_requests_a_minute(self) -> None:
        limit = search_misses._RateLimit()
        assert all(limit.allows("hmac:a", 60.0 + second) for second in range(RATE_LIMIT_MAX))
        assert not limit.allows("hmac:a", 119.0)
        assert limit.allows("hmac:b", 119.0)

    def test_the_next_minute_starts_over_and_forgets_the_keys(self) -> None:
        limit = search_misses._RateLimit()
        for _ in range(RATE_LIMIT_MAX + 5):
            limit.allows("hmac:a", 61.0)
        assert limit.allows("hmac:b", 61.0)

        assert limit.allows("hmac:a", 120.0)
        assert set(limit.requests) == {"hmac:a"}  # no key outlives its minute

    def test_the_networks_followed_in_one_minute_are_bounded(self) -> None:
        limit = search_misses._RateLimit()
        with patch.object(search_misses, "MAX_TRACKED_NETWORKS", 2):
            assert limit.allows("hmac:a", 0.0) and limit.allows("hmac:b", 0.0)
            assert not limit.allows("hmac:c", 0.0)
            assert limit.allows("hmac:a", 0.0)  # a network already followed still counts
            assert limit.allows("hmac:c", 60.0)


class TestRecordMiss:
    """Who is counted, and that only the production service counts."""

    async def test_counts_the_normalised_text_of_the_day_in_production(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"), patch.object(search_misses, "datetime") as clock:
            clock.now.return_value.date.return_value = TODAY
            record_miss(_request(), "  SPIDER   Chart ")
            await _settle()

        counted.assert_awaited_once_with(TODAY, "spider chart")

    @pytest.mark.parametrize("environment", ["development", "test", "staging"])
    async def test_counts_nothing_outside_production(self, counted: AsyncMock, environment: str) -> None:
        with patch.object(settings, "environment", environment):
            record_miss(_request(), "spider")
            await _settle()

        counted.assert_not_called()

    @pytest.mark.parametrize("text", ["s", "  S  ", "", "   ", "a\x00b"])
    async def test_drops_a_text_that_is_not_countable_after_normalising(self, counted: AsyncMock, text: str) -> None:
        with patch.object(settings, "environment", "production"):
            record_miss(_request(), text)
            await _settle()

        counted.assert_not_called()

    async def test_a_network_beyond_its_limit_is_not_counted_and_another_still_is(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"):
            for number in range(RATE_LIMIT_MAX + 3):
                record_miss(_request("203.0.113.7"), f"text {number}")
            record_miss(_request("198.51.100.8"), "spider")
            await _settle()

        assert counted.await_count == RATE_LIMIT_MAX + 1
        assert counted.await_args.args[1] == "spider"

    async def test_every_request_counts_against_the_limit_also_a_dropped_one(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"):
            for _ in range(RATE_LIMIT_MAX):
                record_miss(_request(), "s")
            record_miss(_request(), "spider")
            await _settle()

        counted.assert_not_called()

    async def test_a_flood_is_not_queued_without_end(self, counted: AsyncMock) -> None:
        release = asyncio.Event()

        async def wait(*_args: object) -> None:
            await release.wait()

        counted.side_effect = wait
        with patch.object(settings, "environment", "production"), patch.object(search_misses, "MAX_PENDING_WRITES", 3):
            for number in range(8):
                record_miss(_request(f"203.0.113.{number}"), "spider")
            await asyncio.sleep(0)
            assert len(search_misses._WRITES) == 3
            release.set()
            await _settle()
            await asyncio.sleep(0)  # the done callbacks that take the writes off the list

        assert counted.await_count == 3
        assert not search_misses._WRITES

    async def test_the_write_holds_the_day_and_the_text_only(self, counted: AsyncMock) -> None:
        """A row is a text, a day and a count: the address and the network's key go nowhere."""
        request = _request("203.0.113.7")
        request.headers["user-agent"] = "Mozilla/5.0 (X11; Linux x86_64)"
        with patch.object(settings, "environment", "production"), patch.object(search_misses, "datetime") as clock:
            clock.now.return_value.date.return_value = TODAY
            record_miss(request, "spider")
            await _settle()

        assert counted.await_args.args == (TODAY, "spider")
        assert counted.await_args.kwargs == {}


class TestCount:
    """The background write: the day's cap, the purge once a day, and a failure that reaches nobody."""

    @pytest.fixture
    def repository(self) -> Iterator[MagicMock]:
        with (
            patch.object(search_misses, "get_db_context", side_effect=lambda: FakeSession()),
            patch.object(search_misses, "SearchMissRepository") as repository,
        ):
            repository.return_value.count = AsyncMock(return_value=True)
            repository.return_value.delete_before = AsyncMock(return_value=0)
            yield repository.return_value

    async def test_passes_the_days_cap_to_the_counter(self, repository: MagicMock) -> None:
        await search_misses._count(TODAY, "spider")

        repository.count.assert_awaited_once_with(day=TODAY, query="spider", max_new_per_day=MAX_NEW_QUERIES_PER_DAY)
        assert MAX_NEW_QUERIES_PER_DAY == 1000

    async def test_purges_the_rows_past_the_retention_once_per_utc_day(self, repository: MagicMock) -> None:
        await search_misses._count(TODAY, "spider")
        await search_misses._count(TODAY, "splom")
        await search_misses._count(TODAY + timedelta(days=1), "spider")

        assert [call.args for call in repository.delete_before.await_args_list] == [
            (TODAY - timedelta(days=RETENTION_DAYS),),
            (TODAY + timedelta(days=1) - timedelta(days=RETENTION_DAYS),),
        ]
        assert RETENTION_DAYS == 90

    async def test_a_failed_purge_reaches_nobody_and_waits_for_the_next_day(self, repository: MagicMock) -> None:
        repository.delete_before.side_effect = ProgrammingError("DELETE", {}, Exception("timeout"))
        await search_misses._count(TODAY, "spider")
        await search_misses._count(TODAY, "splom")

        assert repository.delete_before.await_count == 1
        assert repository.count.await_count == 2

    async def test_a_failed_write_logs_its_class_and_never_the_text(
        self, repository: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing table is the case that will happen: the migration reaches production after the deploy."""
        caplog.set_level(logging.DEBUG)
        repository.count.side_effect = ProgrammingError(
            "INSERT INTO search_misses ...", {"query": CANARY}, Exception(f'relation "search_misses" ... {CANARY}')
        )

        await search_misses._count(TODAY, CANARY)

        assert "search miss not counted (non-critical): ProgrammingError" in caplog.text
        assert CANARY not in _logged(caplog)
        repository.delete_before.assert_awaited_once()  # the purge still runs

    async def test_a_failed_connection_reaches_nobody(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        with patch.object(
            search_misses, "get_db_context", side_effect=lambda: FakeSession(RuntimeError(f"no database {CANARY}"))
        ):
            await search_misses._count(TODAY, CANARY)

        assert "search miss not counted (non-critical): RuntimeError" in caplog.text
        assert CANARY not in _logged(caplog)


async def _post(
    body: Any = None, *, content: str | None = None, headers: dict[str, str] | None = None, params: dict | None = None
) -> httpx.Response:
    """POST /search/miss through the whole app, on the test's own loop, so its background write can be awaited."""
    transport = httpx.ASGITransport(app=app, client=("203.0.113.7", 50000))
    async with httpx.AsyncClient(transport=transport, base_url="https://api.anyplot.ai") as client:
        if content is not None:
            return await client.post("/search/miss", content=content, headers=headers, params=params)
        return await client.post("/search/miss", json=body, headers=headers, params=params)


class TestRoute:
    """`POST /search/miss`: always the same `204`, the text from the body only, and errors that do not repeat it."""

    async def test_answers_204_without_a_body_whatever_happens(self, counted: AsyncMock) -> None:
        answers = []
        with patch.object(settings, "environment", "production"):
            answers.append(await _post({"query": "spider"}))  # counted
            answers.append(await _post({"query": "s"}))  # dropped: too short
            for _ in range(RATE_LIMIT_MAX):
                answers.append(await _post({"query": "splom"}))  # the last ones beyond the limit
        with patch.object(settings, "environment", "development"):
            answers.append(await _post({"query": "spider"}))  # not counted outside production
        await _settle()

        assert {(answer.status_code, answer.content) for answer in answers} == {(204, b"")}
        assert counted.await_count == RATE_LIMIT_MAX - 1  # spider once, splom until the network's 20 were used

    async def test_reads_the_text_from_the_body_only(self, counted: AsyncMock) -> None:
        """A text in the URL would stand in the request log for 30 days; neither it nor a header is read."""
        with patch.object(settings, "environment", "production"):
            answer = await _post({"query": "spider"}, params={"query": "from-url"}, headers={"X-Query": "from-header"})
            no_body = await _post(content="", params={"query": "from-url"}, headers={"X-Query": "from-header"})
            await _settle()

        assert answer.status_code == 204
        assert no_body.status_code == 422
        counted.assert_awaited_once()
        assert counted.await_args.args[1] == "spider"

    @pytest.mark.parametrize(
        ("body", "content"),
        [
            ({"query": [CANARY]}, None),  # a text that is no string
            ({"q": CANARY}, None),  # no `query`: the framework's error would hold the whole body
            (CANARY, None),  # a JSON string instead of an object
            (None, f'{{"query": "{CANARY}'),  # broken JSON
            (None, CANARY),  # no JSON at all
        ],
        ids=["not-a-string", "wrong-key", "not-an-object", "broken-json", "plain-text"],
    )
    async def test_a_malformed_body_gets_a_422_that_does_not_repeat_it(
        self, counted: AsyncMock, body: Any, content: str | None, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        headers = {"Content-Type": "text/plain"} if content == CANARY else None
        with patch.object(settings, "environment", "production"):
            answer = await _post(body, content=content, headers=headers)

        assert answer.status_code == 422
        assert CANARY not in answer.text
        assert CANARY.encode() not in answer.content
        for error in answer.json()["detail"]:
            assert set(error) <= {"type", "loc", "msg"}
        assert CANARY not in _logged(caplog)
        counted.assert_not_called()

    async def test_no_log_line_holds_the_text_of_an_accepted_a_refused_or_a_failing_request(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        failing = ProgrammingError("INSERT INTO search_misses ...", {"query": CANARY}, Exception(CANARY))
        with (
            patch.object(settings, "environment", "production"),
            patch.object(search_misses, "get_db_context", side_effect=lambda: FakeSession()),
            patch.object(search_misses, "SearchMissRepository") as repository,
        ):
            repository.return_value.count = AsyncMock(return_value=True)
            repository.return_value.delete_before = AsyncMock(return_value=0)
            accepted = await _post({"query": CANARY})
            refused = await _post({"q": CANARY})
            await _settle()
            repository.return_value.count.side_effect = failing
            failed = await _post({"query": f"{CANARY} 2"})
            await _settle()

        assert (accepted.status_code, refused.status_code, failed.status_code) == (204, 422, 204)
        assert [call.kwargs["query"] for call in repository.return_value.count.await_args_list] == [
            CANARY,
            f"{CANARY} 2",
        ]
        assert "search miss not counted (non-critical): ProgrammingError" in caplog.text
        assert CANARY not in _logged(caplog)


class TestReadMisses:
    async def test_reads_the_retention_window_most_searched_first(self) -> None:
        repository = MagicMock()
        repository.distinct_since = AsyncMock(return_value=612)
        repository.totals = AsyncMock(return_value=[("spider", 9, TODAY - timedelta(days=30), TODAY)])

        answer = await read_misses(repository, today=TODAY)

        since = retention_cutoff(TODAY)
        assert since == TODAY - timedelta(days=90)
        repository.totals.assert_awaited_once_with(since, limit=LIST_LIMIT)
        repository.distinct_since.assert_awaited_once_with(since)
        assert answer.model_dump() == {
            "status": "ok",
            "retention_days": 90,
            "texts": 612,
            "misses": [{"query": "spider", "count": 9, "first_day": "2026-10-18", "last_day": "2026-11-17"}],
        }


class TestDebugEndpoints:
    """`GET` and `DELETE /debug/search-misses`: the owner's list, for an admin only."""

    @staticmethod
    def _client(session: AsyncMock) -> TestClient:
        async def get_session():
            yield session

        fastapi_app.dependency_overrides[get_db] = get_session
        fastapi_app.dependency_overrides[require_admin] = lambda: None
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def _overrides(self) -> Iterator[None]:
        yield
        fastapi_app.dependency_overrides.clear()

    def test_refuses_a_visitor(self) -> None:
        with patch("api.dependencies.is_db_configured", return_value=True):
            client = TestClient(app)
            listed = client.get("/debug/search-misses")
            deleted = client.request("DELETE", "/debug/search-misses", json={"query": "spider"})
        assert listed.status_code in (401, 403, 503)
        assert deleted.status_code in (401, 403, 503)

    def test_lists_the_texts_for_an_admin(self) -> None:
        async def misses(_repository: object) -> SearchMissesResponse:
            return SearchMissesResponse(
                status="ok",
                texts=1,
                misses=[{"query": "spider", "count": 3, "first_day": "2026-11-01", "last_day": "2026-11-17"}],
            )

        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_search_misses", side_effect=misses),
        ):
            body = self._client(AsyncMock()).get("/debug/search-misses").json()

        assert body == {
            "status": "ok",
            "retention_days": 90,
            "texts": 1,
            "misses": [{"query": "spider", "count": 3, "first_day": "2026-11-01", "last_day": "2026-11-17"}],
        }

    def test_is_unavailable_while_the_table_is_missing(self) -> None:
        async def missing(_repository: object) -> SearchMissesResponse:
            raise ProgrammingError("SELECT", {}, Exception('relation "search_misses" does not exist'))

        session = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_search_misses", side_effect=missing),
        ):
            response = self._client(session).get("/debug/search-misses")

        assert response.status_code == 200
        assert response.json() == {"status": "unavailable", "retention_days": 90, "texts": 0, "misses": []}
        session.rollback.assert_awaited_once()

    def test_deletes_every_row_of_a_text_named_in_the_body(self) -> None:
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_query = AsyncMock(return_value=2)
            response = self._client(AsyncMock()).request(
                "DELETE", "/debug/search-misses", json={"query": "spider chart"}
            )

        assert response.status_code == 200
        assert response.json() == {"deleted": 2}
        repository.return_value.delete_query.assert_awaited_once_with("spider chart")

    def test_a_failed_delete_is_a_503_that_names_no_text(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        session = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_query = AsyncMock(
                side_effect=ProgrammingError("DELETE", {"query": CANARY}, Exception(CANARY))
            )
            response = self._client(session).request("DELETE", "/debug/search-misses", json={"query": CANARY})

        assert response.status_code == 503
        assert CANARY not in response.text
        assert CANARY not in _logged(caplog)
        session.rollback.assert_awaited_once()
