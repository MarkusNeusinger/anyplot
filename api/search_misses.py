"""Search misses: the gallery searches that found nothing in the whole catalogue, per UTC day.

The gallery's search box (`app/src/sections/plots-gallery/FilterBar/FilterSearch.tsx`) sends the
finished text of a search that matched no plot to `POST /search/miss` (`api/routers/search.py`),
and this module counts it: one counter per UTC day and text in the `search_misses` table. The
owner reads the list on /debug to see what the catalogue lacks and which words the search does
not know. No public page shows it.

The text is what a visitor typed, so it is handled as little as possible:

- It travels in the request body only, never in a URL or a header. The body is read by hand and
  refused beyond `MAX_BODY_BYTES` before it is parsed (`read_json_body`).
- Nothing logs it. A failed write logs the exception's class and its SQLSTATE, never its message,
  which would carry the statement's parameters; a validation error never repeats the body.
- The server normalises it again with the app's rule (`normalize_query`, held to the app's
  `normalizeQuery` by the shared cases in `app/src/hooks/searchQuery.cases.json`) and keeps only
  a text that reads as a search for a plot (`is_countable`): letters and marks of any script,
  a few digits, spaces and a handful of signs. An address, a phone number or a link fails it.
- A row is the text, the day and a count. No address, no user agent, no time of day, no session.
  The network's salted key (`hash_ip`) is held in this process's memory for the rate limit only,
  until the first request of a later minute clears it, and is never written anywhere. A row is
  pseudonymous, not anonymous: the platform's request log keeps one line per `POST /search/miss`
  for 30 days, with its time and user agent, and until then a text could be matched to such a
  line by its day.
- Rows older than `RETENTION_DAYS` are deleted, once a day: after a count, at the service's
  start and when the owner reads the list.

Only the production service counts and purges (`settings.is_production`): a test or a local
process counts nothing and deletes nothing. The route answers the same `204` whatever happened
here, so a caller learns nothing from it, and the count is written in the background. It is a
best-effort counter: a flood can fill a day, the day's cap then drops new texts, and a write in
flight when an instance stops is lost.
"""

import asyncio
import logging
import re
import time
import unicodedata
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal, TypeVar

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError, model_validator

from api.agent_usage import UsageStatus
from api.request_context import client_ip, hash_ip, network_of, read_body_within
from core.config import settings
from core.database import SearchMissRepository, get_db_context
from core.database.models import SEARCH_MISS_QUERY_LENGTH


logger = logging.getLogger(__name__)

# Bounds what a request may make the API read and parse: 40 characters of any script fit many
# times over, and a larger body is refused before it is parsed.
MAX_BODY_BYTES = 1024

# Bounds the work on one text: the raw text is cut to this many characters before it is
# normalised. The app never sends more than `MAX_QUERY_LENGTH`.
MAX_RAW_QUERY_LENGTH = 200

# The longest text that is kept, in characters: the app's `MAX_QUERY_LENGTH` and the column's length.
MAX_QUERY_LENGTH = SEARCH_MISS_QUERY_LENGTH

# The shortest text that is counted, in characters: one character is the start of a search, not a search.
MIN_QUERY_LENGTH = 2

# Bounds the digits in a countable text: enough for "ggplot2" or a year, too few for a phone number.
MAX_QUERY_DIGITS = 6

# The signs a countable text may hold besides letters, combining marks, decimal digits and spaces.
QUERY_MARKS = frozenset(" -_.+#/&'()")

# Bounds one network (an IPv4 address, or the /64 of an IPv6 address): requests beyond this many in
# one minute are dropped unseen. Twenty finished searches a minute is more than a person types.
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

# Bounds one page of the owner's list.
LIST_LIMIT = 500

# Bounds the failure lines: at most one per this many seconds, however many writes fail.
FAILURE_LOG_SECONDS = 60

# What JavaScript's `\s` and `String.prototype.trim` count as white space, by code point. Python's
# `\s` and `str.strip()` also count U+001C to U+001F and U+0085 and miss U+FEFF, and the two rules
# must give the same text. Code points, not literal characters: most of these are invisible.
JS_WHITESPACE = "".join(
    chr(code)
    for code in (
        *(0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20),
        *(0xA0, 0x1680),
        *range(0x2000, 0x200B),
        *(0x2028, 0x2029, 0x202F, 0x205F, 0x3000, 0xFEFF),
    )
)
_WHITESPACE_RUN = re.compile(f"[{re.escape(JS_WHITESPACE)}]+")

# A SQLSTATE: five characters, a class of error and nothing of the statement.
_SQLSTATE = re.compile(r"[0-9A-Z]{5}")

# Strong references to the writes in flight: asyncio holds a task only weakly, so the collector could
# otherwise drop one before it ran.
_WRITES: set[asyncio.Task[None]] = set()

# How many of the API's database connections the counter may hold at once (the pool has 15 for
# everything, `core/database/connection.py`). The other writes wait their turn.
WRITE_CONNECTIONS = 2
_WRITE_SLOTS = asyncio.Semaphore(WRITE_CONNECTIONS)

