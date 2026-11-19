"""Where a promoted feedback case may replay: on the model route its sender was told about.

A visitor can send feedback on a chat and tick a box that adds the whole data file. Until the
deploy of 2026-11-18 14:13 UTC the consent line under the form said the case was stored "for
the operator to read", and the only AI recipient the site named anywhere was Claude by
Anthropic, served through Google Cloud Vertex AI in the EU. Since that deploy it also says the
operator reads a case "with ai coding assistants and in tests with other ai models". So:

* a promoted case sent before `CUTOFF` (2026-11-19T00:00:00Z, the first midnight after the new
  wording was live) is *pinned*: it replays only on Claude through Vertex AI in location `eu`.
  The pin is on what the sentence named, the provider, the transport and the location, not on
  a model id: another Claude model on Vertex AI in `eu` is the same route;
* so is a case that corrects one sent before the cut-off (`replaces`): a session lives in one
  page load, so the correction came from a tab that showed the old consent line;
* a promoted case sent at or after the cut-off may replay on any route;
* so may a case from the admin lane (`lane: "admin"`, which the importer reads from the
  prefix the BFF gives every admin's user id, `ADMIN_LANE_PREFIX`), and a case marked as
  holding the operator's own data (`owner_chat`, which only `import_case.py --owner-chat`
  writes; a saved session has no manifest and so no lane). The lane says who held the admin
  door, one shared id for every holder of the admin token, not whose data was pasted;
* the committed fixtures are synthetic and replay anywhere.

The check fails closed. A promoted case whose `case.json` records no `sent_at`, or a send time
later than now, is pinned: every case imported before the field existed, and every saved session
bundle, which records no send time. So is one that records no `replaces_sent_at`, or records it
as `unknown`. A case without a lane, or with a `user_hash` of neither known form, is no admin case.
A matrix report's run record whose origin, send time, lane or correction is missing counts the
same way.

`routes_of` resolves every model a matrix run calls from the settings the agents are built
from (after the flags, the environment and the defaults): the root, the adapter and the reviewer
(`models.model_for`) and the scope and dataset judge, each with an endpoint override from the
environment that the Claude client would take ahead of the region (`ENDPOINT_OVERRIDES`).
`checked_routes` also compares them with the agents as `agents.anyplot` built them at import,
and refuses a run whose agents were built for another configuration. The pin is the constant
route the site named, never the route a case's own chat recorded. `check` compares the routes
with the pin and raises `ReplayRefused`, whose message names each pinned case, the pinned route
and each of the run's routes that leaves it, with what leaves it. `cases.select_cases` runs the
check, so every tool that selects eval cases names where their data goes; `score.py` runs it on
the records of the report it scores.

This module imports nothing from `agents.anyplot` at module level: `matrix.py` imports the
agents only after `configure` has written the environment the settings read.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, Literal, Protocol, get_args


if TYPE_CHECKING:
    from agents.anyplot.settings import AgentSettings


CUTOFF: Final = datetime(2026, 11, 19, 0, 0, 0, tzinfo=UTC)
"""A promoted case sent before this second replays only on the pinned route."""
SENT_AT_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"
"""The form of `sent_at` in `case.json` and in a run record: the manifest's `created_at`
(`core.agent_cases._CREATED_AT_FORMAT`; a test holds the two equal)."""
_SENT_AT: Final = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
"""`SENT_AT_FORMAT` in ASCII digits and capitals, padded: `strptime` alone also takes lower case, unpadded fields and
other scripts' digits."""
CASE_ID: Final = re.compile(r"(?P<time>[0-9]{8}T[0-9]{6}Z)-[0-9a-f]{8}")
"""A stored case's id (`core.agent_cases.CASE_ID_PATTERN`), whose first part is the second it was sent."""
UNKNOWN: Final = "unknown"
"""`replaces_sent_at` of a case whose manifest names a replaced case whose time cannot be read."""
PINNED_PROVIDER: Final = "anthropic-vertex"
PINNED_TRANSPORT: Final = "vertex"
PINNED_LOCATION: Final = "eu"
PINNED_FAMILY: Final = "claude-"
"""The model ids Claude has on Vertex AI (`settings.MODEL_PREFIXES`)."""
PINNED_ROUTE: Final = "Claude by Anthropic through Vertex AI in location eu"
PINNED_TERMS: Final = (
    f"provider {PINNED_PROVIDER}, transport {PINNED_TRANSPORT}, location {PINNED_LOCATION}, a {PINNED_FAMILY}* model, "
    "no endpoint override"
)
SKIP_FLAG: Final = "--skip-pinned"
"""The flag of `matrix.py` and `score.py` that leaves the pinned cases out and runs the rest."""
ENDPOINT_OVERRIDES: Final = ("ANTHROPIC_VERTEX_BASE_URL",)
"""The environment variables the Claude-on-Vertex client takes as its endpoint ahead of the region it is given
(`anthropic.lib.vertex`): no client of the agent network passes a base URL, so a set one sends every call there."""

