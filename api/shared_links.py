"""Shared links: how often a link to the site was shared, per day, platform and page.

A messenger or a social network that shows a link's preview fetches the page's
og:image from this API (`api/routers/og_images.py`). It runs no JavaScript, so
no page analytics ever sees it. That fetch is the one trace a share leaves, and
this module counts it: one counter per UTC day, platform and page in the
`link_shares` table.

What a row holds is a count and the seven values that name it. No address, no
user agent and no time of day are stored or sent anywhere: the platform is one
name from the closed set below, read from the user agent and then dropped.

A user agent is whatever the client wrote, so a row also says whether
Cloudflare verified the fetcher as a bot it knows (`verified`). Nothing else
can tell a platform's own fetch from a scanner that signs as one once the user
agent is gone. It is a diagnosis for /debug, not a filter: WhatsApp and Signal
fetch the preview from the sender's own phone, which no one can verify, so the
public numbers count both.

Who fetched decides what the fetch is:

- A crawler or an AI assistant (`detect_ai_agent`) read the image; no person
  shared anything. That is a machine read (`api/machine_reads.py`), not a
  share, and nothing is counted here.
- One of the preview platforms below shared a link.
- Anything else, a scanner, a browser opening the image, an app this list does
  not know yet, is counted as `other`. The public numbers leave it out; the
  owner's section on /debug shows it, so a new platform is noticed.

Only the production service counts (`settings.is_production`): a test or a
local request for an image counts nothing. The count is written after the
image was served and never delays or fails it.
"""

import asyncio
import logging
import re
from datetime import UTC, date, datetime, timedelta

from fastapi import Request
from pydantic import BaseModel

from api.agent_usage import UsageStatus
from api.analytics import detect_ai_agent
from api.machine_reads import source_of, verified_category
from core.config import settings
from core.database import LinkShareRepository, get_db_context
from core.database.models import SHARE_PAGES


logger = logging.getLogger(__name__)

# A fetch by a client that is neither a preview platform nor a known crawler.
OTHER = "other"

# The window of both readers, in UTC days, today included: the same as the
# visitors strip and the machine-readers tile on /stats.
WINDOW_DAYS = 28

# How many entries each "most shared" list holds: the specs and the libraries
# of the tile, and the plot pages of the owner's section.
TOP_ENTRIES = 5

# The clients that fetch a preview image because a person shared a link: the
# token a user agent carries (matched in lowercase) and the platform it stands
# for. The first match wins, so the order matters where one name contains
# another's. WhatsApp is not in the table: `_whatsapp` tells it from the apps
# that borrow its name. Checked against a week of the API's request log
# (2026-11-04 to 2026-11-11), which is where the image proxies come from.
SHARE_TOKENS: tuple[tuple[str, str], ...] = (
    # Telegram signs as "TelegramBot (like TwitterBot)": before Twitter, or
    # every Telegram share is counted there.
    ("telegrambot", "telegram"),
    # Social networks
    ("twitterbot", "twitter"),
    ("facebookexternalhit", "facebook"),
    ("linkedinbot", "linkedin"),
    ("pinterestbot", "pinterest"),
    ("redditbot", "reddit"),
    ("tumblr", "tumblr"),
    ("mastodon", "mastodon"),
    # Messengers. Slack reads the page as Slackbot-LinkExpanding and fetches
    # the image through its image proxy, so the image's fetch carries the
    # second token only.
    ("slackbot", "slack"),
    ("slack-imgproxy", "slack"),
    ("discordbot", "discord"),
    ("viber", "viber"),
    # Microsoft's preview service still signs as SkypeUriPreview. Skype closed
    # in May 2025, so what it fetches is a link shared in Teams.
    ("skypeuripreview", "teams"),
    ("microsoft teams", "teams"),
    # Snap's fetcher, "Snap URL Preview Service; bot; snapchat; ...". Not the
    # token "snapchat": the app's in-app browser carries "Snapchat/<version>",
    # and a person who opens the image there shared nothing.
    ("snap url preview", "snapchat"),
    # GitHub shows an image linked in a README, an issue or a comment through
    # its image proxy.
    ("github-camo", "github"),
    # Link preview services
    ("embedly", "embedly"),
    ("quora link preview", "quora"),
    ("outbrain", "outbrain"),
    ("rogerbot", "rogerbot"),
    ("showyoubot", "showyoubot"),
)

# Apple's Messages app, told by its two borrowed names (`share_platform`).
IMESSAGE = "imessage"

