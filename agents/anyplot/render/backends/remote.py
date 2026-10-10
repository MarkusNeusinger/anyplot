"""The remote render backend: the anyplot-renderer Cloud Run service (phase 1).

`AGENT_RENDERER=remote` posts every job to `AGENT_RENDER_URL/render` and turns the
answer back into a `RenderResult`; the host gates (`gates.py`) judge it exactly as
they judge any other backend's output. The JSON contract is `agents/renderer/wire.py`,
which both sides read (it has no ADK import, so the renderer image needs no ADK).
Because the renderer is its own service, a developer's `adk web` and the deployed
agents service render through the same sandboxes.

**ID token.** The renderer runs with `--no-allow-unauthenticated`, so every request
carries a Google-signed ID token, minted by `IdTokenSource`:

* Deployed (any environment but `development`):
  `google.oauth2.id_token.fetch_id_token_credentials(AGENT_RENDER_URL)`, which on
  Cloud Run asks the metadata server for a token whose `aud` is the renderer URL and
  whose `email` is the agents service account (a service-account or
  impersonated-service-account file in `GOOGLE_APPLICATION_CREDENTIALS` works the same).
  `AGENT_RENDER_URL` must be the service URL (`status.url`): Cloud Run accepts no
  other audience, not even a tag URL.
* Development: `AGENT_RENDER_TOKEN` when set (a token from
  `gcloud auth print-identity-token`, valid for one hour); otherwise Application
  Default Credentials. A user's ADC (`gcloud auth application-default login`) cannot
  mint a token for an audience, so the backend refreshes them and sends their
  `id_token`, whose `aud` is the ADC OAuth client id; the renderer accepts it once
  that id is in `RENDERER_AUDIENCES` and the user's email in
  `RENDERER_ALLOWED_CALLERS`. Other ADC (a service-account key in
  `GOOGLE_APPLICATION_CREDENTIALS`) go through `fetch_id_token_credentials`.

Tokens are cached and refreshed five minutes before they expire; minting runs in a
worker thread, because google-auth blocks.

**Failures.** A connection error, or a Cloud Run front-end answer of 429 or 5xx
without the renderer's own JSON `detail`, is retried after 1, 3, 8 and 15 seconds,
within `RETRY_BUDGET_S`: spike S saw a 500, then a 429 ten seconds later, and a 200
only about 17 s after the first request to a service scaled to zero. The renderer's
own refusals (`503 busy`, `500 internal`, ...) carry a JSON `detail` and are never
retried. Everything else maps to `RendererUnavailable` with a message that names a
status, a fixed error code or an exception class, never a response body; the
message is also logged, so a refused caller or a wrong audience shows in the log.
A theme the renderer did not answer is left out of the result, so R1 reports it; a
theme whose sandbox launcher failed twice (`launcher`) is `RendererUnavailable`,
because it is the renderer's failure and not the code's; the other reasons
(`disk_budget`, `file_budget`, `memory`, `output_rejected`) go to the gates with the
measured value and the limit.

**Cancellation.** When this render is cancelled (an abort, the request deadline) or
its answer does not come in time, the backend also posts
`/render/{job_id}/cancel`, because a front end that does not pass the closed
connection on would leave the sandbox running and the renderer's only slot taken.

No semaphore here: `SerialRenderer` (`render/serial.py`) already hands this backend
one theme at a time, and the renderer keeps its own single render slot for the
callers it serves together.
"""

import asyncio
import base64
import binascii
import json
import logging
import os
import re
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Protocol

import google.auth
import google.auth.exceptions
import google.oauth2.credentials
import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from pydantic import ValidationError

from agents.renderer.wire import MAX_PNG_BYTES, RenderRequest, RenderResponse

from ..contract import RendererUnavailable, RenderJob, RenderResult, ThemeOutput


logger = logging.getLogger(__name__)

