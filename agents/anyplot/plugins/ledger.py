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
a phase-2 item). Days are UTC dates.

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
    adapter_allow_full: bool = False
    review_render_id: str | None = None
    lang: str = "en"
    refusal: tuple[str, str] | None = None
    error: str | None = None
    model_versions: set[str] = field(default_factory=set)
    last_calls: dict[str, CallFacts] = field(default_factory=dict)

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

    def daily_ok(self, user_id: str, settings: AgentSettings) -> bool:
        """Whether the user and the service still have daily token budget."""
        return (
            self.user_tokens(user_id) < settings.daily_token_budget
            and self.global_tokens() < settings.global_daily_token_budget
        )

    def runs_ok(self, user_id: str, settings: AgentSettings) -> bool:
        return self.user_runs(user_id) < settings.daily_pipeline_runs


def request_ok(ledger: RequestLedger, settings: AgentSettings, *, next_calls: int = 1) -> bool:
    """Whether the request may spend `next_calls` more LLM calls (its tokens are cost-weighted)."""
    return (
        ledger.llm_calls + next_calls <= settings.max_llm_calls and ledger.budget_tokens < settings.request_token_budget
    )


def budget_allows(ledger: RequestLedger, usage: UsageBook, settings: AgentSettings, *, next_calls: int = 1) -> bool:
    """`budget.check()`: request, user-day and global-day budgets together."""
    return request_ok(ledger, settings, next_calls=next_calls) and usage.daily_ok(
        ledger.user_id or "anonymous", settings
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
million (Gemini 3.8 Flash has the same ratio, $7.50 over $1.50). A test checks them
against that module, so a price change there names this constant.

Measured on the rerun of spike X (244 runs on main, Claude Haiku 5.5, warm cache), the
median run books 37,157 weighted against 70,488 plain tokens, and a reviewed run with
two adapter attempts 39,499 against 72,172, so a second review (a median of 11,263) or
a third attempt (12,145) fits the 80,000 of `AGENT_REQUEST_TOKEN_BUDGET`, and the 1,000,000 of
`AGENT_DAILY_TOKEN_BUDGET` holds about 26 median runs instead of 14. A cold cache
weighs more: each agent's first call writes its prefix at 1.25 instead of reading it
at 0.1. Simulated from the same calls, a reviewed run with two attempts then books a
median of about 77,700 (95th percentile 87,000), so on a cold cache the request
budget can stop the second review or the root's closing reply."""


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


def judge_budget_tokens(tokens: int, input_tokens: int, output_tokens: int) -> int:
    """A judge verdict in input-token equivalents: its input and output split, else its plain total."""
    if input_tokens or output_tokens:
        return weighted_tokens(uncached=input_tokens, output=output_tokens)
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