# Every name a row's `platform` can hold besides `other`.
SHARE_PLATFORMS = frozenset({platform for _, platform in SHARE_TOKENS} | {"whatsapp", "whatsapp-lite", IMESSAGE})

# Real WhatsApp sends its full version, "WhatsApp/2.23.18.78 i" (iOS) or
# "WhatsApp/2.21.22.23 A" (Android). Signal and others send the bare name or
# "WhatsApp/2" to pass rate limits meant for unknown clients
# (https://github.com/signalapp/Signal-Android/issues/10060).
_REAL_WHATSAPP = re.compile(r"whatsapp/\d+\.\d+\.\d+", re.IGNORECASE)

# Strong references to the writes in flight: asyncio holds a task only weakly,
# so the collector could otherwise drop one before it ran.
_WRITES: set[asyncio.Task[None]] = set()

# How many of the API's database connections the counter may hold at once. The
# pool has 15 for everything (`core/database/connection.py`), and a burst of
# previews must not make a visitor's request wait for one. The other writes
# wait their turn; one takes a few milliseconds.
WRITE_CONNECTIONS = 2
_WRITE_SLOTS = asyncio.Semaphore(WRITE_CONNECTIONS)

# Writes in flight or waiting. A fetch beyond that is not counted: this many
# waiting is a flood, and a count lost in a flood costs less than a queue
# without an end.
MAX_PENDING_WRITES = 256


def _whatsapp(user_agent: str) -> str | None:
    """`whatsapp` for the real app, `whatsapp-lite` for an app that borrows its name, else None."""
    if "whatsapp" not in user_agent.lower():
        return None
    return "whatsapp" if _REAL_WHATSAPP.search(user_agent) else "whatsapp-lite"


def share_platform(user_agent: str) -> str:
    """The preview platform a user agent belongs to, or `other`.

    The answer is always one of a closed set of names (`SHARE_PLATFORMS` and
    `other`), so nothing a client wrote reaches the table.
    """
    whatsapp = _whatsapp(user_agent)
    if whatsapp:
        return whatsapp
    lowered = user_agent.lower()
    # Apple's Messages signs as both crawlers at once, "... facebookexternalhit/1.1
    # Facebot Twitterbot/1.0", which neither of the two does itself.
    if "facebookexternalhit" in lowered and "twitterbot" in lowered:
        return IMESSAGE
    for token, platform in SHARE_TOKENS:
        if token in lowered:
            return platform
    return OTHER


def is_verified(request: Request) -> bool:
    """Whether Cloudflare verified the fetcher as a bot it knows.

    The edge sets the verdict header itself and removes a forged one, so it
    counts only on a request that came through the edge: a caller of the raw
    `*.run.app` origin can write any header.
    """
    path = request.url.path
    return source_of(request.headers, path) == "live" and verified_category(request.headers, path) is not None


async def _count(
    day: date, platform: str, verified: bool, page: str, spec_id: str, language: str, library_id: str
) -> None:
    """Add one to the counter. A failure is logged and goes no further: the image is already out.

    That covers the table not being there yet. The migration reaches production
    through `sync-postgres.yml` after the merge, which can be later than the
    deploy of the code that writes.
    """
    try:
        async with _WRITE_SLOTS, get_db_context() as session:
            await LinkShareRepository(session).count(
                day=day,
                platform=platform,
                verified=verified,
                page=page,
                spec_id=spec_id,
                language=language,
                library_id=library_id,
            )
    except Exception as exc:  # nothing a share counter does may reach the caller
        logger.warning("share not counted (non-critical): %s", type(exc).__name__)


def record_share(request: Request, *, page: str, spec_id: str = "", language: str = "", library_id: str = "") -> None:
    """Count the fetch of a page's preview image as a share, in the background.

    Call it once the image is certain to be served: a fetch that ends in a 404
    is no preview anyone saw. The ids are the route's, which by then named an
    existing spec and implementation.
    """
    if not settings.is_production or page not in SHARE_PAGES:
        return
    user_agent = request.headers.get("user-agent", "")
    if detect_ai_agent(user_agent) is not None:
        return
    if len(_WRITES) >= MAX_PENDING_WRITES:
        return
    write = asyncio.create_task(
        _count(
            datetime.now(UTC).date(),
            share_platform(user_agent),
            is_verified(request),
            page,
            spec_id,
            language,
            library_id,
        )
    )
    _WRITES.add(write)
    write.add_done_callback(_WRITES.discard)


# =============================================================================
# Reading
# =============================================================================