TOKEN_REFRESH_MARGIN_S = 300.0
TOKEN_FALLBACK_LIFETIME_S = 3000.0
"""Used when a token carries no readable `exp` claim; Google ID tokens live an hour."""
CONNECT_TIMEOUT_S = 10.0
RESPONSE_MARGIN_S = 45.0
"""On top of the job's own time per theme: the renderer's slot wait (`RENDERER_SLOT_WAIT_S`,
30 s), the sandbox start and delete, and the transfer of up to 10 MiB of PNG."""
RETRY_DELAYS_S = (1.0, 3.0, 8.0, 15.0)
"""Pauses before the retries of a connection error or a front-end 429/5xx (spike S's cold start)."""
RETRY_BUDGET_S = 30.0
"""No retry starts later than this after the first request."""
CANCEL_TIMEOUT_S = 5.0
FRONT_END_RETRY = frozenset({429, 500, 502, 503, 504})
_DETAIL = re.compile(r"^[a-z_]{1,32}$")
_MAX_PNG_BASE64 = 4 * ((MAX_PNG_BYTES + 2) // 3)


class TokenSource(Protocol):
    """Where the backend gets the bearer token of the next request."""

    async def token(self) -> str: ...


def _unavailable(message: str) -> RendererUnavailable:
    """The error to raise, logged first: every message here is built from statuses, codes and class names."""
    logger.warning("remote renderer: %s", message)
    return RendererUnavailable(message)


def token_expiry(token: str) -> float | None:
    """The `exp` claim of a JWT, read without verifying it (the renderer side relies on Cloud Run IAM)."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    except (ValueError, binascii.Error):
        return None
    expiry = claims.get("exp") if isinstance(claims, dict) else None
    return float(expiry) if isinstance(expiry, int | float) else None


class IdTokenSource:
    """Mints, caches and refreshes the ID token for `audience` (see the module docstring for the order)."""

    def __init__(
        self,
        audience: str,
        *,
        development: bool,
        static_token: str | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.audience = audience
        self.development = development
        self.static_token = static_token
        self.clock = clock
        self._token: str | None = None
        self._expires = 0.0
        self._lock = asyncio.Lock()

    async def token(self) -> str:
        if self.static_token is not None:
            expiry = token_expiry(self.static_token)
            if expiry is not None and expiry <= self.clock():
                raise _unavailable(
                    "AGENT_RENDER_TOKEN has expired; export a fresh one from `gcloud auth print-identity-token`"
                )
            return self.static_token
        async with self._lock:
            if self._token is None or self._expires - self.clock() < TOKEN_REFRESH_MARGIN_S:
                try:
                    token = await asyncio.to_thread(self._mint)
                except google.auth.exceptions.GoogleAuthError as exc:
                    raise _unavailable(
                        f"no ID token for the renderer ({type(exc).__name__}); on a developer machine run "
                        "`gcloud auth application-default login` or set AGENT_RENDER_TOKEN"
                    ) from None
                self._token = token
                self._expires = token_expiry(token) or self.clock() + TOKEN_FALLBACK_LIFETIME_S
            return self._token

    def _mint(self) -> str:
        """Blocking: a fresh ID token."""
        request = GoogleAuthRequest()
        if self.development and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            credentials, _ = google.auth.default()
            if isinstance(credentials, google.oauth2.credentials.Credentials):
                credentials.refresh(request)
                user_token: str | None = credentials.id_token
                if not user_token:
                    raise _unavailable(
                        "the Application Default Credentials carry no ID token; run "
                        "`gcloud auth application-default login` again or set AGENT_RENDER_TOKEN"
                    )
                return user_token
        id_credentials = google_id_token.fetch_id_token_credentials(self.audience, request=request)
        id_credentials.refresh(request)
        token: str = id_credentials.token
        return token


def _detail(response: httpx.Response) -> str | None:
    """The renderer's own error code (`{"detail": "busy"}`); None for any other body."""
    if not response.headers.get("content-type", "").startswith("application/json"):
        return None
    try:
        body = response.json()
    except ValueError:
        return None
    detail = body.get("detail") if isinstance(body, dict) else None
    return detail if isinstance(detail, str) and _DETAIL.fullmatch(detail) else None


def _png(value: str | None) -> bytes | None:
    if value is None or len(value) > _MAX_PNG_BASE64:
        return None
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        return None


class RemoteBackend:
    """Renders through the anyplot-renderer service."""

    name = "remote"

    def __init__(
        self,
        *,
        url: str,
        tokens: TokenSource,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_delays_s: Sequence[float] = RETRY_DELAYS_S,
        retry_budget_s: float = RETRY_BUDGET_S,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.url = url.rstrip("/")
        self.tokens = tokens
        self.retry_delays_s = tuple(retry_delays_s)
        self.retry_budget_s = retry_budget_s
        self.clock = clock
        self.sleep = sleep
        self._client = httpx.AsyncClient(transport=transport, follow_redirects=False)
        self._cancels: set[asyncio.Task[None]] = set()

    async def aclose(self) -> None:
        if self._cancels:
            await asyncio.wait(self._cancels, timeout=CANCEL_TIMEOUT_S)
        await self._client.aclose()

    async def render(self, job: RenderJob) -> RenderResult:
        try:
            body = RenderRequest.model_validate(
                {
                    "job_id": job.job_id,
                    "language": job.language,
                    "library": job.library,
                    "source": job.source,
                    "data_csv": job.data_csv,
                    "themes": list(job.themes),
                    "timeout_s": job.timeout_s,
                }
            ).model_dump(mode="json")
        except ValidationError as exc:
            fields = ",".join(sorted({str(error["loc"][0]) for error in exc.errors() if error["loc"]}))
            raise _unavailable(f"the job does not fit the renderer contract ({fields})") from None
        timeout = httpx.Timeout(job.timeout_s * len(job.themes) + RESPONSE_MARGIN_S, connect=CONNECT_TIMEOUT_S)
        try:
            response = await self._post(body, timeout)
        except asyncio.CancelledError:
            await self._cancel_remote(job.job_id)
            raise
        except httpx.TimeoutException as exc:  # the answer did not come in time; ConnectTimeout is retried in _post
            await self._cancel_remote(job.job_id)
            raise _unavailable(f"the renderer did not answer in time ({type(exc).__name__})") from None
        return self._result(job, response)

    async def _post(self, body: dict[str, object], timeout: httpx.Timeout) -> httpx.Response:
        """POST the job, retrying connection errors and front-end 429/5xx with backoff inside the budget."""
        delays = iter(self.retry_delays_s)
        started = self.clock()
        while True:
            headers = {"Authorization": f"Bearer {await self.tokens.token()}"}
            response: httpx.Response | None = None
            try:
                response = await self._client.post(f"{self.url}/render", json=body, headers=headers, timeout=timeout)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
                failure = f"could not be reached ({type(exc).__name__})"
            except httpx.TimeoutException:
                raise
            except httpx.HTTPError as exc:
                raise _unavailable(f"the render request failed ({type(exc).__name__})") from None
            else:
                if response.status_code not in FRONT_END_RETRY or _detail(response) is not None:
                    return response
                failure = f"front end answered HTTP {response.status_code}"
            delay = next(delays, None)
            if delay is None or self.clock() - started + delay > self.retry_budget_s:
                if response is not None:
                    return response  # `_result` names the status
                raise _unavailable(f"the renderer {failure}")
            logger.warning("remote renderer %s; retrying in %.0f s", failure, delay)
            await self.sleep(delay)

    async def _cancel_remote(self, job_id: str) -> None:
        """Best effort, shielded: ask the renderer to stop the job's sandbox and free its slot."""
        task = asyncio.create_task(self._send_cancel(job_id))
        self._cancels.add(task)
        task.add_done_callback(self._cancels.discard)
        await asyncio.shield(task)

    async def _send_cancel(self, job_id: str) -> None:
        try:
            async with asyncio.timeout(CANCEL_TIMEOUT_S):
                headers = {"Authorization": f"Bearer {await self.tokens.token()}"}
                response = await self._client.post(
                    f"{self.url}/render/{job_id}/cancel", headers=headers, timeout=CANCEL_TIMEOUT_S
                )
            logger.info("remote render %s: cancel sent (HTTP %s)", job_id, response.status_code)
        except (TimeoutError, httpx.HTTPError, RendererUnavailable) as exc:
            logger.warning("remote render %s: the cancel did not reach the renderer (%s)", job_id, type(exc).__name__)

    def _result(self, job: RenderJob, response: httpx.Response) -> RenderResult:
        status = response.status_code
        if status != 200:
            detail = _detail(response)
            suffix = f", {detail}" if detail else ""
            if status in (401, 403):
                raise _unavailable(
                    f"the renderer refused this caller (HTTP {status}{suffix}): check roles/run.invoker, "
                    "AGENT_RENDER_URL (the service URL), RENDERER_AUDIENCES and RENDERER_ALLOWED_CALLERS"
                )
            raise _unavailable(f"the renderer answered HTTP {status}{suffix}")
        try:
            answer = RenderResponse.model_validate_json(response.content)
        except ValidationError:
            raise _unavailable("the renderer's answer does not match the contract") from None
        if answer.job_id != job.job_id:
            raise _unavailable("the renderer answered for another job")
        result = RenderResult(job_id=job.job_id)
        for theme in job.themes:
            run = answer.outputs.get(theme)
            if run is None:
                continue  # R1 reports a theme without an output
            logger.info(
                "remote render %s (%s): exit %s, reason %s, attempts %s, %.2f s",
                job.job_id,
                theme,
                run.exit_code,
                run.reason,
                run.attempts,
                run.wall_s,
            )
            if run.reason == "launcher":
                # The renderer retries a launcher failure once when the job's time
                # allows it, so this is one failure or two: `attempts` says which.
                times = "twice" if run.attempts > 1 else "once, with no time left for a retry"
                raise _unavailable(f"the renderer's sandbox launcher failed {times} ({theme})")
            result.outputs[theme] = ThemeOutput(
                theme=theme,
                exit_code=run.exit_code,
                timed_out=run.timed_out,
                png=_png(run.png_base64),
                probe=run.probe,
                stderr_tail=run.stderr_tail,
                wall_s=run.wall_s,
                reason=run.reason,
                measured=run.measured,
                limit=run.limit,
            )
        return result
