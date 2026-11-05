"""The public lane of the agent chat: `/agent/*`, open to everyone once the owner opens it.

Same agents service, same route functions as the admin lane (`api/routers/agent.py`, which this module
calls), with four differences:

* **Identity.** No login. The page keeps a random id per browser tab (sessionStorage) and sends it as
  `X-Anyplot-Anon`; `require_public_identity` turns a request into that id plus the client's network (its IPv4
  address, or the /64 of an IPv6 one). Both go to the agents service, which salts them with its own per-process
  salt and keys the per-user and per-IP limits on the result (`agents/main.py` `require_user`), so nothing
  durable links usage to an address, and every anyplot-api instance reaches the same user.
* **Bot check.** Opening a session and storing a feedback case need a Cloudflare Turnstile token in
  `X-Turnstile-Token` (`api/turnstile.py`); every other route acts on a session such a call opened.
* **Tier.** Every request asserts `X-Anyplot-Tier: public`: the run queue's `normal` lane with its per-user cap,
  and every day cap.
* **No session id in a URL.** Cloud Run's request log keeps a URL together with the client address for 30 days, so
  the session id travels in `X-Anyplot-Session` instead of the path.
* **No admin-only route.** The fan-out's data copy (`/dataset/copy`) and `source: fanout`, the day budget
  (`/budget`), the feedback triage (`/cases*`) and `.save()`'s session file (`/bundle`) exist only under
  `/debug/agent`.

Every route answers 404 until `AGENT_PUBLIC_ENABLED` is on, on top of `AGENT_ENABLED` and its configuration, which
stays the master switch: closing the public door leaves the admin lane open. `GET /agent/lane` answers
`{"open": true}` without calling the agents service, so the site learns at runtime whether to show the entry
points. Capacity: at most `AGENT_PUBLIC_MAX_STREAMS` chat turns per instance at once (`PublicStreams`), so the
catalogue keeps the rest of the instance's request slots; the agents service caps the public lane's waiting runs
on its side (`AGENT_PUBLIC_QUEUE_MAX_WAITING`). Reference: `docs/reference/api.md` ("Agent chat, public lane");
design: `docs/concepts/agent-network.md`.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import re
import secrets
import time
import uuid
from collections import deque
from collections.abc import AsyncIterator, Callable
from contextlib import aclosing
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

import httpx
from fastapi import APIRouter, Body, Depends, Header, Path, Query, Request, Response
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api import turnstile
from api.dependencies import require_db
from api.origin_gate import gate_is_armed
from api.request_context import client_ip
from api.routers import agent
from api.routers.agent import (
    MEMORY_ENTRY_ID_PATTERN,
    NOT_ENABLED,
    SESSION_ID_PATTERN,
    SPEC_ID_PATTERN,
    AgentConfig,
    AgentContext,
    AgentHTTPError,
    Binding,
    CaseBucket,
    CreateSessionBody,
    DatasetBody,
    FeedbackBody,
    LanguageBody,
    LastEventId,
    LibraryId,
    Locale,
    MessageBody,
    OutcomeBody,
    RenderThemeBody,
    SpecId,
    SwitchLibraryBody,
    UpstreamStream,
    get_agent_client,
    get_case_bucket,
    require_agent_enabled,
    require_body_within_cap,
    require_same_site_client,
    require_utf8_body,
)
from core.config import settings
from core.constants import MAX_AGENT_VERSION


ANON_ID_PATTERN = r"^[A-Za-z0-9_-]{22,64}$"
"""The page's tab id (`X-Anyplot-Anon`): a `crypto.randomUUID()` fits, a short guessable value does not. The agents
service checks the same pattern (`agents/main.py` `ANON_PATTERN`)."""
UNKNOWN_NETWORK = "unknown"
"""The network of a client whose address does not parse: one bucket that every such request shares, so a forged
address that is no address gains nothing."""
IPV6_PREFIX = 64
"""An IPv6 client counts by its /64, the network one subscriber gets at the least: per address, one line holds 2**64
buckets. Many providers delegate a /56 or a /48, which still leaves one subscriber 256 to 65,536 buckets of the day
caps; keying the day caps on a /56 is the next step if that is abused."""
PUBLIC_STATUS_FIELDS = frozenset(
    {
        "enabled",
        "libraries",
        "model",
        "location",
        "provider",
        "version",
        "waiting",
        "in_flight",
        "user_max_runs",
        "tier",
        "paused",
        "resets_at",
    }
)
"""The fields of `GET /v1/status` the public page gets: what the service runs, the queue as counts, the caller's own
cap and the day's pause. A field the service adds later stays upstream until it is named here."""
FEEDBACK_WINDOW_S = 3600.0
_NO_STORE = "private, no-store"
_LANE_MAX_AGE_S = 60
_ELIGIBILITY_MAX_AGE_S = 300

