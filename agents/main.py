"""anyplot-agents: the private `/v1` API in front of the ADK runner.

The service is called only by the BFF (`api/routers/agent.py`, `/debug/agent/*`)
through Cloud Run IAM. It never exposes ADK's own server (`adk web`,
`get_fast_api_app`): the client cannot choose a user id or write state, events or
artifacts. Sessions, datasets, renders and versions live in memory for one instance
lifetime (`max-instances=1`), so a restart answers `404 session_expired`.

| Route | Body | Result | Errors |
|---|---|---|---|
| `GET /v1/status` | | `{libraries, model, location, version, provider, waiting, in_flight}` | |
| `GET /v1/eligibility?spec=&library=` | | `{eligible, status, reasons}` | |
| `POST /v1/sessions` | `{user, spec_id, library, locale, snapshot}` | `{session_id, eligibility}` | `422 not_eligible` |
| `POST /v1/sessions/{sid}/library` | `{library, snapshot}` | `{session_id, eligibility}` | `422 not_eligible`, `409 run_active` |
| `POST /v1/sessions/{sid}/dataset` | `{text}` | `{preview, profile, bindings, warnings, roles}` | `413 too_long`, `422 unparseable`, `403 data_refused`, `503 guard_unavailable` |
| `PUT /v1/sessions/{sid}/bindings` | `[{role, column}]` | `{bindings, complete, missing_roles}` | `409 run_active`, `422 invalid` (with `errors`, at most 20 lines) |
| `POST /v1/sessions/{sid}/messages` | `{text}` or `{action}` | SSE `anyplot/1` | `413 too_long`, `409 run_active`, `503 capacity` |
| `POST /v1/sessions/{sid}/cancel` | | `204` | |
| `POST /v1/sessions/{sid}/versions/{version}/render` | `{theme}` | `{status, reason?, artifacts}` | `404 not_found`, `409 run_active`, `503 capacity` (no render slot in time, or the render store is full) |
| `GET /v1/sessions/{sid}/artifacts/{name}?v=` | | the file | `404` |
| `GET /v1/sessions/{sid}/bundle?version=&include_data=` | | the feedback case bundle | `404` |
| `DELETE /v1/sessions/{sid}` | | `204` | |

Every `/v1` route needs `X-Anyplot-User` (the BFF's opaque user id); sessions are
owned by that id, so another user's session id is `404 session_expired`. Outside
development the caller check decodes the IAM-forwarded ID token (Cloud Run has
already verified it and replaced the signature) and requires its `aud` in
`AGENT_SERVICE_URLS` and its `email` in `AGENT_ALLOWED_CALLERS`. It reads
`X-Serverless-Authorization` whenever that header is present, because Cloud Run then
checks only that one and passes `Authorization` through unverified.

Every `/messages` turn goes through the run queue (`anyplot/run_queue.py`): the route
answers `503 capacity` when the queue is full, otherwise the stream sends `ready`,
then `status{step:"queued", position, waiting}` while the run waits, then the run.
The request deadline and its abort start only when the run leaves the queue; a run
that waited `AGENT_QUEUE_MAX_WAIT_S` ends with `error{code:"capacity"}`. A user with
a queued or running run gets `409 run_active` on a second turn in any session. A
user over the daily token budget gets the `budget` refusal at once, without taking
a place in the queue. The theme toggle (`/versions/{version}/render`) renders the
other theme of a finished version outside the queue, because it costs no tokens,
but behind waiting pipeline renders in the render slot (`render/serial.py`); while
it renders it holds the session's registry entry, so a user has one run or toggle
in flight at a time. `adk web` runs the agents without this service, so its runs
bypass the queue; its renders still go through the one render slot.

The dataset answer lists the spec's data roles as `roles`, each
`{name, kinds, required, variadic, description}`, so a client can offer a column
choice for every role: a single role binds under its own name, a variadic family
`y` binds its members `y1`, `y2`, ... (`data/bindings.py`).

Run locally with `uv run uvicorn agents.main:app --port 8001`.
"""

import asyncio
import base64
import binascii
import contextlib
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import secrets
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from fastapi import Body, Depends, FastAPI, Header, Path, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from google.adk import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.background import BackgroundTask

