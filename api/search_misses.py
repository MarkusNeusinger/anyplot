"""Search misses: the gallery searches that found nothing in the whole catalogue, per UTC day.

The gallery's search box (`app/src/sections/plots-gallery/FilterBar/FilterSearch.tsx`) sends the
finished text of a search that matched no plot to `POST /search/miss` (`api/routers/search.py`),
and this module counts it: one counter per UTC day and text in the `search_misses` table. The
owner reads the list on /debug to see what the catalogue lacks and which words the search does
not know. No public page shows it.

The text is what a visitor typed, so it is handled as little as possible:

- It travels in the request body only, never in a URL or a header: request URLs stand in the
  server logs for 30 days.
- Nothing logs it. A failed write logs the exception's class, never its message, which would
  carry the statement's parameters. The route's validation error leaves the body out
  (`api/routers/search.py`).
- The server normalises it again with the app's rule (`normalize_query`, held to the app's
  `normalizeQuery` by the shared cases in `app/src/hooks/searchQuery.cases.json`) and drops what
  is then shorter than two characters.
- A row is the text, the day and a count. No address, no user agent, no time of day, no session.
  The network's salted key (`hash_ip`) is held in this process's memory for the rate limit only,
  until the first request of a later minute clears it, and is never written anywhere.
- Rows older than `RETENTION_DAYS` are deleted.

Only the production service counts (`settings.is_production`): a test or a local request counts
nothing. The route answers the same `204` whatever happened here, so a caller learns nothing from
it, and the count is written in the background, so it never delays or fails the answer.
"""

import asyncio
import logging
import re
import time
from datetime import UTC, date, datetime, timedelta

from fastapi import Request
from pydantic import BaseModel

from api.agent_usage import UsageStatus
from api.request_context import client_ip, hash_ip
from core.config import settings
from core.database import SearchMissRepository, get_db_context
from core.database.models import SEARCH_MISS_QUERY_LENGTH


logger = logging.getLogger(__name__)

# The longest text that is kept, in characters: the app's `MAX_QUERY_LENGTH` and the column's length.
MAX_QUERY_LENGTH = SEARCH_MISS_QUERY_LENGTH

# The shortest text that is counted, in characters: one character is the start of a search, not a search.
MIN_QUERY_LENGTH = 2

# Bounds one network: requests beyond this many in one minute are dropped unseen. Twenty finished
# searches a minute is more than a person types.
RATE_LIMIT_MAX = 20
RATE_LIMIT_WINDOW_SECONDS = 60

# Bounds the rate limit's memory: the networks it follows within one minute. A request from a network
# beyond them is dropped until the minute ends.
MAX_TRACKED_NETWORKS = 10_000

# Bounds the table against junk: once a UTC day holds this many different texts, a text without a row
# that day is dropped. A text that already has one still counts.
MAX_NEW_QUERIES_PER_DAY = 1000

# Bounds how long a text is kept: the rows of a day more than this many days ago are deleted.
RETENTION_DAYS = 90

# Bounds the owner's list: the texts it shows, most searched first.
LIST_LIMIT = 500

# What JavaScript's `\s` and `String.prototype.trim` count as white space. Python's `\s` and
# `str.strip()` also count U+001C to U+001F and U+0085 and miss U+FEFF, and the two rules must give
# the same text.
_WHITESPACE_RUN = re.compile(r"[\t\n\v\f\r    -     　﻿]+")

# Strong references to the writes in flight: asyncio holds a task only weakly, so the collector could
# otherwise drop one before it ran.
_WRITES: set[asyncio.Task[None]] = set()

# How many of the API's database connections the counter may hold at once (the pool has 15 for
# everything, `core/database/connection.py`). The other writes wait their turn.
WRITE_CONNECTIONS = 2
_WRITE_SLOTS = asyncio.Semaphore(WRITE_CONNECTIONS)

# Writes in flight or waiting. A miss beyond that is not counted: this many waiting is a flood.
MAX_PENDING_WRITES = 256


class SearchMissBody(BaseModel):
    """The body of `POST /search/miss` and of the owner's `DELETE /debug/search-misses`: the text alone."""

    query: str


def normalize_query(text: str) -> str:
    """The app's `normalizeQuery` in Python: lowercase, single spaces, at most 40 characters, no space at the ends.

    The same steps in the same order: lowercase, white space at the ends dropped and every run of it
    made one space, cut after 40 characters (code points, never inside one), and a space left at the
    cut dropped. So "Scatter", "scatter " and "SCATTER" are one row.
    """
    return _WHITESPACE_RUN.sub(" ", text.lower()).strip(" ")[:MAX_QUERY_LENGTH].rstrip(" ")


