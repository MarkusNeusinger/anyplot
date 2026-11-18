"""Tests for the private list of gallery searches that found nothing (`api/search_misses.py`) and its routes.

What is under test: that the text is normalised by the app's rule and kept only when it reads as a
search for a plot, that only the production service counts and purges, that the answer is the same
`204` whatever happened, that a body is bounded before it is parsed, that the limits hold per network,
and that the text goes nowhere but its row: not into a log, not into an error answer, never read from
a URL or a header.
"""

import asyncio
import json
import logging
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError

from api import search_misses
from api.body_limit import TOO_LARGE
from api.main import app, fastapi_app
from api.request_context import network_of
from api.routers.debug import require_admin
from api.search_misses import (
    DEFAULT_IGNORABLE,
    JS_WHITESPACE,
    LIST_LIMIT,
    MAX_BODY_BYTES,
    MAX_NEW_QUERIES_PER_DAY,
    MAX_QUERY_DIGITS,
    MAX_QUERY_LENGTH,
    MAX_RAW_QUERY_LENGTH,
    MIN_QUERY_LENGTH,
    QUERY_MARKS,
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
CANARY = "canary zq"


def _request(address: str = "203.0.113.7") -> MagicMock:
    """A request through the edge from *address*."""
    request = MagicMock()
    request.headers = {"cf-connecting-ip": address}
    return request


@pytest.fixture(autouse=True)
def _fresh_state() -> Iterator[None]:
    """Every test starts with an empty rate limit, a purge that has not run today and no failure line yet."""
    with patch.object(search_misses, "_RATE_LIMIT", search_misses._RateLimit()):
        search_misses._Purge.day = None
        search_misses._FailureLog.last = None
        search_misses._FailureLog.held_back = 0
        yield
        search_misses._Purge.day = None
        search_misses._FailureLog.last = None
        search_misses._FailureLog.held_back = 0


@pytest.fixture
def counted() -> Iterator[AsyncMock]:
    """The background write, replaced: what it was called with is what would be counted."""
    with patch.object(search_misses, "_count", new_callable=AsyncMock) as write:
        yield write


@pytest.fixture
def production() -> Iterator[None]:
    with patch.object(settings, "environment", "production"):
        yield


async def _settle() -> None:
    for write in list(search_misses._WRITES):
        await write


def _logged(caplog: pytest.LogCaptureFixture) -> str:
    """Everything the test's log records hold: the messages, their arguments and any traceback."""
    return (
        "\n".join(f"{record.getMessage()} {record.args!r} {record.exc_text or ''}" for record in caplog.records)
        + caplog.text
    )


class DriverError(Exception):
    """The driver's error under SQLAlchemy's: asyncpg's carries the SQLSTATE beside its message."""

    def __init__(self, message: str, sqlstate: str) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


def _database_error(sqlstate: str = "42P01", detail: str = CANARY) -> ProgrammingError:
    """A database error as SQLAlchemy raises it from asyncpg: the SQLSTATE on `orig`, the text in the message."""
    orig = DriverError(f'relation "search_misses" does not exist {detail}', sqlstate)
    return ProgrammingError("INSERT INTO search_misses ...", {"query": detail}, orig)


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
    def test_gives_the_text_the_app_sends(self, case: dict[str, Any]) -> None:
        assert normalize_query(case["typed"]) == case["sent"]

    def test_the_bounds_are_the_apps(self) -> None:
        assert MAX_QUERY_LENGTH == CASES["max_length"]
        assert MIN_QUERY_LENGTH == CASES["min_length"]

    def test_a_normalised_text_stays_as_it_is(self) -> None:
        """The app sends a normalised text, and the server's second pass changes nothing in it."""
        for case in CASES["cases"]:
            assert normalize_query(case["sent"]) == case["sent"]

    def test_the_cases_hold_every_white_space_of_the_rule(self) -> None:
        """Each of these is invisible in a diff; a case with each one is what notices a lost one."""
        typed = "".join(case["typed"] for case in CASES["cases"])
        assert [f"U+{ord(char):04X}" for char in JS_WHITESPACE if char not in typed] == []
        assert len(JS_WHITESPACE) == 25


class TestIsCountable:
    """What is kept is a search for a plot: the rule is the app's, by character class, in any script."""

    @pytest.mark.parametrize("case", CASES["cases"], ids=[case["rule"] for case in CASES["cases"]])
    def test_keeps_what_the_app_sends(self, case: dict[str, Any]) -> None:
        assert is_countable(case["sent"]) is case["countable"]

    def test_the_rules_bounds_are_the_apps(self) -> None:
        assert MAX_QUERY_DIGITS == CASES["max_digits"]
        assert QUERY_MARKS == frozenset(CASES["marks"])

    def test_the_ignorable_code_points_are_the_ones_the_app_tests(self) -> None:
        """The app tests Unicode's property itself; its own test holds the shared ranges to that property."""
        assert DEFAULT_IGNORABLE == tuple((int(low, 16), int(high, 16)) for low, high in CASES["ignorable"])

    def test_every_ignorable_code_point_is_refused_except_a_joiner_between_letters(self) -> None:
        ignorable = [code for low, high in DEFAULT_IGNORABLE for code in range(low, high + 1)]
        kept = [f"U+{code:04X}" for code in ignorable if is_countable("ab" + chr(code) + "cd")]
        assert kept == ["U+200C", "U+200D"]

    @pytest.mark.parametrize(
        ("query", "countable"),
        [
            ("sp", True),
            ("s", False),
            ("a" + chr(0) + "b", False),  # PostgreSQL holds no NUL
            ("ab" + chr(0xD800), False),  # half of a surrogate pair, which UTF-8 cannot encode
            ("jane@doe", False),
            ("a" + chr(0x202E) + "b", False),  # a right-to-left override
        ],
        ids=["two", "one", "nul", "lone-surrogate", "at-sign", "bidi-override"],
    )
    def test_keeps_nothing_postgresql_cannot_store_or_a_reader_cannot_see(self, query: str, countable: bool) -> None:
        assert is_countable(query) is countable


class TestNetworkOf:
    """The rate limit's unit: an IPv4 address, or the /64 of an IPv6 address."""

    @pytest.mark.parametrize(
        ("address", "network"),
        [
            ("203.0.113.7", "203.0.113.7"),
            ("2001:db8:1:1::17", "2001:db8:1:1::/64"),
            ("2001:db8:1:1:ffff:ffff:ffff:ffff", "2001:db8:1:1::/64"),
            ("::ffff:203.0.113.7", "203.0.113.7"),
            (" 203.0.113.7 ", "203.0.113.7"),
            ("not an address", ""),
            ("", ""),
        ],
    )
    def test_names_the_network(self, address: str, network: str) -> None:
        assert network_of(address) == network


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
        assert set(limit.requests) == {"hmac:a"}  # the earlier minute's keys are gone

    def test_the_networks_followed_in_one_minute_are_bounded(self) -> None:
        limit = search_misses._RateLimit()
        with patch.object(search_misses, "MAX_TRACKED_NETWORKS", 2):
            assert limit.allows("hmac:a", 0.0) and limit.allows("hmac:b", 0.0)
            assert not limit.allows("hmac:c", 0.0)
            assert limit.allows("hmac:a", 0.0)  # a network already followed still counts
            assert limit.allows("hmac:c", 60.0)


class TestRecordMiss:
    """Who is counted, and that only the production service counts."""

    async def test_counts_the_normalised_text_of_the_day_in_production(self, counted: AsyncMock, production) -> None:
        with patch.object(search_misses, "datetime") as clock:
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

    @pytest.mark.parametrize(
        "text", ["s", "  S  ", "", "   ", "a" + chr(0) + "b", "jane.doe@example.org", "+41 79 123 45 67", "http://x.y"]
    )
    async def test_drops_a_text_that_is_not_countable_after_normalising(
        self, counted: AsyncMock, production, text: str
    ) -> None:
        record_miss(_request(), text)
        await _settle()

        counted.assert_not_called()

    async def test_cuts_the_raw_text_before_normalising(self, counted: AsyncMock, production) -> None:
        """No later change to the rule can make it run over more than a few hundred characters."""
        seen: list[int] = []

        def normalize(text: str) -> str:
            seen.append(len(text))
            return "spider"

        with patch.object(search_misses, "normalize_query", side_effect=normalize):
            record_miss(_request(), "x" * 900)
            await _settle()

        assert seen == [MAX_RAW_QUERY_LENGTH]

    async def test_an_address_beyond_its_limit_is_not_counted_and_another_still_is(
        self, counted: AsyncMock, production
    ) -> None:
        for number in range(RATE_LIMIT_MAX + 3):
            record_miss(_request("203.0.113.7"), f"text {number}")
        record_miss(_request("198.51.100.8"), "spider")
        await _settle()

        assert counted.await_count == RATE_LIMIT_MAX + 1
        assert counted.await_args.args[1] == "spider"

    async def test_an_ipv6_subscriber_is_one_network_whatever_address_it_takes(
        self, counted: AsyncMock, production
    ) -> None:
        """A /64 belongs to one subscriber: a new address per request does not make a new key."""
        for number in range(RATE_LIMIT_MAX + 5):
            record_miss(_request(f"2001:db8:1:1::{number + 1:x}"), f"text {number}")
        record_miss(_request("2001:db8:1:2::1"), "spider")  # the next /64: another subscriber
        await _settle()

        assert counted.await_count == RATE_LIMIT_MAX + 1
        assert counted.await_args.args[1] == "spider"

    async def test_values_that_are_no_address_share_one_key(self, counted: AsyncMock, production) -> None:
        for number in range(RATE_LIMIT_MAX + 5):
            record_miss(_request(f"forged-{number}"), f"text {number}")
        await _settle()

        assert counted.await_count == RATE_LIMIT_MAX

    async def test_every_request_counts_against_the_limit_also_a_dropped_one(
        self, counted: AsyncMock, production
    ) -> None:
        for _ in range(RATE_LIMIT_MAX):
            record_miss(_request(), "s")
        record_miss(_request(), "spider")
        await _settle()

        counted.assert_not_called()

    async def test_a_flood_is_not_queued_without_end(self, counted: AsyncMock, production) -> None:
        release = asyncio.Event()

        async def wait(*_args: object) -> None:
            await release.wait()

        counted.side_effect = wait
        with patch.object(search_misses, "MAX_PENDING_WRITES", 3):
            for number in range(8):
                record_miss(_request(f"203.0.113.{number}"), "spider")
            await asyncio.sleep(0)
            assert len(search_misses._WRITES) == 3
            release.set()
            await _settle()
            await asyncio.sleep(0)  # the done callbacks that take the writes off the list

        assert counted.await_count == 3
        assert not search_misses._WRITES

    async def test_the_write_holds_the_day_and_the_text_only(self, counted: AsyncMock, production) -> None:
        """A row is a text, a day and a count: the address and the network's key go nowhere."""
        request = _request("203.0.113.7")
        request.headers["user-agent"] = "Mozilla/5.0 (X11; Linux x86_64)"
        with patch.object(search_misses, "datetime") as clock:
            clock.now.return_value.date.return_value = TODAY
            record_miss(request, "spider")
            await _settle()

        assert counted.await_args.args == (TODAY, "spider")
        assert counted.await_args.kwargs == {}


class TestCount:
    """The background write: the day's cap, the purge once a day, and a failure that reaches nobody."""

    @pytest.fixture
    def repository(self, production) -> Iterator[MagicMock]:
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

    async def test_purges_the_rows_past_the_retention_once_per_utc_day(self, repository: MagicMock) -> None:
        await search_misses._count(TODAY, "spider")
        await search_misses._count(TODAY, "splom")
        await search_misses._count(TODAY + timedelta(days=1), "spider")

        assert [call.args for call in repository.delete_before.await_args_list] == [
            (TODAY - timedelta(days=RETENTION_DAYS),),
            (TODAY + timedelta(days=1) - timedelta(days=RETENTION_DAYS),),
        ]

    async def test_a_failed_purge_reaches_nobody_and_the_next_caller_tries_again(self, repository: MagicMock) -> None:
        repository.delete_before.side_effect = [_database_error(), 0]
        await search_misses._count(TODAY, "spider")
        await search_misses._count(TODAY, "splom")
        await search_misses._count(TODAY, "kreisdiagramm")

        # Failed, tried again and done: the third count of the day finds it done.
        assert repository.delete_before.await_count == 2
        assert repository.count.await_count == 3

    async def test_a_failed_write_logs_its_class_and_sqlstate_and_never_the_text(
        self, repository: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing table is the case that will happen: the migration reaches production after the deploy."""
        caplog.set_level(logging.DEBUG)
        repository.count.side_effect = _database_error("42P01")

        await search_misses._count(TODAY, CANARY)

        assert "search miss not counted (non-critical): ProgrammingError 42P01, 0 more since the last line" in (
            caplog.text
        )
        assert CANARY not in _logged(caplog)
        repository.delete_before.assert_awaited_once()  # the purge still runs

    async def test_failures_write_at_most_one_line_a_minute(
        self, repository: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        repository.count.side_effect = _database_error("42501")
        with patch.object(search_misses.time, "monotonic", side_effect=[1000.0, 1010.0, 1020.0, 1065.0]):
            for _ in range(4):
                await search_misses._count(TODAY, "spider")

        lines = [record.getMessage() for record in caplog.records if "not counted" in record.getMessage()]
        assert lines == [
            "search miss not counted (non-critical): ProgrammingError 42501, 0 more since the last line",
            "search miss not counted (non-critical): ProgrammingError 42501, 2 more since the last line",
        ]

    async def test_a_failed_connection_reaches_nobody(self, production, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        with patch.object(
            search_misses, "get_db_context", side_effect=lambda: FakeSession(RuntimeError(f"no database {CANARY}"))
        ):
            await search_misses._count(TODAY, CANARY)

        assert "search miss not counted (non-critical): RuntimeError -, 0 more since the last line" in caplog.text
        assert CANARY not in _logged(caplog)


class TestPurge:
    """The retention delete does not wait for a miss: it also runs at start and on the owner's read."""

    @pytest.fixture
    def deleted(self) -> Iterator[AsyncMock]:
        with (
            patch.object(search_misses, "get_db_context", side_effect=lambda: FakeSession()),
            patch.object(search_misses, "SearchMissRepository") as repository,
        ):
            repository.return_value.delete_before = AsyncMock(return_value=3)
            yield repository.return_value.delete_before

    @pytest.mark.parametrize("environment", ["development", "test"])
    async def test_deletes_nothing_outside_production(self, deleted: AsyncMock, environment: str) -> None:
        """A local API reads the shared database: it must never delete from it."""
        with patch.object(settings, "environment", environment):
            await search_misses.purge_expired(TODAY)
            assert search_misses.start_purge() is None

        deleted.assert_not_called()

    async def test_runs_once_at_start_in_the_background(self, deleted: AsyncMock, production) -> None:
        with patch.object(search_misses, "datetime") as clock:
            clock.now.return_value.date.return_value = TODAY
            task = search_misses.start_purge()
            assert task is not None and task in search_misses._WRITES
            await task

        deleted.assert_awaited_once_with(retention_cutoff(TODAY))

    async def test_the_service_start_schedules_it(self) -> None:
        import api.main as main

        @asynccontextmanager
        async def noop_lifespan(_app):
            yield

        mcp_stub = MagicMock()
        mcp_stub.lifespan = noop_lifespan
        with (
            patch("api.main.is_db_configured", return_value=True),
            patch("api.main.init_db", new=AsyncMock()),
            patch("api.main.close_db", new=AsyncMock()),
            patch("api.main.mcp_http_app", mcp_stub),
            patch("api.main._prewarm_cache", new=AsyncMock()),
            patch.object(search_misses, "start_purge") as start,
        ):
            async with main.lifespan(fastapi_app):
                start.assert_called_once_with()


async def _post(
    body: Any = None, *, content: str | None = None, headers: dict[str, str] | None = None, params: dict | None = None
) -> httpx.Response:
    """POST /search/miss through the whole app, on the test's own loop, so its background write can be awaited."""
    transport = httpx.ASGITransport(app=app, client=("203.0.113.7", 50000))
    async with httpx.AsyncClient(transport=transport, base_url="https://api.anyplot.ai") as client:
        if content is not None:
            return await client.post("/search/miss", content=content, headers=headers, params=params)
        return await client.post("/search/miss", json=body, headers=headers, params=params)


async def _call_raw(
    method: str, path: str, headers: dict[str, str], chunks: list[bytes], *, gone: bool = False
) -> tuple[int, int]:
    """Call the app with a body in *chunks*; the status, and how many chunks the app asked for.

    With *gone*, the last chunk promises more and the client then goes away (`http.disconnect`)."""
    pulled = 0

    async def receive() -> dict[str, Any]:
        nonlocal pulled
        if pulled < len(chunks):
            pulled += 1
            more = gone or pulled < len(chunks)
            return {"type": "http.request", "body": chunks[pulled - 1], "more_body": more}
        return {"type": "http.disconnect"}

    status = 0

    async def send(message: dict[str, Any]) -> None:
        nonlocal status
        if message["type"] == "http.response.start":
            status = message["status"]

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(name.lower().encode(), value.encode()) for name, value in headers.items()],
        "client": ("203.0.113.7", 50000),
        "server": ("api.anyplot.ai", 443),
    }
    await app(scope, receive, send)
    return status, pulled