_SALT = secrets.token_bytes(32)
"""This process's salt for the case `user_hash` and the feedback limiter's network key; never logged, gone with the
process."""
_ANON_ID = re.compile(ANON_ID_PATTERN)


def _salted(domain: str, value: str) -> str:
    return hmac.new(_SALT, f"{domain}:{value}".encode(), hashlib.sha256).hexdigest()[:16]


# ============================================================================
# Kill switch, identity, capacity
# ============================================================================


def require_public_enabled(config: AgentConfig = Depends(require_agent_enabled)) -> AgentConfig:
    """The public door: 404 unless `AGENT_PUBLIC_ENABLED` is on, on top of the master switch and its configuration.

    In production it also stays shut while the origin gate is unarmed (`ORIGIN_SECRET`, `api/origin_gate.py`): the
    per-IP limits key on `CF-Connecting-IP`, which only a request that came through Cloudflare carries honestly, and
    without the gate a caller on the direct `run.app` URL could forge a fresh address per request. And it stays
    shut without the Turnstile secret (`TURNSTILE_SECRET_KEY`, `api/turnstile.py` `enforced`) or with one of
    Cloudflare's test secrets, either of which would refuse every new session. The deploy smoke then fails on `/agent/lane`, which says so before the switch seems to work.
    """
    if not settings.agent_public_enabled:
        raise AgentHTTPError(404, NOT_ENABLED)
    if settings.is_production and not (gate_is_armed() and turnstile.enforced()):
        raise AgentHTTPError(404, NOT_ENABLED)
    return config


def client_network(request: Request) -> str:
    """The client's network for the per-IP limits: its IPv4 address, or the /64 of its IPv6 address.

    The address is `client_ip`'s: Cloudflare's `CF-Connecting-IP`, which a browser on anyplot.ai cannot set. A caller
    who bypasses Cloudflare for the direct `run.app` URL could set it, and so pick a fresh bucket per request, which is
    why the door opens in production only while the origin gate is armed (`require_public_enabled`): the gate refuses
    every request that skipped the edge. An IPv4-mapped
    IPv6 address counts as its IPv4 address; anything that does not parse is `unknown`, one shared bucket.
    """
    try:
        address = ipaddress.ip_address(client_ip(request))
        if isinstance(address, ipaddress.IPv6Address):
            if address.ipv4_mapped is not None:
                return str(address.ipv4_mapped)
            return str(ipaddress.IPv6Network((address.exploded, IPV6_PREFIX), strict=False))
    except ValueError:
        return UNKNOWN_NETWORK
    return str(address)


@dataclass(frozen=True)
class PublicIdentity:
    """Who a public request is from: the page's anonymous tab id and the client's network (`client_network`)."""

    anon_id: str
    network: str


def require_public_identity(request: Request, x_anyplot_anon: Annotated[str | None, Header()] = None) -> PublicIdentity:
    """Turn a request into the public identity.

    `400 anon_required` without a tab id of `ANON_ID_PATTERN`. Nothing is stored and nothing is logged: the agents
    service salts both values with its per-process salt before it keys anything on them. The bot check is not part
    of it: a token is single-use, so only the calls that open or store something take one (`require_human`).
    """
    if x_anyplot_anon is None or not _ANON_ID.fullmatch(x_anyplot_anon):
        raise AgentHTTPError(400, "anon_required")
    return PublicIdentity(anon_id=x_anyplot_anon, network=client_network(request))


def public_context(
    response: Response,
    identity: PublicIdentity = Depends(require_public_identity),
    config: AgentConfig = Depends(require_public_enabled),
) -> AgentContext:
    """Mint the request id (returned as `X-Request-Id`) and assert the public tier for this identity."""
    request_id = str(uuid.uuid4())
    response.headers["X-Request-Id"] = request_id
    response.headers["Cache-Control"] = _NO_STORE
    return AgentContext(
        base_url=config.service_url,
        user_id=identity.anon_id,
        request_id=request_id,
        tier="public",
        network=identity.network,
        case_user="pub_" + _salted("case", identity.anon_id),
    )


