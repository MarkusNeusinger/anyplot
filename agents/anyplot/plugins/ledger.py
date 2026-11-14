"""The request ledger and the daily usage book shared by the plugins and the pipeline.

A `RequestLedger` holds what one request (one `Runner.run_async` invocation) has
spent and decided: LLM calls, tokens, `plot_pipeline` calls, the scope verdict, a
refusal or error to report, and the model versions seen. The `/v1` route creates it
and binds it to a context variable before the run starts; ADK runs the invocation in
tasks created inside that context, so every plugin hook and the pipeline see the same
object. Without a route (`adk web`), `ledger_for` creates one per invocation id and
keeps the most recent ones in a small bounded map.

The `UsageBook` holds the per-user and global daily counters for one instance
lifetime (the `aiplatform` spend cap is the real backstop; persisting the counters is
a phase-2 item). Days are UTC dates. Besides tokens, pipeline runs and `run_data_code`
runs (`AGENT_DAILY_DATA_RUNS`, counted before each run) it counts the
`attack` verdicts of the scope and dataset judges per user, once per distinct message
or dataset: from `AGENT_ATTACK_STRIKES` of them on, `daily_ok` is false for that user
for the rest of the day, so a turn gets the budget refusal and a dataset
`429 rate_limited`. It counts the paste notes whose `out_of_scope` verdict went on as
`in_scope` per user and network (`AGENT_PASTE_NOTE_RESCUES`). It also counts each user's chat turns, per UTC day
(`AGENT_USER_MESSAGES_PER_DAY`) and in a sliding minute (`AGENT_USER_MESSAGES_PER_MINUTE`),
which the `/messages` route checks before the scope judge (`message_limit`). Only a new
UTC day, a redeploy or a scale-to-zero resets them.

Every check takes the caller's `Tier`, which the `/v1` route reads from the header the BFF
sets (`agents/main.py` `caller_tier`). An `admin` is exempt from the per-user day caps (the
token budget, the pipeline runs, the data runs, the chat turns) and from the chat turns'
minute (owner decision of 2026-11-01: a fan-out over every library starts a turn and a run
per library); the global day budget and the `attack` strikes bind every tier, the one as
the service's runaway guard, the other as a safety rule rather than a usage cap. Pastes,
file conversions and outcome beacons keep their limits for every tier: they bound memory
and sandbox time, not model spend. The fan-out's copies bind no admin (`copy_limit`): three
windows of `.plot_all()` copy 45 datasets within a minute, and the store's byte cap still
refuses a copy it has no room for.

An anonymous public caller (the public BFF's `X-Anyplot-Anon`) is also bound to the network it
came from (`bind_network`, a salted key of its IPv4 address or IPv6 /64), and its tokens and
pipeline runs count against that network's day too: `AGENT_IP_DAILY_TOKEN_BUDGET` and
`AGENT_IP_DAILY_PIPELINE_RUNS`, twice the per-user caps for shared networks, and so do its
pastes, conversions, chat turns and beacons, in the network's own minute and day at twice the
per-user caps (`IP_WINDOW_FACTOR`). A tab id costs nothing to mint, so the per-user caps alone
would not bound one machine; the network's caps do.

The global day budget binds the whole service: once it is spent (`UsageBook.paused`),
every user gets the `service_paused` refusal (`day_refusal`) until 00:00 UTC, told apart
from a user's own spent budget (`budget`, a paste's `daily_limit`). `UsageBook.snapshot`
answers the admin's live view of the day (`GET /v1/budget`): the global spend and how many
users are at their own limits, counts only, for the instance's lifetime.

The request, user-day and global-day budgets count cost-weighted tokens: each kind
weighted by its price relative to an uncached input token (`BUDGET_WEIGHTS`), so a
cache read counts a tenth and an output token five times. `RequestLedger.tokens` and
`judge_tokens` keep the plain counts that the `done` event and the attribution lines
report.

`attribution` writes one JSON log line per hook with ids, counts and verdicts, and
never content: no message text, no code, no data, no tool arguments (only their
hash). The verdicts of the turn hooks (`TURN_HOOKS`) also go into the request's
`guards`, for the turn's record in the feedback case (`turn_record.py`), without the
line's ids or counts.
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast, get_args

from ..schemas import Theme
from ..settings import AgentSettings


ATTRIBUTION_LOGGER = "anyplot.agents.attribution"
"""The logger of the attribution lines and of the usage telemetry (`telemetry.py`), shipped to stdout by
`agents/main.py` `enable_attribution_log`."""
logger = logging.getLogger(ATTRIBUTION_LOGGER)

RequestKind = Literal["action", "text"]
Tier = Literal["admin", "public"]
"""Who the caller is to the limits: `admin` (the BFF asserts it for an admin identity) or `public` (everyone else,
and every request without the assertion)."""
MAX_ADHOC_LEDGERS = 64


@dataclass
class StepUsage:
    """What one agent (or the judges, under `judge`) spent in a request: calls and tokens by kind, and the model."""

    calls: int = 0
    input: int = 0
    """Prompt tokens, cached and cache-write ones included, plus the Gemini tool-use prompt."""
    output: int = 0
    """Candidates plus thoughts."""
    cached: int = 0
    cache_write: int = 0
    model: str | None = None
    thoughts: int = 0
    """The thinking tokens among `output`, a part of it (the usage telemetry's `StepTokens.thoughts`)."""


@dataclass(frozen=True, slots=True)
class CallFacts:
    """The content-free facts of one model call: how it finished and the output tokens it spent."""

    finish_reason: str | None
    candidates: int = 0
    thoughts: int = 0


CallOutcome = Literal[
    "ok", "changed", "viewed", "kept", "shipped", "failed", "not_ready", "unconfirmed", "error", "refused", "unfinished"
]
"""What one root tool call did, as ToolSafety reads it from the tool's own answer (`tool_safety.call_outcome`):

* `ok`: it answered and changed nothing (a reader, or `keep_plot_request` that kept nothing);
* `changed`: it stored a change in the session (the data, the bindings, a language, the plot memory) or asked the
  page for a library switch;
* `viewed`: a `prepare_data` call that changed the view of the plot alone (`plot_view.py`): which rows the next run
  draws, with the table, its version and the user's confirmation as they were, so a plot may run in the same turn;
* `kept`: a first-plot wish kept for the next run (`keep_plot_request`, a `plot_pipeline` that stopped on
  unconfirmed data and kept the request, or one ToolSafety refused before the run and whose request it kept:
  `data_changed_this_turn`, `summary_turn`);
* `shipped`, `failed`: a `plot_pipeline` run that stored a version, or that ran and stored none;
* `not_ready`: the session was not ready for it (no data, open roles), which for `plot_pipeline` the page shows as a
  failed plot card, a wish it kept or not; `unconfirmed`: a `plot_pipeline` call refused for unconfirmed data that
  kept nothing, which runs no round and shows the page no plot card;
* `error`: it answered an error or raised; `refused`: a guard refused it before it ran (`ToolCall.verdict`);
* `unfinished`: it had not answered when the turn ended (a cancel, a deadline)."""
GuardVerdict = Literal[
    "allowed",
    "tool_not_allowed",
    "invalid_arguments",
    "url_or_path_not_allowed",
    "plot_as_confirmed",
    "one_pipeline_per_turn",
    "switch_requested",
    "data_changed_this_turn",
    "summary_turn",
    "combine_choice",
    "plot_already_run",
    "too_many_data_runs",
    "too_many_prepare_calls",
    "too_many_generate_calls",
    "too_many_query_calls",
    "budget",
    "internal",
    "unknown",
]
"""What the guards said to a root tool call: `allowed`, one of ToolSafety's refusals, the Budget plugin's `budget`
(its daily pipeline runs, which it answers before ToolSafety sees the call), `internal` (a guard failed and refused
the call), or `unknown` for a code outside this list, so the record stays closed when a guard gains a refusal."""
GUARD_VERDICTS: frozenset[str] = frozenset(get_args(GuardVerdict))
SafetyCode = Literal[
    # A refusal before the call runs (`ToolSafetyPlugin.before_tool_callback`): each one a `GuardVerdict` too.
    "tool_not_allowed",
    "invalid_arguments",
    "url_or_path_not_allowed",
    "plot_as_confirmed",
    "one_pipeline_per_turn",
    "switch_requested",
    "data_changed_this_turn",
    "summary_turn",
    "combine_choice",
    "plot_already_run",
    "too_many_data_runs",
    "too_many_prepare_calls",
    "too_many_generate_calls",
    "too_many_query_calls",
    # A result ToolSafety refused (`after_tool_callback`), or a tool's exception (`on_tool_error_callback`).
    "invalid_result",
    "result_too_large",
    "timeout",
    "internal",
]
"""Every code ToolSafety answers a call with (`tool_safety.ErrorCode`), closed so that a new refusal must join this
list, and with it `GuardVerdict` (pinned by a test), before any guard can answer with it."""
TOOL_ALLOWED: GuardVerdict = "allowed"
"""The verdict of a root tool call no guard refused."""


def guard_verdict(code: object) -> GuardVerdict:
    """`code` as a `GuardVerdict`: itself when it is one, else `unknown`."""
    return cast(GuardVerdict, code) if isinstance(code, str) and code in GUARD_VERDICTS else "unknown"


TurnHook = Literal[
    "scope_guard",
    "output_guard",
    "empty_reply",
    "root_refusal",
    "reply_language",
    "shipped_reply",
    "plot_button",
    "budget_exempt",
    "budget_halt",
    "queue",
    "session_closed",
    "message_limit",
]
"""The attribution hooks whose verdicts a turn's record keeps (`RequestLedger.guards`): the scope judge and the
output guard, the reply checks, the Budget plugin's exemption and halt, the run queue, and the `/messages` route's
refusals before the judge (`session_closed`, its own `budget_halt`, `message_limit`). The other hooks stay out: a
tool call's lines (`tool`, `tool_error`, `budget_pipeline`, `data_code`, `data_judge`) because the record's call
entries carry their verdict and outcome, the pipeline's and the model's lines because the session's last run carries
the run, and the paste routes' lines because they run outside a turn (`turn_record.OUTSIDE_HOOKS`)."""
TURN_HOOKS: frozenset[str] = frozenset(get_args(TurnHook))


@dataclass(frozen=True, slots=True)
class ToolCall:
    """One root tool call of the turn: its name, the guards' verdict and what it did, closed codes only.

    `tool` is a root tool's name or `other` (a name the model made up); `verdict` a `GuardVerdict`; `outcome` a
    `CallOutcome`; `code` the closed code of its answer (`turn_record.OutcomeCode`: an error's `code`, the `reason` of
    a stop or a failed run, or ToolSafety's refusal of the result), None for an answer without one and for a call a
    guard refused, whose `verdict` says why. Never an argument, a result or a word of the user: what the turn's
    outcome (`stream.turn_outcome`) reads, and what the turn's record in the feedback case carries
    (`turn_record.TurnRecord`). The record keeps the order the guards saw the calls in: ToolSafety notes each call
    before it runs, and the Budget plugin a pipeline run it refuses first."""

    tool: str
    verdict: GuardVerdict = TOOL_ALLOWED
    outcome: CallOutcome = "unfinished"
    code: str | None = None


def finish_name(value: Any) -> str | None:
    """A response's finish reason as its enum name (`MAX_TOKENS`), whether given as the enum or as text."""
    if value is None:
        return None
    name = getattr(value, "name", None)
    text = name if isinstance(name, str) else str(value)
    return text.removeprefix("FinishReason.") or None


@dataclass
class RequestLedger:
    """What one request has spent and decided.

    `last_calls` maps an agent name to the facts of its latest model call (written by
    the Budget plugin), so the pipeline can tell a cut-off answer from a schema miss
    without reading the answer.
    """

    request_id: str = ""
    user_id: str = ""
    session_id: str = ""
    kind: RequestKind = "text"
    tier: Tier = "public"
    """The caller's tier, set by the `/messages` route from the BFF's assertion: the run queue's lane and the day
    caps' exemptions follow it. `public` without a route (`adk web`)."""
    invocation_id: str | None = None
    llm_calls: int = 0
    tokens: int = 0
    cached_tokens: int = 0
    judge_tokens: int = 0
    budget_tokens: int = 0
    """The model calls' and the judge's cost-weighted tokens (`BUDGET_WEIGHTS`): what the request budget counts."""
    pipeline_active: bool = False
    plot_shipped: bool = False
    """A plot shipped in this invocation: the Budget plugin exempts the root's next call once, without tools."""
    shipped_in_turn: bool = False
    """A plot shipped in this invocation, and it stays so: the Budget plugin spends `plot_shipped` on the closing
    reply's call, so the checks of that reply read this one (`plugins/shipped_reply.py`)."""
    adapter_allow_full: bool = False
    review_render_id: str | None = None
    adapter_renders: list[tuple[str, str]] = field(default_factory=list)
    """Renders the adapter's next call sees, as (label, render id): the current render in a self-review,
    the reviewed render before a repair; empty for an ordinary call."""
    lang: str = "en"
    """The ISO 639-1 code of the fixed refusals: the session language's (`language.refusal_lang`), also after the
    scope judge named another language for the message."""
    language_offer: tuple[str, str] | None = None
    """The language the scope guard offered for this turn's typed message and its basis (`message`), set once it
    recorded the offer (`ScopeGuardPlugin._offer`): the turn's `done` carries it as `language.offer`."""
    paste_context: str | None = None
    """The fenced notes and file name of an unsummarized paste, set by the `/messages` route for the note typed with
    it: the root's session block carries them for the whole turn (`agent.session_context`), so the scope judge, the
    language detection and the stored user turn see only what the user typed. They were judged at the paste."""
    summary_turn: bool = False
    """The `/messages` route's turn is the summary of a paste not summarized yet (the summary action, or the note sent
    with the paste): the root's before-agent callback makes the paste's `certain` conversions (`paste_conversions.py`),
    and ToolSafety refuses the turn's `plot_pipeline` before the run while the data is unconfirmed (`summary_turn`).
    False without a route (`adk web`)."""
    choice_asked: bool = False
    """ToolSafety stopped a `plot_pipeline` call of this turn for the user's choice of sum or mean (`combine_choice`):
    the answer is the user's, so a second call of the turn is stopped too, whatever function it names."""
    paste_note: bool = False
    """The turn's typed text is the note sent with a paste not summarized yet: words about the data that came with it,
    so while that table is stored (`paste_table`) the scope guard refuses it only as an `attack` (or with the fixed
    `other_library` pointer), never as a request for data to fetch, nor as off-topic within the user's day of
    `AGENT_PASTE_NOTE_RESCUES` (`ScopeGuardPlugin._judge`)."""
    paste_table: str | None = None
    """The table the note came with as the scope judge reads it, set by the `/messages` route with `paste_note`: the
    spec's title and the table's column names on one bounded line, never a cell (`scope_guard.paste_table_line`)."""
    conversions_made: str | None = None
    """The id of the data version the server's conversions made in this turn: the session block lists them for every
    model call of the turn, and the route clears the summary flag on this version too."""
    refusal: tuple[str, str] | None = None
    error: str | None = None
    model_versions: set[str] = field(default_factory=set)
    last_calls: dict[str, CallFacts] = field(default_factory=dict)
    dataset_changes: list[str] = field(default_factory=list)
    """The change lines of every `prepare_data` call of the turn, in order: the `done` event's `dataset.changes`."""
    data_step: tuple[str, str] | None = None
    """The dataset id and the announcement of the repeated key a plot run of this invocation combined
    (`repeated_keys.combine_repeated_key`), so a run ADK re-runs on resume, which finds the key combined already,
    announces the step all the same."""
    example_data: bool = False
    """A `run_data_code` call of this invocation stored example data the user asked for (`source_language` `example`):
    the `chat_turn` line's `kind` is `example`."""
    root_request: Any = None
    """The root's latest `LlmRequest`, kept by the reply-language plugin so a reply in the wrong language can be
    asked again once with the same context (`plugins/reply_language.py`)."""
    reply_reasked: bool = False
    """The reply-language plugin asked the root again in this invocation: at most once per turn."""
    empty_reasked: bool = False
    """The empty-reply plugin asked the root again for a final reply without text: at most once per turn
    (`plugins/empty_reply.py`)."""
    refusal_reasked: bool = False
    """The root-refusal plugin asked the root again for a message the scope judge passed and the root answered with a
    fixed refusal: at most once per turn (`plugins/root_refusal.py`)."""
    reply_shortened: bool = False
    """The output guard asked the root for a shorter reply in this invocation: at most once per turn
    (`ScopeGuardPlugin._guard_reply`)."""
    run_slot: Callable[[], Awaitable[bool]] | None = None
    """Set by the `/messages` route (`TurnSlot.take`): waits for the run queue's slot and the turn's start in the
    rate window, while the stream sends `status{step:"queued"}`, and holds both until the turn ends. True once the
    turn holds them (at once on a second call); False when the queue is full, the wait ran out or the turn was
    cancelled, after the route failed the turn with `capacity` (or ended it). None without a route (`adk web`),
    whose runs bypass the queue. The one helper for every sandbox run of a turn: `plot_pipeline` and
    `run_data_code` await it before they render or run code."""
    spec_id: str = ""
    library: str = ""
    turn: int = 0
    """The session's spec, library and user turn, set once by the `/v1` route from session state, for the
    usage telemetry's envelope (`telemetry.py`); never set per call site."""
    fanout: bool = False
    """The session was opened by the admin's "plot in all libraries" fan-out (`session_state.TELEMETRY_SOURCE`), set
    with the envelope: its telemetry lines carry the source `fanout` instead of `live`."""
    steps: dict[str, StepUsage] = field(default_factory=dict)
    """Calls and tokens by agent name (`book_step`), and the judges' under `judge` (`book_judge`)."""
    tools: list[str] = field(default_factory=list)
    """The tools the root called and ToolSafety allowed, in order (closed names only: `telemetry.TOOL_NAMES`): the one
    count the turn's caps and bounds read (`calls_of`), so a refused call never counts against them."""
    tool_calls: list[ToolCall] = field(default_factory=list)
    """Every root tool call of the turn in the order the guards saw them, refused ones too, each with the guards'
    verdict and what it did (`ToolCall`), written by ToolSafety and, for a pipeline run it refuses first, the Budget
    plugin (`open_call`, `close_call`, `fail_call`): the turn's `done.turn` (`stream.turn_outcome`) reads it, and the
    turn's record in the feedback case bundle carries it (`turn_record.py`). `tools` stays the allowed names alone,
    which the usage telemetry, EmptyReply and the turn's caps read."""
    open_calls: dict[str, list[int]] = field(default_factory=dict, repr=False)
    """The `tool_calls` indexes still waiting for their answer, by ADK's function call id (the tool's name for a call
    without one): parallel calls of one model answer close in any order. Never logged or sent."""
    guards: list[tuple[str, str | None]] = field(default_factory=list)
    """The verdicts of the turn's hooks (`TURN_HOOKS`) in the order they were logged, as (hook, verdict): written by
    `attribution` itself, so a hook's line and its verdict here never differ. The hook's other fields (counts,
    languages, waits) never come here; the turn's record closes both names (`turn_record.GuardLine`)."""
    shipped_memory: dict[str, list[str]] | None = None
    """The plot memory a shipped version stands on, `{kept, added}`: the ids of the entries from before the run that
    it kept, and of the entries its own `remember` items added (`pipeline.memory_ids`), set once the memory is settled
    with the version. The `plot` event carries it as `memory`; None for a run that stored no version."""
    prep_ops: list[str] = field(default_factory=list)
    """The operation names of every `prepare_data` call that changed the data (closed: `telemetry.PREP_OPS`)."""
    view_ops: list[str] = field(default_factory=list)
    """The operation names of this turn's `prepare_data` calls that landed in the view of the plot (`plot_view.route`;
    closed like `prep_ops`): they changed no data, so nothing that asks whether the turn changed the data reads them."""
    rebuilt_from: list[int] = field(default_factory=list)
    """The numbers of the earlier versions this turn's `prepare_data` calls started from (`from_version`): a rebuild
    changed the data also without an operation, which `prep_ops` would not show."""
    capability_gaps: list[str] = field(default_factory=list)
    """The families of the `unsupported` operations the root named in this turn: a data change no operation can make
    (closed: `telemetry.CAPABILITY_GAPS`), never a word of what the user asked."""
    reply_question: bool = False
    """The root's last reply sent to the page ends with a question mark (`stream.Translator`); the text is never kept."""
    queue_position: int | None = None
    queue_wait_s: float | None = None
    """Where the turn's run-queue entry stood at submit (0: it started at once) and how long it waited, set by the
    route once the entry starts (`TurnSlot.take`); None for a turn that never ran sandbox work. The usage telemetry's
    `queue_position` and `queue_wait_ms` (`pipeline_run`)."""
    user_runs_today: int | None = None
    user_tokens_share: float | None = None
    """This run's ordinal among the user's pipeline runs of the UTC day, and the share of the public per-user daily
    token budget (`AGENT_DAILY_TOKEN_BUDGET`) the user had spent when it was booked, admins measured against it too,
    set by the Budget plugin (`before_tool_callback`). Only their buckets reach the telemetry, never the user."""
    site_theme: Theme | None = None
    """The theme the page showed the site in when the user sent the turn (`/messages?theme=`), which a plot run takes
    when neither the user nor the version it changes asked for one (`pipeline.run_theme`); None without a page."""
    switch_request: dict[str, Any] | None = None
    """The switch the root's `switch_plot` asked for in this turn, `{library, plot}` (and `spec_id` once the plot type
    can change): the `done` event carries it as `switch`, and the page carries it out with the switch route and, with
    `plot`, the carry run (2026-11-02). The tool writes no state, so a turn that asks for it changes nothing itself."""
    fresh_start: bool = False
    """The turn is the page's `create_plot` action (`.create_plot()`, `.start_over()`): its run starts from the
    catalogue code whatever base the root passes, without a switch's carry, and applies the plot memory, which only the
    user clears (`pipeline.Run.fresh`, owner decision of 2026-11-02)."""
    new_data: bool = False
    """The turn is the page's `plot_new_data` action ("plot the new data"): its run starts from the library's latest
    version with the server's data-change request while that version drew the same paste with the same bindings,
    else from the catalogue code like `fresh_start` (`pipeline.new_data_base`, owner decision of 2026-11-08)."""
    plot_action: bool = False
    """The turn is one of the page's plot buttons (`create_plot` or `carry_plot`, which the admin fan-out's `.plot_all()`
    also sends in each library's session, or `plot_new_data`): the click confirmed the data and the bindings as shown,
    so the turn plots them as they are and ToolSafety refuses every tool that would change something
    (`PLOT_ACTION_TOOLS`); the session block says to call `plot_pipeline` with no arguments
    (`agent.PLOT_ACTION_LINE`)."""
    user_words: str | None = None
    """The user's own text for the turn, set by the `/messages` route: the typed message and the notes pasted with
    the session's data; empty for an action on data without notes. A text the plot is checked for must stand in it
    (`pipeline.in_users_words`); None (a caller without a page turn) checks nothing."""
    kept_note: Any = None
    """The `PipelineArgs` of the first-plot note this turn kept (`keep_plot_request`, a run that stopped `not_ready`,
    or a `plot_pipeline` call ToolSafety refused before the run, `pipeline.stop_not_ready`): after the turn the note is held for the bindings and data the turn ends with (`_settle_kept_note`
    in `agents/main.py`), so the turn's own `set_bindings` or `prepare_data` never voids it."""

    def book_step(self, agent: str, *, model: str | None, usage: dict[str, int], cached: int) -> None:
        """Add one model call to the agent's step usage (`usage` as `usage_breakdown` counts it)."""
        step = self.steps.setdefault(agent, StepUsage())
        step.calls += 1
        step.input += usage.get("prompt", 0) + usage.get("tool_use_prompt", 0)
        step.output += usage.get("candidates", 0) + usage.get("thoughts", 0)
        step.thoughts += usage.get("thoughts", 0)
        step.cached += cached
        step.cache_write += usage.get("cache_write", 0)
        if model:
            step.model = model

    def book_judge(self, input_tokens: int, output_tokens: int, tokens: int = 0) -> None:
        """Add one judge verdict (scope, dataset, notes, file name, transcriber) to the `judge` step."""
        step = self.steps.setdefault("judge", StepUsage())
        step.calls += 1
        if input_tokens or output_tokens:
            step.input += input_tokens
            step.output += output_tokens
        else:
            step.input += tokens  # no split reported: the plain total counts as input

    def calls_of(self, tool: str) -> int:
        """How many calls of `tool` ToolSafety allowed in this turn (`tools`): what every per-turn cap counts."""
        return self.tools.count(tool)

    def open_call(self, key: str, tool: str, verdict: str, *, refused: CallOutcome = "refused") -> None:
        """Note a root tool call as the guards judged it; a refused one is closed already, `refused` or what the
        refusal itself did (a `plot_pipeline` refused before the run that kept the request: `kept`)."""
        closed = guard_verdict(verdict)
        self.tool_calls.append(ToolCall(tool, closed, "unfinished" if closed == TOOL_ALLOWED else refused))
        self.open_calls.setdefault(key, []).append(len(self.tool_calls) - 1)

    def close_call(
        self, key: str, tool: str, outcome: CallOutcome, *, early_verdict: str, code: str | None = None
    ) -> None:
        """Note what an opened call did and the code of its answer; a refused call stays `refused`. A call no
        `open_call` noted (its note failed) goes in when it closes: refused by `early_verdict` when its answer is an
        error, which a plugin before ToolSafety may have given, else allowed with what it did, so a change it stored
        still counts."""
        waiting = self.open_calls.get(key)
        if not waiting:
            if outcome == "error":
                self.tool_calls.append(ToolCall(tool, guard_verdict(early_verdict), "refused"))
            else:
                self.tool_calls.append(ToolCall(tool, TOOL_ALLOWED, outcome, code))
            return
        index = waiting.pop(0)
        if not waiting:
            del self.open_calls[key]
        call = self.tool_calls[index]
        if call.outcome == "unfinished":
            self.tool_calls[index] = ToolCall(call.tool, call.verdict, outcome, code)

    def fail_call(self, key: str, code: str) -> None:
        """Note the error answer of an opened call that raised (`on_tool_error_callback`), before its close: a call
        ADK could not find (a tool the request did not declare, as on the closing reply) gets no after-tool callback,
        so it would stay `unfinished`. The call stays open; its close, when it comes, reads the same answer. Calls
        without a function call id share their tool's key and close in order (`close_call`), so of two such calls
        of one tool, one that raised can mark its sibling instead; ADK sets the id on every call."""
        for index in self.open_calls.get(key, []):
            call = self.tool_calls[index]
            if call.outcome == "unfinished":
                self.tool_calls[index] = ToolCall(call.tool, call.verdict, "error", code)
                return

    def note_guard(self, hook: str, verdict: Any) -> None:
        """Note a turn hook's verdict for the turn's record (`guards`), from its attribution line (`attribution`).

        A hook whose line has no `verdict` gets a fixed one: `budget_exempt` reads `exempt`, the Budget plugin's
        `budget_halt` the refusal it set (`refusal`), which the record closes as `telemetry.RefusalCode`."""
        if verdict is None:
            if hook == "budget_exempt":
                verdict = "exempt"
            elif hook == "budget_halt" and self.refusal is not None:
                verdict = self.refusal[0]
        self.guards.append((hook, verdict if isinstance(verdict, str) else None))

    def refuse(self, code: str, text: str) -> None:
        if self.refusal is None and self.error is None:
            self.refusal = (code, text)

    def fail(self, code: str) -> None:
        if self.error is None:
            self.error = code

    @property
    def halted(self) -> bool:
        return self.refusal is not None or self.error is not None


CURRENT_LEDGER: ContextVar[RequestLedger | None] = ContextVar("anyplot_request_ledger", default=None)
_ADHOC: "OrderedDict[str, RequestLedger]" = OrderedDict()


def ledger_for(invocation_id: str) -> RequestLedger:
    """The ledger of the running request: the route's, else one per invocation id."""
    current = CURRENT_LEDGER.get()
    if current is not None:
        if current.invocation_id is None:
            current.invocation_id = invocation_id
        return current
    ledger = _ADHOC.get(invocation_id)
    if ledger is None:
        ledger = RequestLedger(invocation_id=invocation_id)
        _ADHOC[invocation_id] = ledger
        while len(_ADHOC) > MAX_ADHOC_LEDGERS:
            _ADHOC.popitem(last=False)
    return ledger


def today() -> str:
    return datetime.now(UTC).date().isoformat()


def utc_stamp(moment: datetime) -> str:
    """An instant as the API writes one: ISO 8601 in UTC to the second, with a `Z`."""
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def next_reset(now: datetime | None = None) -> datetime:
    """The next 00:00 UTC: when the usage book starts a new day and every daily counter, the global one included,
    starts again from zero."""
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return datetime.combine(current.date() + timedelta(days=1), datetime.min.time(), UTC)


SERVICE_PAUSED = "service_paused"
"""The refusal and the paste route's `429` once the global day budget is spent: the whole service pauses until
00:00 UTC, whatever the user's own counts (owner request of 2026-11-02: tell it apart from the user's own limit)."""


@dataclass
class _Day:
    date: str
    user_tokens: dict[str, int] = field(default_factory=dict)
    user_runs: dict[str, int] = field(default_factory=dict)
    global_tokens: int = 0
    user_strikes: dict[str, set[str]] = field(default_factory=dict)
    user_data_runs: dict[str, int] = field(default_factory=dict)
    user_messages: dict[str, int] = field(default_factory=dict)
    user_pastes: dict[str, int] = field(default_factory=dict)
    user_conversions: dict[str, int] = field(default_factory=dict)
    user_outcomes: dict[str, int] = field(default_factory=dict)
    user_copies: dict[str, int] = field(default_factory=dict)
    admins: set[str] = field(default_factory=set)
    """The users who came in the admin tier today (`mark_admin`): the book has no tier of its own, each request does."""
    user_networks: "OrderedDict[str, str]" = field(default_factory=OrderedDict)
    """The network key (`network_key`) each anonymous user's latest request came from today (`bind_network`)."""
    network_tokens: dict[str, int] = field(default_factory=dict)
    network_runs: dict[str, int] = field(default_factory=dict)
    """The per-IP day counts: what every anonymous user bound to a network booked while bound to it."""
    network_windows: dict[tuple["WindowKind", str], int] = field(default_factory=dict)
    """The per-IP day counts of the windowed kinds (pastes, conversions, chat turns, beacons), by kind and network."""
    user_note_rescues: dict[str, int] = field(default_factory=dict)
    network_note_rescues: dict[str, int] = field(default_factory=dict)
    """The paste notes whose `out_of_scope` verdict went on as `in_scope` today, per user and per network
    (`AGENT_PASTE_NOTE_RESCUES`, `UsageBook.note_rescue_ok`)."""


MESSAGE_WINDOW_S = 60.0
"""The sliding window of `AGENT_USER_MESSAGES_PER_MINUTE` and `AGENT_USER_PASTES_PER_MINUTE`."""
MAX_BOUND_USERS = 50_000
"""The anonymous users the usage book keeps a network binding for (`UsageBook.bind_network`), the least recently
bound leaving first: a few MiB at most, however many tab ids a client mints."""
IP_WINDOW_FACTOR = 2
"""How many users' worth of pastes, conversions, chat turns and beacons the anonymous users of one network share, per
minute and per day: twice the per-user caps, as for the network's runs and tokens (`AGENT_IP_*`), for shared networks.
A constant, like the beacon caps: it scales the per-user settings rather than adding one per kind."""
MessageLimit = Literal["rate_limited", "daily_limit"]
"""Why `message_limit` or `paste_limit` refuses: the minute's count, or the day's."""
WindowKind = Literal["message", "paste", "convert", "outcome", "copy"]
OUTCOMES_PER_MINUTE = 30
OUTCOMES_PER_DAY = 2000
"""The page's outcome beacons per user (`POST /v1/sessions/{sid}/outcome`): a copy or a download is one click, so
30 in a minute is far beyond use; more get `429 rate_limited`, which the page ignores. Constants, not settings: the
beacon spends no model call and no sandbox time, the cap only bounds the telemetry lines one user can write."""
COPIES_PER_MINUTE = 30
COPIES_PER_DAY = 150
"""The admin fan-out's data copies per user (`POST /v1/sessions/{sid}/dataset/copy`): one per library of a
`.plot_all()`, at most 15, so 30 in a minute is two fan-outs and 150 a day about ten (1.5 times the day's 100 pastes,
review of 2026-11-01: 600 let one user put about 3 GiB a day into the 256 MiB store). A copy parses nothing and calls
no model, so it is no paste, but each one takes the dataset's size in the store again: the cap bounds what one user
can put there. A per-user byte budget in the store is the follow-up before the chat goes public. Constants, not
settings, like the outcome beacons'. An admin is exempt from both (owner decision of 2026-11-01, `copy_limit`)."""


LimitKind = Literal["tokens", "runs", "data_runs", "messages", "pastes", "conversions", "locked_out"]
"""The day caps of one user that `UsageBook.snapshot` counts users at: the token budget, the pipeline runs, the
`run_data_code` runs, the chat turns, the pastes, the file conversions, and the `attack` strikes."""
LIMIT_KINDS: tuple[LimitKind, ...] = ("tokens", "runs", "data_runs", "messages", "pastes", "conversions", "locked_out")


@dataclass(frozen=True)
class DaySnapshot:
    """The usage book's day as the admin's live view reads it (`GET /v1/budget`): counts only, never a user id."""

    date: str
    since: datetime
    """When this day's counts began: the book's start when the instance started today, else 00:00 UTC."""
    started_at: datetime
    """When this instance's usage book started: a redeploy or a scale-to-zero starts a new one at zero."""
    global_tokens: int
    users: int
    """Users with a chat turn, a paste, a conversion, a run, booked tokens or a strike today."""
    at_limit: int
    """Users at one or more of their own day caps (`limits`), each counted once."""
    limits: dict[LimitKind, int]
    """Users at each day cap; a user at two caps counts under both, an admin never under one they are exempt from."""


class UsageBook:
    """Per-user and global daily counters for this instance's lifetime, and each user's messages and pastes of the
    last minute."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._day = _Day(today())
        self._previous_networks: dict[str, str] = {}
        """Yesterday's network bindings (`bind_network`), for a turn that started before 00:00 UTC and books after it."""
        self._clock = clock
        self._recent: dict[tuple[WindowKind, str], deque[float]] = {}
        self.started_at = datetime.now(UTC)
        """When the book began counting: in production the instance's first request (`services.get_services`)."""

    def _current(self) -> _Day:
        date = today()
        if self._day.date != date:
            self._previous_networks = self._day.user_networks
            self._day = _Day(date)
        return self._day

    def _network(self, user_id: str) -> str | None:
        """The user's network: today's binding, else yesterday's, so a turn that runs across midnight still counts
        toward the network it came from until the user's next request binds them anew."""
        day = self._current()
        return day.user_networks.get(user_id) or self._previous_networks.get(user_id)

    def bind_network(self, user_id: str, network: str) -> None:
        """Count the anonymous user's tokens and pipeline runs against `network` (a `network_key`) from now on, as
        well as against the user: the per-IP caps (`AGENT_IP_*`). The latest request's network wins, so a phone that
        changes networks moves on; what it booked stays where it was booked. Bound for the UTC day, and into the next
        one until the user's next request, so a turn that runs across midnight keeps counting (`_network`).

        At most `MAX_BOUND_USERS` bindings are kept, the least recently bound one leaving first: every request binds
        again, so an active user is always bound, while a flood of fresh tab ids cannot grow the map without end."""
        bindings = self._current().user_networks
        bindings[user_id] = network
        bindings.move_to_end(user_id)
        while len(bindings) > MAX_BOUND_USERS:
            bindings.popitem(last=False)

    def network_of(self, user_id: str) -> str | None:
        """The network the user is bound to (`bind_network`); None for every caller but an anonymous one."""
        return self._network(user_id)

    def add_tokens(self, user_id: str, tokens: int) -> None:
        """Book cost-weighted tokens (`weighted_tokens`) against the user's, their network's and the service's day."""
        day = self._current()
        day.user_tokens[user_id] = day.user_tokens.get(user_id, 0) + tokens
        day.global_tokens += tokens
        network = self._network(user_id)
        if network is not None:
            day.network_tokens[network] = day.network_tokens.get(network, 0) + tokens

    def add_pipeline_run(self, user_id: str) -> None:
        day = self._current()
        day.user_runs[user_id] = day.user_runs.get(user_id, 0) + 1
        network = self._network(user_id)
        if network is not None:
            day.network_runs[network] = day.network_runs.get(network, 0) + 1

    def network_tokens(self, user_id: str) -> int:
        """The weighted tokens booked today on the user's network; 0 for a user bound to none."""
        network = self._network(user_id)
        return 0 if network is None else self._current().network_tokens.get(network, 0)

    def network_runs(self, user_id: str) -> int:
        """The pipeline runs booked today on the user's network; 0 for a user bound to none."""
        network = self._network(user_id)
        return 0 if network is None else self._current().network_runs.get(network, 0)

    def own_tokens_left(self, user_id: str, settings: AgentSettings, reserve: int = 0) -> bool:
        """The public caps on model spend, `reserve` tokens beyond today's: the user's day budget and, for an
        anonymous user, their network's."""
        return (
            self.user_tokens(user_id) + reserve < settings.daily_token_budget
            and self.network_tokens(user_id) + reserve < settings.ip_daily_token_budget
        )

    def user_tokens(self, user_id: str) -> int:
        return self._current().user_tokens.get(user_id, 0)

    def user_runs(self, user_id: str) -> int:
        return self._current().user_runs.get(user_id, 0)

    def global_tokens(self) -> int:
        return self._current().global_tokens

    def add_strike(self, user_id: str, content: str) -> int:
        """Count one `attack` verdict against the user for today, once per distinct content; the new count.

        `content` is the refused message's text or the refused dataset's canonical CSV;
        only its hash is kept. Retrying the same message or upload after a false
        `attack` verdict therefore costs one strike, not one per try.
        """
        day = self._current()
        day.user_strikes.setdefault(user_id, set()).add(hashlib.sha256(content.encode()).hexdigest()[:16])
        return len(day.user_strikes[user_id])

    def user_strikes(self, user_id: str) -> int:
        return len(self._current().user_strikes.get(user_id, ()))

    def daily_ok(self, user_id: str, settings: AgentSettings, *, reserve: int = 0, tier: Tier = "public") -> bool:
        """Whether the user and the service still have daily token budget, `reserve` tokens beyond the spend, and strikes left.

        An `admin` has no daily token budget of their own: only the service's and the strikes bind them. An anonymous
        user also needs their network's day budget (`AGENT_IP_DAILY_TOKEN_BUDGET`, `bind_network`).
        """
        return (
            (tier == "admin" or self.own_tokens_left(user_id, settings, reserve))
            and self.global_tokens() + reserve < settings.global_daily_token_budget
            and self.user_strikes(user_id) < settings.attack_strikes
        )

    def note_rescue_ok(self, user_id: str, settings: AgentSettings) -> bool:
        """Whether a note typed with a paste may still go on past an `out_of_scope` verdict today: fewer than
        `AGENT_PASTE_NOTE_RESCUES` for the user and, for an anonymous user, fewer than `IP_WINDOW_FACTOR` times as many
        for their network, since a tab id costs nothing to mint. Every tier: the cap bounds a channel to the root that
        no refusal counts, a safety rule like the strikes rather than a usage cap."""
        day = self._current()
        if day.user_note_rescues.get(user_id, 0) >= settings.paste_note_rescues:
            return False
        network = self._network(user_id)
        return (
            network is None or day.network_note_rescues.get(network, 0) < IP_WINDOW_FACTOR * settings.paste_note_rescues
        )

    def add_note_rescue(self, user_id: str) -> None:
        """Count one rescued paste note against the user's day and, for an anonymous user, their network's."""
        day = self._current()
        day.user_note_rescues[user_id] = day.user_note_rescues.get(user_id, 0) + 1
        network = self._network(user_id)
        if network is not None:
            day.network_note_rescues[network] = day.network_note_rescues.get(network, 0) + 1

    def locked_out(self, user_id: str, settings: AgentSettings) -> bool:
        """Whether the user's `attack` strikes reached `AGENT_ATTACK_STRIKES` today: the `locked_out` refusal, which
        `daily_ok` folds into its answer, told apart from a spent token budget."""
        return self.user_strikes(user_id) >= settings.attack_strikes

    def paused(self, settings: AgentSettings) -> bool:
        """Whether the service's day budget (`AGENT_GLOBAL_DAILY_TOKEN_BUDGET`) is spent: the `service_paused` refusal
        for everyone until 00:00 UTC, which `daily_ok` folds into its answer."""
        return self.global_tokens() >= settings.global_daily_token_budget

    def mark_admin(self, user_id: str) -> None:
        """Remember for today that this user came in the admin tier, for `snapshot`: `agents/main.py` `_stamp`, which
        every route that spends passes."""
        self._current().admins.add(user_id)

    def snapshot(self, settings: AgentSettings) -> DaySnapshot:
        """Today's global spend and how many users are at their own day caps, as counts (`DaySnapshot`). An admin
        counts only at the caps that bind every tier: the pastes, the conversions and the strikes."""
        day = self._current()
        reached: dict[LimitKind, set[str]] = {
            "tokens": _at_least(day.user_tokens, settings.daily_token_budget) - day.admins,
            "runs": _at_least(day.user_runs, settings.daily_pipeline_runs) - day.admins,
            "data_runs": _at_least(day.user_data_runs, settings.daily_data_runs) - day.admins,
            "messages": _at_least(day.user_messages, settings.user_messages_per_day) - day.admins,
            "pastes": _at_least(day.user_pastes, settings.user_pastes_per_day),
            "conversions": _at_least(day.user_conversions, settings.user_conversions_per_day),
            "locked_out": {
                user for user, strikes in day.user_strikes.items() if len(strikes) >= settings.attack_strikes
            },
        }
        users = set().union(
            day.user_tokens,
            day.user_runs,
            day.user_data_runs,
            day.user_messages,
            day.user_pastes,
            day.user_conversions,
            day.user_strikes,
        )
        midnight = datetime.fromisoformat(day.date).replace(tzinfo=UTC)
        return DaySnapshot(
            date=day.date,
            since=max(self.started_at, midnight),
            started_at=self.started_at,
            global_tokens=day.global_tokens,
            users=len(users),
            at_limit=len(set().union(*reached.values())),
            limits={kind: len(reached[kind]) for kind in LIMIT_KINDS},
        )

    def runs_ok(self, user_id: str, settings: AgentSettings, tier: Tier = "public") -> bool:
        """Whether the user may start another pipeline run today (`AGENT_DAILY_PIPELINE_RUNS`, and for an anonymous
        user their network's `AGENT_IP_DAILY_PIPELINE_RUNS`); always for an admin."""
        return tier == "admin" or (
            self.user_runs(user_id) < settings.daily_pipeline_runs
            and self.network_runs(user_id) < settings.ip_daily_pipeline_runs
        )

    def add_data_run(self, user_id: str) -> None:
        """Count one `run_data_code` run against the user's day, before it runs."""
        day = self._current()
        day.user_data_runs[user_id] = day.user_data_runs.get(user_id, 0) + 1

    def user_data_runs(self, user_id: str) -> int:
        return self._current().user_data_runs.get(user_id, 0)

    def data_runs_ok(self, user_id: str, settings: AgentSettings, tier: Tier = "public") -> bool:
        """Whether the user may run another data snippet today (`AGENT_DAILY_DATA_RUNS`); always for an admin."""
        return tier == "admin" or self.user_data_runs(user_id) < settings.daily_data_runs

    def user_messages(self, user_id: str) -> int:
        """The user's chat turns today (typed messages and actions alike) that passed `message_limit`."""
        return self._current().user_messages.get(user_id, 0)

    def message_limit(self, user_id: str, settings: AgentSettings, tier: Tier = "public") -> MessageLimit | None:
        """Why the user may not send another chat turn now, or None; checked before the scope judge, so a flood costs
        no model call. A refused turn is not counted: the window frees itself one minute after the last counted one.
        Never a limit for an admin, whose turns are still counted."""
        if tier == "admin":
            return None
        return self._limit(
            "message",
            user_id,
            self.user_messages(user_id),
            settings.user_messages_per_minute,
            settings.user_messages_per_day,
        )

    def add_message(self, user_id: str) -> None:
        """Count one chat turn against the user's minute and day."""
        day = self._current()
        day.user_messages[user_id] = day.user_messages.get(user_id, 0) + 1
        self._stamp("message", user_id)

    def user_pastes(self, user_id: str) -> int:
        """The user's dataset pastes today that passed `paste_limit`."""
        return self._current().user_pastes.get(user_id, 0)

    def paste_limit(self, user_id: str, settings: AgentSettings) -> MessageLimit | None:
        """Why the user may not paste another dataset now, or None: `AGENT_USER_PASTES_PER_MINUTE` and
        `AGENT_USER_PASTES_PER_DAY`, across sessions, checked before any parser or model reads the paste."""
        return self._limit(
            "paste", user_id, self.user_pastes(user_id), settings.user_pastes_per_minute, settings.user_pastes_per_day
        )

    def add_paste(self, user_id: str) -> None:
        """Count one dataset paste against the user's minute and day."""
        day = self._current()
        day.user_pastes[user_id] = day.user_pastes.get(user_id, 0) + 1
        self._stamp("paste", user_id)

    def user_conversions(self, user_id: str) -> int:
        """The user's file conversions today that passed `convert_limit`."""
        return self._current().user_conversions.get(user_id, 0)

    def convert_limit(self, user_id: str, settings: AgentSettings) -> MessageLimit | None:
        """Why the user may not convert another file now, or None: `AGENT_USER_CONVERSIONS_PER_MINUTE` and
        `_PER_DAY`, across sessions, checked before the file reaches the sandbox."""
        return self._limit(
            "convert",
            user_id,
            self.user_conversions(user_id),
            settings.user_conversions_per_minute,
            settings.user_conversions_per_day,
        )

    def add_conversion(self, user_id: str) -> None:
        """Count one file conversion against the user's minute and day."""
        day = self._current()
        day.user_conversions[user_id] = day.user_conversions.get(user_id, 0) + 1
        self._stamp("convert", user_id)

    def outcome_limit(self, user_id: str) -> MessageLimit | None:
        """Why the user's page may not write another outcome beacon now, or None (`OUTCOMES_PER_MINUTE`, `_PER_DAY`)."""
        count = self._current().user_outcomes.get(user_id, 0)
        return self._limit("outcome", user_id, count, OUTCOMES_PER_MINUTE, OUTCOMES_PER_DAY)

    def add_outcome(self, user_id: str) -> None:
        day = self._current()
        day.user_outcomes[user_id] = day.user_outcomes.get(user_id, 0) + 1
        self._stamp("outcome", user_id)

    def copy_limit(self, user_id: str, tier: Tier = "public") -> MessageLimit | None:
        """Why the user may not copy another dataset into a fan-out session now, or None (`COPIES_PER_MINUTE`,
        `_PER_DAY`). Never a limit for an admin (owner decision of 2026-11-01), whose copies are still counted: three
        windows of `.plot_all()` copy 45 datasets within a minute, and the store's own byte cap still refuses a copy
        it has no room for (`503 capacity`)."""
        if tier == "admin":
            return None
        count = self._current().user_copies.get(user_id, 0)
        return self._limit("copy", user_id, count, COPIES_PER_MINUTE, COPIES_PER_DAY)

    def add_copy(self, user_id: str) -> None:
        """Count one dataset copy against the user's minute and day."""
        day = self._current()
        day.user_copies[user_id] = day.user_copies.get(user_id, 0) + 1
        self._stamp("copy", user_id)

    def _limit(
        self, kind: WindowKind, user_id: str, today_count: int, per_minute: int, per_day: int
    ) -> MessageLimit | None:
        """The user's minute and day for `kind`, and for an anonymous user their network's, at `IP_WINDOW_FACTOR`
        times the user's caps: a tab id costs nothing to mint, so the network's windows are what bound one machine's
        pastes, conversions, chat turns and beacons."""
        if today_count >= per_day:
            return "daily_limit"
        recent = self._trimmed(kind, user_id)
        if recent is not None and len(recent) >= per_minute:
            return "rate_limited"
        network = self._network(user_id)
        if network is None:
            return None
        if self._current().network_windows.get((kind, network), 0) >= IP_WINDOW_FACTOR * per_day:
            return "daily_limit"
        shared = self._trimmed(kind, network)
        if shared is not None and len(shared) >= IP_WINDOW_FACTOR * per_minute:
            return "rate_limited"
        return None

    def _stamp(self, kind: WindowKind, user_id: str) -> None:
        """Count one `kind` against the user's minute, and against their network's minute and day."""
        keys = [user_id]
        network = self._network(user_id)
        if network is not None:
            day = self._current()
            day.network_windows[(kind, network)] = day.network_windows.get((kind, network), 0) + 1
            keys.append(network)
        for key in keys:
            recent = self._trimmed(kind, key)
            if recent is None:
                recent = self._recent[(kind, key)] = deque()
            recent.append(self._clock())

    def _trimmed(self, kind: WindowKind, user_id: str) -> deque[float] | None:
        """The user's times of `kind` within the window, oldest first; a user with none left is forgotten."""
        key = (kind, user_id)
        recent = self._recent.get(key)
        if recent is None:
            return None
        now = self._clock()
        while recent and now - recent[0] >= MESSAGE_WINDOW_S:
            recent.popleft()
        if not recent:
            del self._recent[key]
            return None
        return recent


def _at_least(counts: dict[str, int], cap: int) -> set[str]:
    return {user for user, count in counts.items() if count >= cap}


def day_refusal(usage: UsageBook, user_id: str, settings: AgentSettings, *, tier: Tier = "public") -> str:
    """Which refusal a failed `daily_ok` is: `locked_out` past the day's strikes, `budget` when the user's own day
    budget is spent, `service_paused` when only the service's is (its text says the user's own limit is untouched).
    An admin has no own day budget (`UsageBook.daily_ok`), so only the service's can stop them."""
    if usage.locked_out(user_id, settings):
        return "locked_out"
    own_left = tier == "admin" or usage.own_tokens_left(user_id, settings)
    if own_left and usage.paused(settings):
        return SERVICE_PAUSED
    return "budget"


def request_ok(ledger: RequestLedger, settings: AgentSettings, *, next_calls: int = 1, reserve: int = 0) -> bool:
    """Whether the request may make `next_calls` more LLM calls and still has `reserve` cost-weighted tokens left."""
    return (
        ledger.llm_calls + next_calls <= settings.max_llm_calls
        and ledger.budget_tokens + reserve < settings.request_token_budget
    )


def budget_allows(
    ledger: RequestLedger, usage: UsageBook, settings: AgentSettings, *, next_calls: int = 1, reserve: int = 0
) -> bool:
    """`budget.check()`: request, user-day and global-day budgets together.

    `reserve` is what the caller still needs after the check, in cost-weighted tokens:
    the pipeline keeps room for a review and the root's closing reply
    (`pipeline.REVIEW_RESERVE_TOKENS`), so a review never leaves the reply to a shipped
    plot to the `budget` refusal. The user-day budget follows the ledger's tier (`UsageBook.daily_ok`).
    """
    return request_ok(ledger, settings, next_calls=next_calls, reserve=reserve) and usage.daily_ok(
        ledger.user_id or "anonymous", settings, reserve=reserve, tier=ledger.tier
    )


def usage_tokens(usage: Any) -> tuple[int, int]:
    """Billable tokens (prompt + candidates + thoughts + tool-use prompt) and cached tokens of `usage_metadata`."""
    if usage is None:
        return 0, 0

    def count(name: str) -> int:
        value = getattr(usage, name, None)
        return int(value) if isinstance(value, int) else 0

    billable = (
        count("prompt_token_count")
        + count("candidates_token_count")
        + count("thoughts_token_count")
        + count("tool_use_prompt_token_count")
    )
    return billable, count("cached_content_token_count")


USAGE_FIELDS: dict[str, str] = {
    "prompt": "prompt_token_count",
    "candidates": "candidates_token_count",
    "thoughts": "thoughts_token_count",
    "tool_use_prompt": "tool_use_prompt_token_count",
    "cache_write": "cache_creation_input_tokens",
}
"""The `usage_metadata` counts the attribution line carries by kind (`cached` is logged on its own).

`prompt` includes the cached and cache-write tokens (ADK folds Anthropic's disjoint counts
into one prompt count); `cache_write` is the Anthropic cache-creation count ADK attaches to
the usage object. The eval harness prices each kind at its own rate."""


def usage_breakdown(usage: Any) -> dict[str, int]:
    """The token counts of `usage_metadata` by kind (`USAGE_FIELDS`); a missing count is 0."""
    counts: dict[str, int] = {}
    for key, name in USAGE_FIELDS.items():
        value = getattr(usage, name, None) if usage is not None else None
        counts[key] = int(value) if isinstance(value, int) else 0
    return counts


BUDGET_WEIGHTS: dict[str, float] = {"uncached": 1.0, "cached": 0.1, "cache_write": 1.25, "output": 5.0}
"""What one token of each kind counts against the token budgets, in input-token equivalents.

The weights are the list-price ratios of `agents/evals/pricing.py` (2026-10-10): a cache
read costs 0.1 and a five-minute cache write 1.25 of an uncached input token, and an
output token (candidates and thoughts) 5.0, Claude Haiku 5.5's $0.50 over $0.10 per
million (Gemini 3.8 Flash has the same ratio, $7.50 over $1.50). The judges' tokens are
priced against the same unit (`JUDGE_WEIGHTS`). A test checks both against that module,
so a price change there names these constants.

Measured on the rerun of spike X (244 runs on main, Claude Haiku 5.5, warm cache), the
median run books 37,157 weighted against 70,488 plain tokens, and a reviewed run with
two adapter attempts 39,499 against 72,172; a second review adds a median of 11,246.
The 2,000,000 of `AGENT_DAILY_TOKEN_BUDGET` holds about 54 median warm runs, so the 40
runs of `AGENT_DAILY_PIPELINE_RUNS` bind first; a user whose every request starts cold
gets about 26, where the token budget binds instead.
A cold cache weighs more: each agent's first call writes its prefix at 1.25 instead of
reading it at 0.1. The rerun's first, cold run of area-basic-seaborn-decimal-comma
booked 100,282, and simulated cold from the same calls, a reviewed run with two
attempts books a median of 77,747 (95th percentile 87,180, at most 103,800), and
115,046 at most with a second review; with three attempts (`AGENT_MAX_ATTEMPTS=3`, the
three-attempt rerun) at most 106,042, and about 117,300 with a second review. The
160,000 of `AGENT_REQUEST_TOKEN_BUDGET` stays about 36 % above the costliest of these."""


UNIT_PRICES: dict[str, float] = {"claude-haiku-5-5": 0.10, "gemini-3.8-flash": 1.50}
"""The uncached input list price, USD per million tokens at the `global` endpoint, of each main model the budgets
are counted in: one weighted token (`BUDGET_WEIGHTS`, `JUDGE_WEIGHTS`) costs this much. The prices of
`agents/evals/pricing.py`, which the image does not ship (a test keeps both equal)."""
LOCATION_SURCHARGES: dict[str, float] = {"global": 0.0, "eu": 0.10, "us": 0.10}
"""`pricing.LOCATION_SURCHARGE`: the multi-regions add 10 % to the global list price (a test keeps both equal)."""


def weighted_usd(tokens: int, model: str, location: str) -> float | None:
    """Weighted tokens of `model` at `location` in USD at list price; None for a model without a price here."""
    price = UNIT_PRICES.get(model)
    if price is None:
        return None
    return tokens * price * (1.0 + LOCATION_SURCHARGES.get(location, 0.0)) / 1e6


def weighted_tokens(*, uncached: int = 0, cached: int = 0, cache_write: int = 0, output: int = 0) -> int:
    """Token counts in input-token equivalents (`BUDGET_WEIGHTS`), rounded to a whole token."""
    weights = BUDGET_WEIGHTS
    total = (
        uncached * weights["uncached"]
        + cached * weights["cached"]
        + cache_write * weights["cache_write"]
        + output * weights["output"]
    )
    return round(total)


def budget_tokens(usage: Any) -> int:
    """One response's `usage_metadata` in input-token equivalents.

    The prompt count includes the cached and the cache-write tokens (`USAGE_FIELDS`), so
    the uncached part is what is left of it, plus the Gemini tool-use prompt.
    """
    counts = usage_breakdown(usage)
    cached = usage_tokens(usage)[1]
    prompt = counts["prompt"] + counts["tool_use_prompt"]
    return weighted_tokens(
        uncached=max(0, prompt - cached - counts["cache_write"]),
        cached=cached,
        cache_write=counts["cache_write"],
        output=counts["candidates"] + counts["thoughts"],
    )


JUDGE_WEIGHTS: dict[str, tuple[float, float]] = {"claude-haiku-5-5": (1.0, 5.0), "gemini-3.5-flash-lite": (0.2, 5 / 3)}
"""What one input and one output token of a judge model count, in input-token equivalents
of the arm's main model, the unit every budget uses.

The budgets count every token against the main model's uncached input token, so a judge
on a cheaper model counts less (`agents/evals/pricing.py`, 2026-10-10): the Claude arm
judges on Claude Haiku 5.5 itself ($0.10 in and $0.50 out against its own $0.10: 1.0 and
5.0); the Gemini arm judges on Gemini 3.5 Flash-Lite ($0.30 in and $2.50 out against
Gemini 3.8 Flash's $1.50: 0.2 and 1.67). A judge model outside this table counts like
the agents' models (1.0 and `BUDGET_WEIGHTS["output"]`). A judge's input is never
cached."""


def judge_budget_tokens(tokens: int, input_tokens: int, output_tokens: int, model: str = "") -> int:
    """A judge verdict in input-token equivalents of the main model: its split, else its plain total."""
    if input_tokens or output_tokens:
        input_weight, output_weight = JUDGE_WEIGHTS.get(model, (BUDGET_WEIGHTS["uncached"], BUDGET_WEIGHTS["output"]))
        return round(input_tokens * input_weight + output_tokens * output_weight)
    return tokens


def argument_hash(arguments: Any) -> str:
    """A short, stable hash of tool arguments, so logs can correlate calls without their content."""
    try:
        text = json.dumps(arguments, sort_keys=True, default=str)
    except TypeError, ValueError:
        text = repr(type(arguments))
    return hashlib.sha256(text.encode()).hexdigest()[:12]


SESSION_SALT = secrets.token_bytes(32)
"""The per-process salt of every session hash a log line carries: the attribution lines' `session` and the usage
telemetry's (`telemetry.session_key`). The session id travels in every `/v1` request URL Cloud Run logs, so a plain
hash of it could be recomputed and joined to the request log; sessions live in memory and end with the instance,
so a salt that ends with the process keeps a session's lines together for exactly as long as it exists. Never
logged, never configured."""


def salted(session_id: str, domain: str, length: int) -> str:
    """HMAC-SHA256 of the session id under `SESSION_SALT`, separated by `domain`, so the attribution hash and the
    telemetry hash of one session differ and the two kinds of lines cannot be joined by it. The anonymous caller's
    ids go through it too (`anonymous_user`, `network_key`), each under a domain of its own."""
    if not session_id:
        return ""
    return hmac.new(SESSION_SALT, f"{domain}:{session_id}".encode(), hashlib.sha256).hexdigest()[:length]


def session_hash(session_id: str) -> str:
    """The attribution lines' `session`: 12 hex digits, salted (`salted`)."""
    return salted(session_id, "attribution", 12)


ANONYMOUS_PREFIX = "pub_"
NETWORK_PREFIX = "net_"


def anonymous_user(anon_id: str) -> str:
    """The user id of an anonymous public caller: `pub_` and 16 hex digits of the browser tab's random id, salted.

    The public BFF sends the id its page keeps per tab (`X-Anyplot-Anon`, `agents/main.py` `require_user`); the
    salt dies with the process, so no id this service keys its sessions, limits and attribution lines on can be
    recomputed later, and every anyplot-api instance maps the same tab to the same user while this instance lives
    (`max-instances=1`)."""
    return ANONYMOUS_PREFIX + salted(anon_id, "user", 16)


def network_key(network: str) -> str:
    """The key the per-IP caps count an anonymous caller's network under: `net_` and 16 hex digits, salted.

    `network` is the client's IPv4 address or the /64 of its IPv6 address, as the public BFF forwards it
    (`X-Anyplot-Network`). It is turned into this key at once and never stored or logged as sent."""
    return NETWORK_PREFIX + salted(network, "network", 16)


def attribution(hook: str, ledger: RequestLedger, **fields: Any) -> None:
    """One content-free JSON log line for a plugin hook (`severity` is Cloud Logging's level field).

    A turn hook's verdict (`TURN_HOOKS`) also goes into the turn's record (`RequestLedger.note_guard`), here rather
    than at each call site, so a new verdict of a listed hook lands in the record without an edit of its own; the
    line itself is the same either way."""
    if hook in TURN_HOOKS:
        ledger.note_guard(hook, fields.get("verdict"))
    record = {
        "severity": "INFO",
        "hook": hook,
        "request_id": ledger.request_id,
        "user": ledger.user_id,
        "session": session_hash(ledger.session_id),
        "llm_calls": ledger.llm_calls,
        "tokens": ledger.tokens,
        **fields,
    }
    logger.info(json.dumps(record, sort_keys=True, default=str))