Lane = Literal["admin", "public"]
"""The BFF lane that served a stored case's chat, as `case.json` records it."""
LANES: Final[tuple[str, ...]] = get_args(Lane)
ADMIN_LANE_PREFIX: Final = "adm_"
"""How every user id of the admin lane starts (`api.routers.agent.derive_user_id`), on the Cloudflare Access path
and the admin token's alike; the admin lane stores that id as the case's `user_hash`."""
PUBLIC_LANE_PREFIX: Final = "pub_"
"""How the public lane's case user starts (`api.routers.agent_public.public_context`), a salted hash of the tab id.
Both prefixes are written here once, and `tests/unit/api/test_agent_case_lanes.py` holds them to the API's."""
_LANE_IDS: Final[dict[Lane, re.Pattern[str]]] = {
    "admin": re.compile(re.escape(ADMIN_LANE_PREFIX) + r"[0-9a-f]{16}"),
    "public": re.compile(re.escape(PUBLIC_LANE_PREFIX) + r"[0-9a-f]{16}"),
}
Replaces = datetime | Literal["unknown"] | None
"""What a case corrects: the send time of the case it replaces, `unknown`, or None when it replaces none."""


@dataclass(frozen=True)
class Route:
    """One model a run calls, as the run resolved it."""

    role: str
    """Who calls it: `root`, `adapter`, `reviewer`, `judge` or `scorer`."""
    model: str
    provider: str
    """The client family: `anthropic-vertex` (Claude on Vertex AI) or `gemini`."""
    transport: str
    """How the calls travel: `vertex`, or `claude-cli`, the local Claude Code CLI on the developer's subscription,
    which sends them to Anthropic's own API and not through Vertex AI."""
    location: str
    endpoint: str | None = None
    """The set endpoint override (`ENDPOINT_OVERRIDES`) the call would go to instead, by its variable's name."""

    def departures(self) -> list[str]:
        """What takes this route off the pin, one clause each; empty on the pinned route."""
        found: list[str] = []
        if self.provider != PINNED_PROVIDER:
            found.append("the provider is not Claude on Vertex AI")
        if not self.model.startswith(PINNED_FAMILY):
            found.append("the model is not a Claude model")
        if self.transport != PINNED_TRANSPORT:
            found.append("the transport is not Vertex AI")
        if self.location != PINNED_LOCATION:
            found.append(f"the location is not {PINNED_LOCATION}")
        if self.endpoint is not None:
            found.append(f"{self.endpoint} sends the calls to another endpoint")
        return found

    @property
    def keeps_pin(self) -> bool:
        """Whether a pinned case's data may take this route."""
        return not self.departures()

    def describe(self) -> str:
        where = f"provider {self.provider}, transport {self.transport}, location {self.location}"
        if self.endpoint is not None:
            where += f", endpoint from {self.endpoint}"
        return f"{self.role} {self.model}: {where}"


class _NoModelCall:
    """The routes of a caller that calls no model: the static stage, the preflight's catalogue renders."""

    def __repr__(self) -> str:
        return "NO_MODEL_CALL"


NO_MODEL_CALL: Final = _NoModelCall()
"""Passed as `routes` by a caller that calls no model. An empty route list is refused instead, so that a resolver
that found nothing never reads as a run without a model."""
Routes = Sequence[Route] | _NoModelCall