# Writes in flight or waiting. A miss beyond that is not counted: this many waiting is a flood.
MAX_PENDING_WRITES = 256

# The two orders of the owner's list.
ListOrder = Literal["count", "recent"]


# =============================================================================
# The body
# =============================================================================


class SearchMissBody(BaseModel):
    """The body of `POST /search/miss`: the text alone."""

    query: str


class SearchMissDelete(BaseModel):
    """The body of the owner's `DELETE /debug/search-misses`: a text, or a UTC day, never both."""

    query: str | None = None
    day: date | None = None

    @model_validator(mode="after")
    def _one_of_them(self) -> "SearchMissDelete":
        if (self.query is None) == (self.day is None):
            raise ValueError("give either query or day")
        return self


Body = TypeVar("Body", bound=BaseModel)


def _is_json(content_type: str | None) -> bool:
    """Whether a `Content-Type` names JSON: `application/json` or an `application/...+json` type."""
    media = (content_type or "").split(";", 1)[0].strip().lower()
    return media == "application/json" or (media.startswith("application/") and media.endswith("+json"))


def json_body_doc(model: type[BaseModel]) -> dict[str, Any]:
    """The OpenAPI description of a JSON body that a route reads by hand rather than through a parameter."""
    return {"requestBody": {"required": True, "content": {"application/json": {"schema": model.model_json_schema()}}}}


async def read_json_body(request: Request, model: type[Body]) -> Body:
    """The request body as *model*: JSON only, at most `MAX_BODY_BYTES`, and errors that never repeat it.

    Read by hand, not through a body parameter: the framework would read and parse a body of any size
    before the route could refuse it. A body that is not JSON is refused before it is read. That also
    keeps a page on another site from posting in a visitor's name: only a request with a JSON content
    type is read, and a browser asks the API's CORS before it sends one from a foreign origin. A body
    that does not fit *model* gets the framework's `422`, whose entries keep their type, location and
    message and leave out the input.
    """
    if not _is_json(request.headers.get("content-type")):
        raise RequestValidationError(
            [{"type": "json_required", "loc": ("body",), "msg": "The body must be JSON (application/json)"}]
        )
    raw = await read_body_within(request, MAX_BODY_BYTES)
    try:
        return model.model_validate_json(raw)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False, include_input=False)
        raise RequestValidationError(
            [{"type": error["type"], "loc": ("body", *error["loc"]), "msg": error["msg"]} for error in errors]
        ) from None


# =============================================================================
# The text
# =============================================================================


def normalize_query(text: str) -> str:
    """The app's `normalizeQuery` in Python: one Unicode form, lowercase, single spaces, at most 40 characters.

    The same steps in the same order: composed to Unicode form NFC, lowercase, white space at the ends
    dropped and every run of it made one space, cut after 40 characters (code points, never inside
    one), and a space left at the cut dropped. So "Scatter", "scatter " and "SCATTER" are one row, and
    so is a word typed with a composed or a decomposed accent.
    """
    composed = unicodedata.normalize("NFC", text)
    return _WHITESPACE_RUN.sub(" ", composed.lower()).strip(" ")[:MAX_QUERY_LENGTH].rstrip(" ")


def is_countable(query: str) -> bool:
    """Whether a normalised text is kept: a search for a plot, by what its characters are, in any script.

    Two characters or more, each a letter, a combining mark, a decimal digit (at most
    `MAX_QUERY_DIGITS` in all), a space or one of `QUERY_MARKS`. Nothing else: no `@` and no `:`, so
    no address and no link, and no control, format or direction character, so no row looks empty or
    reads backwards. That also keeps out a NUL and half of a surrogate pair, which PostgreSQL cannot
    store. The app applies the same rule (`isCountableMiss` in `app/src/lib/searchMiss.ts`).
    """
    if len(query) < MIN_QUERY_LENGTH:
        return False
    digits = 0
    for char in query:
        category = unicodedata.category(char)
        if category == "Nd":
            digits += 1
        elif category[0] not in "LM" and char not in QUERY_MARKS:
            return False
    return digits <= MAX_QUERY_DIGITS


def retention_cutoff(today: date) -> date:
    """The first UTC day that is kept: the rows of the days before it are deleted, and no list shows them."""
    return today - timedelta(days=RETENTION_DAYS)


# =============================================================================
# Counting
# =============================================================================


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


class _FailureLog:
    """When the last failure line was written, and how many failures were held back since."""

    last: float | None = None
    held_back = 0


def _sqlstate(exc: BaseException) -> str:
    """The SQLSTATE of a database error (five characters, such as `42P01` for a missing table), or `-`."""
    code = getattr(getattr(exc, "orig", None), "sqlstate", None)
    return code if isinstance(code, str) and _SQLSTATE.fullmatch(code) else "-"