@dataclass
class PublicStreams:
    """The public chat turns this instance relays right now, at most `AGENT_PUBLIC_MAX_STREAMS`.

    Every turn holds one of the instance's request slots (`--concurrency`) for as long as it streams, up to
    `AGENT_TURN_MAX_S`, and the catalogue shares those slots. One asyncio loop drives the count; nothing is locked.
    """

    open: int = 0

    def take(self) -> bool:
        if self.open >= settings.agent_public_max_streams:
            return False
        self.open += 1
        return True

    def release(self) -> None:
        self.open = max(self.open - 1, 0)


PUBLIC_STREAMS = PublicStreams()


@dataclass
class FeedbackLimiter:
    """Feedback cases per network and hour, `AGENT_PUBLIC_FEEDBACK_PER_HOUR`, in this process's memory only.

    A case stores the session in the private bucket and a row in `agent_feedback`, so a page that loops over the
    button would fill both. The key is the network salted with this process's salt; a network without a case in
    the last hour is forgotten.
    """

    window_s: float = FEEDBACK_WINDOW_S
    clock: Callable[[], float] = time.monotonic
    sent: dict[str, deque[float]] = field(default_factory=dict)

    def allow(self, network: str) -> bool:
        """Whether the network may store one more case now; counts it when it may."""
        now = self.clock()
        for key in [key for key, times in self.sent.items() if not times or now - times[-1] >= self.window_s]:
            del self.sent[key]
        times = self.sent.setdefault(_salted("feedback", network), deque())
        while times and now - times[0] >= self.window_s:
            times.popleft()
        if len(times) >= settings.agent_public_feedback_per_hour:
            return False
        times.append(now)
        return True


FEEDBACK_LIMITER = FeedbackLimiter()


def get_feedback_limiter() -> FeedbackLimiter:
    """The process's feedback limiter; tests override it with a fresh one."""
    return FEEDBACK_LIMITER


router = APIRouter(
    prefix="/agent",
    tags=["agent-public"],
    # The door first, so a closed lane answers 404 to everything; then the CSRF guard and the body checks the admin
    # lane runs too (`api/routers/agent.py`). The identity is each route's own (`public_context`): `GET /lane` needs
    # none.
    dependencies=[
        Depends(require_public_enabled),
        Depends(require_same_site_client),
        Depends(require_body_within_cap),
        Depends(require_utf8_body),
    ],
)

Ctx = Annotated[AgentContext, Depends(public_context)]
Client = Annotated[httpx.AsyncClient, Depends(get_agent_client)]
Cases = Annotated[CaseBucket, Depends(get_case_bucket)]
Db = Annotated[AsyncSession, Depends(require_db)]
SessionId = Annotated[str, Header(alias="X-Anyplot-Session", pattern=SESSION_ID_PATTERN)]
"""The session id, in a header: Cloud Run logs every URL with the client's address."""
HumanToken = Annotated[str | None, Header(alias=turnstile.TOKEN_HEADER)]
"""The page's Turnstile token for this one call; checked by `require_human`."""
Siteverify = Annotated[httpx.AsyncClient, Depends(turnstile.get_turnstile_client)]


async def require_human(token: str | None, client: httpx.AsyncClient, ctx: AgentContext) -> None:
    """Redeem the call's Turnstile token: `403 bot_check_failed` or `503 bot_check_unavailable` unless it passes.

    Called inside the route, after its body and identity are validated, so a malformed request costs no
    siteverify call.
    """
    refused = turnstile.refusal(await turnstile.verify(token, client))
    if refused is not None:
        raise AgentHTTPError(refused[0], refused[1], ctx.request_id)


class PublicCreateSessionBody(BaseModel):
    """`POST /agent/sessions`: the admin body without `source`, which only the admin's fan-out sets."""

    model_config = ConfigDict(extra="forbid")

    spec_id: SpecId
    library: LibraryId
    locale: Locale


# ============================================================================
# Routes
# ============================================================================


@router.get("/lane")
async def lane(response: Response) -> dict[str, bool]:
    """Whether the public lane is open: `{"open": true}`, or the router's 404 while it is closed.

    No identity and no upstream call, so the landing page and every spec page can ask; cacheable for a minute.
    """
    response.headers["Cache-Control"] = f"public, max-age={_LANE_MAX_AGE_S}"
    return {"open": True}


@router.get("/status")
async def status(ctx: Ctx, client: Client) -> dict[str, Any]:
    """The agents service's status as the public page needs it (`PUBLIC_STATUS_FIELDS`), plus `enabled`."""
    answer = await agent.agent_status(ctx, client)
    return {key: value for key, value in answer.items() if key in PUBLIC_STATUS_FIELDS}


