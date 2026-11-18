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
- The server applies the app's rule again (`kept_query`, held to the app's `keptMissText` by the
  shared cases in `app/src/hooks/searchQuery.cases.json`): it folds the whole text, keeps it only
  when the whole reads as a search for a plot (`is_countable`: letters and marks of any script, a
  few digits, spaces and a handful of signs), and only then cuts it to 40 characters. An e-mail
  address, a phone number or a link with its scheme fails it, also past the 40th character.
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

# Bounds the work on one text, and what the rule judges: a raw text longer than this is dropped
# unread, so the rule always judges a whole text and nothing the API did not read is ever kept.
# The app never sends more than `MAX_QUERY_LENGTH`.
MAX_RAW_QUERY_LENGTH = 200

# The longest text that is kept, in characters: the app's `MAX_QUERY_LENGTH` and the column's length.
MAX_QUERY_LENGTH = SEARCH_MISS_QUERY_LENGTH

# The shortest text that is counted, in characters: one character is the start of a search, not a search.
MIN_QUERY_LENGTH = 2

# Bounds the digits in a countable text: enough for "ggplot2" or a year, too few for a phone number.
MAX_QUERY_DIGITS = 6

# The signs a countable text may hold besides letters, combining marks, decimal digits and spaces:
# those a plot search uses, and those some scripts spell their words with. By code point: the middle
# dot (U+00B7), the katakana middle dot (U+30FB), the Hebrew geresh (U+05F3), gershayim (U+05F4) and
# maqaf (U+05BE), the Tibetan tsheg (U+0F0B) and the Ethiopic wordspace (U+1361).
QUERY_MARKS = frozenset(" -_.+#/&'(),%" + "".join(map(chr, (0x00B7, 0x30FB, 0x05F3, 0x05F4, 0x05BE, 0x0F0B, 0x1361))))

# The code points made to show as nothing (Unicode's Default_Ignorable_Code_Point, by range): the
# Hangul fillers, the variation selectors, the grapheme joiner, the format characters and their
# kind. The app tests the same property (`\p{Default_Ignorable_Code_Point}`); the shared cases carry
# these ranges, and the app's test holds them to its property.
DEFAULT_IGNORABLE = (
    (0x00AD, 0x00AD),
    (0x034F, 0x034F),
    (0x061C, 0x061C),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)

# The zero width non-joiner and joiner: ignorable, but ordinary spelling between two letters or marks
# in several scripts, and allowed there and nowhere else.
JOINERS = frozenset((chr(0x200C), chr(0x200D)))

# The typographic marks that stand for the plain ones (the curly apostrophes; the hyphen, the
# non-breaking hyphen, the minus sign, the en and the em dash), and the soft hyphen, which shows as
# nothing and comes with a word copied from a page: it is dropped rather than refusing the word. A
# search with any of them is the same search.
_TYPOGRAPHIC = str.maketrans(
    {
        **dict.fromkeys(map(chr, (0x2018, 0x2019)), "'"),
        **dict.fromkeys(map(chr, (0x2010, 0x2011, 0x2212, 0x2013, 0x2014)), "-"),
        chr(0x00AD): None,
    }
)

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

# Bounds how long a text is kept: the rows of a day more than this many days ago are deleted. One
# period for every text, also one searched only once; the same as the machine reads and the chat's
# telemetry keep.
RETENTION_DAYS = 180

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


def fold_query(text: str) -> str:
    """The app's `foldQuery` in Python: one Unicode form, lowercase, single spaces, not yet cut.

    The same steps in the same order: compatibility forms folded (Unicode form NFKC: a fullwidth
    bracket becomes the plain one, `²` becomes `2`, a ligature its letters), lowercase, the curly
    apostrophes, the hyphens, the minus sign and the dashes made the plain ones and a soft hyphen
    dropped, folded again (a small letter can have a composed form its capital lacks, and a letter
    and its mark that a soft hyphen kept apart join), white space at the ends dropped and every run
    of it made one space. The map comes before the second fold, so folding a folded text changes
    nothing. So "Scatter", "scatter " and "SCATTER" are one row, and so is a word typed with a
    composed or a decomposed accent.
    """
    plain = unicodedata.normalize("NFKC", text).lower().translate(_TYPOGRAPHIC)
    return _WHITESPACE_RUN.sub(" ", unicodedata.normalize("NFKC", plain)).strip(" ")


