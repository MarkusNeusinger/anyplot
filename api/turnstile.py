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

**Fail closed.** A missing, malformed, expired, reused or refused token is `403 bot_check_failed`, and so is a
passing token that production finds was solved on a host other than anyplot.ai or one of its subdomains;
siteverify unreachable, or answering `internal-error` after the one retry, refusing the secret, or calling the
request itself malformed, is `503 bot_check_unavailable`. Only an HTTP 200 with `success: true` passes.

**Not checked: `action`.** The page names the call in the widget's `action` for Cloudflare's per-action counts.
Anyone who renders the widget picks the action, so comparing it would refuse nothing a script could not mint.

**No `remoteip`.** Cloudflare documents the parameter as optional and documents no check it would enable;
Cloudflare already sees the address in the widget and at the edge, so leaving it out keeps the visitor's
address off one more request without weakening anything the check relies on. If tokens solved in one place and
redeemed from another ever show up, sending it is a one-line change. The request carries the secret, the token
and an idempotency key, so the one retry after a lost answer cannot fail as a duplicate of the first attempt.
Nothing about the token or the answer is logged except Cloudflare's error codes and a foreign hostname.
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
_SERVER_ERRORS = _SECRET_ERRORS | {"bad-request"}
"""Codes that blame this server's request, not the visitor's token: a `503`, never a `403`."""
SITE_HOSTNAME = "anyplot.ai"
"""Where a production token must have been solved: this host or a subdomain. The widget's hostname list in
Cloudflare's dashboard is the first fence; this one holds if a development host is ever added there."""


def _site_hostname(hostname: object) -> bool:
    return isinstance(hostname, str) and (hostname == SITE_HOSTNAME or hostname.endswith(f".{SITE_HOSTNAME}"))


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
            if response.status_code != 200:
                logger.warning("turnstile siteverify answered success with status %d", response.status_code)
                return "unavailable"
            if settings.is_production and not _site_hostname(answer.get("hostname")):
                logger.warning("turnstile token solved on a foreign host: %.100s", answer.get("hostname"))
                return "rejected"
            return "passed"
        if "internal-error" in codes:
            logger.warning("turnstile siteverify answered internal-error")
            continue
        if _SERVER_ERRORS.intersection(codes):
            logger.warning("turnstile siteverify refused this server's request: %s", ",".join(sorted(codes)))
            return "unconfigured"
        return "rejected"
    return "unavailable"


def refusal(verdict: Verdict) -> tuple[int, str] | None:
    """The status and error code a verdict answers with, or None when the call may go on."""
    return _REFUSALS.get(verdict)
