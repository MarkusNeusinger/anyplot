"""Feedback endpoint — in-app quick feedback widget (issue #5662).

Accepts a single POST with an optional short free-text message and/or
reaction, free-form contact handle, and page context. At least one of
message or reaction must be present. Guards against spam with a honeypot
field, hard length caps, reaction allow-list, a Cloudflare Turnstile token
(`X-Turnstile-Token`, `api/turnstile.py`, #7249), and per-IP rate limit.
"""

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api import turnstile
from api.dependencies import require_db
from api.exceptions import raise_validation_error
from api.request_context import client_ip as _client_ip
from api.schemas import FeedbackRequest, FeedbackResponse
from core.database import FEEDBACK_REACTIONS, FeedbackRepository
from core.plot_votes import PLOT_VOTE_REACTIONS


logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])

MAX_MESSAGE_LENGTH = 500
MAX_CONTACT_LENGTH = 255
RATE_LIMIT_WINDOW = timedelta(minutes=1)
# Free-text entries: 5 per minute per IP, counted over message-bearing rows only.
RATE_LIMIT_MAX = 5
# Reaction-only entries (a 👍/👎 tap on a plot): someone flipping through the
# library carousel rates several images in quick succession, so the cap is
# looser and counted over every row from that IP.
REACTION_RATE_LIMIT_MAX = 30

# Anti-spam heuristics — see _is_link_stuffed and the duplicate check below.
# Both branches return 200 silently (mirroring the honeypot) so bots can't
# distinguish accepted from suppressed submissions and adapt their payloads.
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
MAX_URLS_IN_MESSAGE = 1  # 2+ links treated as link-stuffing SEO spam
DUPLICATE_LOOKBACK = timedelta(minutes=10)


IP_HASH_PREFIX = "hmac:"
"""Marks a salted `ip_hash` (`_hash_ip`). The unsalted SHA-256 hashes that rows written before it
carried were cleared once by hand on 2026-11-02 after a snapshot; no migration is needed."""
_IP_SALT = secrets.token_bytes(32)
"""This process's salt for `_hash_ip`. Never logged and never configured, so it dies with the
process, and with it every way to tell which address a stored hash came from."""