class TestBodyCap:
    """A body is bounded before it is parsed: one oversized body must not be read, let alone normalised."""

    JSON = {"content-type": "application/json"}

    async def test_a_declared_length_above_the_cap_is_refused_before_anything_is_read(
        self, counted: AsyncMock, production
    ) -> None:
        with patch.object(search_misses, "normalize_query") as normalised:
            status, pulled = await _call_raw(
                "POST", "/search/miss", {**self.JSON, "content-length": str(30 * 1024 * 1024)}, [b"{" * 4096] * 64
            )

        assert (status, pulled) == (413, 0)
        normalised.assert_not_called()
        counted.assert_not_called()

    async def test_a_chunked_body_is_read_only_until_it_passes_the_cap(self, counted: AsyncMock, production) -> None:
        chunk = 256
        body = json.dumps({"query": "ä" + "A" * (64 * 1024)}).encode()
        chunks = [body[start : start + chunk] for start in range(0, len(body), chunk)]
        with patch.object(search_misses, "normalize_query") as normalised:
            status, pulled = await _call_raw("POST", "/search/miss", self.JSON, chunks)

        assert status == 413
        assert pulled <= MAX_BODY_BYTES // chunk + 1 < len(chunks)
        normalised.assert_not_called()
        counted.assert_not_called()

    async def test_the_413_says_nothing_of_the_body_and_is_never_cached(self, counted: AsyncMock, production) -> None:
        answer = await _post({"query": CANARY + "x" * 2000})
        declared, _ = await _call_raw("POST", "/search/miss", {**self.JSON, "content-length": "5000"}, [b"{"])

        assert answer.status_code == 413
        # The same words as the general bound in front of the router: one refusal, whoever sends it.
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/search/miss"}
        assert answer.headers["cache-control"] == "private, no-store"
        assert declared == 413
        counted.assert_not_called()

    @pytest.mark.parametrize(
        ("method", "path"), [("POST", "/search/miss"), ("DELETE", "/debug/search-misses")], ids=["public", "owner"]
    )
    async def test_a_client_that_goes_away_mid_body_ends_quietly(
        self, counted: AsyncMock, production, caplog: pytest.LogCaptureFixture, method: str, path: str
    ) -> None:
        """No fault of the service: nothing counted, nothing logged, and no exception out of the app."""
        caplog.set_level(logging.DEBUG)

        async def session():
            yield AsyncMock()

        fastapi_app.dependency_overrides[require_admin] = lambda: None
        fastapi_app.dependency_overrides[get_db] = session
        try:
            with patch("api.dependencies.is_db_configured", return_value=True):
                status, pulled = await _call_raw(method, path, self.JSON, [b'{"query": "spider ch'], gone=True)
        finally:
            fastapi_app.dependency_overrides.clear()

        assert (status, pulled) == (400, 1)
        assert [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING] == []
        assert "Unhandled exception" not in caplog.text
        counted.assert_not_called()

    @pytest.mark.parametrize("declared", ["-5", "five"])
    async def test_a_declared_length_that_is_no_size_is_refused(self, counted: AsyncMock, production, declared) -> None:
        status, pulled = await _call_raw("POST", "/search/miss", {**self.JSON, "content-length": declared}, [b"{}"])

        assert (status, pulled) == (400, 0)
        counted.assert_not_called()

    async def test_a_body_within_the_cap_is_counted(self, counted: AsyncMock, production) -> None:
        answer = await _post({"query": "spider " + "ä" * 30})
        await _settle()

        assert answer.status_code == 204
        counted.assert_awaited_once()

    async def test_the_owners_delete_has_the_same_cap(self) -> None:
        fastapi_app.dependency_overrides[require_admin] = lambda: None
        try:
            with patch("api.dependencies.is_db_configured", return_value=True):
                status, pulled = await _call_raw(
                    "DELETE", "/debug/search-misses", {**self.JSON, "content-length": str(10 * 1024 * 1024)}, [b"{"]
                )
        finally:
            fastapi_app.dependency_overrides.clear()

        assert (status, pulled) == (413, 0)


