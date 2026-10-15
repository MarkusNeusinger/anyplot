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
| `POST /v1/sessions/{sid}/dataset` | `{text, confirmed?, source?, table?}` (`source`: the name of the file the page read the text from, at most 1,024 characters; screened on its own, never a note; `table`: 1 to 10, which of several tables in the text to read, from the previous answer's `tables`) | `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version, language, file_name?, tables?, table?}` (`file_name`: the dropped file's name as the session keeps it, `(name withheld)` when the screen refused it; `tables`: one label per table, its header names and its row count, when the text held two or more tables each under its own header after a blank line, and `table` the one read, see `data/parse.py` `_one_table`;`suggestion`: the wide-table offer of `data/shape.py`, or null; `context_lines`: the notes pasted above or below the table that passed the pre-filter and the scope judge, which the root gets with the next `summarize_data` turn; `language`: the session language as `{language, source}`, which a paste before any typed message or choice sets from the notes' or the column names' language, source `pasted`), stored as version 1 (the undo history of an earlier paste is dropped); or, for free text, `{transcribed, text, preview, profile, warnings, note}`, not stored (`confirmed: true` skips that fallback and keeps every row) | `413 too_long`, `422 unparseable` (both with `cause`, the parser's sentence naming what the data fails on, at most 300 characters), `422 formula` (text of at most 2,000 characters that asks for a formula, which the chat's `generate_data` computes; never transcribed), `403 data_refused`, `403 session_closed` (the scope judge closed the session), `409 run_active` (a turn of the user in any session, or another paste of the user in flight), `429 rate_limited` / `429 daily_limit` (`AGENT_USER_PASTES_PER_MINUTE` / `_PER_DAY`, or the daily token budgets for `daily_limit`), `429 locked_out` (the day's `attack` strikes), `503 guard_unavailable` |
| `POST /v1/sessions/{sid}/dataset/convert` | `{data_base64, sheet?}` (a dropped Excel, OpenDocument, Parquet, Feather, Arrow or NumPy file, at most 5 MiB; `sheet` a sheet or `.npz` array the previous answer named) | `{text, format, kind, rows, columns, sheet, sheets, sheet_count, warnings, dropped}`: the file read in the renderer's sandbox (`harness.py --convert`) into the text the paste box takes (CSV, or JSON records for a table with list columns, `format`), every value with the precision it came with, the sheet read and at most 10 visible ones with cells (`sheet_count` all of them), `warnings` counts (`formulas_without_value`, `hidden_sheets`, `dropped_columns`, `list_columns`, `utc_timestamps`, `renamed_columns`), `dropped` the names of the columns left out; nothing stored, no model call | `413 too_long`, `422 invalid`, `422 file_<refusal>` (`wire.CONVERT_REASONS`, with `measured` and `limit` for a broken cap) and `file_timeout`, `file_too_complex` (also a reader that died without its `status.json`), `file_too_large`, `file_unreadable`, `403 session_closed`, `409 run_active` (another conversion of the user in flight), `429 rate_limited` / `429 daily_limit` (`AGENT_USER_CONVERSIONS_PER_MINUTE` / `_PER_DAY`, or the daily token budgets), `429 locked_out`, `503 capacity` (no render slot within `AGENT_CONVERT_SLOT_WAIT_S`), `503 convert_unavailable` (no renderer, or one without `/convert`) |
| `PUT /v1/sessions/{sid}/bindings` | `[{role, column}]` | `{bindings, complete, missing_roles, warnings}`: `warnings` names a role that needs values of 0 or more bound to a column with a negative value, or left open for that reason (`data/signs.py`); never a refusal | `409 run_active`, `422 invalid` (with `errors`, at most 20 lines) |
| `PUT /v1/sessions/{sid}/language` | `{language}` (a short name or code, `^[A-Za-z][A-Za-z -]{0,39}$`) | `{language, source}`: the session language in its stored form (`English` is `en`), source `chosen`, which detection never overrides | `409 run_active`, `422` (the pattern) |
| `POST /v1/sessions/{sid}/dataset/confirm` | | `{confirmed, rows, columns}`: step 1 of two, the user confirmed the dataset with its bindings; the pipeline runs only then | `409 run_active`, `422 no_dataset` |
| `POST /v1/sessions/{sid}/dataset/undo` | | `{preview, profile, bindings, warnings, context_lines, roles, suggestion, version}`: the dataset version before the root's last `prepare_data` or `generate_data` is the current one again, its bindings carried over (`dataset_versions.py`); unconfirmed, like any version the user has not confirmed | `409 run_active`, `422 nothing_to_undo` |
| `POST /v1/sessions/{sid}/dataset/to_long` | | The undo route's shape plus `changes`: the page's `.to_long()` applies the wide-table suggestion, recomputed on the server, as the next dataset version with the default bindings for the new columns; no model call | `409 run_active`, `422 no_suggestion` |
| `POST /v1/sessions/{sid}/messages` | `{text}` or `{action}` (`create_plot`, `summarize_data`) | SSE `anyplot/1`; the `done` event carries `dataset` (with `roles` and `changes`) after a turn whose `prepare_data` or `generate_data` changed the data, version 1 when `generate_data` made the session's first data, and `language` (`{language, source}`) after every run | `413 too_long`, `409 run_active` |
| `POST /v1/sessions/{sid}/cancel` | | `204` | |
| `POST /v1/sessions/{sid}/versions/{version}/render` | `{theme}` | `{status, reason?, artifacts}` | `404 not_found`, `409 run_active`, `503 capacity` (no render slot in time, or the render store is full) |
| `GET /v1/sessions/{sid}/artifacts/{name}?v=` | | the file | `404` |
| `GET /v1/sessions/{sid}/bundle?version=&include_data=` | | the feedback case bundle: every version, or the one numbered `version`, or with `version=0` the conversation alone (no version; `data_csv`, the current data, with `include_data`); with `AGENT_KEEP_REFUSALS` also `refusals`, the session's refused messages `[{verdict, lang, text, at}]` | `404` |
| `DELETE /v1/sessions/{sid}` | | `204` | |

Every `/v1` route needs `X-Anyplot-User` (the BFF's opaque user id); sessions are
owned by that id, so another user's session id is `404 session_expired`. Outside
development the caller check decodes the IAM-forwarded ID token (Cloud Run has
already verified it and replaced the signature) and requires its `aud` in
`AGENT_SERVICE_URLS` and its `email` in `AGENT_ALLOWED_CALLERS`. It reads
`X-Serverless-Authorization` whenever that header is present, because Cloud Run then
checks only that one and passes `Authorization` through unverified.

A `/messages` turn starts at once: the stream sends `ready` and the run begins, so a
plain answer, a refusal, `prepare_data` or `generate_data` never waits (owner decision
of 2026-10-14). Only sandbox work goes through the run queue (`anyplot/run_queue.py`):
the turn's first `plot_pipeline` or `run_data_code` call takes the queue's slot and the
turn's start in the rate window (`TurnSlot`, the ledger's `run_slot`), and the stream
sends `status{step:"queued", position, waiting}` while it waits, mid-turn, then the
run's own events. The request deadline is paused while the turn waits and resumes
with the time it had left when the slot comes, so queued time never counts. A full queue, or a
wait of `AGENT_QUEUE_MAX_WAIT_S`, ends the turn with `error{code:"capacity"}`. A user
with a turn in flight gets `409 run_active` on a second turn in any session.

Before the scope judge runs, and before any model call, the route answers with a fixed
refusal right after `ready`: `locked_out` for a user past the day's `attack` strikes
(`AGENT_ATTACK_STRIKES`), `budget` for a user over the daily token budget,
`session_closed` in a session the scope judge closed (`AGENT_SESSION_REFUSALS`
refusals of type `out_of_scope` or `attack`), and `rate_limited` or `daily_limit` past
the user's message limits (`AGENT_USER_MESSAGES_PER_MINUTE`,
`AGENT_USER_MESSAGES_PER_DAY`, counted in the usage book; actions count too).