@router.get("/eligibility")
async def eligibility(
    ctx: Ctx,
    client: Client,
    response: Response,
    spec: Annotated[str, Query(pattern=SPEC_ID_PATTERN)],
    library: Annotated[LibraryId, Query()],
) -> Any:
    """Whether the page may offer the chat for this pair; the agents service decides.

    The plot page asks on every visit, crawlers that render it too, and the answer is the same for every
    caller, so browsers may keep it for five minutes (`_ELIGIBILITY_MAX_AGE_S`)."""
    answer = await agent.agent_eligibility(ctx, client, spec, library)
    response.headers["Cache-Control"] = f"public, max-age={_ELIGIBILITY_MAX_AGE_S}"
    return answer


@router.post("/sessions")
async def create_session(
    body: PublicCreateSessionBody, ctx: Ctx, client: Client, db: Db, siteverify: Siteverify, human: HumanToken = None
) -> Any:
    """Open a chat session: `{session_id, eligibility, roles}`. The page keeps the id and sends it as
    `X-Anyplot-Session`.

    Needs a Turnstile token (`require_human`), checked before the agents service is asked.
    """
    await require_human(human, siteverify, ctx)
    admin_body = CreateSessionBody(spec_id=body.spec_id, library=body.library, locale=body.locale)
    return await agent.create_session(admin_body, ctx, client, db)