def _hash_ip(ip: str) -> str:
    """The client address as this process's rate-limit key: `hmac:` and 32 hex digits.

    An HMAC-SHA256 under a random per-process salt, not a plain hash: there are only about
    four billion IPv4 addresses, so a plain SHA-256 of one is undone by trying them all. The
    windows below need the key only within one process, and the row keeps it only until the
    longest of them has passed (`FeedbackRepository.clear_ip_hashes`). With more than one
    instance, each counts its own requests: a limit then binds per instance."""
    if not ip:
        return ""
    return IP_HASH_PREFIX + hmac.new(_IP_SALT, ip.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _is_link_stuffed(message: str | None) -> bool:
    """True if the message reads as link-bait spam (≥2 http(s) URLs)."""
    if not message:
        return False
    return len(_URL_RE.findall(message)) > MAX_URLS_IN_MESSAGE


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackRequest,
    request: Request,
    siteverify: Annotated[httpx.AsyncClient, Depends(turnstile.get_turnstile_client)],
    human: Annotated[str | None, Header(alias=turnstile.TOKEN_HEADER)] = None,
    db: AsyncSession = Depends(require_db),
) -> FeedbackResponse:
    """Accept a feedback entry from the in-app widget or a plot page's 👍/👎."""
    # Honeypot: bots auto-fill every input. Real users never see this field.
    # Return 200 silently so bots can't probe for the guard.
    if payload.website:
        return FeedbackResponse(status="ok")

    message = (payload.message or "").strip() or None
    if message is not None and len(message) > MAX_MESSAGE_LENGTH:
        raise_validation_error(f"message must be {MAX_MESSAGE_LENGTH} characters or fewer")

    reaction = payload.reaction
    if reaction is not None and reaction not in FEEDBACK_REACTIONS:
        raise_validation_error(f"reaction must be one of {FEEDBACK_REACTIONS}")

    if message is None and reaction is None:
        raise_validation_error("message or reaction must be provided")

    contact = (payload.contact or "").strip() or None
    if contact is not None and len(contact) > MAX_CONTACT_LENGTH:
        raise_validation_error(f"contact must be {MAX_CONTACT_LENGTH} characters or fewer")

    # Link-stuffing spam: drop silently with 200 so the bot can't tell its
    # payload was rejected (same idea as the honeypot above).
    if _is_link_stuffed(message):
        return FeedbackResponse(status="ok")

    # The bot check answers with its own status rather than a silent 200 like the
    # filters above: a visitor's token can expire or a check can fail, and the
    # widget then says so and offers to send again. That tells a bot nothing the
    # site's own script does not show it already. After the
    # cheap filters, so a refused payload costs no siteverify call; before the
    # database, so an unchecked one costs no query.
    refused = turnstile.refusal(await turnstile.verify(human, siteverify))
    if refused is not None:
        raise HTTPException(status_code=refused[0], detail=refused[1])

    ip_hash = _hash_ip(_client_ip(request))
    repo = FeedbackRepository(db)

    # `feedback.created_at` is TIMESTAMP WITHOUT TIME ZONE (UTC) in Postgres,
    # so any cutoff used in WHERE clauses must be tz-naive UTC too.
    now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    # The hash outlives no window: every submission that reaches the database, refused or
    # stored, first clears the salted hashes past the longest window.
    await _clear_expired_ip_hashes(repo, now_utc_naive)

    if ip_hash:
        since = now_utc_naive - RATE_LIMIT_WINDOW
        if message is not None:
            recent = await repo.count_recent_by_ip(ip_hash, since, messages_only=True)
            limit = RATE_LIMIT_MAX
        else:
            recent = await repo.count_recent_by_ip(ip_hash, since)
            limit = REACTION_RATE_LIMIT_MAX
        if recent >= limit:
            raise HTTPException(status_code=429, detail="Too many feedback submissions, please slow down")

    # Silent duplicate suppression: same message text from the same IP or
    # session id within DUPLICATE_LOOKBACK is dropped without an error — keeps
    # repeated bot copy-paste out of the DB without revealing the filter.
    session_id = (payload.session_id or None) and payload.session_id[:64]
    if message and await repo.has_recent_duplicate(
        message, ip_hash or None, session_id, now_utc_naive - DUPLICATE_LOOKBACK
    ):
        return FeedbackResponse(status="ok")

    # One 👍/👎 per image per session: the plot buttons lock after the first
    # tap, so a second vote from the same session on the same version of an
    # implementation only ever comes from someone working around the UI — drop
    # it silently. A regeneration starts a new version (`core.plot_votes`), and
    # the same session may rate that one once.
    spec_id = (payload.spec_id or None) and payload.spec_id[:100]
    library_id = (payload.library_id or None) and payload.library_id[:50]
    language = (payload.language or None) and payload.language[:50]
    if reaction in PLOT_VOTE_REACTIONS and session_id and spec_id and library_id:
        version_start = await repo.version_start(spec_id, library_id, language)
        if await repo.has_plot_vote(session_id, spec_id, library_id, language, since=version_start):
            return FeedbackResponse(status="ok")

    user_agent = request.headers.get("user-agent", "")[:500] or None

    await repo.create(
        {
            "message": message,
            "reaction": reaction,
            "contact": contact,
            "path": (payload.path or None) and payload.path[:500],
            "spec_id": spec_id,
            "library_id": library_id,
            "language": language,
            "viewport": (payload.viewport or None) and payload.viewport[:20],
            "session_id": session_id,
            "user_agent": user_agent,
            "ip_hash": ip_hash or None,
        }
    )

    return FeedbackResponse(status="ok")


async def _clear_expired_ip_hashes(repo: FeedbackRepository, now_utc_naive: datetime) -> None:
    """Null the salted hashes older than `DUPLICATE_LOOKBACK`, the longest window that reads them.

    A failure costs the visitor nothing: it is rolled back and logged, and the next submission
    clears them instead. A hash that a stopped process wrote cannot be recomputed by anyone, since
    its salt died with that process."""
    try:
        await repo.clear_ip_hashes(IP_HASH_PREFIX, now_utc_naive - DUPLICATE_LOOKBACK)
    except Exception as exc:  # the driver, the pool: never the visitor's problem
        await repo.session.rollback()
        logger.warning("feedback ip_hash cleanup failed: %s", type(exc).__name__)