from agents.anyplot import agent as agent_module
from agents.anyplot.code.readiness import MAP_SPECS
from agents.anyplot.data.parse import MAX_INPUT_BYTES, ParseError, parse_dataset
from agents.anyplot.data.roles import DataRole
from agents.anyplot.data.store import StoreFull
from agents.anyplot.dev_fixture import FixtureError, load_case
from agents.anyplot.models import JudgeUnavailable
from agents.anyplot.opening import Eligibility, assess, dataset_judge_input, opening_state, store_dataset
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, attribution, budget_allows
from agents.anyplot.policy import data_rubric, fence, refusal
from agents.anyplot.render.serial import RenderBusy
from agents.anyplot.render.store import RenderStoreFull
from agents.anyplot.run_queue import HEARTBEAT_S, QueueFull, QueueTimeout, QueueWithdrawn, RunQueue, Ticket
from agents.anyplot.schemas import MAX_COLUMNS, Binding, Theme
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import BINDINGS, CatalogueSnapshot, apply_bindings, read_session
from agents.anyplot.settings import AgentSettings, get_settings
from agents.anyplot.theme_render import RenderGone, render_theme
from agents.stream import Translator
from core.constants import SUPPORTED_LIBRARIES


logger = logging.getLogger("anyplot.agents")

