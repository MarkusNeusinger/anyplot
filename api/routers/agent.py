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
import gzip
import hashlib
import hmac
import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import aclosing
from dataclasses import dataclass
from datetime import UTC, datetime
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

from api.agent_cases import (
    CASE_ID_PATTERN,
    CASE_MEDIA_TYPES,
    BundleError,
    CaseBucket,
    GcsCaseBucket,
    NoChatData,
    Submission,
    build_case,
    code_diff,
    manifest_detail,
    new_case_id,
    read_manifest,
    write_case,
)
from api.dependencies import require_db
from api.routers.debug import AdminIdentity, require_admin, require_admin_identity
from core.agent_cases import (
    CASE_FILE_NAMES,
    EXPECTED_BY_REACTION,
    MAX_TAGS,
    TAG_PATTERN,
    case_object,
    row_from_manifest,
)
from core.config import settings
from core.constants import SUPPORTED_LIBRARIES
from core.database import FEEDBACK_REACTIONS, AgentFeedback, AgentFeedbackRepository, ImplRepository, SpecRepository
from core.utils import strip_noqa_comments


logger = logging.getLogger(__name__)

NOT_ENABLED = "agent chat is not enabled"
CLIENT_HEADER_VALUE = "agent-chat/1"
"""Required `X-Anyplot-Client` value on every method but GET, HEAD and OPTIONS (so
PATCH too). A custom header forces a CORS preflight, which a foreign origin cannot pass."""

MAX_DATASET_BYTES = 1024 * 1024
"""Pasted data, "1 MB" of UTF-8 (200 KB before 2026-10-14): the agents parser's `MAX_INPUT_BYTES`, copied
because the API image does not ship the agents package."""
MAX_MESSAGE_CHARS = 2000
MAX_FEEDBACK_CHARS = 500
"""The cap of a feedback message after the strip, the site feedback's own (`api/routers/feedback.py`)."""
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

MAX_BUNDLE_BYTES = 32 * 1024 * 1024
"""The cap of a session bundle the BFF relays: Cloud Run's 32 MiB limit on an HTTP/1 response that is
not streamed. The agents service answers its bundle (every version's PNGs as base64) as one
`JSONResponse`, so on Cloud Run a larger bundle never reaches the BFF: Cloud Run refuses it on the
agents service's side with a 500, which the BFF maps to `500 upstream` like any other. This cap is
the BFF's own bound on what it buffers, and answers `502 too_large` where nothing sits in front of
the agents service (a local run) or should that service ever stream the bundle."""
_BUNDLE_SID_CHARS = 8
"""The session id characters in a bundle's file name, `anyplot-session-<first 8>.json`."""
_BUNDLE_GZIP_LEVEL = 6
"""zlib's default level: base64 of PNGs shrinks by about a quarter at level 6 and no further at
the API's middleware level 9, which costs about a fifth more time."""

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
    # `attempt` on a pipeline step, plus `outcome` and `findings` (how the round before ended) on
    # `repairing`; `position` and `waiting` on `step: "queued"`.
    "status": frozenset({"step", "attempt", "outcome", "findings", "position", "waiting"}),
    "message": frozenset({"text"}),
    # `version` is the agents service's number of the stored version (ok and needs_attention only);
    # `rounds` lists how each attempt ended (`{attempt, outcome, findings}`), for the page's progress grid.
    "plot": frozenset(
        {"status", "reason", "attempts", "artifacts", "changes", "residual_defects", "version", "rounds"}
    ),
    "refusal": frozenset({"code", "text"}),
    "error": frozenset({"code", "ref"}),
    # `bindings` and `data_confirmed` sync the page after a turn in which the root changed the bindings;
    # `dataset` carries the new data version after a turn in which the root's `prepare_data` or
    # `generate_data` changed the data (version 1 when `generate_data` made the session's first data);
    # `language` carries the session language `{language, source}` after every run, so the page syncs its chip.
    "done": frozenset({"llm_calls", "tokens", "bindings", "data_confirmed", "dataset", "language"}),
}
_ERROR_CODES = frozenset({"capacity", "deadline", "guard_unavailable", "upstream", "internal"})
_MAX_BINDING_ERRORS = 20
_MAX_BINDING_ERROR_CHARS = 300
_MAX_EVENT_CHARS = 64 * 1024
_MAX_DONE_EVENT_CHARS = 512 * 1024
"""The cap of a `done` event: after a turn in which the assistant changed the data it carries
`dataset` (20 preview rows, the profile of up to 50 columns, the bindings, the change lines
and up to 50 spec roles), which at every schema maximum is about 393,000 characters. The agents service proves
that its largest `done` fits (`agents/stream.py`, `MAX_DONE_EVENT_CHARS`, the same number;
copied, because the API image does not ship the agents package)."""
_QUEUED_STEP = "queued"
"""The status step of a run that waits in the agents service's run queue."""
_QUEUED_HEARTBEAT_S = 15.0
"""The agents run queue's `HEARTBEAT_S`: a waiting run's status repeats at least this
often, so its run may have started up to this long before the BFF sees its first event."""