class Replayable(Protocol):
    """What the rule reads of a case: an `EvalCase`, or the facts of a run record (`RecordFacts`)."""

    @property
    def case_id(self) -> str: ...

    @property
    def origin(self) -> str | None: ...

    @property
    def sent_at(self) -> datetime | None: ...

    @property
    def lane(self) -> str | None: ...

    @property
    def owner_chat(self) -> bool: ...

    @property
    def replaces(self) -> Replaces: ...

    @property
    def saved_session(self) -> bool: ...


@dataclass(frozen=True)
class RecordFacts:
    """The facts a matrix run record carries about its case, for `score.py`."""

    case_id: str
    origin: str | None
    sent_at: datetime | None
    lane: str | None
    owner_chat: bool
    replaces: Replaces
    saved_session: bool


def lane_of(user_hash: Any) -> Lane | None:
    """The lane a stored case's `user_hash` says served its chat; None for a value of neither lane's exact form.

    Only the form the BFF writes counts (the prefix and 16 hex digits), so a value that merely starts like an admin
    id is no admin case. The value itself is never kept: `case.json` records the lane alone.
    """
    if not isinstance(user_hash, str):
        return None
    for lane, pattern in _LANE_IDS.items():
        if pattern.fullmatch(user_hash):
            return lane
    return None


def parse_sent_at(value: Any) -> datetime:
    """`sent_at` as an aware UTC time; ValueError for anything but `YYYY-MM-DDTHH:MM:SSZ` in ASCII digits, padded, with
    a capital T and Z."""
    if not isinstance(value, str) or not _SENT_AT.fullmatch(value):
        raise ValueError("sent_at must be YYYY-MM-DDTHH:MM:SSZ")
    return datetime.strptime(value, SENT_AT_FORMAT).replace(tzinfo=UTC)


def format_sent_at(value: datetime) -> str:
    return value.astimezone(UTC).strftime(SENT_AT_FORMAT)