APP_NAME = agent_module.APP_NAME
MAX_MESSAGE_CHARS = 2_000
USER_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
SESSION_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"
SPEC_PATTERN = r"^[a-z0-9-]{1,100}$"
LOCALE_PATTERN = r"^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$"
ACTION_MESSAGE = "[action] Create the plot from my dataset and bindings."
SWEEP_INTERVAL_S = 300
ARTIFACT_TYPES: dict[str, str] = {
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
_USER = re.compile(USER_PATTERN)
_NO_STORE = {"Cache-Control": "private, no-store"}

CONTENT_LOGGERS = ("google_adk", "google.adk", "google_genai", "anthropic", "httpx")


def disable_content_capture() -> None:
    """No content in logs or spans.

    Debug logging of ADK and the model SDKs prints request and response content, ADK
    puts message content into its spans unless told otherwise (`telemetry/context.py`
    reads the variable on every span), and the OpenTelemetry GenAI instrumentation
    does the same when its capture variable is set.
    """
    for name in CONTENT_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    os.environ["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] = "false"
    os.environ.pop("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", None)


disable_content_capture()


class AgentsError(Exception):
    """A `/v1` error answered as `{"detail": code}`; never an exception text."""

    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


def _version() -> str:
    try:
        return importlib.metadata.version("anyplot")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


# --- Runtime -----------------------------------------------------------------------------


STALE_RUN_MARGIN_S = 30
"""Seconds past the request deadline (or the queue's maximum wait) after which an entry counts as abandoned."""


@dataclass
class ActiveRun:
    """A `/messages` request from its queue entry to the end of its stream, or a theme toggle while it renders.

    `started` is the registration time on the queue's clock, and the start of the run
    once it left the queue; the ticket's own times decide the stale check when there
    is one, so a run that just left a long wait is not mistaken for an old run. A
    toggle has no ticket, and its abort signal is never read: it ends within the
    request deadline on its own (a bounded slot wait plus one render).
    """

    abort: asyncio.Event
    user: str = ""
    started: float = field(default_factory=time.monotonic)
    deadline_hit: bool = False
    ticket: Ticket | None = None

    def stale(self, now: float, deadline_s: float, max_wait_s: float) -> bool:
        """An entry past the queue's maximum wait, or a run past the hard deadline, plus a margin, was abandoned."""
        if self.ticket is not None and self.ticket.waiting:
            return now - self.ticket.enqueued_at > max_wait_s + STALE_RUN_MARGIN_S
        began = self.started
        if self.ticket is not None and self.ticket.started_at is not None:
            began = max(began, self.ticket.started_at)
        return now - began > deadline_s + STALE_RUN_MARGIN_S


@dataclass
class Runtime:
    """The runner, the run queue and the run registry for this process.

    `active` is the run registry: one entry per session with a queued or running
    `/messages` turn or a theme toggle in flight, which is what `409 run_active`
    checks. The queue is built from the settings on first use; its clock is the
    registry's clock too.
    """

    session_service: InMemorySessionService = field(default_factory=InMemorySessionService)
    artifact_service: InMemoryArtifactService = field(default_factory=InMemoryArtifactService)
    active: dict[str, ActiveRun] = field(default_factory=dict)
    eligibility_cache: dict[tuple[str, str], Eligibility] = field(default_factory=dict)
    runner: Runner | None = None
    queue: RunQueue | None = None
    clock: Callable[[], float] = time.monotonic

    def run_queue(self) -> RunQueue:
        if self.queue is None:
            self.queue = RunQueue.from_settings(get_settings(), clock=self.clock)
        return self.queue

    def now(self) -> float:
        return self.run_queue().now()

    def get_runner(self) -> Runner:
        if self.runner is None:
            self.runner = Runner(
                app=agent_module.app, session_service=self.session_service, artifact_service=self.artifact_service
            )
        return self.runner

    async def session(self, user: str, sid: str) -> Session:
        session = await self.session_service.get_session(app_name=APP_NAME, user_id=user, session_id=sid)
        if session is None:
            raise AgentsError(404, "session_expired")
        return session

    async def write_state(self, session: Session, delta: dict[str, Any]) -> None:
        # Authored "user" like ADK's own state-only events, so the agent router does not
        # look for an agent of that name; it has no content, so no model ever reads it.
        event = Event(invocation_id=f"route-{secrets.token_hex(6)}", author="user")
        event.actions = EventActions(state_delta=delta)
        await self.session_service.append_event(session=session, event=event)

    async def purge(self, user: str, sid: str, services: Services) -> None:
        run = self.active.pop(sid, None)
        if run is not None:
            self.stop(run)
        await self.session_service.delete_session(app_name=APP_NAME, user_id=user, session_id=sid)
        services.purge_session(sid)

    def stop(self, run: ActiveRun) -> None:
        """Abort a run and take it out of the queue if it still waits; a running one keeps its slot until it ends."""
        run.abort.set()
        if run.ticket is not None:
            self.run_queue().withdraw(run.ticket)

    def drop_stale(self, settings: AgentSettings) -> None:
        """Forget entries whose stream never ran its cleanup (a client gone before the first byte), and free their slot."""
        now = self.now()
        max_wait_s = self.run_queue().max_wait_s
        for sid, run in list(self.active.items()):
            if run.stale(now, settings.request_deadline_s, max_wait_s):
                run.abort.set()
                if run.ticket is not None:
                    self.run_queue().release(run.ticket)
                del self.active[sid]

    def finish(self, sid: str, run: ActiveRun) -> None:
        """The stream ended: free the run's queue slot, and forget `run` if it is still the session's entry."""
        if run.ticket is not None:
            self.run_queue().release(run.ticket)
        if self.active.get(sid) is run:
            del self.active[sid]

    async def sweep(self, idle_s: float, services: Services) -> int:
        """Drop sessions idle for longer than `idle_s`, with their stores."""
        self.drop_stale(get_settings())
        self.run_queue().pump()
        listing = await self.session_service.list_sessions(app_name=APP_NAME)
        now = time.time()
        removed = 0
        for session in listing.sessions:
            if session.id in self.active or now - session.last_update_time <= idle_s:
                continue
            await self.purge(session.user_id, session.id, services)
            removed += 1
        services.datasets.sweep(idle_s)
        services.renders.sweep(idle_s)
        return removed


RUNTIME = Runtime()


def get_runtime() -> Runtime:
    return RUNTIME


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async def sweeper() -> None:
        while True:
            await asyncio.sleep(SWEEP_INTERVAL_S)
            try:
                await get_runtime().sweep(get_settings().session_idle_s, get_services())
            except Exception as exc:
                logger.warning("session sweep failed: %s", type(exc).__name__)

    task = asyncio.create_task(sweeper())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="anyplot-agents", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.exception_handler(AgentsError)
async def _agents_error(_: Request, exc: AgentsError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={"detail": exc.code}, headers=_NO_STORE)


# --- Caller and user ---------------------------------------------------------------------


def decode_claims(authorization: str | None) -> dict[str, Any] | None:
    """The claims of a bearer JWT, decoded without verifying the signature (Cloud Run IAM did)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    parts = authorization[7:].strip().split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, binascii.Error):
        return None
    return claims if isinstance(claims, dict) else None


def checked_token(request: Request) -> str | None:
    """The header Cloud Run IAM verified: `X-Serverless-Authorization` when present, else `Authorization`.

    With both headers present Cloud Run checks only `X-Serverless-Authorization`, so an
    invoker could otherwise add an unsigned `Authorization` that names an allowed email.
    """
    serverless = request.headers.get("x-serverless-authorization")
    return serverless if serverless is not None else request.headers.get("authorization")


def check_caller(request: Request) -> None:
    """Outside development: an IAM-forwarded ID token whose `aud` and `email` are allowed."""
    settings = get_settings()
    if settings.is_development:
        return
    claims = decode_claims(checked_token(request))
    if claims is None:
        raise AgentsError(401, "unauthenticated")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if not any(isinstance(item, str) and item in settings.service_urls for item in audiences):
        raise AgentsError(403, "forbidden")
    if claims.get("email") not in settings.allowed_callers:
        raise AgentsError(403, "forbidden")


def require_user(x_anyplot_user: Annotated[str | None, Header()] = None) -> str:
    if not x_anyplot_user or not _USER.fullmatch(x_anyplot_user):
        raise AgentsError(400, "user_required")
    return x_anyplot_user


def request_id(x_request_id: Annotated[str | None, Header()] = None) -> str:
    if x_request_id and re.fullmatch(r"^[A-Za-z0-9-]{1,64}$", x_request_id):
        return x_request_id
    return secrets.token_hex(8)


User = Annotated[str, Depends(require_user)]
RequestId = Annotated[str, Depends(request_id)]
SessionId = Annotated[str, Path(pattern=SESSION_PATTERN)]
RuntimeDep = Annotated[Runtime, Depends(get_runtime)]
v1_dependencies = [Depends(check_caller)]


# --- Bodies ------------------------------------------------------------------------------


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateSessionBody(_Body):
    user: str = Field(pattern=USER_PATTERN)
    spec_id: str = Field(pattern=SPEC_PATTERN)
    library: str
    locale: str = Field(max_length=16, pattern=LOCALE_PATTERN)
    snapshot: CatalogueSnapshot


class SwitchLibraryBody(_Body):
    library: str
    snapshot: CatalogueSnapshot


class DatasetBody(_Body):
    text: str = Field(min_length=1)


class BindingBody(_Body):
    role: str = Field(min_length=1, max_length=32)
    column: str | None = Field(default=None, max_length=64)


class MessageBody(_Body):
    text: str | None = None
    action: Literal["create_plot"] | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "MessageBody":
        if (self.text is None) == (self.action is None):
            raise ValueError("send exactly one of text or action")
        return self


def _library(library: str, settings: AgentSettings) -> str:
    if library not in SUPPORTED_LIBRARIES:
        raise AgentsError(422, "invalid")
    return library


# --- Routes ------------------------------------------------------------------------------


@app.get("/v1/status", dependencies=v1_dependencies)
async def status(runtime: RuntimeDep) -> dict[str, Any]:
    """The service's configuration, plus the run queue: `waiting` entries and runs `in_flight`."""
    settings = get_settings()
    queue = runtime.run_queue()
    queue.pump()
    return {
        "libraries": list(settings.libraries),
        "model": settings.model,
        "location": settings.location,
        "provider": settings.provider,
        "version": _version(),
        "waiting": queue.waiting_count,
        "in_flight": queue.in_flight,
    }


@app.get("/v1/eligibility", dependencies=v1_dependencies)
async def eligibility(
    runtime: RuntimeDep, _: User, spec: Annotated[str, Query(pattern=SPEC_PATTERN)], library: Annotated[str, Query()]
) -> dict[str, Any]:
    """Without a snapshot the service knows the static rules and the pairs it has already scanned."""
    settings = get_settings()
    _library(library, settings)
    cached = runtime.eligibility_cache.get((spec, library))
    if cached is not None:
        return cached.public()
    reasons = []
    if spec in MAP_SPECS:
        reasons.append("map-spec")
    if library not in settings.libraries:
        reasons.append("library-disabled")
    if reasons:
        return {"eligible": False, "status": "blocked", "reasons": reasons}
    return {"eligible": True, "status": "unchecked", "reasons": []}


def _assess(runtime: Runtime, snapshot: CatalogueSnapshot, library: str) -> tuple[Eligibility, str]:
    eligibility_result, normalised = assess(snapshot, library, get_settings())
    runtime.eligibility_cache[(snapshot.spec_id, library)] = eligibility_result
    return eligibility_result, normalised


@app.post("/v1/sessions", dependencies=v1_dependencies)
async def create_session(body: CreateSessionBody, user: User, runtime: RuntimeDep) -> JSONResponse:
    settings = get_settings()
    if body.user != user or body.snapshot.spec_id != body.spec_id:
        raise AgentsError(422, "invalid")
    library = _library(body.library, settings)
    result, normalised = _assess(runtime, body.snapshot, library)
    if not result.eligible:
        raise AgentsError(422, "not_eligible")
    session_id = secrets.token_urlsafe(24)
    state = opening_state(
        spec_id=body.spec_id,
        library=library,
        locale=body.locale,
        snapshot=body.snapshot,
        normalised=normalised,
        eligibility=result,
    )
    state.update(_fixture_seed(body.spec_id, library, session_id, body.snapshot, settings))
    await runtime.session_service.create_session(app_name=APP_NAME, user_id=user, state=state, session_id=session_id)
    return JSONResponse({"session_id": session_id, "eligibility": result.public()}, headers=_NO_STORE)


def _fixture_seed(
    spec_id: str, library: str, session_id: str, snapshot: CatalogueSnapshot, settings: AgentSettings
) -> dict[str, Any]:
    """Development only: the fixture case's dataset and bindings when it matches the opened pair."""
    if not settings.dev_fixture or not settings.is_development:
        return {}
    try:
        case = load_case(settings.dev_fixture)
    except FixtureError as exc:
        logger.warning("fixture seed skipped: %s", exc)
        return {}
    if (case.spec_id, case.library) != (spec_id, library):
        return {}
    ingested = store_dataset(get_services().datasets, session_id, parse_dataset(case.data_text), snapshot)
    delta = ingested.state_delta()
    if case.bindings is not None:
        delta[BINDINGS] = [binding.model_dump() for binding in case.bindings]
    return delta


def _active(runtime: Runtime, sid: str, user: str | None = None) -> None:
    """409 while the session has a queued or running run, or, with `user`, while that user has one in any session."""
    runtime.drop_stale(get_settings())
    if sid in runtime.active:
        raise AgentsError(409, "run_active")
    if user is not None and any(run.user == user for run in runtime.active.values()):
        raise AgentsError(409, "run_active")


@app.post("/v1/sessions/{sid}/library", dependencies=v1_dependencies)
async def switch_library(sid: SessionId, body: SwitchLibraryBody, user: User, runtime: RuntimeDep) -> JSONResponse:
    settings = get_settings()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None or body.snapshot.spec_id != view.spec_id:
        raise AgentsError(422, "invalid")
    library = _library(body.library, settings)
    result, normalised = _assess(runtime, body.snapshot, library)
    if not result.eligible:
        raise AgentsError(422, "not_eligible")
    delta = opening_state(
        spec_id=view.spec_id,
        library=library,
        locale=view.locale,
        snapshot=body.snapshot,
        normalised=normalised,
        eligibility=result,
    )
    await runtime.write_state(session, delta)
    return JSONResponse({"session_id": sid, "eligibility": result.public()}, headers=_NO_STORE)


@app.post("/v1/sessions/{sid}/dataset", dependencies=v1_dependencies)
async def upload_dataset(
    sid: SessionId, body: DatasetBody, user: User, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    if len(body.text.encode("utf-8", errors="surrogatepass")) > MAX_INPUT_BYTES:
        raise AgentsError(413, "too_long")
    try:
        parsed = parse_dataset(body.text)
    except ParseError as exc:
        raise AgentsError(
            413 if exc.code == "too_long" else 422, "too_long" if exc.code == "too_long" else "unparseable"
        ) from None
    ledger = RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action")
    if not services.usage.daily_ok(user, get_settings()):
        raise AgentsError(429, "rate_limited")
    try:
        verdict = await services.judge.judge(fence("dataset", dataset_judge_input(parsed)), data_rubric())
    except JudgeUnavailable:
        attribution("data_judge", ledger, verdict="guard_unavailable")
        raise AgentsError(503, "guard_unavailable") from None
    services.usage.add_tokens(user, verdict.tokens)
    attribution(
        "data_judge",
        ledger,
        verdict=verdict.verdict,
        judge_tokens=verdict.tokens,
        judge_input=verdict.input_tokens,
        judge_output=verdict.output_tokens,
    )
    if verdict.verdict != "in_scope":  # fail closed, like the scope guard
        raise AgentsError(403, "data_refused")
    try:
        ingested = store_dataset(services.datasets, sid, parsed, view.snapshot, previous_id=view.dataset_id)
    except StoreFull:
        raise AgentsError(503, "capacity") from None
    await runtime.write_state(session, ingested.state_delta())
    return JSONResponse(
        {
            "preview": parsed.preview,
            "profile": parsed.profile.model_dump(mode="json"),
            "bindings": [binding.model_dump() for binding in ingested.bindings],
            "warnings": parsed.warnings,
            "roles": [_role_body(role) for role in view.snapshot.roles()],
        },
        headers=_NO_STORE,
    )


MAX_ROLE_DESCRIPTION_CHARS = 200


def _role_body(role: DataRole) -> dict[str, Any]:
    """One spec data role for the binding controls; the description is the spec's own text, capped."""
    description = role.description
    if len(description) > MAX_ROLE_DESCRIPTION_CHARS:
        description = description[: MAX_ROLE_DESCRIPTION_CHARS - 1].rstrip() + "…"
    return {
        "name": role.name,
        "kinds": list(role.kinds),
        "required": role.required,
        "variadic": role.variadic,
        "description": description,
    }


@app.put("/v1/sessions/{sid}/bindings", dependencies=v1_dependencies)
async def put_bindings(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    bindings: Annotated[list[BindingBody], Body(max_length=MAX_COLUMNS)],
) -> JSONResponse:
    services = get_services()
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    try:
        parsed = [Binding(role=item.role, column=item.column) for item in bindings if item.column]
    except ValueError:
        raise AgentsError(422, "invalid") from None
    check, delta = apply_bindings(parsed, view.snapshot.roles(), stored.profile)
    if not delta:
        return JSONResponse(
            status_code=422, content={"detail": "invalid", "errors": check.errors[:20]}, headers=_NO_STORE
        )
    await runtime.write_state(session, delta)
    return JSONResponse(
        {"bindings": delta[BINDINGS], "complete": check.complete, "missing_roles": check.missing_roles},
        headers=_NO_STORE,
    )


async def _refused(translator: Translator, ledger: RequestLedger) -> AsyncIterator[str]:
    """A turn the ledger refused before it entered the queue: `ready`, the refusal, `done`."""
    yield translator.ready()
    for chunk in translator.refusal():
        yield chunk
    attribution("run", ledger, model_versions=[], kind=ledger.kind)
    yield translator.done()


def _error_code(exc: BaseException) -> str:
    name = type(exc).__name__
    if "RateLimit" in name or "ResourceExhausted" in name or getattr(exc, "code", None) == 429:
        return "capacity"
    if name == "LlmCallsLimitExceededError":
        return "capacity"
    return "internal"


@app.post("/v1/sessions/{sid}/messages", dependencies=v1_dependencies)
async def post_message(
    sid: SessionId, body: MessageBody, user: User, runtime: RuntimeDep, rid: RequestId
) -> StreamingResponse:
    if body.text is not None and len(body.text) > MAX_MESSAGE_CHARS:
        raise AgentsError(413, "too_long")
    session = await runtime.session(user, sid)
    _active(runtime, sid, user)
    settings = get_settings()
    services = get_services()
    view = read_session(session.state)
    ledger = RequestLedger(
        request_id=rid,
        user_id=user,
        session_id=sid,
        kind="action" if body.action else "text",
        lang=view.lang if view else "en",
    )
    translator = Translator(ledger, run_id=secrets.token_hex(8), spec_id=view.spec_id if view else None)
    if not budget_allows(ledger, services.usage, settings):
        # The refusal the root would send after the wait, sent now: a user over the daily
        # budget neither takes a place in the queue nor spends the minute's start.
        ledger.refuse("budget", refusal("budget", ledger.lang))
        attribution("budget_halt", ledger, agent="run_queue")
        return StreamingResponse(
            _refused(translator, ledger),
            media_type="text/event-stream",
            headers={**_NO_STORE, "X-Accel-Buffering": "no"},
        )
    queue = runtime.run_queue()
    try:
        ticket = queue.submit(user, sid)
    except QueueFull:
        logger.info("run queue full (ref %s): %d waiting", rid, queue.waiting_count)
        raise AgentsError(503, "capacity") from None
    run = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now(), ticket=ticket)
    # Registered here so a second request cannot slip in before the stream starts; the
    # stream's finally and the background task both clear it and free its queue slot,
    # and an entry neither reached (a client gone before the first byte) goes stale
    # after the queue's maximum wait or the deadline.
    runtime.active[sid] = run
    if view is not None and view.dataset_id:
        # A hit counts as use: the idle sweep must not take the dataset while the run waits.
        services.datasets.get(view.dataset_id, sid)
    text = ACTION_MESSAGE if body.action else (body.text or "")
    message = types.Content(role="user", parts=[types.Part(text=text)])

    async def stream() -> AsyncIterator[str]:
        token = CURRENT_LEDGER.set(ledger)
        loop = asyncio.get_running_loop()

        def deadline() -> None:
            run.deadline_hit = True
            run.abort.set()

        timer: asyncio.TimerHandle | None = None
        failure: str | None = None
        try:
            yield translator.ready()
            outcome = "started"
            async with contextlib.aclosing(queue.wait(ticket, heartbeat_s=HEARTBEAT_S)) as positions:
                try:
                    async for position in positions:
                        yield translator.queued(position.position, position.waiting)
                except QueueTimeout:  # waited the maximum: the same answer as a full queue
                    outcome, failure = "expired", "capacity"
                except QueueWithdrawn:  # cancelled or purged while it waited: nothing to report
                    outcome = "withdrawn"
            attribution("queue", ledger, verdict=outcome, waited_s=round(runtime.now() - ticket.enqueued_at, 1))
            if outcome == "started":
                # Queued time never counts: the deadline and its abort start with the run.
                run.started = runtime.now()
                timer = loop.call_later(settings.request_deadline_s, deadline)
                events = runtime.get_runner().run_async(
                    user_id=user,
                    session_id=sid,
                    new_message=message,
                    run_config=RunConfig(max_llm_calls=settings.max_llm_calls, streaming_mode=StreamingMode.NONE),
                    abort_signal=run.abort,
                )
                async with contextlib.aclosing(events) as iterator:
                    async for event in iterator:
                        for chunk in translator.translate(event):
                            yield chunk
        except Exception as exc:  # the stream always ends with error + done, never a traceback
            logger.warning("run failed (ref %s): %s", rid, type(exc).__name__)
            failure = _error_code(exc)
        finally:
            if timer is not None:
                timer.cancel()
            runtime.finish(sid, run)
            CURRENT_LEDGER.reset(token)
        if ledger.error is not None:
            failure = ledger.error
        elif run.deadline_hit and not translator.plot_sent:
            failure = "deadline"
        if failure is not None:
            for chunk in translator.error(failure):
                yield chunk
        attribution("run", ledger, model_versions=sorted(ledger.model_versions), kind=ledger.kind)
        yield translator.done()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={**_NO_STORE, "X-Accel-Buffering": "no"},
        background=BackgroundTask(runtime.finish, sid, run),
    )


@app.post("/v1/sessions/{sid}/cancel", status_code=204, dependencies=v1_dependencies)
async def cancel(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    """Abort the session's run; a run that still waits leaves the queue at once. A theme toggle runs to its end."""
    await runtime.session(user, sid)
    run = runtime.active.get(sid)
    if run is not None:
        runtime.stop(run)
    return Response(status_code=204, headers=_NO_STORE)


class RenderThemeBody(_Body):
    theme: Theme


@app.post("/v1/sessions/{sid}/versions/{version}/render", dependencies=v1_dependencies)
async def render_version_theme(
    sid: SessionId, version: Annotated[int, Path(ge=0, le=999)], body: RenderThemeBody, user: User, runtime: RuntimeDep
) -> JSONResponse:
    """The theme toggle: render `theme` of a finished version from its stored run form, with no model call.

    Version 0 is the latest. Synchronous (a render takes seconds): it renders in the
    render slot's `toggle` lane, behind waiting pipeline renders, but not through the
    run queue. It is registered in the run registry while it renders, so it and a turn
    refuse each other with `409 run_active` in both directions, and a user has one run
    or toggle in flight at a time. `503 capacity` when no render slot came free in time
    or the render store is full.
    """
    await runtime.session(user, sid)
    _active(runtime, sid, user)
    services = get_services()
    stored = services.versions.get(sid, version or None)
    if stored is None:
        raise AgentsError(404, "not_found")
    toggle = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now())
    runtime.active[sid] = toggle  # no await since the check above, so nothing slipped in between
    try:
        result = await render_theme(services, get_settings(), sid, stored, body.theme)
    except RenderGone:
        raise AgentsError(404, "not_found") from None
    except (RenderBusy, RenderStoreFull):
        raise AgentsError(503, "capacity") from None
    finally:
        runtime.finish(sid, toggle)
    return JSONResponse(result.public(), headers=_NO_STORE)


@app.get("/v1/sessions/{sid}/artifacts/{name}", dependencies=v1_dependencies)
async def artifact(
    sid: SessionId, name: str, user: User, runtime: RuntimeDep, v: Annotated[int | None, Query(ge=0, le=999)] = None
) -> Response:
    media_type = ARTIFACT_TYPES.get(name)
    if media_type is None:
        raise AgentsError(404, "not_found")
    await runtime.session(user, sid)
    services = get_services()
    version = services.versions.get(sid, v or None)
    if version is None:
        raise AgentsError(404, "not_found")
    content: bytes | None
    if name == "plot.py":
        content = version.export.encode("utf-8")
    elif name == "data.csv":
        content = version.data_csv.encode("utf-8")
    else:
        stored = services.renders.get(version.render_id, sid) if version.render_id else None
        content = stored.pngs.get("light" if name == "plot-light.png" else "dark") if stored else None
    if content is None:
        raise AgentsError(404, "not_found")
    return Response(content, media_type=media_type, headers={**_NO_STORE, "X-Content-Type-Options": "nosniff"})


def _prompt_hashes() -> dict[str, str]:
    from agents.anyplot import policy

    texts = {
        "root": policy.root_instruction(),
        "reviewer": policy.reviewer_instruction(),
        **{f"adapter_{library}": policy.adapter_instruction(library) for library in agent_module.ADAPTERS},
    }
    return {name: hashlib.sha256(text.encode()).hexdigest()[:16] for name, text in texts.items()}


@app.get("/v1/sessions/{sid}/bundle", dependencies=v1_dependencies)
async def bundle(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    version: Annotated[int | None, Query(ge=0, le=999)] = None,
    include_data: bool = False,
) -> JSONResponse:
    """The feedback case: transcript, code versions, plans, results, profile, bindings, PNGs, config."""
    session = await runtime.session(user, sid)
    services = get_services()
    settings = get_settings()
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    versions = services.versions.all(sid)
    if version:
        versions = [item for item in versions if item.number == version]
        if not versions:
            raise AgentsError(404, "not_found")
    transcript = []
    for event in session.events:
        if event.author not in ("user", agent_module.ROOT_NAME) or not event.content or not event.content.parts:
            continue
        if event.get_function_calls() or event.get_function_responses():
            continue
        text = "".join(part.text or "" for part in event.content.parts if part.text and not part.thought)
        if text.strip():
            transcript.append({"role": "user" if event.author == "user" else "assistant", "text": text})
    dataset = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    items = []
    for item in versions:
        stored = services.renders.get(item.render_id, sid) if item.render_id else None
        items.append(
            {
                "number": item.number,
                "title": item.title,
                "working": item.working,
                "run_form": item.run_form,
                "plot_py": item.export,
                "plan": item.plan.model_dump(mode="json") if item.plan else None,
                "result": item.result.model_dump(mode="json"),
                "theme": item.theme,
                "themes": {
                    theme: {"status": record.status, "reason": record.reason} for theme, record in item.themes.items()
                },
                "images": {
                    theme: base64.b64encode(data).decode() for theme, data in (stored.pngs.items() if stored else [])
                },
                "data_csv": item.data_csv if include_data else None,
            }
        )
    payload = {
        "session": {"spec_id": view.spec_id, "library": view.library, "locale": view.locale},
        "snapshot": {"spec_id": view.snapshot.spec_id, "library_version": view.snapshot.library_version},
        "transcript": transcript,
        "versions": items,
        "profile": dataset.profile.model_dump(mode="json") if dataset else None,
        "bindings": [binding.model_dump() for binding in view.bindings],
        "config": {
            "provider": settings.provider,
            "model": settings.model,
            "judge_model": settings.judge_model,
            "location": settings.location,
            "adk_version": importlib.metadata.version("google-adk"),
            "service_version": _version(),
            "prompt_hashes": _prompt_hashes(),
        },
    }
    return JSONResponse(payload, headers=_NO_STORE)


@app.delete("/v1/sessions/{sid}", status_code=204, dependencies=v1_dependencies)
async def delete_session(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    await runtime.session(user, sid)
    await runtime.purge(user, sid, get_services())
    return Response(status_code=204, headers=_NO_STORE)