def cut_query(folded: str) -> str:
    """A folded text cut after 40 characters (code points, never inside one), a space at the cut dropped."""
    return folded[:MAX_QUERY_LENGTH].rstrip(" ")


def normalize_query(text: str) -> str:
    """The app's `normalizeQuery` in Python: the text folded and cut to at most 40 characters."""
    return cut_query(fold_query(text))


def _is_ignorable(char: str) -> bool:
    code = ord(char)
    return any(low <= code <= high for low, high in DEFAULT_IGNORABLE)


def _is_letter_or_mark(char: str) -> bool:
    return unicodedata.category(char)[0] in "LM"


def is_countable(query: str) -> bool:
    """Whether a normalised text is kept: a search for a plot that shows something, in any script.

    Two characters or more, each a letter, a combining mark on a letter or a mark, a decimal digit
    (at most `MAX_QUERY_DIGITS` in all), a space or one of `QUERY_MARKS`, and at least one letter or
    digit. A zero width non-joiner or joiner counts only between two letters or marks. Nothing else:
    no `@` and no `:`, so no address and no link; no control, format, direction or other ignorable
    character, so no row looks empty or reads backwards; no bare combining mark. A text has to show
    something, but a joiner inside a word can still make a row that looks like another in a script
    where it changes nothing that is seen; each such row is its own entry, which the owner can
    delete. That also keeps out a NUL and half of a surrogate pair, which PostgreSQL cannot store. The
    app applies the same rule (`isCountableMiss` in `app/src/lib/searchMiss.ts`).
    """
    if len(query) < MIN_QUERY_LENGTH:
        return False
    digits = 0
    shows = False
    last = len(query) - 1
    for index, char in enumerate(query):
        if char in JOINERS:
            between = 0 < index < last and _is_letter_or_mark(query[index - 1]) and _is_letter_or_mark(query[index + 1])
            if not between:
                return False
            continue
        if _is_ignorable(char):
            return False
        category = unicodedata.category(char)
        if category == "Nd":
            digits += 1
            shows = True
        elif category[0] == "L":
            shows = True
        elif category[0] == "M":
            # A mark sits on the letter or mark before it; a joiner in between belongs to the spelling.
            base = index - 1
            while base >= 0 and query[base] in JOINERS:
                base -= 1
            if base < 0 or not _is_letter_or_mark(query[base]):
                return False
        elif char not in QUERY_MARKS:
            return False
    return shows and digits <= MAX_QUERY_DIGITS


def kept_query(text: str) -> str | None:
    """The text a row keeps of what was typed, or `None` when nothing of it is kept; the app's `keptMissText`.

    Judged whole, then cut, then judged again: the rule runs over the whole folded text first, so an
    `@`, a `:` or a seventh digit past the 40th character refuses the text as it would within them,
    and a long address or number is never kept in part. Only a text that passed is cut to 40
    characters, and the cut text is judged once more, since a cut can end on a joiner.
    """
    folded = fold_query(text)
    if not is_countable(folded):
        return None
    query = cut_query(folded)
    return query if is_countable(query) else None


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

    Each request of a network counts against its limit, whether its text is then counted or not. A text
    longer than `MAX_RAW_QUERY_LENGTH` is dropped unread: the app never sends one, and the rule must
    judge a whole text. Any other is judged and cut here (`kept_query`), whatever the app did.
    """
    if not settings.is_production:
        return
    if not _RATE_LIMIT.allows(hash_ip(network_of(client_ip(request))), time.monotonic()):
        return
    if len(text) > MAX_RAW_QUERY_LENGTH:
        return
    query = kept_query(text)
    if query is None or len(_WRITES) >= MAX_PENDING_WRITES:
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