# Error codes the agents service documents for its /v1 routes; an upstream error
# body is never forwarded, only one of these codes when it names one.
_UPSTREAM_CODES = frozenset(
    {
        "not_eligible",
        "run_active",
        "too_long",
        "unparseable",
        "formula",
        "code",
        "data_refused",
        "session_expired",
        "guard_unavailable",
        "capacity",
        "no_dataset",
        "nothing_to_undo",
        "no_suggestion",
        "rate_limited",
        "daily_limit",
        "locked_out",
        "session_closed",
    }
)
# A spec data role, as the agents contract defines it (`agents/anyplot/schemas.py`,
# `ROLE_PATTERN`; copied, because the API image does not ship the agents package).
# Specs name roles such as `temperature_K`, `X1` or `lead_aVR`.
ROLE_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]{0,31}$"
# A session language, a short name or code such as `de`, `Deutsch` or `Klingon`, as the
# agents service defines it (`agents/anyplot/language.py`, `LANGUAGE_PATTERN`; copied,
# because the API image does not ship the agents package).
LANGUAGE_PATTERN = r"^[A-Za-z][A-Za-z -]{0,39}$"
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
    page needs a stable code and the request id to quote. `errors` carries the
    binding check lines of a `422 invalid`; `case_id` the stored case of a
    `502 row_missing`, so the page can chain its next edit to it.
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        ref: str | None = None,
        errors: list[str] | None = None,
        *,
        case_id: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.ref = ref
        self.errors = errors
        self.case_id = case_id


async def agent_http_error_handler(request: Request, exc: AgentHTTPError) -> JSONResponse:
    """Render an `AgentHTTPError`; registered on the app in api/main.py."""
    content: dict[str, Any] = {"detail": exc.detail}
    headers = {"Cache-Control": _NO_STORE}
    if exc.ref:
        content["ref"] = exc.ref
        headers["X-Request-Id"] = exc.ref
    if exc.errors:
        content["errors"] = exc.errors
    if exc.case_id:
        content["case_id"] = exc.case_id
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
    to cross-site requests too. So a POST, PUT, PATCH or DELETE also needs the
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


def get_case_bucket() -> CaseBucket:
    """The private bucket the feedback cases go to; tests override it with a fake."""
    return GcsCaseBucket(settings.agent_cases_bucket)


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
Cases = Annotated[CaseBucket, Depends(get_case_bucket)]
Db = Annotated[AsyncSession, Depends(require_db)]
SessionId = Annotated[str, Path(pattern=SESSION_ID_PATTERN)]
CaseId = Annotated[str, Path(pattern=CASE_ID_PATTERN)]
CaseFileName = Annotated[str, Path(pattern="^(" + "|".join(re.escape(name) for name in CASE_FILE_NAMES) + ")$")]


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


class LanguageBody(_StrictBody):
    # The chat header's language chip. The pattern runs on the value as sent, which is
    # forwarded untrimmed: a leading space is a 422 here as at the agents service, which
    # stores the normalised form and answers it.
    language: Annotated[str, Field(min_length=1, max_length=40, pattern=LANGUAGE_PATTERN)]


class DatasetBody(_StrictBody):
    text: Text
    # `.use()` on a transcription: the table the user confirmed; the agents service then never
    # hands the text to its transcriber again (a one-column table would loop otherwise).
    confirmed: bool = False


class Binding(_StrictBody):
    role: Annotated[str, Field(pattern=ROLE_PATTERN)]
    column: Annotated[str, Field(min_length=1, max_length=64)] | None = None


class MessageBody(_StrictBody):
    text: Text | None = None
    # `create_plot` starts step 2; `summarize_data` asks the assistant for the step-1 summary of the data.
    action: Literal["create_plot", "summarize_data"] | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> MessageBody:
        if (self.text is None) == (self.action is None):
            raise ValueError("send exactly one of text or action")
        return self


class RenderThemeBody(_StrictBody):
    theme: Literal["light", "dark"]


def _check_reaction(value: str) -> str:
    if value not in FEEDBACK_REACTIONS:
        raise ValueError(f"reaction must be one of {', '.join(FEEDBACK_REACTIONS)}")
    return value


def _feedback_message(value: str | None) -> str | None:
    """The message stripped, None when nothing is left; over `MAX_FEEDBACK_CHARS` after the strip is refused."""
    if value is None:
        return None
    text = value.strip()
    if len(text) > MAX_FEEDBACK_CHARS:
        raise ValueError(f"message must be {MAX_FEEDBACK_CHARS} characters or fewer")
    return text or None


class FeedbackBody(_StrictBody):
    # The site feedback's reaction set (`core.database.FEEDBACK_REACTIONS`).
    reaction: Annotated[str, AfterValidator(_check_reaction)]
    message: Annotated[str | None, AfterValidator(_feedback_message)] = None
    # Strict: a JSON boolean and a JSON integer only. A lax `"yes"` or `true` would
    # store a case the client never meant (`true` is version 1).
    include_data: Annotated[bool, Field(strict=True)]
    # The result version the feedback is about; 0 is the chat itself, for a session that made no plot.
    result_version: Annotated[int, Field(ge=0, le=999, strict=True)]
    # The case id of the earlier submission for this version, when this one is an edit of it.
    replaces: Annotated[str | None, Field(pattern=CASE_ID_PATTERN)] = None


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