def replaced_sent_at(replaces: Any) -> Replaces:
    """When the case a manifest's `replaces` names was sent: the time its id begins with, None for no replaced case,
    `UNKNOWN` for a value that is not a case id or whose time cannot be read. Only the time is kept, never the id."""
    if replaces is None:
        return None
    match = CASE_ID.fullmatch(replaces) if isinstance(replaces, str) else None
    if match is None:
        return UNKNOWN
    try:
        return datetime.strptime(match.group("time"), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError:
        return UNKNOWN


def parse_replaces(value: Any, *, present: bool) -> Replaces:
    """`replaces_sent_at` of `case.json` or of a run record: absent or `unknown` is `UNKNOWN`, null is no replaced case,
    else a send time in the exact form; ValueError for any other value."""
    if not present or value == UNKNOWN:
        return UNKNOWN
    if value is None:
        return None
    return parse_sent_at(value)


def format_replaces(value: Replaces) -> str | None:
    return format_sent_at(value) if isinstance(value, datetime) else value


def record_facts(record: dict[str, Any]) -> RecordFacts:
    """The facts of one run record. A missing or malformed value reads as pinned."""
    origin = record.get("origin")
    lane = record.get("lane")
    try:
        sent_at: datetime | None = parse_sent_at(record.get("sent_at"))
    except ValueError:
        sent_at = None
    try:
        replaces = parse_replaces(record.get("replaces_sent_at"), present="replaces_sent_at" in record)
    except ValueError:
        replaces = UNKNOWN
    return RecordFacts(
        case_id=str(record.get("case_id")),
        origin=origin if isinstance(origin, str) else None,
        sent_at=sent_at,
        lane=lane if lane in LANES else None,
        owner_chat=record.get("owner_chat") is True,
        replaces=replaces,
        saved_session=record.get("saved_session") is True,
    )


def is_pinned(case: Replayable, *, now: datetime | None = None) -> bool:
    """Whether the case replays only on the pinned route: a promoted case, neither from the admin lane nor marked as
    the operator's own, that was sent before the cut-off, records no send time or one later than `now`, or corrects a
    case sent before the cut-off or one it cannot name. A committed fixture never is."""
    now = now or datetime.now(UTC)
    if case.origin == "fixtures":
        return False
    if case.owner_chat is True or case.lane == "admin":
        return False
    replaces = case.replaces
    if replaces == UNKNOWN or (isinstance(replaces, datetime) and (replaces < CUTOFF or replaces > now)):
        return True
    return case.sent_at is None or case.sent_at < CUTOFF or case.sent_at > now


def _reason(case: Replayable, now: datetime) -> str:
    if case.origin not in ("fixtures", "promoted"):
        return "its origin is not recorded"
    if case.saved_session:
        return "a saved session, which records no send time and no lane"
    if case.sent_at is None:
        when = "no send time recorded"
    elif case.sent_at > now:
        when = f"a send time later than now ({format_sent_at(case.sent_at)})"
    else:
        when = f"sent {format_sent_at(case.sent_at)}"
    parts = [when, "from the public lane" if case.lane == "public" else "no lane recorded"]
    if case.replaces == UNKNOWN:
        parts.append("no readable record of whether it corrects an earlier case")
    elif isinstance(case.replaces, datetime) and (case.replaces < CUTOFF or case.replaces > now):
        parts.append(f"it corrects a case sent {format_sent_at(case.replaces)}")
    return ", ".join(parts)


def _missing(case: Replayable) -> bool:
    """Whether importing the case again could add what pins it: a stored case imported before the fields existed."""
    return not case.saved_session and (case.sent_at is None or case.lane is None or case.replaces == UNKNOWN)


def _cases(count: int) -> str:
    return "1 pinned eval case" if count == 1 else f"{count} pinned eval cases"


class ReplayRefused(Exception):
    """A run would send pinned cases to a route their senders were not told about; the message says which and where."""

    def __init__(self, cases: Iterable[Replayable], routes: Iterable[Route], *, now: datetime | None = None) -> None:
        unique: dict[str, Replayable] = {}
        for case in cases:
            unique.setdefault(case.case_id, case)
        self.cases: tuple[Replayable, ...] = tuple(unique.values())
        self.routes: tuple[Route, ...] = tuple(routes)
        self.now = now or datetime.now(UTC)
        super().__init__(self._message())

    def _message(self) -> str:
        count = len(self.cases)
        them = "it" if count == 1 else "them"
        lines = [
            f"{_cases(count)} may replay only on {PINNED_ROUTE}, and this run would send {them} elsewhere.",
            f"A promoted case sent before {format_sent_at(CUTOFF)}, or without a recorded send time, keeps to the "
            "route its sender was told about, and so does a correction of such a case, unless it comes from the admin "
            "lane or you marked its data as your own.",
            *(f"  {case.case_id}: {_reason(case, self.now)}." for case in self.cases),
            "This run resolved "
            + ("this model call" if len(self.routes) == 1 else "these model calls")
            + " to another route:",
            *(f"  {route.describe()} ({'; '.join(route.departures())})." for route in self.routes),
            f"Run on the pinned route ({PINNED_TERMS}), or pass {SKIP_FLAG} to leave the pinned cases out.",
        ]
        if any(_missing(case) for case in self.cases):
            lines.append(
                "A stored case imported before these fields existed gets them when you import it again: python -m "
                "agents.evals.sync_cases --force, or python -m agents.evals.import_case <case directory> --force; a "
                "report gets them from a new matrix run."
            )
        return "\n".join(lines)

    def left_out(self) -> str:
        """The line a run prints to stderr when `--skip-pinned` left these cases out; no written file holds the ids."""
        ids = ", ".join(case.case_id for case in self.cases)
        return f"left out {_cases(len(self.cases))} ({SKIP_FLAG}), which replay only on {PINNED_ROUTE}: {ids}"


def check(cases: Iterable[Replayable], routes: Routes, *, now: datetime | None = None) -> None:
    """Raise `ReplayRefused` when a pinned case among `cases` would take a route of `routes` that leaves the pin.

    `routes` is every model route the caller sends the cases' data to, or `NO_MODEL_CALL`.
    """
    if isinstance(routes, _NoModelCall):
        return
    resolved = tuple(routes)
    if not resolved:
        raise ValueError("no model route given; a caller that calls no model passes NO_MODEL_CALL")
    leaving = [route for route in resolved if not route.keeps_pin]
    if not leaving:
        return
    pinned = [case for case in cases if is_pinned(case, now=now)]
    if pinned:
        raise ReplayRefused(pinned, leaving, now=now)


def endpoint_override(environ: Mapping[str, str] | None = None) -> str | None:
    """The name of the first set endpoint override (`ENDPOINT_OVERRIDES`), or None."""
    environ = os.environ if environ is None else environ
    return next((name for name in ENDPOINT_OVERRIDES if environ.get(name, "").strip()), None)


def cli_transport(role: str) -> str:
    """The transport a role's calls take on `claude-cli`: the CLI answers every structured call and hands the root's
    chat with tools to Vertex AI (`cli_transport.ClaudeCliClient`, its fallback)."""
    return PINNED_TRANSPORT if role == "root" else "claude-cli"


def routes_of(settings: AgentSettings, environ: Mapping[str, str] | None = None) -> tuple[Route, ...]:
    """Every model a matrix run calls, resolved from the settings the agents and the judge are built from.

    `models.make_model` builds the root, the adapter and the reviewer, each on `model_for(kind)`, and
    `models.make_judge_client` the scope and dataset judge on `judge_model`; all of them on the settings' provider,
    transport and location, and every Claude client takes an endpoint override from the environment.
    """
    from agents.anyplot.models import MODEL_KINDS, model_for

    endpoint = endpoint_override(environ)

    def route(role: str, model: str) -> Route:
        transport = cli_transport(role) if settings.transport == "claude-cli" else settings.transport
        on_vertex = settings.provider == PINNED_PROVIDER and transport == PINNED_TRANSPORT
        return Route(role, model, settings.provider, transport, settings.location, endpoint if on_vertex else None)

    return (*(route(kind, model_for(kind, settings)) for kind in MODEL_KINDS), route("judge", settings.judge_model))


class RoutesDiffer(ValueError):
    """The agents were built for another configuration than the one the run checked; the message says how."""


def built_routes(environ: Mapping[str, str] | None = None) -> tuple[Route, ...]:
    """The routes of the agents as `agents.anyplot` built them at import: the root, each adapter and the reviewer.

    The judge is not among them: `services.judge_factory` builds it from the settings when it is first used.
    """
    from google.adk.models.google_llm import Gemini

    from agents.anyplot import agent
    from agents.anyplot.models import VertexClaude
    from agents.anyplot.sub_agents.adapter import ADAPTERS
    from agents.anyplot.sub_agents.reviewer import reviewer

    endpoint = endpoint_override(environ)
    built = [("root", agent.root_agent.model), *(("adapter", item.model) for item in ADAPTERS.values())]
    built.append(("reviewer", reviewer.model))
    routes: list[Route] = []
    for role, model in built:
        if isinstance(model, VertexClaude):
            transport = cli_transport(role) if model.transport_client is not None else PINNED_TRANSPORT
            claude_endpoint = endpoint if transport == PINNED_TRANSPORT else None
            routes.append(Route(role, model.model, PINNED_PROVIDER, transport, model.vertex_region, claude_endpoint))
        elif isinstance(model, Gemini):
            location = str((model.client_kwargs or {}).get("location"))
            routes.append(Route(role, model.model, "gemini", PINNED_TRANSPORT, location))
        else:
            name = getattr(model, "model", type(model).__name__)
            routes.append(Route(role, str(name), type(model).__name__, "unknown", "unknown"))
    return tuple(routes)


def checked_routes(settings: AgentSettings, environ: Mapping[str, str] | None = None) -> tuple[Route, ...]:
    """`routes_of(settings)`, once the agents as built match it role by role; `RoutesDiffer` otherwise.

    The agents are built when `agents.anyplot` is first imported, from the settings of that moment; a process that
    imported them under one configuration and checks another would check models the run does not call.
    """
    routes = routes_of(settings, environ)
    by_role = {route.role: route for route in routes}
    differing = [
        (built, by_role[built.role])
        for built in built_routes(environ)
        if built.role in by_role and built != by_role[built.role]
    ]
    if differing:
        lines = [
            "the agents were built for another configuration than the one this run checked, so the check would be "
            "about models the run does not call:",
            *(f"  built {built.describe()}; checked {checked.describe()}." for built, checked in differing),
            "Start the run in a fresh process, such as python -m agents.evals.matrix, so the agents are built from "
            "its settings.",
        ]
        raise RoutesDiffer("\n".join(lines))
    return routes