def is_countable(query: str) -> bool:
    """Whether a normalised text is counted: two characters or more, and nothing PostgreSQL cannot hold.

    A NUL or half of a surrogate pair would make the write fail; no one types either.
    """
    if len(query) < MIN_QUERY_LENGTH or "\x00" in query:
        return False
    try:
        query.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def retention_cutoff(today: date) -> date:
    """The first UTC day that is kept: the rows of the days before it are deleted, and no list shows them."""
    return today - timedelta(days=RETENTION_DAYS)


class _RateLimit:
    """The requests of each network in the current minute, in memory only.

    A fixed window of whole minutes: the first request of a later minute drops every count and key of
    the earlier one at once, so a key is held until that request at the latest, and never written.
    """

    def __init__(self) -> None:
        self.minute = -1
        self.requests: dict[str, int] = {}

    def allows(self, key: str, now: float) -> bool:
        """Count one request of *key* at *now* (seconds, monotonic); whether it is within the limit."""
        minute = int(now // RATE_LIMIT_WINDOW_SECONDS)
        if minute != self.minute:
            self.minute = minute
            self.requests.clear()
        seen = self.requests.get(key)
        if seen is None and len(self.requests) >= MAX_TRACKED_NETWORKS:
            return False
        self.requests[key] = (seen or 0) + 1
        return self.requests[key] <= RATE_LIMIT_MAX


_RATE_LIMIT = _RateLimit()


class _Purge:
    """The UTC day the retention delete last ran on in this process: it runs at most once per day."""

    day: date | None = None


async def _purge(today: date) -> None:
    """Delete the rows past the retention period, at most once per process and UTC day. A failure is logged and
    goes no further; the next day tries again."""
    if _Purge.day == today:
        return
    # Marked before the attempt, so a failing delete is not tried again with every miss of the day.
    _Purge.day = today
    try:
        async with _WRITE_SLOTS, get_db_context() as session:
            await SearchMissRepository(session).delete_before(retention_cutoff(today))
    except Exception as exc:  # the purge is housekeeping: nothing it does may reach a caller
        logger.warning("search misses not purged (non-critical): %s", type(exc).__name__)


async def _count(day: date, query: str) -> None:
    """Add one to the text's counter of the day, then purge once a day. A failure is logged by its class only.

    The class, never the message: a database error's message carries the statement's parameters, and
    with them the text. That covers the table not being there yet: the migration reaches production
    through `sync-postgres.yml` after the merge, which can be later than the deploy of this code.
    """
    try:
        async with _WRITE_SLOTS, get_db_context() as session:
            await SearchMissRepository(session).count(day=day, query=query, max_new_per_day=MAX_NEW_QUERIES_PER_DAY)
    except Exception as exc:  # nothing a search-miss counter does may reach the caller
        logger.warning("search miss not counted (non-critical): %s", type(exc).__name__)
    await _purge(day)


def record_miss(request: Request, text: str) -> None:
    """Count a gallery search that found nothing, in the background; silent whatever happens.

    Each request of a network counts against its limit, whether its text is then counted or not. The
    text is normalised here, whatever the app did, and only a countable one is written.
    """
    if not settings.is_production:
        return
    if not _RATE_LIMIT.allows(hash_ip(client_ip(request)), time.monotonic()):
        return
    query = normalize_query(text)
    if not is_countable(query) or len(_WRITES) >= MAX_PENDING_WRITES:
        return
    write = asyncio.create_task(_count(datetime.now(UTC).date(), query))
    _WRITES.add(write)
    write.add_done_callback(_WRITES.discard)


# =============================================================================
# The owner's list
# =============================================================================


class SearchMissEntry(BaseModel):
    """One text of the retention window: how often it was searched, and on which days first and last (UTC)."""

    query: str
    count: int
    first_day: str
    last_day: str


class SearchMissesResponse(BaseModel):
    """The owner's list: the texts of the retention window, most searched first.

    `texts` is how many different texts the window holds; `misses` lists up to `LIST_LIMIT` of
    them. `unavailable` with an empty list when the database does not answer or the table is not
    there yet.
    """

    status: UsageStatus
    retention_days: int = RETENTION_DAYS
    texts: int = 0
    misses: list[SearchMissEntry] = []


class SearchMissDeleted(BaseModel):
    """The answer of the owner's delete: how many rows (days) of the text were removed."""

    deleted: int


async def read_misses(repository: SearchMissRepository, today: date | None = None) -> SearchMissesResponse:
    """The texts of the retention window, read fresh.

    The window is the purge's, so the list never shows a row the purge would have deleted, also on
    a day no miss has run the purge yet.
    """
    since = retention_cutoff(today or datetime.now(UTC).date())
    return SearchMissesResponse(
        status="ok",
        texts=await repository.distinct_since(since),
        misses=[
            SearchMissEntry(query=query, count=count, first_day=first.isoformat(), last_day=last.isoformat())
            for query, count, first, last in await repository.totals(since, limit=LIST_LIMIT)
        ],
    )