The theme toggle (`/versions/{version}/render`) renders the other theme of a finished
version outside the queue, because it costs no tokens, but behind waiting pipeline
renders in the render slot (`render/serial.py`); while it renders it holds the
session's registry entry, so a user has one run or toggle in flight at a time.
`adk web` runs the agents without this service, so its runs bypass the queue; its
renders still go through the one render slot.

Before a dataset is stored, a deterministic pre-filter reads every header and cell
for text addressed to an AI, then the dataset judge reads the judged view (every
header, the five rows and top values the root and the adapter get, cells in full) in
parts of about 4,000 characters, four at a time (`opening.py`). Both look for
injection only: names, addresses, e-mail addresses, phone numbers and web addresses
are the user's data and pass. A pre-filter hit or any refusing part is
`403 data_refused` (the `data_judge` attribution line tells `prefilter` and the
judge's verdict apart); a part the judge cannot answer is `503 guard_unavailable`.
The notes pasted around the table (`context_lines`) go through the same pre-filter and
then the scope judge (`_screen_notes`); any refusal or outage there drops only the notes,
with a warning, never the table, and is never a strike. A dropped file's name (`source`) is
never a note and never part of the text: sanitised (`opening.source_name`), it goes through
the same pre-filter and then its own scope-judge call (`_screen_file_name`), and the session
keeps it as `StoredDataset.file_name` (`(name withheld)` after a refusal or an outage, no
strike, the notes untouched). The root reads it fenced as data, never as a request; its
judge's `lang` never sets the session language; it is never logged.

The dataset answer lists the spec's data roles as `roles`, each
`{name, kinds, required, variadic, description, non_negative}`, so a client can offer a column
choice for every role: a single role binds under its own name, a variadic family
`y` binds its members `y1`, `y2`, ... (`data/bindings.py`). `non_negative` marks a
role that needs values of 0 or more (`data/signs.py`): the defaults never give it a
column with a negative value, and the page warns when one is chosen by hand.

The PNG artifacts and the bundle's images carry the footer strip ("made with
any.plot()", "anyplot.ai/<spec-id>", `render/watermark.py`), so a 3200x1800 render
is served as 3200x1864. It is composed from the raw render on the first request and
cached in the render store; `AGENT_WATERMARK=false` serves the raw renders. The
gates, the reviewer and the exported `plot.py` never see the strip.

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
from dataclasses import asdict, dataclass, field
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
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator
from starlette.background import BackgroundTask

from agents.anyplot import agent as agent_module
from agents.anyplot.code.readiness import MAP_SPECS
from agents.anyplot.data.classify import classify_paste
from agents.anyplot.data.parse import (
    MAX_COMPUTED_BYTES,
    MAX_INPUT_BYTES,
    MAX_TABLES,
    ParsedDataset,
    ParseError,
    parse_dataset,
    without_context,
)
from agents.anyplot.data.prepare import Operation, PrepareError, apply_operations, with_date_notes
from agents.anyplot.data.roles import DataRole
from agents.anyplot.data.shape import long_suggestion
from agents.anyplot.data.store import StoreFull
from agents.anyplot.data.transcribe import MAX_TRANSCRIBE_CHARS, looks_like_free_text, table_to_csv, transcribable
from agents.anyplot.dataset_context import FILE_NAME_WITHHELD
from agents.anyplot.dataset_guard import DataRefused, GuardUnavailable, check_dataset
from agents.anyplot.dataset_versions import dataset_payload, push_version, undo_version
from agents.anyplot.dev_fixture import FixtureError, load_case
from agents.anyplot.language import (
    DEFAULT_LANGUAGE,
    LANGUAGE_PATTERN,
    MAX_LANGUAGE_CHARS,
    english_name,
    is_valid,
    normalise,
    pasted_language,
    refusal_lang,
)
from agents.anyplot.models import JudgeUnavailable
from agents.anyplot.opening import (
    INSTRUCTION_LIKE,
    MAX_SOURCE_RAW_CHARS,
    NOTES_INSTRUCTION_WARNING,
    NOTES_REFUSED_WARNING,
    NOTES_UNCHECKED_WARNING,
    Eligibility,
    assess,
    file_name_judge_input,
    notes_instruction_like,
    notes_judge_input,
    opening_state,
    source_name,
    store_dataset,
)
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, attribution, budget_allows, judge_budget_tokens
from agents.anyplot.plugins.scope_guard import LOCKED_OUT, SESSION_CLOSED, scope_refusals
from agents.anyplot.policy import fence, file_name_block, refusal, scope_rubric, transcribe_rubric, user_notes_block
from agents.anyplot.render.contract import ConvertJob, RendererUnavailable
from agents.anyplot.render.serial import RenderBusy
from agents.anyplot.render.store import RenderStoreFull
from agents.anyplot.render.watermark import add_footer
from agents.anyplot.run_queue import (
    HEARTBEAT_S,
    QueueFull,
    QueuePosition,
    QueueTimeout,
    QueueWithdrawn,
    RunQueue,
    Ticket,
)
from agents.anyplot.schemas import MAX_COLUMNS, MAX_MESSAGE_CHARS, Binding, DatasetProfile, Theme
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import (
    BINDINGS,
    CONFIRMED,
    PENDING_BINDINGS,
    CatalogueSnapshot,
    SessionView,
    apply_bindings,
    confirm_delta,
    confirmation_fingerprint,
    language_delta,
    read_session,
)
from agents.anyplot.settings import AgentSettings, get_settings
from agents.anyplot.theme_render import RenderGone, render_theme
from agents.renderer.wire import (
    CONVERT_DAMAGES,
    CONVERT_HARNESS_EXITS,
    MAX_CONVERT_BASE64_CHARS,
    MAX_CONVERT_INPUT_BYTES,
    MAX_SHEET_NAME_CHARS,
)
from agents.stream import MAX_DONE_ROLES, Translator
from core.constants import SUPPORTED_LIBRARIES


logger = logging.getLogger("anyplot.agents")

APP_NAME = agent_module.APP_NAME
USER_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"
SESSION_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"
SPEC_PATTERN = r"^[a-z0-9-]{1,100}$"
LOCALE_PATTERN = r"^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$"
Action = Literal["create_plot", "summarize_data"]
ACTION_MESSAGES: dict[str, str] = {
    "create_plot": "[action] Create the plot from my dataset and bindings.",
    "summarize_data": "[action] Summarize the dataset for the user.",
}
"""The fixed user message of each structured action; the scope judge is skipped for them (`ledger.kind`).
`summarize_data` also carries the notes the user pasted with the data, when the stored dataset kept any
(`user_notes_block`): the dataset route ran the pre-filter and the scope judge on them at the paste."""
ACTION_LANGUAGE_LINE = "Reply in {name}, the session language."
"""Appended to an action message when the session language is a known one other than English (`english_name`)."""
ACTION_MESSAGE = ACTION_MESSAGES["create_plot"]
SWEEP_INTERVAL_S = 300
ARTIFACT_TYPES: dict[str, str] = {
    "plot-light.png": "image/png",
    "plot-dark.png": "image/png",
    "plot.py": "text/x-python; charset=utf-8",
    "data.csv": "text/csv; charset=utf-8",
}
_USER = re.compile(USER_PATTERN)
_NO_STORE = {"Cache-Control": "private, no-store"}
OPERATIONS = TypeAdapter(list[Operation])

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


MAX_CAUSE_CHARS = 300
"""The longest `cause` an error answer carries (`AgentsError`); the BFF applies the same cap."""


def clip_cause(cause: str) -> str:
    """The cause within `MAX_CAUSE_CHARS`, a longer one cut at a word boundary with `…` (never mid-word)."""
    if len(cause) <= MAX_CAUSE_CHARS:
        return cause
    head = cause[: MAX_CAUSE_CHARS - 1]
    space = head.rfind(" ")
    return (head[:space] if space >= MAX_CAUSE_CHARS // 2 else head).rstrip(" ,;:") + "…"


class AgentsError(Exception):
    """A `/v1` error answered as `{"detail": code}`, plus `"cause"` when the refusal names one; never an exception text.

    `cause` is a sentence the service wrote for the user about their own data, such as the
    parser's `ParseError.message` ("the header has 3 fields, but line 3 has 4"): owner rule
    of 2026-10-16, a paste that is refused says what it fails on. It never carries an
    exception's text, a stack or a model's words.
    """

    def __init__(self, status: int, code: str, cause: str | None = None) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.cause = cause


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
    """A `/messages` request from its registration to the end of its stream, or a theme toggle while it renders.

    `started` is the registration time on the queue's clock, and the end of the turn's
    queue wait once a sandbox run waited for the slot (`RunDeadline.arm`). `ticket` is
    the turn's queue entry, set by its first sandbox run (`TurnSlot`); the ticket's own
    times decide the stale check when there is one, so a run that just left a long
    wait is not mistaken for an old run. A toggle has no ticket, and its abort signal
    is never read: it ends within the request deadline on its own (a bounded slot wait
    plus one render).
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
class RunDeadline:
    """A turn's request deadline: armed when the turn starts, paused while it waits in the run queue, and resumed
    with the time it had left when it leaves the queue. Queued time never counts, and the time before the wait is
    never granted twice, so a turn's active time stays within `seconds` and the whole turn within `seconds` plus the
    queue's maximum wait, below the BFF's turn cap and both services' Cloud Run timeouts."""

    run: ActiveRun
    seconds: float
    handle: asyncio.TimerHandle | None = None
    elapsed: float = 0.0  # active time spent before the last pause
    armed_at: float | None = None

    def arm(self, now: float) -> None:
        self.cancel()
        self.run.started = now - self.elapsed
        self.armed_at = now
        self.handle = asyncio.get_running_loop().call_later(max(self.seconds - self.elapsed, 0.0), self._hit)

    def pause(self, now: float) -> None:
        if self.armed_at is not None:
            self.elapsed += now - self.armed_at
            self.armed_at = None
        self.cancel()

    def cancel(self) -> None:
        if self.handle is not None:
            self.handle.cancel()
            self.handle = None

    def _hit(self) -> None:
        self.run.deadline_hit = True
        self.run.abort.set()


StreamNote = tuple[Literal["queued"], QueuePosition] | tuple[Literal["event"], Event] | tuple[Literal["end"], None]
"""What the stream's outbox carries: a queue position of a waiting sandbox run, an ADK event, or the run's end."""


@dataclass
class TurnSlot:
    """A `/messages` turn's claim on the run queue: taken by its first sandbox run, held until the turn ends.

    `take` is the ledger's `run_slot`, awaited by `plot_pipeline` and `run_data_code`
    inside the ADK run. The first call submits the turn's queue entry (a start in the rate
    window and the run slot), pauses the deadline while the entry waits, puts every
    position into the stream's outbox as it changes (the stream sends it as
    `status{step:"queued"}`), and resumes the deadline with the time it had left when the entry starts.
    A later call in the same turn answers at once: one start per turn. A full queue or
    an expired wait fails the turn with `capacity` and aborts the run, so the stream ends
    with `error{code:"capacity"}` and the root spends no further call; a cancelled wait
    ends the run like any cancel. The entry is released with the turn (`Runtime.finish`).
    """

    runtime: "Runtime"
    run: ActiveRun
    session_id: str
    ledger: RequestLedger
    deadline: RunDeadline
    outbox: "asyncio.Queue[StreamNote]"

    async def take(self) -> bool:
        if self.run.ticket is not None:
            return self.run.ticket.running
        if self.run.abort.is_set():
            return False
        queue = self.runtime.run_queue()
        try:
            ticket = queue.submit(self.run.user, self.session_id)
        except QueueFull:
            logger.info("run queue full (ref %s): %d waiting", self.ledger.request_id, queue.waiting_count)
            attribution("queue", self.ledger, verdict="full", waited_s=0.0)
            self._fail()
            return False
        self.run.ticket = ticket
        outcome = "started"
        waited = False
        try:
            async with contextlib.aclosing(queue.wait(ticket, heartbeat_s=HEARTBEAT_S)) as positions:
                async for position in positions:
                    if not waited:
                        waited = True
                        self.deadline.pause(self.runtime.now())  # queued time never counts
                    self.outbox.put_nowait(("queued", position))
        except QueueTimeout:  # waited the maximum: the same answer as a full queue
            outcome = "expired"
        except QueueWithdrawn:  # cancelled or purged while it waited: nothing to report
            outcome = "withdrawn"
        attribution("queue", self.ledger, verdict=outcome, waited_s=round(self.runtime.now() - ticket.enqueued_at, 1))
        if outcome == "expired":
            self._fail()
        if outcome != "started":
            return False
        if waited:
            self.deadline.arm(self.runtime.now())
        return True

    def _fail(self) -> None:
        self.ledger.fail("capacity")
        self.run.abort.set()


@dataclass
class Runtime:
    """The runner, the run queue and the run registry for this process.

    `active` is the run registry: one entry per session with a queued or running
    `/messages` turn or a theme toggle in flight, which is what `409 run_active`
    checks. `pasting` holds the users with a dataset paste in flight, so a user has one
    paste at a time across sessions (`409 run_active` for a second one). The queue is built
    from the settings on first use; its clock is the registry's clock too.
    """

    session_service: InMemorySessionService = field(default_factory=InMemorySessionService)
    artifact_service: InMemoryArtifactService = field(default_factory=InMemoryArtifactService)
    active: dict[str, ActiveRun] = field(default_factory=dict)
    pasting: set[str] = field(default_factory=set)
    converting: set[str] = field(default_factory=set)
    """The users with a file conversion in flight: one per user at a time (`409 run_active` for a second)."""
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
    content: dict[str, Any] = {"detail": exc.code}
    if exc.cause:
        # Backstop: a cause that names the user's text must never turn a refusal into a 500 on encoding.
        content["cause"] = clip_cause(exc.cause).encode("utf-8", "replace").decode("utf-8")
    return JSONResponse(status_code=exc.status, content=content, headers=_NO_STORE)


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


class LanguageBody(_Body):
    """The chat header's language chip: a short language name or code (`de`, `English`, `Swedish`)."""

    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_CHARS, pattern=LANGUAGE_PATTERN)


class DatasetBody(_Body):
    text: str = Field(min_length=1)
    confirmed: bool = False
    """The text is a table the user confirmed (the page's `.use()` on a transcription): the
    route never hands it to the transcriber again, so a one-column reading can be stored,
    and the parse keeps every row of it (no `table_block` narrowing: the user has seen the
    table row by row); the pre-filter, the judge and the store run as for any paste."""
    source: str | None = Field(default=None, min_length=1, max_length=MAX_SOURCE_RAW_CHARS)
    """The name of the file the page read `text` from (a drop, `.open()` or a pasted file), as the browser
    gave it. Screened on its own (`_screen_file_name`) and kept as `StoredDataset.file_name`, never as a
    note; the text itself is the file's, unchanged. Never logged."""
    table: int | None = Field(default=None, strict=True, ge=1, le=MAX_TABLES)
    """Which table to read when the text holds several (the page's table picker, from the previous answer's
    `tables`, 1-based); None reads the first. A number past the tables found is `422 unparseable`."""


class ConvertBody(_Body):
    """A dropped binary data file as base64 (the BFF's CSRF guard takes JSON only), and the sheet the page chose."""

    data_base64: str = Field(min_length=4, max_length=MAX_CONVERT_BASE64_CHARS)
    sheet: str | None = Field(default=None, min_length=1, max_length=MAX_SHEET_NAME_CHARS)
    """A sheet of a workbook or an array of an `.npz`, as the previous answer named it; None reads the first."""


class BindingBody(_Body):
    role: str = Field(min_length=1, max_length=32)
    column: str | None = Field(default=None, max_length=64)


class MessageBody(_Body):
    text: str | None = None
    action: Action | None = None

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
    # A fixture is the developer's own, confirmed data: its bindings (the case's or the defaults) count.
    bindings = case.bindings if case.bindings is not None else ingested.bindings
    delta[CONFIRMED] = confirmation_fingerprint(ingested.dataset_id, bindings)
    return delta


def _active(runtime: Runtime, sid: str, user: str | None = None) -> None:
    """409 while the session has a queued or running run, or, with `user`, while that user has one in any session
    or a dataset paste in flight (`Runtime.pasting`), so a turn, a theme toggle and a paste exclude each other."""
    runtime.drop_stale(get_settings())
    if sid in runtime.active:
        raise AgentsError(409, "run_active")
    if user is not None and (user in runtime.pasting or any(run.user == user for run in runtime.active.values())):
        raise AgentsError(409, "run_active")


def _data_route_free(runtime: Runtime, sid: str, user: str) -> None:
    """`_active` for the session's data routes (library, bindings, confirm, undo, to_long): 409 while the session
    has a run, or while the user's paste is in flight in any session. A paste holds the view it read before its
    judges ran and writes the next dataset from it, so a version another tab stored meanwhile would be dropped
    silently. A run of the user in another session does not block them, as before."""
    _active(runtime, sid)
    if user in runtime.pasting:
        raise AgentsError(409, "run_active")


@app.post("/v1/sessions/{sid}/library", dependencies=v1_dependencies)
async def switch_library(sid: SessionId, body: SwitchLibraryBody, user: User, runtime: RuntimeDep) -> JSONResponse:
    settings = get_settings()
    session = await runtime.session(user, sid)
    _data_route_free(runtime, sid, user)
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
    settings = get_settings()
    session = await runtime.session(user, sid)
    # A closed session takes no paste either: each one spends judge calls, and the chat it would feed is closed.
    if scope_refusals(session.events) >= settings.session_refusals:
        raise AgentsError(403, SESSION_CLOSED)
    _active(runtime, sid, user)  # also one paste per user at a time, across sessions
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    if len(body.text.encode("utf-8", errors="surrogatepass")) > MAX_INPUT_BYTES:
        raise AgentsError(413, "too_long")
    _paste_budget(services, user, settings)
    limit = services.usage.paste_limit(user, settings)
    if limit is not None:
        attribution("paste_limit", RequestLedger(request_id=rid, user_id=user, session_id=sid), verdict=limit)
        raise AgentsError(429, limit)
    runtime.pasting.add(user)  # no await since the check above, so no second paste slipped in between
    try:
        return await _ingest_paste(services, runtime, body, user, sid, rid, view)
    finally:
        runtime.pasting.discard(user)


CONVERT_FAILURES: dict[str, str] = {
    "timeout": "file_timeout",
    "memory": "file_too_complex",
    "disk_budget": "file_too_complex",
    "file_budget": "file_too_complex",
    "output_rejected": "file_too_large",
}
"""A conversion the renderer stopped, by its run reason, as the route's refusal code; any other failure (the reader
raised, the guard refused an operation) is `file_unreadable`."""


@app.post("/v1/sessions/{sid}/dataset/convert", dependencies=v1_dependencies)
async def convert_dataset_file(
    sid: SessionId, body: ConvertBody, user: User, runtime: RuntimeDep, rid: RequestId
) -> JSONResponse:
    """A dropped binary data file read in the renderer's sandbox into the text the paste box takes.

    Nothing is stored and no model reads anything: the page puts the text into the box and
    the user presses `.parse()`, which goes through the ordinary paste route (its limits, the
    pre-filter, the judges) with the file's name and sheet as `source`. The conversion has its
    own counter (`AGENT_USER_CONVERSIONS_PER_MINUTE` / `_PER_DAY`, counted when the file goes to
    the sandbox), checked after the paste route's daily budget and strikes, so a user who may
    not paste spends no sandbox time; the paste that follows counts as one paste (owner
    decision of 2026-10-15). One conversion per user at a time (`Runtime.converting`), across
    sessions; it waits for the render slot behind every pipeline render. The attribution line
    carries the kind, the outcome, the byte count and the time, never the file, its text or its
    sheet names.
    """
    services = get_services()
    settings = get_settings()
    session = await runtime.session(user, sid)
    if scope_refusals(session.events) >= settings.session_refusals:
        raise AgentsError(403, SESSION_CLOSED)
    if user in runtime.converting:
        raise AgentsError(409, "run_active")
    try:
        data = base64.b64decode(body.data_base64, validate=True)
    except (ValueError, binascii.Error):
        raise AgentsError(422, "invalid") from None
    if not data:
        raise AgentsError(422, "invalid")
    if len(data) > MAX_CONVERT_INPUT_BYTES:
        raise AgentsError(413, "too_long")
    _paste_budget(services, user, settings)
    ledger = RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action")
    limit = services.usage.convert_limit(user, settings)
    if limit is not None:
        attribution("convert_limit", ledger, verdict=limit)
        raise AgentsError(429, limit)
    runtime.converting.add(user)  # no await since the check above, so no second conversion slipped in between
    try:
        services.usage.add_conversion(user)
        job = ConvertJob(
            job_id=f"c{secrets.token_hex(8)}", data=data, sheet=body.sheet, timeout_s=settings.convert_timeout_s
        )
        try:
            output = await services.backend.convert(job, wait_s=settings.convert_slot_wait_s)
        except RenderBusy:
            attribution("data_convert", ledger, outcome="capacity", bytes=len(data))
            raise AgentsError(503, "capacity") from None
        except (RendererUnavailable, NotImplementedError):
            attribution("data_convert", ledger, outcome="unavailable", bytes=len(data))
            raise AgentsError(503, "convert_unavailable") from None
    finally:
        runtime.converting.discard(user)
    kind = output.meta.kind if output.meta is not None else None
    if output.exit_code == 0 and output.text is not None and output.meta is not None:
        meta = output.meta
        attribution(
            "data_convert",
            ledger,
            outcome="ok",
            kind=kind,
            format=meta.format,
            rows=meta.rows,
            columns=meta.columns,
            sheets=meta.sheet_count,
            bytes=len(data),
            wall_s=round(output.wall_s, 3),
        )
        return JSONResponse(
            {
                "text": output.text,
                "format": meta.format,
                "kind": meta.kind,
                "rows": meta.rows,
                "columns": meta.columns,
                "sheet": meta.sheet,
                "sheets": meta.sheets,
                "sheet_count": meta.sheet_count,
                "warnings": dict(meta.warnings),
                "dropped": list(meta.dropped),
            },
            headers=_NO_STORE,
        )
    if output.refusal is not None:
        code = f"file_{output.refusal}"
    elif output.timed_out:
        code = "file_timeout"
    elif output.reason is not None:
        code = CONVERT_FAILURES.get(output.reason, "file_unreadable")
    elif output.exit_code is None or output.exit_code not in CONVERT_HARNESS_EXITS:
        # A process that died without its `status.json` (a native reader's SIGABRT on an allocation it could not
        # make; security review of #12194): the file was too much for the sandbox, not unreadable.
        code = "file_too_complex"
    else:
        code = "file_unreadable"
    attribution(
        "data_convert",
        ledger,
        outcome=code,
        exit_code=output.exit_code,
        reason=output.reason,
        damage=output.damage,
        bytes=len(data),
        wall_s=round(output.wall_s, 3),
    )
    content: dict[str, Any] = {"detail": code}
    if output.refusal is not None:
        content.update(
            {key: value for key, value in (("measured", output.measured), ("limit", output.limit)) if value is not None}
        )
    if output.refusal == "corrupt" and output.damage in CONVERT_DAMAGES:
        content["damage"] = output.damage  # which part is broken, a closed name the page words (owner, 2026-10-16)
    return JSONResponse(status_code=422, content=content, headers=_NO_STORE)


def _paste_budget(services: Services, user: str, settings: AgentSettings) -> None:
    """`429 locked_out` past the day's `attack` strikes, `429 daily_limit` past the daily token budgets."""
    if services.usage.daily_ok(user, settings):
        return
    raise AgentsError(429, LOCKED_OUT if services.usage.locked_out(user, settings) else "daily_limit")


async def _ingest_paste(
    services: Services, runtime: Runtime, body: DatasetBody, user: str, sid: str, rid: str, view: SessionView
) -> JSONResponse:
    """The paste route past its limits: classify, parse or transcribe, judge, screen the notes, store."""
    ledger = RequestLedger(request_id=rid, user_id=user, session_id=sid, kind="action")
    if not body.confirmed:  # a confirmed transcription is the service's own CSV
        _refuse_code_or_formula(ledger, body.text)
    try:
        # A confirmed transcription is the service's own CSV, which the user has seen row by row: no row is left out.
        # A dropped `.jsonl` or `.ndjson` file is JSON Lines by its name, so a file of one record is one row.
        json_lines = body.source is not None and body.source.lower().rstrip().endswith((".jsonl", ".ndjson"))
        parsed = parse_dataset(body.text, find_table=not body.confirmed, table=body.table or 1, json_lines=json_lines)
    except ParseError as exc:
        if exc.code == "too_long":
            raise AgentsError(413, "too_long", exc.message) from None
        # Text with no table in it (prose, a list on one line) is the transcriber's; a broken
        # table (ragged rows, bad quoting, an over-long cell, invalid JSON) stays the parser's refusal,
        # which names its cause (owner rule of 2026-10-16).
        if exc.code == "no_table" and transcribable(body.text):
            return await _transcribe(services, ledger, body.text)
        cause = exc.message
        if exc.code == "no_table":
            cause = (
                f"{cause}, and the text is longer than the {MAX_TRANSCRIBE_CHARS:,} characters the model that reads "
                "free text as a table takes"
            )
        raise AgentsError(422, "unparseable", cause) from None
    if not body.confirmed and looks_like_free_text(parsed) and transcribable(body.text):
        return await _transcribe(services, ledger, body.text)
    services.usage.add_paste(user)  # the first model call of this paste: only a paste that reaches one counts
    try:
        header_lang = await check_dataset(services, ledger, parsed)
    except DataRefused:
        raise AgentsError(403, "data_refused") from None
    except GuardUnavailable:
        raise AgentsError(503, "guard_unavailable") from None
    notes_lang = None
    if parsed.context_lines:
        parsed, notes_lang = await _screen_notes(services, ledger, parsed)
    # The name is screened apart from the notes and its `lang` is not read: neither can cost the other.
    file_name = await _screen_file_name(services, ledger, body.source) if body.source is not None else None
    try:
        ingested = store_dataset(
            services.datasets,
            sid,
            parsed,
            view.snapshot,
            previous_id=view.dataset_id,
            history=view.dataset_history,
            notes_screened=True,  # `_screen_notes` above kept only the notes that passed
            file_name=file_name,
        )
    except StoreFull:
        raise AgentsError(503, "capacity") from None
    delta = ingested.state_delta()
    # Read again: the chip's choice may have landed while the judges ran, and a choice is never overwritten.
    # From this read to the append below nothing suspends: `InMemorySessionService.get_session` and
    # `append_event` (ADK 2.11) contain no `await` that yields, and the code between them is synchronous,
    # so on the one event loop no `PUT /language` can land in between; the read and the conditional
    # write are atomic. A persistent session service with I/O in either call would need a
    # compare-and-set instead. Keep any new `await` out of this block.
    session = await runtime.session(user, sid)
    current = read_session(session.state) or view
    language, language_source = current.language, current.language_source
    derived = pasted_language(current.language_source, notes_lang, header_lang)
    if derived is not None:
        language, language_source = derived, "pasted"
        delta.update(language_delta(derived, "pasted"))
        attribution("data_language", ledger, lang=derived, basis="notes" if derived == notes_lang else "headers")
    await runtime.write_state(session, delta)
    return JSONResponse(
        {
            "preview": parsed.preview,
            "profile": parsed.profile.model_dump(mode="json"),
            "bindings": [binding.model_dump() for binding in ingested.bindings],
            "warnings": parsed.warnings,
            "context_lines": parsed.context_lines,
            "roles": _page_roles(view.snapshot.roles()),
            "suggestion": _suggestion(view, parsed.profile),
            "version": 1,
            "language": {"language": language, "source": language_source},
            **({"file_name": file_name} if file_name is not None else {}),
            **({"tables": parsed.tables, "table": parsed.table} if parsed.tables else {}),
        },
        headers=_NO_STORE,
    )


async def _screen_file_name(services: Services, ledger: RequestLedger, raw: str) -> str | None:
    """A dropped file's name as the session keeps it: sanitised, then screened like a note, on its own.

    None when nothing readable is left (`source_name`). The pre-filter (`INSTRUCTION_LIKE`) runs on
    the name alone, then the scope judge on one `source file: <name>` line (`file_name_judge_input`),
    always, also for a name that looks harmless (owner decision of 2026-10-15). A hit, a verdict
    other than `in_scope` or no verdict keeps `FILE_NAME_WITHHELD` instead: the notes and the table
    are untouched, and it is never a strike, as for the notes (a file's name is often someone
    else's). The judge's `lang` is ignored: a name such as `datos_2025.csv` must not set the session
    language of a German table. Kept names still reach the root only fenced as data with a preamble
    that says a name is never a request (`policy.file_name_block`), because the scope judge passes
    plot wishes, and a name that reads like one ("drop rows where…") was not written to the root.
    The judge's tokens are the user's; the `file_name_judge` attribution line carries the verdict
    and the length, never the name.
    """
    name = source_name(raw)
    if name is None:
        return None
    chars = len(name)
    if notes_instruction_like([name]):
        attribution("file_name_judge", ledger, verdict="prefilter", chars=chars)
        return FILE_NAME_WITHHELD
    try:
        answer = await services.judge.judge(file_name_judge_input(name), scope_rubric())
    except JudgeUnavailable:
        attribution("file_name_judge", ledger, verdict="guard_unavailable", chars=chars)
        return FILE_NAME_WITHHELD
    services.usage.add_tokens(
        ledger.user_id,
        judge_budget_tokens(answer.tokens, answer.input_tokens, answer.output_tokens, get_settings().judge_model),
    )
    attribution("file_name_judge", ledger, verdict=answer.verdict, judge_tokens=answer.tokens, chars=chars)
    return name if answer.verdict == "in_scope" else FILE_NAME_WITHHELD


async def _screen_notes(
    services: Services, ledger: RequestLedger, parsed: ParsedDataset
) -> tuple[ParsedDataset, str | None]:
    """The notes pasted around the table, kept only when the pre-filter and the scope judge pass them.

    Returns the dataset and, for kept notes, the judge's `lang` for them, which may set the
    session language (`language.pasted_language`); None when the notes were dropped.

    `parsed.context_lines` (a title, an export's metadata, a source line, "values in
    Fahrenheit, make it a line chart") reach the root as the user's words, so they are
    checked like a chat message: first the deterministic pre-filter (`INSTRUCTION_LIKE`),
    then the scope judge with the scope rubric on the lines inside `<user_notes>`. It runs
    after the dataset judge, so a refused table spends no call on its notes. A hit, a
    verdict other than `in_scope` or no verdict (`JudgeUnavailable`: fail closed) drops
    every note with a warning (`without_context`), and the table is stored all the same.
    No verdict on notes is a strike: a hidden injection in a copied web table is not the
    user's doing, and the notes never reach a model. The judge's tokens are booked to the
    user like the dataset judge's, and the `notes_judge` attribution line carries the
    verdict and the counts, never the text.
    """
    lines = parsed.context_lines
    counts = {"lines": len(lines), "chars": len("\n".join(lines))}  # as the cap and the judge input count them
    if notes_instruction_like(lines):
        attribution("notes_judge", ledger, verdict="prefilter", **counts)
        return without_context(parsed, NOTES_INSTRUCTION_WARNING), None
    try:
        answer = await services.judge.judge(notes_judge_input(lines), scope_rubric())
    except JudgeUnavailable:
        attribution("notes_judge", ledger, verdict="guard_unavailable", **counts)
        return without_context(parsed, NOTES_UNCHECKED_WARNING), None
    services.usage.add_tokens(
        ledger.user_id,
        judge_budget_tokens(answer.tokens, answer.input_tokens, answer.output_tokens, get_settings().judge_model),
    )
    attribution(
        "notes_judge",
        ledger,
        verdict=answer.verdict,
        judge_tokens=answer.tokens,
        judge_input=answer.input_tokens,
        judge_output=answer.output_tokens,
        **counts,
    )
    if answer.verdict != "in_scope":
        return without_context(parsed, NOTES_REFUSED_WARNING), None
    return parsed, answer.lang


def _refuse_code_or_formula(ledger: RequestLedger, text: str) -> None:
    """`422 code` or `422 formula` for pasted text that is a program or asks for a formula, before any parser or
    model reads it (`data/classify.py`).

    A snippet such as `np.linspace(0, 10, 100)` would parse as a one-row table, and the
    transcriber would compute a formula's rows, which is the one thing no model may do:
    code is the root's `run_data_code` and a formula its `generate_data`, asked for in
    the chat, where the server computes the table. A formula is refused only within the
    chat's cap (`MAX_MESSAGE_CHARS`), because the page's offer sends the refused text to
    the chat as a turn; longer text goes on to the transcriber, whose rubric computes
    nothing. Code is refused at any length, because it is never a table; the page asks
    to shorten what the chat cannot take. Writes a `data_transcribe` attribution line
    with the outcome `code` or `formula` (no text, no tokens).
    """
    kind = classify_paste(text)
    if kind is not None:
        attribution("data_transcribe", ledger, outcome=kind)
        raise AgentsError(422, kind)


async def _transcribe(services: Services, ledger: RequestLedger, text: str) -> JSONResponse:
    """Read free text as a table with the transcriber and answer with it, storing nothing.

    The answer carries `transcribed: true` and the table's CSV in `text`; the user
    confirms the preview, and the confirmation posts that CSV through the ordinary path
    (parse, pre-filter, judge, store). The model reads the raw text, so the pre-filter runs
    on it first; its answer is bound to `TranscribedTable`, then parsed like any paste, so
    a reading that is no table (one column of prose) is `422 unparseable` here too. The
    call books its tokens like a judge call and writes a `data_transcribe` attribution line.
    """
    user = ledger.user_id
    services.usage.add_paste(user)  # a paste counts against `paste_limit` when it reaches a model (or its pre-filter)
    if INSTRUCTION_LIKE.search(text):
        attribution("data_transcribe", ledger, outcome="prefilter")
        raise AgentsError(403, "data_refused")
    try:
        reading = await services.judge.transcribe(fence("user_text", text), transcribe_rubric())
    except JudgeUnavailable:
        attribution("data_transcribe", ledger, outcome="guard_unavailable")
        raise AgentsError(503, "guard_unavailable") from None
    services.usage.add_tokens(
        user,
        judge_budget_tokens(reading.tokens, reading.input_tokens, reading.output_tokens, get_settings().judge_model),
    )
    csv_text = table_to_csv(reading.table)
    try:
        parsed = parse_dataset(csv_text, find_table=False)
    except ParseError as exc:
        attribution("data_transcribe", ledger, outcome="unparseable", judge_tokens=reading.tokens)
        raise AgentsError(
            422, "unparseable", f"the model read the text as a table, but that table was refused: {exc.message}"
        ) from None
    if looks_like_free_text(parsed) and parsed.profile.columns[0].name == "text":
        # The rubric's answer for text that holds no table: one column named `text`.
        attribution("data_transcribe", ledger, outcome="no_table", judge_tokens=reading.tokens)
        raise AgentsError(
            422,
            "unparseable",
            "no table found: the text has no separators between columns, and the model that reads free text found "
            "no rows and columns in it",
        )
    attribution(
        "data_transcribe",
        ledger,
        outcome="ok",
        rows=parsed.profile.rows,
        columns=len(parsed.profile.columns),
        judge_tokens=reading.tokens,
        judge_input=reading.input_tokens,
        judge_output=reading.output_tokens,
    )
    return JSONResponse(
        {
            "transcribed": True,
            "text": csv_text,
            "preview": parsed.preview,
            "profile": parsed.profile.model_dump(mode="json"),
            "warnings": parsed.warnings,
            "note": reading.table.note,
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
        # A role the plot can compute is never missing: the page marks it optional (`data/computed.py`).
        "required": role.required and not role.computed,
        "variadic": role.variadic,
        "description": description,
        # The page warns at the dropdown when the bound column has a negative value (`data/signs.py`).
        "non_negative": role.non_negative,
        # Left open, the plot computes the role from the data: the dropdown's empty choice says so.
        "computed": role.computed,
    }


def _page_roles(roles: list[DataRole]) -> list[dict[str, Any]]:
    """The roles the page offers a dropdown for, every one: a role the plot can compute shows "computed by
    the plot" as its empty choice (`computed`, owner decision of 2026-10-15, "both allowed")."""
    return [_role_body(role) for role in roles]


@app.put("/v1/sessions/{sid}/bindings", dependencies=v1_dependencies)
async def put_bindings(
    sid: SessionId,
    user: User,
    runtime: RuntimeDep,
    bindings: Annotated[list[BindingBody], Body(max_length=MAX_COLUMNS)],
) -> JSONResponse:
    services = get_services()
    session = await runtime.session(user, sid)
    _data_route_free(runtime, sid, user)
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
    check, delta = apply_bindings(parsed, view.snapshot.roles(), stored.profile, session.state.get(PENDING_BINDINGS))
    if not delta:
        return JSONResponse(
            status_code=422, content={"detail": "invalid", "errors": check.errors[:20]}, headers=_NO_STORE
        )
    # Other bindings than the user confirmed leave the confirmation's fingerprint behind: step 1 again.
    await runtime.write_state(session, delta)
    return JSONResponse(
        {
            "bindings": delta[BINDINGS],
            "complete": check.complete,
            "missing_roles": check.missing_roles,
            "warnings": check.warnings,
        },
        headers=_NO_STORE,
    )


@app.put("/v1/sessions/{sid}/language", dependencies=v1_dependencies)
async def put_language(sid: SessionId, body: LanguageBody, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The user's choice (the chat header's chip): the session language with the source `chosen`.

    Detection never writes over a choice, and the root's `set_language` tool makes the
    same change. The next reply and the next plot version use it; earlier versions keep
    their text. The pattern runs before `normalise` (a leading space is a `422`), and the
    answer carries the stored form, which the page shows: `English` comes back as `en`,
    `Swedish` as typed. `409 run_active` while a turn or a theme render is in flight, so
    a choice never races detection inside a run.
    """
    session = await runtime.session(user, sid)
    _active(runtime, sid)
    if read_session(session.state) is None:
        raise AgentsError(404, "session_expired")
    value = normalise(body.language)
    if not is_valid(value):
        raise AgentsError(422, "invalid")
    await runtime.write_state(session, language_delta(value, "chosen"))
    return JSONResponse({"language": value, "source": "chosen"}, headers=_NO_STORE)


@app.post("/v1/sessions/{sid}/dataset/confirm", dependencies=v1_dependencies)
async def confirm_dataset(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """Step 1 of two: the user confirms that the stored dataset and its bindings fit (owner rule of 2026-10-11).

    The plot pipeline runs only on a confirmed dataset (`not_ready: data_unconfirmed`
    otherwise). A new dataset or a binding change drops the confirmation; a library switch
    keeps it, because the data and the bindings stay.
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _data_route_free(runtime, sid, user)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    if stored is None:
        raise AgentsError(422, "no_dataset")
    await runtime.write_state(session, confirm_delta(view))
    return JSONResponse(
        {"confirmed": True, "rows": stored.profile.rows, "columns": len(stored.profile.columns)}, headers=_NO_STORE
    )


@app.post("/v1/sessions/{sid}/dataset/undo", dependencies=v1_dependencies)
async def undo_dataset(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The user's undo of the root's last `prepare_data` or `generate_data`: the version before it is current again.

    The session keeps the last five versions (`dataset_versions.MAX_DATASET_HISTORY`);
    the bindings are carried over like after a `prepare_data`, and the restored version
    is unconfirmed, because the user confirms every version they see. `422
    nothing_to_undo` for a paste that was never prepared (or whose history is spent),
    and for data that `generate_data` made in a session without data (its version 1).
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _data_route_free(runtime, sid, user)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    restored = undo_version(services.datasets, sid, view, view.snapshot)
    if restored is None:
        raise AgentsError(422, "nothing_to_undo")
    await runtime.write_state(session, restored.delta)
    return JSONResponse(
        {
            **restored.payload(),
            "roles": _page_roles(view.snapshot.roles()),
            "suggestion": _suggestion(view, restored.stored.profile),
        },
        headers=_NO_STORE,
    )


@app.post("/v1/sessions/{sid}/dataset/to_long", dependencies=v1_dependencies)
async def dataset_to_long(sid: SessionId, user: User, runtime: RuntimeDep) -> JSONResponse:
    """The page's `.to_long()`: apply the wide-table suggestion to the current dataset, without a model call.

    The server recomputes the suggestion (`data/shape.py`) from the session's spec and
    current profile, so the client never names an operation; `422 no_suggestion` when
    the table is not wide for this spec (any more). The result is stored as the next
    dataset version like a `prepare_data` (undo, history), with the default bindings for
    the new columns, unconfirmed, and the answer is the undo route's shape plus
    `changes`, the operation's change line.
    """
    services = get_services()
    session = await runtime.session(user, sid)
    _data_route_free(runtime, sid, user)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    stored = services.datasets.get(view.dataset_id, sid) if view.dataset_id else None
    suggestion = long_suggestion(view.snapshot.roles(), stored.profile) if stored is not None else None
    if stored is None or suggestion is None:
        raise AgentsError(422, "no_suggestion")
    try:
        operations = OPERATIONS.validate_python([suggestion.operation()])
        prepared = apply_operations(stored.as_parsed(), operations)
        parsed = parse_dataset(
            prepared.csv,
            text_columns=prepared.text_columns,
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
        parsed = with_date_notes(parsed, prepared)
    except (PrepareError, ParseError, ValidationError):
        raise AgentsError(422, "no_suggestion") from None
    try:
        version = push_version(services.datasets, sid, view, parsed, view.snapshot, rebind=True)
    except StoreFull:
        raise AgentsError(503, "capacity") from None
    await runtime.write_state(session, version.delta)
    return JSONResponse(
        {
            **version.payload(),
            "roles": _page_roles(view.snapshot.roles()),
            "suggestion": _suggestion(view, version.stored.profile),
            "changes": prepared.changes,
        },
        headers=_NO_STORE,
    )


def _suggestion(view: SessionView, profile: DatasetProfile) -> dict[str, Any] | None:
    """The wide-table suggestion for a dataset answer (`data/shape.py`), or None."""
    suggestion = long_suggestion(view.snapshot.roles(), profile)
    return suggestion.body() if suggestion is not None else None


async def _session_sync(
    runtime: Runtime, user: str, sid: str, *, dataset_before: str | None = None, ledger: RequestLedger | None = None
) -> dict[str, Any]:
    """The `done` event's sync fields after a turn: the bindings, whether the data is confirmed, a changed dataset,
    the session language.

    The root's `set_bindings` tool may have changed the bindings (and dropped the
    confirmation) during the turn, and its `prepare_data` or `generate_data` tool the
    dataset itself: when the dataset id differs from `dataset_before`, `dataset` carries
    the new version as the dataset route would answer it (`roles` included, because a
    `generate_data` in a session without data stores its first version, and the page
    learns the spec's roles only from a dataset answer), plus the turn's change lines
    from the ledger. The page learns both from `done`. The scope guard's detection or the
    root's `set_language` may have set the session language, so `language` carries it as
    `{language, source}` after every run, for the page's chip. Empty when the session is
    gone, so the stream still closes.
    """
    try:
        session = await runtime.session(user, sid)
    except Exception:  # expired or purged while the turn ran: the page's next request learns it
        return {}
    view = read_session(session.state)
    if view is None:
        return {}
    payload: dict[str, Any] = {
        "bindings": [binding.model_dump() for binding in view.bindings],
        "data_confirmed": view.data_confirmed,
        "language": {"language": view.language, "source": view.language_source},
    }
    if view.dataset_id and view.dataset_id != dataset_before:
        stored = get_services().datasets.get(view.dataset_id, sid)
        if stored is not None:
            changes = list(ledger.dataset_changes) if ledger is not None else []
            payload["dataset"] = {
                **dataset_payload(stored, view.bindings, view.dataset_version),
                "roles": _page_roles(view.snapshot.roles())[:MAX_DONE_ROLES],
                "suggestion": _suggestion(view, stored.profile),
                "changes": changes,
            }
    return payload


async def _refused(translator: Translator, ledger: RequestLedger) -> AsyncIterator[str]:
    """A turn the ledger refused before the scope judge and any model call: `ready`, the refusal, `done`."""
    yield translator.ready()
    for chunk in translator.refusal():
        yield chunk
    attribution("run", ledger, model_versions=[], kind=ledger.kind)
    yield translator.done()


def _refuse_now(
    translator: Translator, ledger: RequestLedger, code: str, hook: str, **fields: Any
) -> StreamingResponse:
    """The fixed refusal `code` as the whole turn, sent before the judge: no model call, no queue, no message counted."""
    ledger.refuse(code, refusal(code, ledger.lang))
    attribution(hook, ledger, verdict=code, **fields)
    return StreamingResponse(
        _refused(translator, ledger), media_type="text/event-stream", headers={**_NO_STORE, "X-Accel-Buffering": "no"}
    )


async def _produce(
    runtime: Runtime, user: str, sid: str, message: types.Content, run: ActiveRun, outbox: "asyncio.Queue[StreamNote]"
) -> None:
    """The ADK run in a task of its own, its events into the stream's outbox.

    The stream reads the outbox, so the queue positions a sandbox run's `TurnSlot.take`
    puts there while the run is blocked in that tool reach the client meanwhile. An
    exception ends the outbox like the run's end and is raised in the stream.
    """
    settings = get_settings()
    try:
        events = runtime.get_runner().run_async(
            user_id=user,
            session_id=sid,
            new_message=message,
            run_config=RunConfig(max_llm_calls=settings.max_llm_calls, streaming_mode=StreamingMode.NONE),
            abort_signal=run.abort,
        )
        async with contextlib.aclosing(events) as iterator:
            async for event in iterator:
                outbox.put_nowait(("event", event))
    finally:
        outbox.put_nowait(("end", None))


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
        # The refusals sent before the judge (the budget, unsupported content) follow the
        # session language, never the browser's locale; after the judge, the message's.
        lang=refusal_lang(view.language) if view else DEFAULT_LANGUAGE,
    )
    translator = Translator(ledger, run_id=secrets.token_hex(8), spec_id=view.spec_id if view else None)
    # The fixed refusals sent before the scope judge, so none of these turns costs a model call.
    # A closed session answers `session_closed` first: its third `attack` refusal also reaches the strike lockout,
    # which would otherwise mask the closure behind `budget` here (the lockout still covers the user's other sessions).
    refused = scope_refusals(session.events)
    if refused >= settings.session_refusals:
        return _refuse_now(translator, ledger, SESSION_CLOSED, "session_closed", refusals=refused)
    if services.usage.locked_out(user, settings):
        # Past the day's `attack` strikes: its own refusal, never the misleading "usage limit" text (2026-10-14).
        return _refuse_now(translator, ledger, LOCKED_OUT, "budget_halt", agent="route")
    if not budget_allows(ledger, services.usage, settings):
        # The refusal the root would send, sent now: a user over the daily budget spends nothing.
        return _refuse_now(translator, ledger, "budget", "budget_halt", agent="route")
    limit = services.usage.message_limit(user, settings)
    if limit is not None:
        return _refuse_now(translator, ledger, limit, "message_limit")
    services.usage.add_message(user)
    run = ActiveRun(abort=asyncio.Event(), user=user, started=runtime.now())
    # Registered here so a second request cannot slip in before the stream starts; the
    # stream's finally and the background task both clear it and free its queue slot,
    # and an entry neither reached (a client gone before the first byte) goes stale
    # after the deadline (or, while a sandbox run waits, the queue's maximum wait).
    runtime.active[sid] = run
    dataset_before = view.dataset_id if view is not None else None
    if view is not None and view.dataset_id:
        # A hit counts as use: the idle sweep must not take the dataset while the run waits.
        services.datasets.get(view.dataset_id, sid)
    text = ACTION_MESSAGES[body.action] if body.action else (body.text or "")
    reply_language = english_name(view.language) if view is not None else None
    if body.action and reply_language is not None and reply_language != "English":
        # The page's English action line is the turn's only user text: it names the reply language itself
        # (live case of 2026-10-14, a German CSV paste answered in English). The name is the server's own word.
        text = f"{text} {ACTION_LANGUAGE_LINE.format(name=reply_language)}"
    if body.action == "summarize_data" and view is not None and view.dataset_id:
        stored = services.datasets.get(view.dataset_id, sid)
        if stored is not None and stored.context_lines:
            # The notes pasted with the table, judged at the paste (`_screen_notes`): the root sees them with the
            # summary turn that follows every paste, so it can act on a request in them at once.
            text = f"{text}\n\n{user_notes_block(stored.context_lines)}"
        if stored is not None and stored.file_name:
            # A dropped file's name, screened at the paste (`_screen_file_name`): fenced as data, never a note.
            text = f"{text}\n\n{file_name_block(stored.file_name)}"
    message = types.Content(role="user", parts=[types.Part(text=text)])

    async def stream() -> AsyncIterator[str]:
        token = CURRENT_LEDGER.set(ledger)
        deadline = RunDeadline(run, settings.request_deadline_s)
        outbox: asyncio.Queue[StreamNote] = asyncio.Queue()
        # Only a sandbox run takes the queue's slot, mid-turn: everything before it answers at once.
        ledger.run_slot = TurnSlot(runtime, run, sid, ledger, deadline, outbox).take
        producer: asyncio.Task[None] | None = None
        failure: str | None = None
        try:
            yield translator.ready()
            deadline.arm(runtime.now())
            producer = asyncio.create_task(_produce(runtime, user, sid, message, run, outbox))
            while True:
                note = await outbox.get()
                if note[0] == "queued":
                    yield translator.queued(note[1].position, note[1].waiting)
                elif note[0] == "event":
                    for chunk in translator.translate(note[1]):
                        yield chunk
                else:
                    await producer  # raises the run's exception, if it ended with one
                    break
        except Exception as exc:  # the stream always ends with error + done, never a traceback
            logger.warning("run failed (ref %s): %s", rid, type(exc).__name__)
            failure = _error_code(exc)
        except BaseException:  # the generator is closed or cancelled (the client went): release the run now
            runtime.finish(sid, run)
            raise
        finally:
            deadline.cancel()
            if producer is not None and not producer.done():
                producer.cancel()
                with contextlib.suppress(BaseException):
                    await producer
            CURRENT_LEDGER.reset(token)
        try:
            if ledger.error is not None:
                failure = ledger.error
            elif run.deadline_hit and not translator.plot_sent:
                failure = "deadline"
            if failure is not None:
                for chunk in translator.error(failure):
                    yield chunk
            attribution("run", ledger, model_versions=sorted(ledger.model_versions), kind=ledger.kind)
            # Read while the run is still active: no undo or paste can slip in between the run's end
            # and the `done` that reports its dataset, so the version and the change lines agree.
            sync = await _session_sync(runtime, user, sid, dataset_before=dataset_before, ledger=ledger)
        finally:
            runtime.finish(sid, run)
        yield translator.done(**sync)

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


async def _served_png(services: Services, sid: str, render_id: str, theme: Theme, spec_id: str) -> bytes | None:
    """One theme's PNG as a user gets it: with the footer strip (`render/watermark.py`) unless `AGENT_WATERMARK` is off.

    The strip is composed in a worker thread on the first request and cached next to
    the raw render (`RenderStore.shown_png`); the raw PNG itself never changes.
    """
    if not get_settings().watermark:
        stored = services.renders.get(render_id, sid)
        return stored.pngs.get(theme) if stored else None

    async def compose(raw: bytes) -> bytes:
        return await asyncio.to_thread(add_footer, raw, theme=theme, spec_id=spec_id)

    return await services.renders.shown_png(render_id, sid, theme, compose)


@app.get("/v1/sessions/{sid}/artifacts/{name}", dependencies=v1_dependencies)
async def artifact(
    sid: SessionId, name: str, user: User, runtime: RuntimeDep, v: Annotated[int | None, Query(ge=0, le=999)] = None
) -> Response:
    """One artifact of a version; the PNGs carry the footer strip (`AGENT_WATERMARK`), the code and data do not."""
    media_type = ARTIFACT_TYPES.get(name)
    if media_type is None:
        raise AgentsError(404, "not_found")
    session = await runtime.session(user, sid)
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    services = get_services()
    version = services.versions.get(sid, v or None)
    if version is None:
        raise AgentsError(404, "not_found")
    content: bytes | None
    if name == "plot.py":
        content = version.export.encode("utf-8")
    elif name == "data.csv":
        content = version.data_csv.encode("utf-8")
    elif version.render_id:
        theme: Theme = "light" if name == "plot-light.png" else "dark"
        content = await _served_png(services, sid, version.render_id, theme, view.spec_id)
    else:
        content = None
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
    """The feedback case: transcript, code versions, plans, results, profile, bindings, PNGs, config.

    Without `version` every version; with a number above 0 that version only (`404 not_found`
    when the session lacks it); with `version=0` the conversation alone, the feedback on a chat
    that made no plot: no version, and with `include_data` the session's current `data.csv` as
    the top-level `data_csv`.
    """
    session = await runtime.session(user, sid)
    services = get_services()
    settings = get_settings()
    view = read_session(session.state)
    if view is None:
        raise AgentsError(404, "session_expired")
    versions = services.versions.all(sid)
    if version == 0:
        versions = []
    elif version is not None:
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
        images: dict[Theme, str] = {}
        stored = services.renders.get(item.render_id, sid) if item.render_id else None
        if stored is not None:
            for theme in list(stored.pngs):  # a copy: a theme toggle may add a theme during an await
                png = await _served_png(services, sid, stored.render_id, theme, view.spec_id)
                if png is not None:
                    images[theme] = base64.b64encode(png).decode()
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
                "language": item.language,
                "themes": {
                    theme: {"status": record.status, "reason": record.reason} for theme, record in item.themes.items()
                },
                "images": images,
                "data_csv": item.data_csv if include_data else None,
            }
        )
    payload: dict[str, Any] = {
        "session": {
            "spec_id": view.spec_id,
            "library": view.library,
            # The browser's locale (the feedback manifest's `language`); the session language is its own pair.
            "locale": view.locale,
            "plot_language": view.language,
            "plot_language_source": view.language_source,
        },
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
    if version == 0 and include_data:
        # The chat's case has no version to carry the data: the session's current dataset, or none yet.
        payload["data_csv"] = dataset.csv if dataset else None
    if settings.keep_refusals:
        # The transcript holds only the placeholder of a refused message; the ring holds its text.
        payload["refusals"] = [asdict(item) for item in services.refusals.all(sid)]
    return JSONResponse(payload, headers=_NO_STORE)


@app.delete("/v1/sessions/{sid}", status_code=204, dependencies=v1_dependencies)
async def delete_session(sid: SessionId, user: User, runtime: RuntimeDep) -> Response:
    await runtime.session(user, sid)
    await runtime.purge(user, sid, get_services())
    return Response(status_code=204, headers=_NO_STORE)