@router.delete("/session", status_code=204)
async def delete_session(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Purge the session, its data and its renders."""
    return await agent.delete_session(sid, ctx, client)


@router.post("/session/library")
async def switch_library(sid: SessionId, body: SwitchLibraryBody, ctx: Ctx, client: Client, db: Db) -> Any:
    """Switch the session to another library; the data, the bindings and the plot memory stay."""
    return await agent.switch_library(sid, body, ctx, client, db)


@router.get("/session/memory")
async def get_memory(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """The plot memory the page lists."""
    return await agent.get_memory(sid, ctx, client)


@router.delete("/session/memory")
async def forget_all_memory(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Forget every entry of the plot memory."""
    return await agent.forget_all_memory(sid, ctx, client)


@router.delete("/session/memory/{entry_id}")
async def delete_memory_entry(
    sid: SessionId, entry_id: Annotated[str, Path(pattern=MEMORY_ENTRY_ID_PATTERN)], ctx: Ctx, client: Client
) -> Any:
    """Remove one entry of the plot memory."""
    return await agent.delete_memory_entry(sid, entry_id, ctx, client)


@router.post("/session/dataset")
async def upload_dataset(sid: SessionId, body: DatasetBody, ctx: Ctx, client: Client) -> Any:
    """Parse pasted data, as the admin lane's route."""
    return await agent.upload_dataset(sid, body, ctx, client)


@router.post("/session/dataset/convert")
async def convert_dataset_file(sid: SessionId, request: Request, ctx: Ctx, client: Client) -> Any:
    """Read a dropped binary data file into text, as the admin lane's route (5 MB raw at most)."""
    return await agent.convert_dataset_file(sid, request, ctx, client)


@router.put("/session/bindings")
async def put_bindings(
    sid: SessionId, bindings: Annotated[list[Binding], Body(max_length=50)], ctx: Ctx, client: Client
) -> Any:
    """Replace the role-to-column bindings."""
    return await agent.put_bindings(sid, bindings, ctx, client)


@router.put("/session/language")
async def put_language(sid: SessionId, body: LanguageBody, ctx: Ctx, client: Client) -> Any:
    """Set the session language."""
    return await agent.put_language(sid, body, ctx, client)


@router.post("/session/dataset/confirm")
async def confirm_dataset(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Step 1 of two: the user confirms the data and its bindings."""
    return await agent.confirm_dataset(sid, ctx, client)


@router.post("/session/dataset/undo")
async def undo_dataset(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Undo the assistant's last change to the data."""
    return await agent.undo_dataset(sid, ctx, client)


@router.post("/session/dataset/to_long")
async def dataset_to_long(sid: SessionId, ctx: Ctx, client: Client) -> Any:
    """Make a wide table long for the spec's roles, without a model call."""
    return await agent.dataset_to_long(sid, ctx, client)


@router.get("/session/dataset/data.csv")
async def get_dataset_csv(sid: SessionId, request: Request, ctx: Ctx, client: Client) -> Response:
    """The current data version's `data.csv`, read-only."""
    return await agent.get_dataset_csv(sid, request, ctx, client)


async def open_public_message_stream(
    sid: SessionId, body: MessageBody, ctx: Ctx, client: Client, theme: Literal["light", "dark"] | None = None
) -> AsyncIterator[UpstreamStream]:
    """Take one of the instance's public stream slots (`503 capacity` when none is free), then open the upstream
    stream as the admin lane does (`agent.open_message_stream`). The slot is freed when the stream ends."""
    if not PUBLIC_STREAMS.take():
        raise AgentHTTPError(503, "capacity", ctx.request_id)
    try:
        async with aclosing(agent.open_message_stream(sid, body, ctx, client, theme)) as streams:
            async for upstream in streams:
                yield upstream
    finally:
        PUBLIC_STREAMS.release()


@router.post("/session/messages", response_class=EventSourceResponse)
async def post_message(
    upstream: UpstreamStream = Depends(open_public_message_stream),
) -> AsyncIterator[ServerSentEvent]:
    """Relay one chat turn as SSE `anyplot/1`, as the admin lane does; always ends with a `done` event."""
    async with aclosing(agent.relay_turn(upstream)) as events:
        async for event in events:
            yield event


async def open_public_turn_stream(
    sid: SessionId, last_event_id: LastEventId, ctx: Ctx, client: Client
) -> AsyncIterator[UpstreamStream]:
    """A public stream slot, as for a turn (`open_public_message_stream`), then the upstream read of the session's
    latest turn as the admin lane opens it (`agent.open_turn_stream`). The run id travels in `Last-Event-ID`, a
    header like the session id, never in the URL."""
    if not PUBLIC_STREAMS.take():
        raise AgentHTTPError(503, "capacity", ctx.request_id)
    try:
        async with aclosing(agent.open_turn_stream(sid, last_event_id, ctx, client)) as streams:
            async for upstream in streams:
                yield upstream
    finally:
        PUBLIC_STREAMS.release()


@router.get("/session/turn", response_class=EventSourceResponse)
async def get_turn(upstream: UpstreamStream = Depends(open_public_turn_stream)) -> AsyncIterator[ServerSentEvent]:
    """The rest of the session's latest turn for a page that lost its stream, as the admin lane relays it."""
    async with aclosing(agent.relay_turn(upstream)) as events:
        async for event in events:
            yield event


@router.post("/session/cancel", status_code=204)
async def cancel_run(sid: SessionId, ctx: Ctx, client: Client) -> Response:
    """Stop the session's active run."""
    return await agent.cancel_run(sid, ctx, client)


@router.post("/session/outcome", status_code=204)
async def post_outcome(sid: SessionId, body: OutcomeBody, ctx: Ctx, client: Client) -> Response:
    """The page's content-free outcome beacon."""
    return await agent.post_outcome(sid, body, ctx, client)


@router.post("/session/versions/{version}/render")
async def render_version_theme(
    sid: SessionId,
    version: Annotated[int, Path(ge=0, le=MAX_AGENT_VERSION)],
    body: RenderThemeBody,
    ctx: Ctx,
    client: Client,
) -> Any:
    """The theme toggle: render the other theme of a finished version, with no model call."""
    return await agent.render_version_theme(sid, version, body, ctx, client)


@router.get("/session/artifacts/{name}")
async def get_artifact(
    sid: SessionId,
    name: str,
    ctx: Ctx,
    client: Client,
    v: Annotated[int | None, Query(ge=0, le=MAX_AGENT_VERSION)] = None,
    theme: Literal["light", "dark"] | None = None,
) -> Response:
    """Stream one result file; only the allowlisted names exist."""
    return await agent.get_artifact(sid, name, ctx, client, v, theme)


@router.post("/session/feedback", status_code=201)
async def submit_feedback(
    sid: SessionId,
    body: FeedbackBody,
    ctx: Ctx,
    client: Client,
    cases: Cases,
    db: Db,
    limiter: Annotated[FeedbackLimiter, Depends(get_feedback_limiter)],
    siteverify: Siteverify,
    human: HumanToken = None,
) -> dict[str, Any]:
    """Store the feedback case the user sent, as the admin lane does: `201 {case_id, stored}`.

    `include_data` carries the user's consent to store the data with the case; the page leaves it unticked. The
    token comes first (`require_human`), so a script without one cannot spend the hourly cases of a network it
    shares with real visitors; then a network past `AGENT_PUBLIC_FEEDBACK_PER_HOUR` cases gets `429 rate_limited`
    before the bundle is fetched.
    """
    await require_human(human, siteverify, ctx)
    if ctx.network is None or not limiter.allow(ctx.network):
        raise AgentHTTPError(429, "rate_limited", ctx.request_id)
    return await agent.submit_feedback(sid, body, ctx, client, cases, db)