class TestRoute:
    """`POST /search/miss`: always the same `204`, the text from the body only, and errors that do not repeat it."""

    async def test_answers_204_without_a_body_whatever_happens(self, counted: AsyncMock) -> None:
        answers = []
        with patch.object(settings, "environment", "production"):
            answers.append(await _post({"query": "spider"}))  # counted
            answers.append(await _post({"query": "s"}))  # dropped: too short
            answers.append(await _post({"query": "jane@example.org"}))  # dropped: no search for a plot
            for _ in range(RATE_LIMIT_MAX):
                answers.append(await _post({"query": "splom"}))  # the last ones beyond the limit
        with patch.object(settings, "environment", "development"):
            answers.append(await _post({"query": "spider"}))  # not counted outside production
        await _settle()

        assert {(answer.status_code, answer.content) for answer in answers} == {(204, b"")}
        assert counted.await_count == RATE_LIMIT_MAX - 2  # spider once, splom until the network's 20 were used

    async def test_reads_the_text_from_the_body_only(self, counted: AsyncMock, production) -> None:
        """A text in the URL would stand in the request log for 30 days; neither it nor a header is read."""
        answer = await _post({"query": "spider"}, params={"query": "from-url"}, headers={"X-Query": "from-header"})
        no_body = await _post(content="", params={"query": "from-url"}, headers={"X-Query": "from-header"})
        await _settle()

        assert answer.status_code == 204
        assert no_body.status_code == 422
        counted.assert_awaited_once()
        assert counted.await_args.args[1] == "spider"

    @pytest.mark.parametrize("content_type", [None, "text/plain", "application/x-www-form-urlencoded"])
    async def test_reads_only_a_json_body(self, counted: AsyncMock, production, content_type: str | None) -> None:
        """A page on another site can post without a preflight only with no type or a simple one: never read."""
        headers = {"Content-Type": content_type} if content_type else {}
        transport = httpx.ASGITransport(app=app, client=("203.0.113.7", 50000))
        async with httpx.AsyncClient(transport=transport, base_url="https://api.anyplot.ai") as client:
            request = client.build_request("POST", "/search/miss", content=b'{"query": "spider"}', headers=headers)
            assert request.headers.get("content-type") == content_type
            answer = await client.send(request)
        await _settle()

        assert answer.status_code == 422
        assert answer.json()["detail"] == [
            {"type": "json_required", "loc": ["body"], "msg": "The body must be JSON (application/json)"}
        ]
        counted.assert_not_called()

    @pytest.mark.parametrize(
        ("body", "content"),
        [
            ({"query": [CANARY]}, None),  # a text that is no string
            ({"q": CANARY}, None),  # no `query`
            (CANARY, None),  # a JSON string instead of an object
            (None, f'{{"query": "{CANARY}'),  # broken JSON
            (None, f'{{"query": "{CANARY}", "query": 5}}'),  # the last of two keys wins and is no string
        ],
        ids=["not-a-string", "wrong-key", "not-an-object", "broken-json", "duplicate-key"],
    )
    async def test_a_malformed_body_gets_a_422_that_does_not_repeat_it(
        self, counted: AsyncMock, production, body: Any, content: str | None, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        headers = {"Content-Type": "application/json"} if content is not None else None
        answer = await _post(body, content=content, headers=headers)

        assert answer.status_code == 422
        assert CANARY not in answer.text
        assert CANARY.encode() not in answer.content
        for error in answer.json()["detail"]:
            assert set(error) <= {"type", "loc", "msg"}
        assert CANARY not in _logged(caplog)
        counted.assert_not_called()

    async def test_no_log_line_holds_the_text_of_an_accepted_a_refused_or_a_failing_request(
        self, production, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        with (
            patch.object(search_misses, "get_db_context", side_effect=lambda: FakeSession()),
            patch.object(search_misses, "SearchMissRepository") as repository,
        ):
            repository.return_value.count = AsyncMock(return_value=True)
            repository.return_value.delete_before = AsyncMock(return_value=0)
            accepted = await _post({"query": CANARY})
            refused = await _post({"q": CANARY})
            too_large = await _post({"query": CANARY * 200})
            await _settle()
            repository.return_value.count.side_effect = _database_error()
            failed = await _post({"query": f"{CANARY} two"})
            await _settle()

        statuses = (accepted.status_code, refused.status_code, too_large.status_code, failed.status_code)
        assert statuses == (204, 422, 413, 204)
        assert [call.kwargs["query"] for call in repository.return_value.count.await_args_list] == [
            CANARY,
            f"{CANARY} two",
        ]
        assert "search miss not counted (non-critical): ProgrammingError 42P01" in caplog.text
        assert CANARY not in _logged(caplog)


class TestReadMisses:
    async def test_reads_one_page_of_the_retention_window_and_the_capped_days(self) -> None:
        repository = MagicMock()
        repository.distinct_since = AsyncMock(return_value=612)
        repository.totals = AsyncMock(return_value=[("spider", 9, TODAY - timedelta(days=30), TODAY)])
        repository.full_days = AsyncMock(return_value=[TODAY, TODAY - timedelta(days=3)])

        answer = await read_misses(repository, order="recent", offset=500, today=TODAY)

        since = retention_cutoff(TODAY)
        assert since == TODAY - timedelta(days=RETENTION_DAYS)
        repository.totals.assert_awaited_once_with(since, limit=LIST_LIMIT, offset=500, order="recent")
        repository.distinct_since.assert_awaited_once_with(since)
        repository.full_days.assert_awaited_once_with(since, MAX_NEW_QUERIES_PER_DAY)
        assert answer.model_dump() == {
            "status": "ok",
            "retention_days": RETENTION_DAYS,
            "day_cap": MAX_NEW_QUERIES_PER_DAY,
            "order": "recent",
            "offset": 500,
            "texts": 612,
            "misses": [{"query": "spider", "count": 9, "first_day": "2026-10-18", "last_day": "2026-11-17"}],
            "capped_days": ["2026-11-17", "2026-11-14"],
        }


class TestDebugEndpoints:
    """`GET` and `DELETE /debug/search-misses`: the owner's list and its deletes, for an admin only."""

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
            broken = client.request(
                "DELETE", "/debug/search-misses", content="{broken", headers={"Content-Type": "application/json"}
            )
        assert listed.status_code in (401, 403, 503)
        assert deleted.status_code in (401, 403, 503)
        # The gate comes before the body is read: broken JSON from a visitor is refused, not parsed.
        assert broken.status_code in (401, 403, 503)

    def test_lists_a_page_for_an_admin_with_no_cache_and_the_purge_run(self) -> None:
        reads: list[dict[str, Any]] = []

        async def misses(_repository: object, **page: Any) -> SearchMissesResponse:
            reads.append(page)
            return SearchMissesResponse(
                status="ok",
                order=page["order"],
                offset=page["offset"],
                texts=1,
                misses=[{"query": "spider", "count": 3, "first_day": "2026-11-01", "last_day": "2026-11-17"}],
                capped_days=["2026-11-16"],
            )

        purged = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_search_misses", side_effect=misses),
            patch("api.routers.debug.purge_expired", purged),
        ):
            response = self._client(AsyncMock()).get("/debug/search-misses?order=recent&offset=500")

        assert response.headers["cache-control"] == "private, no-store"
        purged.assert_awaited_once_with()
        assert reads == [{"order": "recent", "offset": 500}]
        assert response.json() == {
            "status": "ok",
            "retention_days": RETENTION_DAYS,
            "day_cap": MAX_NEW_QUERIES_PER_DAY,
            "order": "recent",
            "offset": 500,
            "texts": 1,
            "misses": [{"query": "spider", "count": 3, "first_day": "2026-11-01", "last_day": "2026-11-17"}],
            "capped_days": ["2026-11-16"],
        }

    @pytest.mark.parametrize("query", ["order=random", "offset=-1"])
    def test_refuses_an_unknown_order_or_a_negative_offset(self, query: str) -> None:
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.purge_expired", AsyncMock()),
        ):
            response = self._client(AsyncMock()).get(f"/debug/search-misses?{query}")

        assert response.status_code == 422

    def test_is_unavailable_while_the_table_is_missing(self) -> None:
        async def missing(_repository: object, **_page: Any) -> SearchMissesResponse:
            raise ProgrammingError("SELECT", {}, Exception('relation "search_misses" does not exist'))

        session = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_search_misses", side_effect=missing),
            patch("api.routers.debug.purge_expired", AsyncMock()),
        ):
            response = self._client(session).get("/debug/search-misses")

        assert response.status_code == 200
        assert response.json()["status"] == "unavailable" and response.json()["misses"] == []
        assert response.headers["cache-control"] == "private, no-store"
        session.rollback.assert_awaited_once()

    def test_deletes_every_row_of_a_text_named_in_the_body_and_commits_first(self) -> None:
        session = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_query = AsyncMock(return_value=2)
            response = self._client(session).request("DELETE", "/debug/search-misses", json={"query": "spider chart"})

        assert response.status_code == 200
        assert response.json() == {"deleted": 2}
        repository.return_value.delete_query.assert_awaited_once_with("spider chart")
        session.commit.assert_awaited()

    def test_deletes_every_row_of_a_day(self) -> None:
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_day = AsyncMock(return_value=1000)
            response = self._client(AsyncMock()).request("DELETE", "/debug/search-misses", json={"day": "2026-11-16"})

        assert response.json() == {"deleted": 1000}
        repository.return_value.delete_day.assert_awaited_once_with(date(2026, 11, 16))
        repository.return_value.delete_query.assert_not_called()

    @pytest.mark.parametrize(
        "body",
        [{}, {"query": "spider", "day": "2026-11-16"}, {"day": "yesterday"}, {"query": 5}],
        ids=["neither", "both", "not-a-day", "not-a-text"],
    )
    def test_a_delete_names_a_text_or_a_day(self, body: dict[str, Any]) -> None:
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            response = self._client(AsyncMock()).request("DELETE", "/debug/search-misses", json=body)

        assert response.status_code == 422
        repository.return_value.delete_query.assert_not_called()
        repository.return_value.delete_day.assert_not_called()

    def test_a_failed_commit_is_a_503_and_never_a_200(self) -> None:
        session = AsyncMock()
        session.commit.side_effect = _database_error()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_query = AsyncMock(return_value=3)
            response = self._client(session).request("DELETE", "/debug/search-misses", json={"query": "spider"})

        assert response.status_code == 503
        session.rollback.assert_awaited()

    def test_a_failed_delete_is_a_503_that_names_no_text(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        session = AsyncMock()
        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.SearchMissRepository") as repository,
        ):
            repository.return_value.delete_query = AsyncMock(side_effect=_database_error())
            response = self._client(session).request("DELETE", "/debug/search-misses", json={"query": CANARY})

        assert response.status_code == 503
        assert CANARY not in response.text
        assert CANARY not in _logged(caplog)
        session.rollback.assert_awaited_once()


def test_the_legal_page_states_the_period_the_api_keeps() -> None:
    """The privacy policy promises the period the purge applies: one period for every text."""
    legal = (ROOT / "app" / "src" / "pages" / "LegalPage.tsx").read_text(encoding="utf-8")

    assert f"['searches without a hit', '{RETENTION_DAYS} days']" in legal
    assert f"kept: {RETENTION_DAYS} days" in legal
    assert RETENTION_DAYS == 180