def _log_failure(what: str, exc: BaseException) -> None:
    """Log a failed write or purge by its class and SQLSTATE, at most one line a minute.

    Never the message: a database error's message carries the statement's parameters, and with them
    the text. The SQLSTATE tells a missing table (`42P01`) from a missing privilege (`42501`), which
    share a class. A line says how many failures were held back since the one before it.
    """
    now = time.monotonic()
    if _FailureLog.last is not None and now - _FailureLog.last < FAILURE_LOG_SECONDS:
        _FailureLog.held_back += 1
        return
    held_back, _FailureLog.held_back, _FailureLog.last = _FailureLog.held_back, 0, now
    logger.warning(
        "%s (non-critical): %s %s, %d more since the last line", what, type(exc).__name__, _sqlstate(exc), held_back
    )


class _Purge:
    """The UTC day the retention delete last succeeded on in this process: it runs at most once a day."""

    day: date | None = None


async def purge_expired(today: date | None = None) -> None:
    """Delete the rows past the retention period, once per process and UTC day; production only.

    Called after a count, at the service's start (`start_purge`) and when the owner reads the list, so
    it does not wait for a miss. Marked before the attempt, so callers at the same moment do not run it
    twice, and unmarked when it fails, so the next caller tries again. A failure goes no further.
    """
    if not settings.is_production:
        return
    today = today or datetime.now(UTC).date()
    if _Purge.day == today:
        return
    earlier, _Purge.day = _Purge.day, today
    try:
        async with _WRITE_SLOTS, get_db_context() as session:
            await SearchMissRepository(session).delete_before(retention_cutoff(today))
    except Exception as exc:  # the purge is housekeeping: nothing it does may reach a caller
        _Purge.day = earlier
        _log_failure("search misses not purged", exc)


def start_purge() -> asyncio.Task[None] | None:
    """Run the retention delete once in the background at the service's start; production only.

    A task, not awaited: the start never waits for the database. It is held with the writes, so the
    collector keeps it.
    """
    if not settings.is_production:
        return None
    task = asyncio.create_task(purge_expired(), name="search-misses-purge")
    _WRITES.add(task)
    task.add_done_callback(_WRITES.discard)
    return task


async def _count(day: date, query: str) -> None:
    """Add one to the text's counter of the day, then purge once a day. A failure is logged without the text.

    That covers the table not being there yet: the migration reaches production through
    `sync-postgres.yml` after the merge, which can be later than the deploy of this code.
    """
    try:
        async with _WRITE_SLOTS, get_db_context() as session:
            await SearchMissRepository(session).count(day=day, query=query, max_new_per_day=MAX_NEW_QUERIES_PER_DAY)
    except Exception as exc:  # nothing a search-miss counter does may reach the caller
        _log_failure("search miss not counted", exc)
    await purge_expired(day)


def record_miss(request: Request, text: str) -> None:
    """Count a gallery search that found nothing, in the background; silent whatever happens.

    Each request of a network counts against its limit, whether its text is then counted or not. The
    text is cut to `MAX_RAW_QUERY_LENGTH`, normalised here, whatever the app did, and written only when
    it is countable.
    """
    if not settings.is_production:
        return
    if not _RATE_LIMIT.allows(hash_ip(network_of(client_ip(request))), time.monotonic()):
        return
    query = normalize_query(text[:MAX_RAW_QUERY_LENGTH])
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
    """One page of the owner's list: the texts of the retention window, in the order asked for.

    `texts` is how many different texts the window holds; `misses` lists up to `LIST_LIMIT` of them
    from `offset` on, most searched first (`count`) or most recently searched first (`recent`).
    `capped_days` are the UTC days of the window, newest first, that reached `day_cap` texts: on those
    a new text was dropped, and a flood shows there. `unavailable` with an empty list when the database
    does not answer or the table is not there yet.
    """

    status: UsageStatus
    retention_days: int = RETENTION_DAYS
    day_cap: int = MAX_NEW_QUERIES_PER_DAY
    order: ListOrder = "count"
    offset: int = 0
    texts: int = 0
    misses: list[SearchMissEntry] = []
    capped_days: list[str] = []


class SearchMissDeleted(BaseModel):
    """The answer of the owner's delete: how many rows were removed."""

    deleted: int


async def read_misses(
    repository: SearchMissRepository, *, order: ListOrder = "count", offset: int = 0, today: date | None = None
) -> SearchMissesResponse:
    """One page of the texts of the retention window, read fresh, and the days that reached the cap.

    The window is the purge's, so the list never shows a row the purge would have deleted.
    """
    since = retention_cutoff(today or datetime.now(UTC).date())
    return SearchMissesResponse(
        status="ok",
        order=order,
        offset=offset,
        texts=await repository.distinct_since(since),
        misses=[
            SearchMissEntry(query=query, count=count, first_day=first.isoformat(), last_day=last.isoformat())
            for query, count, first, last in await repository.totals(
                since, limit=LIST_LIMIT, offset=offset, order=order
            )
        ],
        capped_days=[day.isoformat() for day in await repository.full_days(since, MAX_NEW_QUERIES_PER_DAY)],
    )
