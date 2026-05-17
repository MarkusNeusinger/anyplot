"""Feedback endpoint — in-app quick feedback widget (issue #5662).

Accepts a single POST with a short free-text message plus optional reaction,
email, and page context. Guards against spam with a honeypot field, hard
length cap, reaction allow-list, and per-IP rate limit.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.exceptions import raise_validation_error
from api.schemas import FeedbackRequest, FeedbackResponse
from core.database import FEEDBACK_REACTIONS, FeedbackRepository


logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])

MAX_MESSAGE_LENGTH = 500
MAX_EMAIL_LENGTH = 255
RATE_LIMIT_WINDOW = timedelta(minutes=1)
RATE_LIMIT_MAX = 5


def _client_ip(request: Request) -> str:
    """Resolve the client IP, preferring x-forwarded-for (Cloud Run + CF)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        # x-forwarded-for can be a comma-separated chain; the first entry is the original client.
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _hash_ip(ip: str) -> str:
    """SHA-256 of the IP, hex. Used for rate-limit lookups only — never reversed."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else ""


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackRequest, request: Request, db: AsyncSession = Depends(require_db)
) -> FeedbackResponse:
    """Accept a feedback entry from the in-app widget."""
    # Honeypot: bots auto-fill every input. Real users never see this field.
    # Return 200 silently so bots can't probe for the guard.
    if payload.website:
        return FeedbackResponse(status="ok")

    message = (payload.message or "").strip()
    if not message:
        raise_validation_error("message must not be empty")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise_validation_error(f"message must be {MAX_MESSAGE_LENGTH} characters or fewer")

    reaction = payload.reaction
    if reaction is not None and reaction not in FEEDBACK_REACTIONS:
        raise_validation_error(f"reaction must be one of {FEEDBACK_REACTIONS}")

    email = (payload.email or "").strip() or None
    if email is not None:
        if "@" not in email or len(email) > MAX_EMAIL_LENGTH:
            raise_validation_error("email is not valid")

    ip_hash = _hash_ip(_client_ip(request))
    repo = FeedbackRepository(db)

    if ip_hash:
        since = datetime.now(timezone.utc) - RATE_LIMIT_WINDOW
        recent = await repo.count_recent_by_ip(ip_hash, since)
        if recent >= RATE_LIMIT_MAX:
            raise HTTPException(status_code=429, detail="Too many feedback submissions, please slow down")

    user_agent = request.headers.get("user-agent", "")[:500] or None

    await repo.create(
        {
            "message": message,
            "reaction": reaction,
            "email": email,
            "path": (payload.path or None) and payload.path[:500],
            "spec_id": (payload.spec_id or None) and payload.spec_id[:100],
            "viewport": (payload.viewport or None) and payload.viewport[:20],
            "session_id": (payload.session_id or None) and payload.session_id[:64],
            "user_agent": user_agent,
            "ip_hash": ip_hash or None,
        }
    )

    return FeedbackResponse(status="ok")
