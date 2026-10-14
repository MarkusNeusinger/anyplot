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
`429 rate_limited`. Only a new UTC day, a redeploy or a scale-to-zero resets them.

The request, user-day and global-day budgets count cost-weighted tokens: each kind
weighted by its price relative to an uncached input token (`BUDGET_WEIGHTS`), so a
cache read counts a tenth and an output token five times. `RequestLedger.tokens` and
`judge_tokens` keep the plain counts that the `done` event and the attribution lines
report.

`attribution` writes one JSON log line per hook with ids, counts and verdicts, and
never content: no message text, no code, no data, no tool arguments (only their
hash).
"""

import hashlib
import json
import logging
from collections import OrderedDict
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from ..settings import AgentSettings


logger = logging.getLogger("anyplot.agents.attribution")

RequestKind = Literal["action", "text"]
MAX_ADHOC_LEDGERS = 64


@dataclass(frozen=True, slots=True)
class CallFacts:
    """The content-free facts of one model call: how it finished and the output tokens it spent."""

    finish_reason: str | None
    candidates: int = 0
    thoughts: int = 0


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
    invocation_id: str | None = None
    llm_calls: int = 0
    tokens: int = 0
    cached_tokens: int = 0
    judge_tokens: int = 0
    budget_tokens: int = 0
    """The model calls' and the judge's cost-weighted tokens (`BUDGET_WEIGHTS`): what the request budget counts."""
    pipeline_calls: int = 0
    pipeline_active: bool = False
    plot_shipped: bool = False
    """A plot shipped in this invocation: the Budget plugin exempts the root's next call once, without tools."""
    adapter_allow_full: bool = False
    review_render_id: str | None = None
    adapter_renders: list[tuple[str, str]] = field(default_factory=list)
    """Renders the adapter's next call sees, as (label, render id): the current render in a self-review,
    the reviewed render before a repair; empty for an ordinary call."""
    lang: str = "en"
    """The ISO 639-1 code of the fixed refusals: the session language's (`language.refusal_lang`) until the
    scope judge answers, then the language the judged message is written in."""
    refusal: tuple[str, str] | None = None
    error: str | None = None
    model_versions: set[str] = field(default_factory=set)
    last_calls: dict[str, CallFacts] = field(default_factory=dict)
    dataset_changes: list[str] = field(default_factory=list)
    """The change lines of every `prepare_data` call of the turn, in order: the `done` event's `dataset.changes`."""
    data_code_calls: int = 0
    """`run_data_code` calls of this invocation; ToolSafety allows `MAX_DATA_CODE_CALLS`."""
    rate_start: Callable[[], bool] | None = None
    """Set by the `/messages` route: books a start in the run queue's rate window for this turn (`RunQueue.rate`),
    False when the window is full; idempotent per turn. None without a route (`adk web`), whose runs bypass the
    queue. The one helper for every sandbox run of a turn: `run_data_code` calls it today, and the plot pipeline can
    take its rated start through it once the queue no longer rates whole turns."""

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


@dataclass
class _Day:
    date: str
    user_tokens: dict[str, int] = field(default_factory=dict)
    user_runs: dict[str, int] = field(default_factory=dict)
    global_tokens: int = 0
    user_strikes: dict[str, set[str]] = field(default_factory=dict)
    user_data_runs: dict[str, int] = field(default_factory=dict)


class UsageBook:
    """Per-user and global daily counters for this instance's lifetime."""

    def __init__(self) -> None:
        self._day = _Day(today())

    def _current(self) -> _Day:
        date = today()
        if self._day.date != date:
            self._day = _Day(date)
        return self._day

    def add_tokens(self, user_id: str, tokens: int) -> None:
        """Book cost-weighted tokens (`weighted_tokens`) against the user's and the service's day."""
        day = self._current()
        day.user_tokens[user_id] = day.user_tokens.get(user_id, 0) + tokens
        day.global_tokens += tokens

    def add_pipeline_run(self, user_id: str) -> None:
        day = self._current()
        day.user_runs[user_id] = day.user_runs.get(user_id, 0) + 1

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

    def daily_ok(self, user_id: str, settings: AgentSettings, *, reserve: int = 0) -> bool:
        """Whether the user and the service still have daily token budget, `reserve` tokens beyond the spend, and strikes left."""
        return (
            self.user_tokens(user_id) + reserve < settings.daily_token_budget
            and self.global_tokens() + reserve < settings.global_daily_token_budget
            and self.user_strikes(user_id) < settings.attack_strikes
        )

    def runs_ok(self, user_id: str, settings: AgentSettings) -> bool:
        return self.user_runs(user_id) < settings.daily_pipeline_runs

    def add_data_run(self, user_id: str) -> None:
        """Count one `run_data_code` run against the user's day, before it runs."""
        day = self._current()
        day.user_data_runs[user_id] = day.user_data_runs.get(user_id, 0) + 1

    def user_data_runs(self, user_id: str) -> int:
        return self._current().user_data_runs.get(user_id, 0)

    def data_runs_ok(self, user_id: str, settings: AgentSettings) -> bool:
        return self.user_data_runs(user_id) < settings.daily_data_runs


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
    plot to the `budget` refusal.
    """
    return request_ok(ledger, settings, next_calls=next_calls, reserve=reserve) and usage.daily_ok(
        ledger.user_id or "anonymous", settings, reserve=reserve
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
    except (TypeError, ValueError):
        text = repr(type(arguments))
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def session_hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:12] if session_id else ""


def attribution(hook: str, ledger: RequestLedger, **fields: Any) -> None:
    """One content-free JSON log line for a plugin hook."""
    record = {
        "hook": hook,
        "request_id": ledger.request_id,
        "user": ledger.user_id,
        "session": session_hash(ledger.session_id),
        "llm_calls": ledger.llm_calls,
        "tokens": ledger.tokens,
        **fields,
    }
    logger.info(json.dumps(record, sort_keys=True, default=str))
