"""Cloudflare Turnstile: the bot check on the calls that open or store something for an anonymous visitor.

Three calls carry a token, each in the `X-Turnstile-Token` header: opening a public chat session
(`POST /agent/sessions`), a public chat feedback case (`POST /agent/session/feedback`) and a site feedback
entry (`POST /feedback`, the widget and the plot pages' votes). A chat message, a paste or a render does not:
those act on a session that a checked call opened, and the per-user and per-network limits bound them.

The page renders the widget in Managed mode with `appearance: 'interaction-only'`, so most visitors never see
it, and asks for a fresh token per protected call: a token is valid for 300 seconds and only once
(Cloudflare, "Server-side validation"). This module redeems it at Cloudflare's siteverify endpoint.

**On while `TURNSTILE_SECRET_KEY` is set**, in every environment. Unset, local development and the test suite
skip the check, and production refuses the protected calls (`503 bot_check_unavailable`) and keeps the public
chat's door shut (`api/routers/agent_public.py` `require_public_enabled`), so a revision that lost the secret
says so on the deploy smoke instead of serving unchecked. A siteverify answer from one of Cloudflare's test
secrets counts as no secret in production for the same reason: one test secret passes every token, and the
others refuse every visitor.

**Fail closed.** A missing, malformed, expired, reused or refused token is `403 bot_check_failed`; siteverify
unreachable, or answering `internal-error` after the one retry, or refusing the secret itself, is
`503 bot_check_unavailable`. Nothing passes on an error.

**No `remoteip`.** Cloudflare's widget already sees the visitor's address when it runs in their browser; sending
it again from the server would add a second, server-side copy of the address to Cloudflare's request for a
parameter Cloudflare marks optional. The request carries the secret, the token and an idempotency key, so the
one retry after a lost answer cannot fail as a duplicate of the first attempt. Nothing about the token or the
answer is logged except Cloudflare's error codes on the server-side failures.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Literal

import httpx

from core.config import settings


logger = logging.getLogger(__name__)

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TOKEN_HEADER = "X-Turnstile-Token"
MAX_TOKEN_CHARS = 2048
"""Cloudflare's own bound on a token; a longer value is refused without asking siteverify."""
ATTEMPT_TIMEOUT_S = 5.0
ATTEMPTS = 2
"""The first call and at most one retry, after a timeout, a transport error, a 5xx or `internal-error`."""
RETRY_DELAY_S = 0.5

FAILED = "bot_check_failed"
UNAVAILABLE = "bot_check_unavailable"

Verdict = Literal["passed", "skipped", "missing", "rejected", "unavailable", "unconfigured"]
"""What `verify` made of a token: `passed`, or `skipped` without a secret outside production, let the call
through; every other verdict refuses it (`refusal`)."""

_REFUSALS: dict[str, tuple[int, str]] = {
    "missing": (403, FAILED),
    "rejected": (403, FAILED),
    "unavailable": (503, UNAVAILABLE),
    "unconfigured": (503, UNAVAILABLE),
}
_SECRET_ERRORS = frozenset({"missing-input-secret", "invalid-input-secret"})


def enforced() -> bool:
    """Whether a secret is configured. Read per call: the tests flip the setting between requests."""
    return bool(settings.turnstile_secret_key)


async def get_turnstile_client() -> AsyncIterator[httpx.AsyncClient]:
    """The HTTP client for siteverify; tests override it with a mock transport."""
    async with httpx.AsyncClient(timeout=httpx.Timeout(ATTEMPT_TIMEOUT_S)) as client:
        yield client


def _error_codes(answer: dict[str, Any]) -> list[str]:
    codes = answer.get("error-codes")
    return [code for code in codes if isinstance(code, str)] if isinstance(codes, list) else []


def _from_testing_key(answer: dict[str, Any]) -> bool:
    metadata = answer.get("metadata")
    return isinstance(metadata, dict) and metadata.get("result_with_testing_key") is True


async def verify(token: str | None, client: httpx.AsyncClient) -> Verdict:
    """Redeem one token at siteverify; see the module docstring for what each verdict means."""
    secret = settings.turnstile_secret_key
    if not secret:
        return "unconfigured" if settings.is_production else "skipped"
    if not token or len(token) > MAX_TOKEN_CHARS:
        return "missing"
    payload = {"secret": secret, "response": token, "idempotency_key": str(uuid.uuid4())}
    for attempt in range(ATTEMPTS):
        if attempt:
            await asyncio.sleep(RETRY_DELAY_S)
        try:
            response = await client.post(SITEVERIFY_URL, data=payload)
        except httpx.HTTPError as exc:
            logger.warning("turnstile siteverify unreachable: %s", type(exc).__name__)
            continue
        if response.status_code >= 500:
            logger.warning("turnstile siteverify answered %d", response.status_code)
            continue
        try:
            answer = response.json()
        except ValueError:
            answer = None
        if not isinstance(answer, dict):
            logger.warning("turnstile siteverify answered %d without a JSON object", response.status_code)
            return "unavailable"
        codes = _error_codes(answer)
        if settings.is_production and _from_testing_key(answer):
            # Whatever it answered: one test secret passes every token, the others refuse every visitor.
            logger.warning("turnstile secret is one of Cloudflare's test secrets; refusing in production")
            return "unconfigured"
        if answer.get("success") is True:
            return "passed"
        if "internal-error" in codes:
            logger.warning("turnstile siteverify answered internal-error")
            continue
        if _SECRET_ERRORS.intersection(codes):
            logger.warning("turnstile siteverify refused the secret: %s", ",".join(sorted(codes)))
            return "unconfigured"
        return "rejected"
    return "unavailable"


def refusal(verdict: Verdict) -> tuple[int, str] | None:
    """The status and error code a verdict answers with, or None when the call may go on."""
    return _REFUSALS.get(verdict)