def _binding_errors(body: Any) -> list[str] | None:
    """The agents service's binding check lines of a `422 invalid`, at most 20 strings of 300 characters.

    The one part of an upstream error body the BFF passes on: lines `check_bindings`
    builds from spec role names and the admin's own column names, such as
    "role 'y' takes numbered members such as 'y1'". Anything else is dropped.
    """
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(errors, list):
        return None
    lines = [" ".join(item.split())[:_MAX_BINDING_ERROR_CHARS] for item in errors if isinstance(item, str)]
    return [line for line in lines if line][:_MAX_BINDING_ERRORS] or None


def _upstream_error(response: httpx.Response, ref: str, *, binding_errors: bool = False) -> AgentHTTPError:
    """Map an upstream error to the same status with a generic code; never echo its body.

    With `binding_errors`, a `422 invalid` keeps the agents service's binding check
    lines (`_binding_errors`), so the chat page can say which binding was refused.
    """
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
    if binding_errors and status == 422 and code == "invalid":
        return AgentHTTPError(status, code, ref, errors=_binding_errors(body))
    return AgentHTTPError(status, code, ref)


async def _call_upstream(
    client: httpx.AsyncClient,
    ctx: AgentContext,
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: dict[str, str | int] | None = None,
    binding_errors: bool = False,
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
        raise _upstream_error(response, ctx.request_id, binding_errors=binding_errors)
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


async def _read_capped(response: httpx.Response, max_bytes: int) -> bytes | None:
    """The whole body of an opened upstream response, or None once it passes `max_bytes`.

    A declared `Content-Length` over the cap is refused before a byte is read; the count
    is kept while reading too, because a chunked body declares none.
    """
    declared = response.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        return None
    body = bytearray()
    async for chunk in response.aiter_bytes():
        body += chunk
        if len(body) > max_bytes:
            return None
    return bytes(body)


async def _fetch_bundle(
    client: httpx.AsyncClient, ctx: AgentContext, sid: str, *, version: int | None, include_data: bool
) -> bytes:
    """The agents service's bundle of the session (`GET /v1/sessions/{sid}/bundle`), read whole.

    `version` above 0 asks for that version only. Shared by `.save()` and the feedback
    route: an upstream error keeps its status and code (`404 session_expired` for
    another user's session, `404 not_found` for a version the session lacks),
    `502 upstream` when the service cannot be reached, and `502 too_large` above
    `MAX_BUNDLE_BYTES`.
    """
    path = f"/sessions/{sid}/bundle"
    params: dict[str, str | int] = {"include_data": "true" if include_data else "false"}
    if version is not None:
        params["version"] = version
    try:
        response = await _open_stream(client, ctx, "GET", path, params=params)
        try:
            body = await _read_capped(response, MAX_BUNDLE_BYTES)
        finally:
            await response.aclose()
    except _UNREACHABLE as exc:
        _log_unreachable(ctx, "GET", path, exc)
        raise AgentHTTPError(502, "upstream", ctx.request_id) from exc
    if body is None:
        logger.warning("agent bundle over %d bytes refused (ref %s)", MAX_BUNDLE_BYTES, ctx.request_id)
        raise AgentHTTPError(502, "too_large", ctx.request_id)
    return body


def _prepare_bundle(content: bytes, compress: bool) -> bytes | None:
    """The bundle as the browser gets it, gzip-compressed with `compress`; None unless it is a JSON object.

    Runs in a worker thread: checking and compressing tens of megabytes of base64 would hold the
    event loop for over a second, and the API's `GZipMiddleware` compresses a buffered response in
    one call on the loop. That middleware leaves a response that already has a `Content-Encoding`
    as it is. A nesting deeper than the parser's recursion limit counts as no JSON.
    """
    try:
        if not isinstance(json.loads(content), dict):
            return None
    except (ValueError, RecursionError):
        return None
    return gzip.compress(content, compresslevel=_BUNDLE_GZIP_LEVEL, mtime=0) if compress else content


def _bundle_filename(sid: str) -> str:
    """`anyplot-session-<the session id's first 8 characters>.json`, those reduced to `[A-Za-z0-9_-]`."""
    short = re.sub(r"[^A-Za-z0-9_-]", "", sid[:_BUNDLE_SID_CHARS]) or "session"
    return f"anyplot-session-{short}.json"


def _no_content(ctx: AgentContext) -> Response:
    # A returned Response skips the headers `agent_context` set, so repeat them.
    return Response(status_code=204, headers={"X-Request-Id": ctx.request_id, "Cache-Control": _NO_STORE})


# ============================================================================
# SSE relay (anyplot/1)
# ============================================================================


@dataclass
class TurnDeadline:
    """Loop times that bound one chat turn.

    `at` is when the turn has to be over unless an event moves it: `AGENT_REQUEST_TIMEOUT_S`
    after it opened, restarted while the run waits in the upstream queue. `end` never
    moves: `AGENT_TURN_MAX_S` after the turn opened, below anyplot-api's own request
    timeout, so the stream always ends with `error` and `done` instead of being cut.
    """

    at: float
    end: float

    @classmethod
    def open(cls) -> TurnDeadline:
        now = asyncio.get_running_loop().time()
        end = now + settings.agent_turn_max_s
        return cls(at=min(now + settings.agent_request_timeout_s, end), end=end)

    def restart(self, *, queued: bool) -> bool:
        """A fresh `AGENT_REQUEST_TIMEOUT_S` from now, capped at `end`.

        A queued status adds `_QUEUED_HEARTBEAT_S`, because the run may start up to that
        long before its first event arrives, and the budget must not end before the
        agents service's own deadline. False when a queued run could no longer finish
        before `end`: the caller ends the turn before the run spends a token.
        """
        now = asyncio.get_running_loop().time()
        budget = settings.agent_request_timeout_s + (_QUEUED_HEARTBEAT_S if queued else 0.0)
        if queued and now + budget > self.end:
            return False
        self.at = min(now + budget, self.end)
        return True


async def _read_events(
    lines: AsyncIterator[str], deadline: TurnDeadline
) -> AsyncGenerator[tuple[str | None, str], None]:
    """Assemble complete SSE events from upstream lines until the loop-time `deadline.at`.

    Comments (the upstream's own keep-alive pings) and the `id` and `retry`
    fields are dropped; the browser gets FastAPI's pings from this route.
    Raises TimeoutError when the deadline passes. The deadline is read before
    every line, so the caller may move it between events. An event over its
    cap (`_MAX_EVENT_CHARS`, or `_MAX_DONE_EVENT_CHARS` for `done`) is dropped
    whole; the data lines are kept up to the larger cap, because the type may
    only be known once the event is complete.
    """
    event_type: str | None = None
    data: list[str] = []
    size = 0
    while True:
        # The timeout wraps the read only, never a yield (PEP 789).
        async with asyncio.timeout_at(deadline.at):
            try:
                line = await anext(lines)
            except StopAsyncIteration:
                return
        if not line:
            if (event_type is not None or data) and size <= _event_cap(event_type):
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
            if size <= _MAX_DONE_EVENT_CHARS:
                data.append(value)


def _event_cap(event_type: str | None) -> int:
    """The size cap of one upstream event in characters of its data lines."""
    return _MAX_DONE_EVENT_CHARS if event_type == "done" else _MAX_EVENT_CHARS


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


def _turn_failed(ref: str, code: str = "upstream") -> list[ServerSentEvent]:
    return [ServerSentEvent(event="error", data={"code": code, "ref": ref}), ServerSentEvent(event="done", data={})]


@dataclass(frozen=True)
class UpstreamStream:
    """The opened upstream chat stream; `response` is None when it could not be reached."""

    request_id: str
    response: httpx.Response | None
    deadline: TurnDeadline
    """Loop times by which the whole turn, opening included, has to be over; queueing restarts `at`."""


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
    deadline = TurnDeadline.open()
    response: httpx.Response | None
    try:
        async with asyncio.timeout_at(deadline.at):
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
    """The agents service's status plus `enabled`.

    Upstream fields: `libraries`, `model`, `location`, `version`, `provider`, and the
    run queue's `waiting` entries and `in_flight` runs.
    """
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
    """Parse pasted data: `{preview, profile, bindings, warnings, context_lines, roles, language}`, stored
    (`context_lines`: the notes pasted above or below the table that the assistant reads with the data;
    `language`: the session language as `{language, source}`, source `pasted` when the notes' or the column
    names' language set it before any typed message or choice); or, for free text the
    parser cannot read, the agents service's `{transcribed, text, preview, profile, warnings, note}`, a
    model's reading that the page shows for confirmation and nothing stored. 413 above 1 MB of UTF-8;
    `422 formula` for text that asks for a formula, which the assistant computes in the chat instead, and
    `422 code` for a program (Python, JavaScript, R) that generates data, which the assistant runs in the chat;
    `403 session_closed` in a closed session, `429 rate_limited` / `daily_limit` past the paste limits and
    `429 locked_out` past the day's attack strikes, passed through from the agents service."""
    if len(body.text.encode("utf-8")) > MAX_DATASET_BYTES:
        raise AgentHTTPError(413, "too_long", ctx.request_id)
    payload: dict[str, Any] = {"text": body.text}
    if body.confirmed:
        payload["confirmed"] = True
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/dataset", json_body=payload)


@router.put("/sessions/{sid}/bindings")
async def put_bindings(
    sid: SessionId, bindings: Annotated[list[Binding], Body(max_length=50)], ctx: Ctx, client: Client
) -> Any:
    """Replace the role-to-column bindings; a refused set answers `422 invalid` with the check's `errors` lines."""
    payload = [binding.model_dump() for binding in bindings]
    path = f"/sessions/{sid}/bindings"
    return await _call_upstream(client, ctx, "PUT", path, json_body=payload, binding_errors=True)


@router.put("/sessions/{sid}/language")
async def put_language(sid: SessionId, body: LanguageBody, ctx: Ctx, client: Client) -> Any:
    """Set the session language for the replies and the plot text (the chat header's chip).

    The agents service answers `{language, source}`: the stored form (`English` comes back
    as `en`, `Klingon` as typed) and the source `chosen`, which detection never overrides.
    `409 run_active` while a turn or a render is in flight, `422 invalid` for a value the
    agents service refuses.
    """
    return await _call_upstream(client, ctx, "PUT", f"/sessions/{sid}/language", json_body={"language": body.language})


@router.post("/sessions/{sid}/dataset/confirm")
async def confirm_dataset(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Step 1 of two: the user confirms that the stored dataset and its bindings fit.

    The agents service answers `{confirmed, rows, columns}` and runs the plot pipeline
    only on a confirmed dataset; `422 no_dataset` before a parse, `409 run_active` while
    a turn or a render is in flight.
    """
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/dataset/confirm")


@router.post("/sessions/{sid}/dataset/undo")
async def undo_dataset(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Undo the assistant's last change to the data: the version before it becomes the current dataset.

    The agents service answers `{preview, profile, bindings, warnings, context_lines, roles, version}` like
    the dataset route, unconfirmed; `422 nothing_to_undo` when the paste was never changed,
    `409 run_active` while a turn or a render is in flight.
    """
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/dataset/undo")


@router.post("/sessions/{sid}/dataset/to_long")
async def dataset_to_long(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """The page's `.to_long()`: make a wide table long for the spec's category and value roles.

    No body: the agents service recomputes its wide-table suggestion and applies that
    one `pivot_longer`, without a model call, as the next dataset version. It answers
    like the undo route plus `changes`; `422 no_suggestion` when the table is not wide
    for this spec, `409 run_active` while a turn or a render is in flight.
    """
    return await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/dataset/to_long")


@router.post("/sessions/{sid}/messages", response_class=EventSourceResponse)
async def post_message(upstream: UpstreamStream = Depends(open_message_stream)) -> AsyncIterator[ServerSentEvent]:
    """Relay one chat turn as SSE `anyplot/1`; always ends with a `done` event.

    Queued time does not count toward the turn's budget, as it does not count
    toward the agents service's own deadline: every `status{step:"queued"}`
    restarts the budget with the queue's heartbeat on top, and so does the first
    event after the wait, when the run has started. Nothing moves the turn past
    `AGENT_TURN_MAX_S`: a queued turn whose run could no longer finish before it
    ends with `error{code:"capacity"}` there, and closing the upstream stream takes
    it out of the queue before it spends a token.
    """
    finished = False
    queued = False
    if upstream.response is not None:
        lines = upstream.response.aiter_lines()
        try:
            async with aclosing(_read_events(lines, upstream.deadline)) as events:
                async for event_type, data in events:
                    relayed = _translate(event_type, data, upstream.request_id)
                    if relayed is None:
                        continue
                    is_queued = relayed.event == "status" and relayed.data.get("step") == _QUEUED_STEP
                    if is_queued and not upstream.deadline.restart(queued=True):
                        logger.info("agent turn left the queue at AGENT_TURN_MAX_S (ref %s)", upstream.request_id)
                        for failure in _turn_failed(upstream.request_id, "capacity"):
                            yield failure
                        finished = True
                        break
                    if queued and not is_queued:
                        upstream.deadline.restart(queued=False)
                    queued = is_queued
                    yield relayed
                    if relayed.event == "done":
                        finished = True
                        break
        except (httpx.HTTPError, TimeoutError) as exc:
            logger.warning("agent upstream stream failed (ref %s): %s", upstream.request_id, type(exc).__name__)
    if not finished:
        # Unreachable, cut off, out of time, or ended without `done`: the
        # browser always learns that the turn is over.
        for failure in _turn_failed(upstream.request_id):
            yield failure


@router.post("/sessions/{sid}/cancel", status_code=204)
async def cancel_run(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Stop the session's active run."""
    await _call_upstream(client, ctx, "POST", f"/sessions/{sid}/cancel")
    return _no_content(ctx)


@router.post("/sessions/{sid}/versions/{version}/render")
async def render_version_theme(
    sid: SessionId, version: Annotated[int, Path(ge=0, le=999)], body: RenderThemeBody, ctx: Ctx, client: Client
) -> Any:
    """The theme toggle: render the other theme of a finished version (0 is the latest), with no model call.

    Synchronous: `{status, reason?, artifacts}` once the render is done.
    """
    path = f"/sessions/{sid}/versions/{version}/render"
    return await _call_upstream(client, ctx, "POST", path, json_body={"theme": body.theme})


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


@router.get("/sessions/{sid}/bundle")
async def get_bundle(
    sid: SessionId,
    request: Request,
    ctx: Ctx,
    client: Client,
    version: Annotated[int | None, Query(ge=0, le=999)] = None,
    include_data: bool = False,
) -> Response:
    """The session's feedback case as a JSON file to save: the page's `.save()`.

    The agents service assembles it (`GET /v1/sessions/{sid}/bundle`): the transcript, every
    version's code, plan, result and PNGs as base64, the dataset profile, the bindings and a
    config stamp; each version's `data.csv` only with `include_data`, and only `version` when
    one above 0 is given. The BFF reads it whole up to `MAX_BUNDLE_BYTES` (`502 too_large`
    above), checks that it is a JSON object and compresses it in a worker thread
    (`_prepare_bundle`), and answers it as an attachment. Here `version=0` keeps its
    documented meaning, every version: the agents service reads 0 as the chat's feedback
    case, so the BFF leaves the parameter out instead of forwarding it.
    """
    upstream_version = version if version else None
    body = await _fetch_bundle(client, ctx, sid, version=upstream_version, include_data=include_data)
    # The middleware's own test for whether the client takes gzip.
    compress = "gzip" in request.headers.get("Accept-Encoding", "")
    content = await run_in_threadpool(_prepare_bundle, body, compress)
    if content is None:
        raise AgentHTTPError(502, "upstream", ctx.request_id)
    headers = {
        "Content-Disposition": f'attachment; filename="{_bundle_filename(sid)}"',
        "Cache-Control": _NO_STORE,
        "X-Content-Type-Options": "nosniff",
        "X-Request-Id": ctx.request_id,
    }
    if compress:
        # The middleware adds `Vary` to the responses it handles, and passes this one through.
        headers["Content-Encoding"] = "gzip"
        headers["Vary"] = "Accept-Encoding"
    return Response(content, media_type="application/json", headers=headers)


@router.post("/sessions/{sid}/feedback", status_code=201)
async def submit_feedback(
    sid: SessionId, body: FeedbackBody, ctx: Ctx, client: Client, cases: Cases, db: Db
) -> dict[str, Any]:
    """Quick feedback on one result version, or on the chat: store its case in the private bucket, `201 {case_id, stored}`.

    The agents service assembles the version's bundle (`version=result_version`, its
    `data.csv` only with `include_data`); `result_version` 0 is the feedback on a chat
    that made no plot, whose bundle is the conversation, the profile and bindings and,
    with `include_data`, the session's current data (`422 no_data` before any data was
    pasted or computed), but no image and no `plot.py`; `api/agent_cases.py` splits it into the case
    files and the manifest, which it uploads last, all in a worker thread. A later
    submission for the same version is a new case that names the earlier one in
    `replaces`, which supersedes that case's row for the same session hash and result
    version; the row is inserted after the last upload, and `502 row_missing` with the
    `case_id` says the files are stored but the row is not. An API without a configured
    database answers `503` before the bundle fetch, so it never stores a case it cannot
    index. Upstream errors map as for `.save()`, a bundle that is not the documented
    shape is `502 upstream`, and a failed upload is `502 storage`, which leaves no
    manifest: files without one are an aborted case, never a case.
    """
    content = await _fetch_bundle(client, ctx, sid, version=body.result_version, include_data=body.include_data)
    created_at = datetime.now(UTC)
    submission = Submission(
        reaction=body.reaction,
        message=body.message,
        include_data=body.include_data,
        result_version=body.result_version,
        replaces=body.replaces,
    )
    try:
        case = await run_in_threadpool(
            build_case,
            content,
            submission,
            case_id=new_case_id(created_at),
            created_at=created_at,
            bucket=settings.agent_cases_bucket,
            user_hash=ctx.user_id,
            session_id=sid,
        )
    except NoChatData as exc:
        raise AgentHTTPError(422, "no_data", ctx.request_id) from exc
    except BundleError as exc:
        # The reason names a field of the bundle, never its content.
        logger.warning("agent feedback bundle refused (ref %s): %s", ctx.request_id, exc)
        raise AgentHTTPError(502, "upstream", ctx.request_id) from exc
    try:
        await run_in_threadpool(write_case, cases, case)
    except Exception as exc:  # any client, auth or transport error of the storage library
        logger.warning(
            "agent feedback case %s not stored (ref %s): %s", case.case_id, ctx.request_id, type(exc).__name__
        )
        raise AgentHTTPError(502, "storage", ctx.request_id) from exc
    try:
        await AgentFeedbackRepository(db).create_case(row_from_manifest(case.manifest))
    except Exception as exc:  # the driver, the pool or a constraint: the case is in the bucket already
        logger.warning(
            "agent feedback case %s stored but not indexed (ref %s): %s",
            case.case_id,
            ctx.request_id,
            type(exc).__name__,
        )
        raise AgentHTTPError(502, "row_missing", ctx.request_id, case_id=case.case_id) from exc
    logger.info("agent feedback case %s stored with %d files (ref %s)", case.case_id, len(case.files), ctx.request_id)
    return {"case_id": case.case_id, "stored": case.stored}


@router.delete("/sessions/{sid}", status_code=204)
async def delete_session(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Purge the session, its dataset and its renders."""
    await _call_upstream(client, ctx, "DELETE", f"/sessions/{sid}")
    return _no_content(ctx)


# ============================================================================
# Feedback triage: the "Agent cases" section of /debug
# ============================================================================
#
# The `agent_feedback` row is the source of truth for status, tags, the expected outcome and
# the promotion; the bucket holds the files until its lifecycle rule deletes them. These
# routes never call the agents service.

# `core.database.FEEDBACK_STATUSES`, `FEEDBACK_REACTIONS` and `AGENT_CASE_EXPECTED` as types;
# a test keeps each pair equal.
CaseStatus = Literal["new", "in_progress", "done", "wont_solve"]
Reaction = Literal["thumbs_up", "thumbs_down", "bug", "idea"]
Expected = Literal["accepted", "rejected"]
StatusFilter = Literal["new", "in_progress", "done", "wont_solve", "open"]
"""A status, or `open` for the two unresolved ones (`new`, `in_progress`), as on /debug's feedback list."""
OPEN_STATUSES = ("new", "in_progress")
LIBRARY_FILTER_PATTERN = r"^[a-z0-9]{1,50}$"
Tag = Annotated[str, Field(pattern=TAG_PATTERN)]


class CaseItem(BaseModel):
    """One `agent_feedback` row as the triage list shows it; timestamps are UTC ISO 8601 with `Z`."""

    id: str
    created_at: str
    reaction: str
    message: str | None
    include_data: bool
    status: str
    tags: list[str]
    spec_id: str | None
    library_id: str | None
    locale: str | None
    result_version: int
    replaces: str | None
    superseded_by: str | None
    promoted_at: str | None
    expected: str | None
    model: str | None
    model_version: str | None
    judge_model: str | None
    prompt_hash: str | None
    pipeline_status: str | None
    attempts: int | None
    tokens: int | None
    cost_estimate: float | None
    files: list[str]
    user_hash: str
    session_hash: str
    case_uri: str
    manifest_schema: int
    updated_at: str


class CasePage(BaseModel):
    """One page of the list; `has_more` says a further page exists (pass the last item's id as `before`)."""

    items: list[CaseItem]
    has_more: bool


class TranscriptTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class CaseDetail(CaseItem):
    """The row plus what the case's `manifest.json` in the bucket adds.

    `expired` when the lifecycle rule has deleted the manifest: then every field read from it
    is null or empty, and the row and `siblings` remain. `diff` and `catalogue_library_version`
    come from the catalogue at triage time, which may differ from the one the session adapted
    (`snapshot_library_version`).
    """

    expired: bool
    transcript: list[TranscriptTurn] | None
    code: str | None
    diff: str | None
    catalogue_library_version: str | None
    snapshot_library_version: str | None
    residual_defects: list[str]
    changes: list[str]
    result_reason: str | None
    config: dict[str, Any] | None
    bindings: list[dict[str, str]]
    siblings: list[str]


class CasePatch(_StrictBody):
    """The triage's changes to one row; at least one field.

    `tags` replaces the whole list (unique slugs, stored sorted); `promoted: true` sets
    `promoted_at` once and `false` clears it; `expected` is the outcome the regression
    harness checks once the case is promoted.
    """

    status: CaseStatus | None = None
    tags: Annotated[list[Tag], Field(max_length=MAX_TAGS)] | None = None
    promoted: Annotated[bool, Field(strict=True)] | None = None
    expected: Expected | None = None

    @model_validator(mode="after")
    def _check(self) -> CasePatch:
        if self.status is None and self.tags is None and self.promoted is None and self.expected is None:
            raise ValueError("send at least one of status, tags, promoted or expected")
        if self.tags is not None and len(set(self.tags)) != len(self.tags):
            raise ValueError("tags must be unique")
        return self


def _utc(value: datetime) -> str:
    """A naive UTC timestamp from the table as ISO 8601 with `Z`, so the browser does not read it as local time."""
    return value.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _case_fields(row: AgentFeedback) -> dict[str, Any]:
    return {
        "id": row.id,
        "created_at": _utc(row.created_at),
        "reaction": row.reaction,
        "message": row.message,
        "include_data": row.include_data,
        "status": row.status,
        "tags": list(row.tags or []),
        "spec_id": row.spec_id,
        "library_id": row.library_id,
        "locale": row.locale,
        "result_version": row.result_version,
        "replaces": row.replaces,
        "superseded_by": row.superseded_by,
        "promoted_at": _utc(row.promoted_at) if row.promoted_at is not None else None,
        "expected": row.expected,
        "model": row.model,
        "model_version": row.model_version,
        "judge_model": row.judge_model,
        "prompt_hash": row.prompt_hash,
        "pipeline_status": row.pipeline_status,
        "attempts": row.attempts,
        "tokens": row.tokens,
        "cost_estimate": row.cost_estimate,
        "files": list(row.files or []),
        "user_hash": row.user_hash,
        "session_hash": row.session_hash,
        "case_uri": row.case_uri,
        "manifest_schema": row.manifest_schema,
        "updated_at": _utc(row.updated_at),
    }


async def _case_or_404(repo: AgentFeedbackRepository, case_id: str, ctx: AgentContext) -> AgentFeedback:
    row = await repo.get_by_id(case_id)
    if row is None:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    return row


def _storage_failed(case_id: str, ctx: AgentContext, exc: BaseException) -> AgentHTTPError:
    # The exception class only, as for the upload: a storage error's message can carry URLs.
    logger.warning("agent case %s not read (ref %s): %s", case_id, ctx.request_id, type(exc).__name__)
    return AgentHTTPError(502, "storage", ctx.request_id)


@router.get("/cases", response_model=CasePage)
async def list_agent_cases(
    ctx: Ctx,
    db: Db,
    reaction: Reaction | None = None,
    status: StatusFilter | None = None,
    spec: Annotated[str | None, Query(pattern=SPEC_ID_PATTERN)] = None,
    library: Annotated[str | None, Query(pattern=LIBRARY_FILTER_PATTERN)] = None,
    model_version: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    tag: Annotated[str | None, Query(pattern=TAG_PATTERN)] = None,
    include_superseded: bool = False,
    before: Annotated[str | None, Query(pattern=CASE_ID_PATTERN)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> CasePage:
    """The feedback cases, newest first, `limit` per page; superseded ones only with `include_superseded`.

    `status=open` is `new` and `in_progress`. `before` is the exclusive cursor: the last
    item's id of the page before.
    """
    rows = await AgentFeedbackRepository(db).list_cases(
        reaction=reaction,
        status=OPEN_STATUSES if status == "open" else status,
        spec_id=spec,
        library_id=library,
        model_version=model_version,
        tag=tag,
        include_superseded=include_superseded,
        before=before,
        limit=limit + 1,
    )
    return CasePage(items=[CaseItem(**_case_fields(row)) for row in rows[:limit]], has_more=len(rows) > limit)


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_agent_case(case_id: CaseId, ctx: Ctx, cases: Cases, db: Db) -> CaseDetail:
    """One case: the row, what its manifest adds, the diff against the catalogue, and its siblings.

    `404 not_found` without a row (a case in the bucket is not a row until the backfill
    indexes it), `502 storage` when the bucket could not be read; a manifest the lifecycle
    rule deleted is `expired`, not an error.
    """
    repo = AgentFeedbackRepository(db)
    row = await _case_or_404(repo, case_id, ctx)
    try:
        manifest = await run_in_threadpool(read_manifest, cases, case_id)
    except Exception as exc:  # any client, auth or transport error of the storage library, or a manifest no JSON
        raise _storage_failed(case_id, ctx, exc) from exc
    siblings = await repo.siblings(row.session_hash, row.result_version, row.id)
    impl = None
    if row.spec_id and row.library_id:
        impl = await ImplRepository(db).get_code(row.spec_id, row.library_id)
    original = strip_noqa_comments(impl.code) if impl is not None else None
    catalogue_version = impl.library_version if impl is not None else None
    if manifest is None:
        return CaseDetail(
            **_case_fields(row),
            catalogue_library_version=catalogue_version,
            expired=True,
            transcript=None,
            code=None,
            diff=None,
            snapshot_library_version=None,
            residual_defects=[],
            changes=[],
            result_reason=None,
            config=None,
            bindings=[],
            siblings=siblings,
        )
    detail = manifest_detail(manifest, row.result_version)
    diff = None
    if original and detail.code and row.spec_id and row.library_id:
        diff = code_diff(original, detail.code, spec_id=row.spec_id, library_id=row.library_id)
    return CaseDetail(
        **_case_fields(row),
        catalogue_library_version=catalogue_version,
        expired=False,
        transcript=[TranscriptTurn(role=role, text=text) for role, text in detail.transcript],
        code=detail.code,
        diff=diff,
        snapshot_library_version=detail.snapshot_library_version,
        residual_defects=list(detail.residual_defects),
        changes=list(detail.changes),
        result_reason=detail.result_reason,
        config=detail.config,
        bindings=[{"role": role, "column": column} for role, column in detail.bindings],
        siblings=siblings,
    )


@router.get("/cases/{case_id}/files/{name}")
async def get_agent_case_file(case_id: CaseId, name: CaseFileName, ctx: Ctx, cases: Cases, db: Db) -> Response:
    """One file of a case as stored, with its stored content type; never cached.

    `404 not_found` for an unknown id, a file the case does not hold, or one the lifecycle
    rule deleted; `502 storage` for any other bucket error.
    """
    row = await _case_or_404(AgentFeedbackRepository(db), case_id, ctx)
    if name not in row.files:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    try:
        data = await run_in_threadpool(cases.download, case_object(case_id, name))
    except Exception as exc:  # any client, auth or transport error of the storage library
        raise _storage_failed(case_id, ctx, exc) from exc
    if data is None:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    # A returned Response skips the headers `agent_context` set, so repeat them.
    headers = {
        "Cache-Control": _NO_STORE,
        "Content-Disposition": f'inline; filename="{name}"',
        "X-Content-Type-Options": "nosniff",
        "X-Request-Id": ctx.request_id,
    }
    return Response(data, media_type=CASE_MEDIA_TYPES[name], headers=headers)


@router.patch("/cases/{case_id}", response_model=CaseItem)
async def update_agent_case(case_id: CaseId, body: CasePatch, ctx: Ctx, db: Db) -> CaseItem:
    """Change a case's triage state: status, tags, expected outcome, promotion; answers the whole row.

    Promoting needs a plot (`422 no_plot` for a chat case, `result_version` 0, which the
    regression harness cannot replay), the case's data (`422 no_data` otherwise: the
    harness cannot run a case without its `data.csv`) and an expected outcome: the one in the body or on the
    row, else the reaction rule (`thumbs_up` accepted, `thumbs_down` rejected), and
    `422 expected_required` for a `bug` or `idea` without one. A superseded or retired case
    can still be changed.
    """
    repo = AgentFeedbackRepository(db)
    row = await _case_or_404(repo, case_id, ctx)
    updates: dict[str, Any] = {}
    if body.status is not None:
        updates["status"] = body.status
    if body.tags is not None:
        updates["tags"] = sorted(body.tags)
    if body.expected is not None:
        updates["expected"] = body.expected
    if body.promoted is True:
        if row.result_version == 0:
            # A chat case has no plot to replay: the regression harness needs a version.
            raise AgentHTTPError(422, "no_plot", ctx.request_id)
        if not row.include_data:
            raise AgentHTTPError(422, "no_data", ctx.request_id)
        if body.expected is None and row.expected is None:
            rule = EXPECTED_BY_REACTION.get(row.reaction)
            if rule is None:
                raise AgentHTTPError(422, "expected_required", ctx.request_id)
            updates["expected"] = rule
        if row.promoted_at is None:
            updates["promoted_at"] = datetime.now(UTC).replace(tzinfo=None)
    elif body.promoted is False:
        updates["promoted_at"] = None
    updated = await repo.update(case_id, updates)
    if updated is None:
        raise AgentHTTPError(404, "not_found", ctx.request_id)
    return CaseItem(**_case_fields(updated))
