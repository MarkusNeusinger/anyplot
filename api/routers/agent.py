"""Admin-only BFF for the agent chat: `/debug/agent/*` in front of anyplot-agents.

The browser never talks to the agents service. This router sits behind the
same gate as every other `/debug` route and in front of the private
anyplot-agents Cloud Run service: it derives the opaque user id, accepts only
allowlisted request fields, presents a Cloud Run ID token upstream, and
re-frames the chat stream so only the documented `anyplot/1` events reach the
browser. Design: `docs/concepts/agent-network.md` ("Serving and
infrastructure", "Guardrails"); reference: `docs/reference/api.md` ("Agent
chat").

Shipped dark: while `AGENT_ENABLED` is off, or the service URL or the user-id
key is unset, every route answers 404, so a deploy that carries this router but
not its configuration never breaks.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import aclosing
from dataclasses import dataclass
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTask

from api.dependencies import require_db
from api.routers.debug import AdminIdentity, require_admin, require_admin_identity
from core.config import settings
from core.constants import SUPPORTED_LIBRARIES
from core.database import SpecRepository
from core.utils import strip_noqa_comments


logger = logging.getLogger(__name__)

NOT_ENABLED = "agent chat is not enabled"
CLIENT_HEADER_VALUE = "agent-chat/1"
"""Required `X-Anyplot-Client` value on every POST, PUT and DELETE. A custom
header forces a CORS preflight, which a foreign origin cannot pass."""

MAX_DATASET_BYTES = 200 * 1024
MAX_MESSAGE_CHARS = 2000
SPEC_ID_PATTERN = r"^[a-z0-9-]{1,100}$"
SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"

ARTIFACT_MEDIA_TYPES: dict[str, str] = {
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
"""The only artifact names the BFF fetches. The media type is set here and the
upstream one is never forwarded."""

# Local dev servers on any port. api/main.py passes this same constant to
# CORSMiddleware as `allow_origin_regex`, so the CSRF Origin check and CORS
# always agree on what counts as local.
LOCAL_ORIGIN_REGEX = r"http://localhost:\d+"
_LOCAL_ORIGIN = re.compile(LOCAL_ORIGIN_REGEX)
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1"})
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_NO_STORE = "private, no-store"

# SSE protocol anyplot/1: the event types the browser may see and the top-level
# fields each may carry. Anything else, including `error_details` and stack
# traces, is dropped. Change this table and docs/reference/api.md together with
# the agents service's stream translator.
_EVENT_FIELDS: dict[str, frozenset[str]] = {
    "ready": frozenset({"v", "run_id"}),
    "status": frozenset({"step", "attempt"}),
    "message": frozenset({"text"}),
    "plot": frozenset({"status", "reason", "attempts", "artifacts", "changes", "residual_defects"}),
    "refusal": frozenset({"code", "text"}),
    "error": frozenset({"code", "ref"}),
    "done": frozenset({"llm_calls", "tokens"}),
}
_ERROR_CODES = frozenset({"capacity", "deadline", "guard_unavailable", "upstream", "internal"})
_MAX_EVENT_CHARS = 64 * 1024

# Error codes the agents service documents for its /v1 routes; an upstream error
# body is never forwarded, only one of these codes when it names one.
_UPSTREAM_CODES = frozenset(
    {"not_eligible", "run_active", "too_long", "unparseable", "data_refused", "session_expired"}
)
_GENERIC_CODES: dict[int, str] = {
    400: "bad_request",
    404: "not_found",
    409: "conflict",
    413: "too_long",
    422: "invalid",
    429: "rate_limited",
}
# What counts as "the agents service could not be reached": transport errors,
# timeouts, and an ID token that could not be minted.
_UNREACHABLE = (httpx.HTTPError, google_auth_exceptions.GoogleAuthError)


# ============================================================================
# Errors
# ============================================================================


class AgentHTTPError(Exception):
    """An agent-route error, answered as `{"detail": code}` plus `"ref"` when known.

    Not an `HTTPException` on purpose: the API-wide handler reshapes those into
    `{"status", "message", "path"}` and drops their headers, while the chat
    page needs a stable code and the request id to quote.
    """

    def __init__(self, status_code: int, detail: str, ref: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.ref = ref


async def agent_http_error_handler(request: Request, exc: AgentHTTPError) -> JSONResponse:
    """Render an `AgentHTTPError`; registered on the app in api/main.py."""
    content = {"detail": exc.detail}
    headers = {"Cache-Control": _NO_STORE}
    if exc.ref:
        content["ref"] = exc.ref
        headers["X-Request-Id"] = exc.ref
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


# ============================================================================
# Gate, kill switch, CSRF, identity
# ============================================================================


@dataclass(frozen=True)
class AgentConfig:
    """The configuration every agent route needs, present only when enabled."""

    service_url: str
    user_id_key: bytes


def require_agent_enabled() -> AgentConfig:
    """The kill switch: 404 unless the feature is on AND fully configured."""
    service_url = settings.agent_service_url
    key = settings.agent_user_id_key
    if not settings.agent_enabled or not service_url or not key:
        raise AgentHTTPError(404, NOT_ENABLED)
    return AgentConfig(service_url=service_url.rstrip("/"), user_id_key=key.encode())


def _origin_allowed(origin: str) -> bool:
    return origin in settings.cors_origins or _LOCAL_ORIGIN.fullmatch(origin) is not None


def _is_json(content_type: str | None) -> bool:
    return (content_type or "").split(";", 1)[0].strip().lower() == "application/json"


def _has_body(request: Request) -> bool:
    return request.headers.get("content-length", "0") != "0" or "transfer-encoding" in request.headers


def require_same_site_client(request: Request) -> None:
    """CSRF guard for every state-changing method.

    The admin gate accepts a Cloudflare Access cookie, which a browser attaches
    to cross-site requests too. So a POST, PUT or DELETE also needs the
    `X-Anyplot-Client` header, an allowed `Origin` when the browser sends one,
    and a JSON content type when it carries a body (the body-less cancel and
    delete calls need none). Each of those defeats a different forged "simple"
    request.
    """
    if request.method in _SAFE_METHODS:
        return
    if request.headers.get("x-anyplot-client") != CLIENT_HEADER_VALUE:
        raise AgentHTTPError(403, "client_header_required")
    origin = request.headers.get("origin")
    if origin is not None and not _origin_allowed(origin):
        raise AgentHTTPError(403, "origin_not_allowed")
    if _has_body(request) and not _is_json(request.headers.get("content-type")):
        raise AgentHTTPError(403, "json_required")


async def require_utf8_body(request: Request) -> None:
    """Refuse a JSON body that carries a lone surrogate (`"\\ud800"`) with a clean 422.

    JSON allows the escape, UTF-8 cannot carry it, and Pydantic refuses it —
    but FastAPI's default 422 body echoes the input, and rendering a lone
    surrogate there fails with a 500. A router dependency runs before that
    body is built: FastAPI has already parsed the JSON, and raises the
    validation errors only after every dependency has run.
    """
    if request.method in _SAFE_METHODS or not _has_body(request):
        return
    try:
        payload = json.loads(await request.body())
    except ValueError:
        return  # malformed JSON was already answered by FastAPI, or the route takes no body
    try:
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError:
        raise AgentHTTPError(422, "invalid_text") from None


def derive_user_id(key: bytes, identity: AdminIdentity) -> str:
    """The opaque, stable user id the agents service sees instead of an email.

    Keyed, so nobody without `AGENT_USER_ID_KEY` can map an id back to an
    address. Every token-path caller shares one id, because the token proves
    possession of a secret, not a person.
    """
    digest = hmac.new(key, (identity.email or "token").encode(), hashlib.sha256).hexdigest()
    return "adm_" + digest[:16]


@dataclass(frozen=True)
class AgentContext:
    """Per-request upstream context: where to call, as whom, under which id."""

    base_url: str
    user_id: str
    request_id: str


def agent_context(
    response: Response,
    identity: AdminIdentity = Depends(require_admin_identity),
    config: AgentConfig = Depends(require_agent_enabled),
) -> AgentContext:
    """Mint the request id (returned as `X-Request-Id`) and derive the user id."""
    request_id = str(uuid.uuid4())
    response.headers["X-Request-Id"] = request_id
    response.headers["Cache-Control"] = _NO_STORE
    return AgentContext(
        base_url=config.service_url, user_id=derive_user_id(config.user_id_key, identity), request_id=request_id
    )


async def get_agent_client() -> AsyncIterator[httpx.AsyncClient]:
    """The HTTP client for upstream calls; tests override it with a mock transport."""
    timeout = httpx.Timeout(settings.agent_request_timeout_s, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


router = APIRouter(
    prefix="/debug/agent",
    tags=["agent"],
    # Order matters: the admin gate answers first (so the deploy smoke reads a
    # 401 whatever the switch says), then the kill switch, then the CSRF guard,
    # then the body check.
    dependencies=[
        Depends(require_admin),
        Depends(require_agent_enabled),
        Depends(require_same_site_client),
        Depends(require_utf8_body),
    ],
)

Ctx = Annotated[AgentContext, Depends(agent_context)]
Client = Annotated[httpx.AsyncClient, Depends(get_agent_client)]
SessionId = Annotated[str, Path(pattern=SESSION_ID_PATTERN)]


# ============================================================================
# Request bodies (only these fields are ever forwarded)
# ============================================================================


def _check_library(value: str) -> str:
    if value not in SUPPORTED_LIBRARIES:
        raise ValueError("unknown library")
    return value


SpecId = Annotated[str, Field(pattern=SPEC_ID_PATTERN)]
LibraryId = Annotated[str, AfterValidator(_check_library)]
Locale = Annotated[str, Field(max_length=16, pattern=r"^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$")]
Text = Annotated[str, Field(min_length=1)]


class _StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSessionBody(_StrictBody):
    spec_id: SpecId
    library: LibraryId
    locale: Locale


class SwitchLibraryBody(_StrictBody):
    # The spec id travels with the library because the BFF keeps no session
    # state; the agents service checks it against the session's spec.
    spec_id: SpecId
    library: LibraryId


class DatasetBody(_StrictBody):
    text: Text


class Binding(_StrictBody):
    role: Annotated[str, Field(pattern=r"^[a-z_]{1,32}$")]
    column: Annotated[str, Field(min_length=1, max_length=64)] | None = None


class MessageBody(_StrictBody):
    text: Text | None = None
    action: Literal["create_plot"] | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> MessageBody:
        if (self.text is None) == (self.action is None):
            raise ValueError("send exactly one of text or action")
        return self


# ============================================================================
# Catalogue snapshot
# ============================================================================


class CatalogueSnapshot(BaseModel):
    """What the agents service knows about the catalogue pair; it has no DB access."""

    spec_id: str
    title: str
    description: str
    data_roles: list[str]
    notes: list[str]
    code: str
    library_version: str | None


async def load_catalogue_snapshot(db: AsyncSession, spec_id: str, library: str) -> CatalogueSnapshot | None:
    """Build the snapshot for one spec and library, or None when either is missing.

    Interim home: this moves into `core/catalogue/queries.py` once that module
    exists, so the MCP server and the BFF share one query.
    """
    spec = await SpecRepository(db).get_by_id_with_code(spec_id)
    if spec is None:
        return None
    impl = next((impl for impl in spec.impls if impl.library_id == library), None)
    code = strip_noqa_comments(impl.code) if impl is not None else None
    if impl is None or not code:
        return None
    return CatalogueSnapshot(
        spec_id=spec.id,
        title=spec.title,
        description=spec.description or "",
        data_roles=list(spec.data or []),
        notes=list(spec.notes or []),
        code=code,
        library_version=impl.library_version,
    )


async def _snapshot_or_404(db: AsyncSession, spec_id: str, library: str, ctx: AgentContext) -> CatalogueSnapshot:
    snapshot = await load_catalogue_snapshot(db, spec_id, library)
    if snapshot is None:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    return snapshot


# ============================================================================
# Upstream calls
# ============================================================================


def _is_local(url: str) -> bool:
    return urlsplit(url).hostname in _LOCAL_HOSTS


def _fetch_id_token(audience: str) -> str:
    """Blocking: an ID token for Cloud Run IAM (metadata server on Cloud Run, ADC locally)."""
    token: str = google_id_token.fetch_id_token(GoogleAuthRequest(), audience)
    return token


async def _upstream_headers(ctx: AgentContext) -> dict[str, str]:
    headers = {"X-Anyplot-User": ctx.user_id, "X-Request-Id": ctx.request_id}
    if not _is_local(ctx.base_url):
        token = await run_in_threadpool(_fetch_id_token, ctx.base_url)
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _log_unreachable(ctx: AgentContext, method: str, path: str, exc: BaseException) -> None:
    # The exception class only: the message of a transport or auth error can
    # carry URLs and token fragments, and request content never belongs in logs.
    logger.warning("agent upstream %s %s unreachable (ref %s): %s", method, path, ctx.request_id, type(exc).__name__)


def _upstream_error(response: httpx.Response, ref: str) -> AgentHTTPError:
    """Map an upstream error to the same status with a generic code; never echo its body."""
    status = response.status_code
    if status < 400 or status > 599:
        return AgentHTTPError(502, "upstream", ref)
    if status == 401:
        # Only Cloud Run IAM answers 401 here: it refused the BFF's own ID
        # token. Passed through, it would read in the browser as the admin's
        # session failing.
        return AgentHTTPError(502, "upstream_auth", ref)
    code: str | None = None
    try:
        body = response.json()
    except ValueError:
        body = None
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, str) and detail in _UPSTREAM_CODES:
        code = detail
    if code is None and status == 403:
        # A 403 without a documented code (`data_refused` is one) is IAM too.
        return AgentHTTPError(502, "upstream_auth", ref)
    if code is None:
        code = "upstream" if status >= 500 else _GENERIC_CODES.get(status, "rejected")
    return AgentHTTPError(status, code, ref)


async def _call_upstream(
    client: httpx.AsyncClient,
    ctx: AgentContext,
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: dict[str, str | int] | None = None,
) -> Any:
    """Call `/v1{path}` and return its JSON (None for an empty 2xx body)."""
    try:
        headers = await _upstream_headers(ctx)
        response = await client.request(
            method, f"{ctx.base_url}/v1{path}", json=json_body, params=params, headers=headers
        )
    except _UNREACHABLE as exc:
        _log_unreachable(ctx, method, path, exc)
        raise AgentHTTPError(502, "upstream", ctx.request_id) from exc
    if not response.is_success:
        raise _upstream_error(response, ctx.request_id)
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise AgentHTTPError(502, "upstream", ctx.request_id) from exc


async def _open_stream(
    client: httpx.AsyncClient,
    ctx: AgentContext,
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: dict[str, str | int] | None = None,
    accept: str | None = None,
) -> httpx.Response:
    """Open a streamed upstream response; the caller closes it. Raises on a non-2xx status."""
    headers = await _upstream_headers(ctx)
    if accept:
        headers["Accept"] = accept
    request = client.build_request(method, f"{ctx.base_url}/v1{path}", json=json_body, params=params, headers=headers)
    response = await client.send(request, stream=True)
    if not response.is_success:
        try:
            await response.aread()
        finally:
            await response.aclose()
        raise _upstream_error(response, ctx.request_id)
    return response


def _no_content(ctx: AgentContext) -> Response:
    # A returned Response skips the headers `agent_context` set, so repeat them.
    return Response(status_code=204, headers={"X-Request-Id": ctx.request_id, "Cache-Control": _NO_STORE})


# ============================================================================
# SSE relay (anyplot/1)
# ============================================================================


async def _read_events(lines: AsyncIterator[str], deadline: float) -> AsyncGenerator[tuple[str | None, str], None]:
    """Assemble complete SSE events from upstream lines until the loop-time `deadline`.

    Comments (the upstream's own keep-alive pings) and the `id` and `retry`
    fields are dropped; the browser gets FastAPI's pings from this route.
    Raises TimeoutError when the deadline passes.
    """
    event_type: str | None = None
    data: list[str] = []
    size = 0
    while True:
        # The timeout wraps the read only, never a yield (PEP 789).
        async with asyncio.timeout_at(deadline):
            try:
                line = await anext(lines)
            except StopAsyncIteration:
                return
        if not line:
            if (event_type is not None or data) and size <= _MAX_EVENT_CHARS:
                yield event_type, "\n".join(data)
            event_type, data, size = None, [], 0
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")
        if field == "event":
            event_type = value
        elif field == "data":
            size += len(value) + 1
            if size <= _MAX_EVENT_CHARS:
                data.append(value)


def _translate(event_type: str | None, data: str, ref: str) -> ServerSentEvent | None:
    """Re-validate one upstream event; None drops it."""
    fields = _EVENT_FIELDS.get(event_type or "")
    if fields is None:
        return None
    try:
        payload = json.loads(data)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    if event_type == "error":
        code = payload.get("code")
        return ServerSentEvent(
            event="error",
            data={"code": code if isinstance(code, str) and code in _ERROR_CODES else "internal", "ref": ref},
        )
    return ServerSentEvent(event=event_type, data={key: value for key, value in payload.items() if key in fields})


def _upstream_failed(ref: str) -> list[ServerSentEvent]:
    return [
        ServerSentEvent(event="error", data={"code": "upstream", "ref": ref}),
        ServerSentEvent(event="done", data={}),
    ]


@dataclass(frozen=True)
class UpstreamStream:
    """The opened upstream chat stream; `response` is None when it could not be reached."""

    request_id: str
    response: httpx.Response | None
    deadline: float
    """Loop time by which the whole turn, opening included, has to be over."""


async def open_message_stream(
    sid: SessionId, body: MessageBody, ctx: Ctx, client: Client
) -> AsyncIterator[UpstreamStream]:
    """Open the upstream stream BEFORE the SSE response starts.

    A dependency rather than the generator itself, so a 413 here or an upstream
    409 `run_active` still reaches the browser as an HTTP status: once the
    generator runs, the 200 is already on the wire.
    """
    if body.text is not None and len(body.text) > MAX_MESSAGE_CHARS:
        raise AgentHTTPError(413, "too_long", ctx.request_id)
    payload = {"text": body.text} if body.text is not None else {"action": body.action}
    path = f"/sessions/{sid}/messages"
    # One wall-clock budget for the whole turn: the ID token, the connection
    # and the upstream's response headers spend from it too.
    deadline = asyncio.get_running_loop().time() + settings.agent_request_timeout_s
    response: httpx.Response | None
    try:
        async with asyncio.timeout_at(deadline):
            response = await _open_stream(client, ctx, "POST", path, json_body=payload, accept="text/event-stream")
    except (*_UNREACHABLE, TimeoutError) as exc:
        _log_unreachable(ctx, "POST", path, exc)
        response = None
    try:
        yield UpstreamStream(request_id=ctx.request_id, response=response, deadline=deadline)
    finally:
        if response is not None:
            await response.aclose()


# ============================================================================
# Routes
# ============================================================================


@router.get("/status")
async def agent_status(ctx: Ctx, client: Client) -> dict[str, Any]:
    """The agents service's status (`libraries`, `model`, `location`, `version`) plus `enabled`."""
    upstream = await _call_upstream(client, ctx, "GET", "/status")
    return {**(upstream if isinstance(upstream, dict) else {}), "enabled": True}


@router.get("/eligibility")
async def agent_eligibility(
    ctx: Ctx,
    client: Client,
    spec: Annotated[str, Query(pattern=SPEC_ID_PATTERN)],
    library: Annotated[str, AfterValidator(_check_library), Query()],
) -> Any:
    """Whether the "Use with my data" button may show for this pair; the agents service decides."""
    return await _call_upstream(client, ctx, "GET", "/eligibility", params={"spec": spec, "library": library})


@router.post("/sessions")
async def create_session(
    body: CreateSessionBody, ctx: Ctx, client: Client, db: AsyncSession = Depends(require_db)
) -> Any:
    """Open a chat session for one spec and library: `{session_id, eligibility}`."""
    snapshot = await _snapshot_or_404(db, body.spec_id, body.library, ctx)
    payload = {
        "user": ctx.user_id,
        "spec_id": body.spec_id,
        "library": body.library,
        "locale": body.locale,
        "snapshot": snapshot.model_dump(),
    }
    return await _call_upstream(client, ctx, "POST", "/sessions", json_body=payload)


@router.post("/sessions/{sid}/library")
async def switch_library(
    sid: SessionId, body: SwitchLibraryBody, ctx: Ctx, client: Client, db: AsyncSession = Depends(require_db)
) -> Any:
    """Switch the session to another library with a fresh snapshot; dataset and bindings stay."""
    snapshot = await _snapshot_or_404(db, body.spec_id, body.library, ctx)
    payload = {"library": body.library, "snapshot": snapshot.model_dump()}
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/library", json_body=payload)


@router.post("/sessions/{sid}/dataset")
async def upload_dataset(sid: SessionId, body: DatasetBody, ctx: Ctx, client: Client) -> Any:
    """Parse pasted data: `{preview, profile, bindings, warnings}`. 413 above 200 KB of UTF-8."""
    if len(body.text.encode("utf-8")) > MAX_DATASET_BYTES:
        raise AgentHTTPError(413, "too_long", ctx.request_id)
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/dataset", json_body={"text": body.text})


@router.put("/sessions/{sid}/bindings")
async def put_bindings(
    sid: SessionId, bindings: Annotated[list[Binding], Body(max_length=50)], ctx: Ctx, client: Client
) -> Any:
    """Replace the role-to-column bindings."""
    payload = [binding.model_dump() for binding in bindings]
    return await _call_upstream(client, ctx, "PUT", f"/sessions/{sid}/bindings", json_body=payload)


@router.post("/sessions/{sid}/messages", response_class=EventSourceResponse)
async def post_message(upstream: UpstreamStream = Depends(open_message_stream)) -> AsyncIterator[ServerSentEvent]:
    """Relay one chat turn as SSE `anyplot/1`; always ends with a `done` event."""
    finished = False
    if upstream.response is not None:
        lines = upstream.response.aiter_lines()
        try:
            async with aclosing(_read_events(lines, upstream.deadline)) as events:
                async for event_type, data in events:
                    relayed = _translate(event_type, data, upstream.request_id)
                    if relayed is None:
                        continue
                    yield relayed
                    if relayed.event == "done":
                        finished = True
                        break
        except (httpx.HTTPError, TimeoutError) as exc:
            logger.warning("agent upstream stream failed (ref %s): %s", upstream.request_id, type(exc).__name__)
    if not finished:
        # Unreachable, cut off, out of time, or ended without `done`: the
        # browser always learns that the turn is over.
        for failure in _upstream_failed(upstream.request_id):
            yield failure


@router.post("/sessions/{sid}/cancel", status_code=204)
async def cancel_run(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Stop the session's active run."""
    await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/cancel")
    return _no_content(ctx)


@router.get("/sessions/{sid}/artifacts/{name}")
async def get_artifact(
    sid: SessionId, name: str, ctx: Ctx, client: Client, v: Annotated[int | None, Query(ge=0, le=999)] = None
) -> Response:
    """Stream one result file; only the four allowlisted names exist."""
    media_type = ARTIFACT_MEDIA_TYPES.get(name)
    if media_type is None:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    path = f"/sessions/{sid}/artifacts/{name}"
    try:
        response = await _open_stream(client, ctx, "GET", path, params={"v": v} if v is not None else None)
    except _UNREACHABLE as exc:
        _log_unreachable(ctx, "GET", path, exc)
        raise AgentHTTPError(502, "upstream", ctx.request_id) from exc
    return StreamingResponse(
        response.aiter_bytes(),
        media_type=media_type,
        headers={"Cache-Control": _NO_STORE, "X-Content-Type-Options": "nosniff", "X-Request-Id": ctx.request_id},
        background=BackgroundTask(response.aclose),
    )


@router.delete("/sessions/{sid}", status_code=204)
async def delete_session(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Purge the session, its dataset and its renders."""
    await _call_upstream(client, ctx, "DELETE", f"/sessions/{sid}")
    return _no_content(ctx)