class SharedLinksDay(BaseModel):
    """One UTC day of the window."""

    date: str
    shares: int


class SharedLinksPlatform(BaseModel):
    """One platform's shares over the window."""

    platform: str
    shares: int


class SharedLinksPlot(BaseModel):
    """One plot page's shares over the window: a spec's hub, or one implementation of it."""

    spec_id: str
    language: str | None = None
    library: str | None = None
    shares: int


class SharedLinksSpec(BaseModel):
    """One spec's shares over the window: its hub and all of its implementation pages together."""

    spec_id: str
    shares: int


class SharedLinksLibrary(BaseModel):
    """One library's shares over the window: its implementation pages, whatever the spec."""

    library: str
    shares: int


class SharedLinksResponse(BaseModel):
    """The public numbers: shares by the named platforms only.

    `days` has one entry per UTC day of the window, oldest first, zeros
    included. `platforms`, `top_specs` and `top_libraries` are sorted by
    shares, largest first. A share of a spec's hub counts for the spec and for
    no library, so the libraries add up to less than the specs.
    `not_configured` without a database and `unavailable` when it does not
    answer, both with zeros.
    """

    status: UsageStatus
    window_days: int = WINDOW_DAYS
    total: int = 0
    days: list[SharedLinksDay] = []
    platforms: list[SharedLinksPlatform] = []
    top_specs: list[SharedLinksSpec] = []
    top_libraries: list[SharedLinksLibrary] = []


class SharedLinksDetail(SharedLinksResponse):
    """The owner's numbers: the public ones, plus what they leave out.

    `top` lists the most shared plot pages, a hub and each implementation as
    entries of their own. `other` is the fetches that are not counted as
    shares. `verified` says, per platform and for `other`, how many of its
    fetches Cloudflare verified; a platform with none is absent. A platform
    Cloudflare verifies whose shares are mostly unverified is being imitated.
    """

    top: list[SharedLinksPlot] = []
    other: int = 0
    verified: dict[str, int] = {}


def window_start(today: date) -> date:
    """The first UTC day of the window that ends on *today*."""
    return today - timedelta(days=WINDOW_DAYS - 1)


async def read_detail(repository: LinkShareRepository, today: date | None = None) -> SharedLinksDetail:
    """The window's numbers from the counters; `other` is kept apart from everything else."""
    until = today or datetime.now(UTC).date()
    since = window_start(until)
    per_day = dict.fromkeys((since + timedelta(days=offset) for offset in range(WINDOW_DAYS)), 0)
    per_platform: dict[str, int] = {}
    verified_fetches: dict[str, int] = {}
    other = 0
    for day, platform, verified, fetches in await repository.by_day_and_platform(since, until):
        if verified:
            verified_fetches[platform] = verified_fetches.get(platform, 0) + fetches
        if platform == OTHER:
            other += fetches
        else:
            per_day[day] += fetches
            per_platform[platform] = per_platform.get(platform, 0) + fetches
    top = await repository.top_plots(since, until, without_platform=OTHER, limit=TOP_ENTRIES)
    top_specs = await repository.top_specs(since, until, without_platform=OTHER, limit=TOP_ENTRIES)
    top_libraries = await repository.top_libraries(since, until, without_platform=OTHER, limit=TOP_ENTRIES)
    return SharedLinksDetail(
        status="ok",
        total=sum(per_day.values()),
        days=[SharedLinksDay(date=day.isoformat(), shares=shares) for day, shares in per_day.items()],
        platforms=[
            SharedLinksPlatform(platform=platform, shares=shares)
            for platform, shares in sorted(per_platform.items(), key=lambda item: (-item[1], item[0]))
        ],
        top_specs=[SharedLinksSpec(spec_id=spec_id, shares=shares) for spec_id, shares in top_specs],
        top_libraries=[SharedLinksLibrary(library=library_id, shares=shares) for library_id, shares in top_libraries],
        top=[
            SharedLinksPlot(spec_id=spec_id, language=language or None, library=library_id or None, shares=shares)
            for spec_id, language, library_id, shares in top
        ],
        other=other,
        verified=dict(sorted(verified_fetches.items())),
    )


async def load_public() -> SharedLinksResponse:
    """The public numbers through a session of their own, for a cached answer and its background refresh.

    Raises when the database does not answer or the table is not there yet; the
    caller turns that into `unavailable` and keeps nothing.
    """
    async with get_db_context() as session:
        detail = await read_detail(LinkShareRepository(session))
    return SharedLinksResponse(**detail.model_dump(exclude={"top", "other", "verified"}))
