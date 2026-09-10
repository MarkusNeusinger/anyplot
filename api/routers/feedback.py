"""Feedback endpoint — in-app quick feedback widget (issue #5662).

Accepts a single POST with an optional short free-text message and/or
reaction, free-form contact handle, and page context. At least one of
message or reaction must be present. Guards against spam with a honeypot
field, hard length caps, reaction allow-list, and per-IP rate limit.
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.exceptions import raise_validation_error
from api.request_context import client_ip as _client_ip
from api.schemas import FeedbackRequest, FeedbackResponse
from core.database import FEEDBACK_REACTIONS, FeedbackRepository


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
# The two reactions the plot buttons send — the ones subject to one-vote-per-image.
PLOT_VOTE_REACTIONS = ("thumbs_up", "thumbs_down")

# Anti-spam heuristics — see _is_link_stuffed and the duplicate check below.
# Both branches return 200 silently (mirroring the honeypot) so bots can't
# distinguish accepted from suppressed submissions and adapt their payloads.
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
MAX_URLS_IN_MESSAGE = 1  # 2+ links treated as link-stuffing SEO spam
DUPLICATE_LOOKBACK = timedelta(minutes=10)


def _hash_ip(ip: str) -> str:
    """SHA-256 of the IP, hex. Used for rate-limit lookups only — never reversed."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else ""


def _is_link_stuffed(message: str | None) -> bool:
    """True if the message reads as link-bait spam (≥2 http(s) URLs)."""
    if not message:
        return False
    return len(_URL_RE.findall(message)) > MAX_URLS_IN_MESSAGE


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackRequest, request: Request, db: AsyncSession = Depends(require_db)
) -> FeedbackResponse:
    """Accept a feedback entry from the in-app widget."""
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

    ip_hash = _hash_ip(_client_ip(request))
    repo = FeedbackRepository(db)

    # `feedback.created_at` is TIMESTAMP WITHOUT TIME ZONE (UTC) in Postgres,
    # so any cutoff used in WHERE clauses must be tz-naive UTC too.
    now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)

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
    # tap, so a second vote from the same session for the same implementation
    # only ever comes from someone working around the UI — drop it silently.
    spec_id = (payload.spec_id or None) and payload.spec_id[:100]
    library_id = (payload.library_id or None) and payload.library_id[:50]
    language = (payload.language or None) and payload.language[:50]
    if (
        reaction in PLOT_VOTE_REACTIONS
        and session_id
        and spec_id
        and library_id
        and await repo.has_plot_vote(session_id, spec_id, library_id, language)
    ):
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
