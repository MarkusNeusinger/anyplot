"""Every model and model client of the agent network, built from `AgentSettings` only.

`make_model(kind)` returns the ADK model object of one agent kind and
`make_content_config(kind)` its generation config; `make_judge_client()` returns the
scope and dataset judge. No other module constructs a model, a `genai.Client` or an
Anthropic client (a unit test greps for it), so the provider, model id, project and
location of every call come from `AGENT_PROVIDER`, `AGENT_MODEL`,
`AGENT_JUDGE_MODEL`, `AGENT_PROJECT` and `AGENT_LOCATION`.

**Claude on Vertex AI** (`anthropic-vertex`, the default). The model is
`google.adk.models.anthropic_llm.Claude` with an `AsyncAnthropicVertex` client built
from the settings (ADK's own builds one from `GOOGLE_CLOUD_PROJECT` and
`GOOGLE_CLOUD_LOCATION`, which would let the environment pick the project).
Reasoning depth is the Claude `effort` of `AnthropicGenerateContentConfig`; ADK 2.11
ignores `thinking_config.thinking_level` for Claude and raises when both are set.

Claude thinks adaptively by default (since 2026-10-11): the root with
`AGENT_ROOT_THINKING_BUDGET` (1,024) and the adapter with `AGENT_ADAPTER_THINKING_BUDGET`
(2,048) extra output tokens, at most `settings.MAX_THINKING_BUDGET` each; the reviewer
never thinks, and a budget of 0 turns thinking off for that kind (`thinking_budget=0`,
which ADK maps to `thinking: {type: "disabled"}`; Gemini ignores both budgets). Haiku 5.5
takes no thinking budget of its own (`budget_tokens` is a 400), so the config asks for
ADK's adaptive mode (`thinking_budget=-1`, sent as
`thinking: {type: "adaptive", display: "summarized"}`), the depth follows the kind's
effort, and the budget is added to the kind's output cap, so the answer keeps its whole
measured headroom however much the thinking uses. The summary comes back as thought
parts, which the answer guard, ADK's output parsing and the stream translator all skip.

Two details keep the replayed thinking blocks harmless. Left unset, Haiku 5.5 would
think with the display omitted, and ADK 2.11 sends such a signature-only block back as
`redacted_thinking`, which breaks the root's call after a tool result; the summarized
display avoids that. And the root replays its thinking block after a tool result while
ADK moves the session-context block between calls, which fails the block's signature
check; `VertexClaude` asks the API to drop such a block instead (`block_binding`, see
`THINKING_BINDING_BETA`). Haiku 5.5 accepts disabled thinking at effort `high` or below,
so every kind stays at `low` or `medium`.

ADK 2.11 sends no response schema to Claude: `basic.py` sets
`config.response_schema` for a tool-less agent with an `output_schema`, and
`anthropic_llm.py` never reads it, so the adapter and reviewer would get free text.
`VertexClaude` closes that gap with Claude's structured outputs: when a request
carries a response schema and no tools, it sets `output_config.format` to that
schema (`structured_output_format`), so constrained decoding makes the answer text
valid JSON of exactly that shape, and ADK's `validate_schema` parses it as it is.
The judge answers the same way. The grammar enforces types, enums, required fields
and `additionalProperties: false`; what it cannot enforce (string lengths, item
counts, a verdict's `ok` agreeing with its defects) the SDK's `transform_schema`
moves into the field descriptions as hints, and `schemas.repair_plan` and
`schemas.repair_verdict` mend after the strict check. Unlike a forced tool call, the
format lets a thinking model think before it answers (on Haiku 5.5 a forced tool
call skips thinking), and Claude Opus 5.5, Sonnet 5.5 and Fable 5.1 accept it.
Those three refuse disabled thinking with a 400, so the settings still accept only
the Claude models in `settings.CLAUDE_MODELS`.

**Gemini** (`gemini`). `google.adk.models.google_llm.Gemini` with
`client_kwargs={"enterprise": True, "project": ..., "location": ...}`, HTTP retries
(3 attempts), explicit safety settings at `BLOCK_MEDIUM_AND_ABOVE`, and a thinking
level per kind; no temperature, top_p or thinking budget, which Gemini 3 does not
want.

Per kind: the root chats (4,096 output tokens, low effort), the adapter edits code
(medium effort; 8,192 tokens for edits, `MAX_OUTPUT_TOKENS` on Claude and
`GEMINI_ADAPTER_MAX_OUTPUT_TOKENS` on Gemini, whose thinking tokens count toward the
cap; `allow_full_file`, called by
the adapter's callback when a full file is allowed, raises the cap to
`ADAPTER_FULL_MAX_OUTPUT_TOKENS` on Claude and `GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS`
on Gemini, and on Gemini lowers thinking to `GEMINI_ADAPTER_FULL_THINKING`), the
reviewer judges the render (4,096 tokens, low effort, medium media resolution on
Gemini). Every cap leaves ample headroom above the measured answers (`MAX_OUTPUT_TOKENS`):
an answer that finishes costs the same under any cap, and a cut-off wastes the call.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Literal, Protocol

from anthropic import transform_schema
from google.adk.models.anthropic_llm import AnthropicGenerateContentConfig, Claude
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .data.transcribe import TranscribedTable
from .settings import CLI_JUDGE_TIMEOUT_S, AgentSettings, get_settings


ModelKind = Literal["root", "adapter", "reviewer"]
MODEL_KINDS: tuple[ModelKind, ...] = ("root", "adapter", "reviewer")

MAX_OUTPUT_TOKENS: dict[ModelKind, int] = {"root": 4096, "adapter": 8192, "reviewer": 4096}
"""Output caps per kind: every kind on Claude, the root and the reviewer on Gemini.

The owner's rule (2026-10-10): a cap leaves ample headroom above the measured answers,
because an unused cap costs nothing and a cut-off wastes the call. Measured in the
rerun of spike X on main (244 runs, Claude Haiku 5.5, 2026-10-10):

* adapter, edits only (attempt 1): at the old cap of 2,048, 23 of 244 first calls
  ended with `MAX_TOKENS` (22 of them box-basic and heatmap-basic matplotlib), and the
  finished ones reached 2,030, so the cap cut the distribution. Plans on attempt 2
  finished at a median of 1,562 and at most 2,606 tokens. 8,192 is 3.1 times the
  largest measured plan.
* reviewer: at most 600 tokens (95th percentile 515) in 218 answers, all `STOP`; 4,096
  is 6.8 times that.
* root: at most 259 tokens (95th percentile 180) in 566 calls; 4,096 leaves room for
  a longer reply in German or a code explanation.

The caps also fit the soft deadline. Fitted on the rerun's run times, Claude Haiku 5.5
takes about 0.8 s per call plus 0.0029 s per output token (R² 0.95), so a call that
uses the whole 8,192 takes about 25 s, the whole 16,384 of `ADAPTER_FULL_MAX_OUTPUT_TOKENS`
about 49 s (both inside the 60 s of `pipeline.ADAPTER_P95_S`), and the whole 4,096
of the reviewer about 13 s (inside the 30 s of `pipeline.REVIEWER_P95_S`). On Gemini,
whose thinking counts toward the cap, a reviewer call that uses all 4,096 takes about
30 s at spike X's fitted rate (see `GEMINI_ADAPTER_MAX_OUTPUT_TOKENS`). The Gemini
adapter keeps its own caps (`GEMINI_ADAPTER_MAX_OUTPUT_TOKENS`,
`GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS`)."""
ADAPTER_FULL_MAX_OUTPUT_TOKENS = 16_384
"""The Claude adapter's cap when a full file is allowed (the repair attempt).

Measured full-file plans finished at most at 2,606 tokens. A full file may hold
`schemas.MAX_FULL_CODE_CHARS` (24 KB), about 9,800 tokens at the 2.5 characters per
token measured for Haiku 5.5 before JSON escaping, so 16,384 holds a plan at the
schema's own limit with its change notes; the largest phase-1 catalogue file
(star-chart-constellation, matplotlib, 20,677 characters) is about 8,300. The
Anthropic SDK accepts the cap without streaming (its limit is about 21,300 tokens)."""
GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS = 12_288
"""The Gemini adapter's cap when a full file is allowed, thinking included.

The soft deadline bounds it like the edit cap: at spike X's fitted rate a call that
uses all 12,288 tokens takes about 85 s, more than the 60 s that `pipeline.ADAPTER_P95_S`
reserves, so a higher cap would only make a runaway call later."""
GEMINI_THINKING: dict[ModelKind, types.ThinkingLevel] = {
    "root": types.ThinkingLevel.LOW,
    "adapter": types.ThinkingLevel.MEDIUM,
    "reviewer": types.ThinkingLevel.LOW,
}
GEMINI_ADAPTER_MAX_OUTPUT_TOKENS = 8_192
"""The Gemini adapter's cap for an edit-only call (attempt 1).

Gemini 3 counts thinking tokens toward `max_output_tokens`. At 2,048 every first
adapter call of the spike-X Gemini arm (2026-10-10) ended with `MAX_TOKENS` after
about 1,970 thought and 65 answer tokens. The plan calls of that run needed a median
of about 4,700 output tokens; 8,192 holds 101 of the 112 measured ones (10,240 would
hold 110).

The cap is also bounded by the pipeline's soft deadline: at spike X's fitted Gemini
rate (1.83 s plus 0.00681 s per output token) a call that uses the whole cap takes
about 58 s, so even a cut-off attempt 1 leaves the 75 s the repair attempt needs of
the 140 s (`pipeline.ADAPTER_P95_S` plus `RENDER_P95_S`). At 10,240 a cut-off call
takes about 72 s and the deadline check would cancel attempt 2 exactly when it is
needed. The trade-off: the 11 measured plans above 8,192 tokens are cut off and come
back on attempt 2 (full file allowed, LOW thinking), without a repair round of their
own; at the fitted rate, a finished plan of more than about 8,700 tokens leaves less
than 75 s after its render anyway. Claude has the same 8,192 in
`MAX_OUTPUT_TOKENS["adapter"]`, chosen from its own measurements, with its 2,048 tokens
of thinking room added on top (`AGENT_ADAPTER_THINKING_BUDGET`)."""
GEMINI_ADAPTER_FULL_THINKING = types.ThinkingLevel.LOW
"""The Gemini adapter's thinking level when a full file is allowed (the repair attempt).

At MEDIUM, 10 runs of the spike-X Gemini arm thought past the 12,288-token cap of
that attempt as well (`GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS`); LOW leaves the answer
room. The first attempt keeps MEDIUM."""
ClaudeEffort = Literal["low", "medium", "high", "xhigh", "max"]
CLAUDE_EFFORT: dict[ModelKind, ClaudeEffort] = {"root": "low", "adapter": "medium", "reviewer": "low"}
SAFETY_CATEGORIES: tuple[types.HarmCategory, ...] = (
    types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
)
RETRY_ATTEMPTS = 3
ADAPTIVE_THINKING = -1
"""ADK's `thinking_budget` for Claude's adaptive thinking; 0 is disabled, a positive budget is the
`budget_tokens` mode that Haiku 5.5 refuses."""

JUDGE_MAX_OUTPUT_TOKENS = 256
"""The scope and dataset judge's cap. Its answer (`verdict` and `lang`) took 59 tokens as a
forced tool call in every one of the rerun's 244 runs, 5 below the old cap of 64, and the
Gemini judge 15 to 22 in spike X. 256 is 4.3 times the Claude answer and leaves room
for a Gemini judge's minimal thinking; a finished answer costs the same under any cap."""


def _labels(kind: str) -> dict[str, str]:
    """Low-cardinality billing labels (Gemini on Vertex AI; Claude ignores them)."""
    return {"service": "anyplot-agents", "agent_kind": kind}


# --- Claude ------------------------------------------------------------------------------


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """A JSON schema with every local `$ref` replaced by its `$defs` entry (tool schemas stay flat)."""
    definitions: dict[str, Any] = schema.get("$defs", {})

    def resolve(node: Any, depth: int = 0) -> Any:
        if depth > 20:
            raise ValueError("the response schema nests too deeply")
        if isinstance(node, dict):
            reference = node.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                target = definitions[reference.removeprefix("#/$defs/")]
                merged = {**target, **{key: value for key, value in node.items() if key != "$ref"}}
                return resolve(merged, depth + 1)
            return {key: resolve(value, depth + 1) for key, value in node.items() if key != "$defs"}
        if isinstance(node, list):
            return [resolve(item, depth + 1) for item in node]
        return node

    resolved: dict[str, Any] = resolve(schema)
    return resolved


def response_json_schema(schema: Any) -> dict[str, Any]:
    """The JSON schema of an ADK response schema (a Pydantic model, a `types.Schema` or a dict)."""
    if isinstance(schema, dict):
        raw = schema
    elif isinstance(schema, type) and issubclass(schema, BaseModel):
        raw = schema.model_json_schema()
    elif isinstance(schema, types.Schema):
        raw = schema.model_dump(exclude_none=True, mode="json")
    else:
        from pydantic import TypeAdapter

        raw = TypeAdapter(schema).json_schema()
    result = _inline_refs(raw)
    if result.get("type") != "object":
        raise ValueError("a Claude structured answer needs an object schema")
    return result


def structured_output_format(schema: Any) -> dict[str, Any]:
    """The `output_config.format` that constrains a Claude answer to `schema`.

    `anthropic.transform_schema` (the SDK's own helper behind `messages.parse`) makes
    the inlined schema strict: `additionalProperties: false` on every object, and the
    keywords constrained decoding does not support (`minLength`, `maxLength`,
    `maxItems`, defaults) moved into the field's description, where the model still
    reads them; the schema's own validators check them afterwards.
    """
    return {"type": "json_schema", "schema": transform_schema(response_json_schema(schema))}


THINKING_BINDING_BETA = "thinking-binding-controls-2026-08-01"
"""The Anthropic beta that lets a request say what to do with a replayed thinking block whose
signature no longer matches the conversation prefix (`thinking.block_binding`)."""


def _has_tools(llm_request: LlmRequest) -> bool:
    return bool(llm_request.config and llm_request.config.tools)


class VertexClaude(Claude):
    """ADK's `Claude` with a client from the settings and structured output through `output_config.format`."""

    vertex_project: str
    vertex_region: str
    transport_client: Any = None
    """The `claude-cli` transport's client, used instead of Vertex AI's (ADK's `client` field
    accepts only the SDK's own client classes)."""

    @cached_property
    def _anthropic_client(self) -> Any:
        """The Vertex AI client for the configured project and location, built on first use."""
        if self.transport_client is not None:
            return self.transport_client
        if self.client is not None:
            return self.client
        from anthropic import AsyncAnthropicVertex

        return AsyncAnthropicVertex(project_id=self.vertex_project, region=self.vertex_region)

    def _build_anthropic_kwargs(
        self, llm_request: LlmRequest, messages: Any, tools: Any, tool_choice: Any, thinking: Any
    ) -> dict[str, Any]:
        """ADK's request arguments, plus the structured-output format when a response schema is set.

        The format joins ADK's `output_config` (which holds the effort) rather than
        replacing it. A request with tools (the root) gets no format: its answer is chat.
        """
        kwargs: dict[str, Any] = super()._build_anthropic_kwargs(llm_request, messages, tools, tool_choice, thinking)
        schema = llm_request.config.response_schema if llm_request.config else None
        if schema is not None and not _has_tools(llm_request):
            kwargs["output_config"] = {
                **(kwargs.get("output_config") or {}),
                "format": structured_output_format(schema),
            }
        thinking_param = kwargs.get("thinking")
        if isinstance(thinking_param, dict) and thinking_param.get("type") != "disabled":
            # The root replays its thinking block after a tool result while ADK moves the session
            # block between the two calls, so the block's signature no longer matches the prefix
            # and the API answers 400 "Invalid `signature` in `thinking` block" (2 of 122 runs on
            # 2026-10-11, every run on the rerun). With this control the API drops such a block
            # instead of refusing the call; it needs the beta header, which the SDK knows.
            kwargs["thinking"] = {**thinking_param, "block_binding": {"prefix_mismatch_behavior": "drop_block"}}
            headers = dict(kwargs.get("extra_headers") or {})
            betas = [value for value in (headers.get("anthropic-beta"), THINKING_BINDING_BETA) if value]
            headers["anthropic-beta"] = ",".join(betas)
            kwargs["extra_headers"] = headers
        return kwargs

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        structured = bool(llm_request.config and llm_request.config.response_schema) and not _has_tools(llm_request)
        # A structured answer is read whole, so it never streams.
        async for response in super().generate_content_async(llm_request, stream=stream and not structured):
            yield response


# --- Gemini ------------------------------------------------------------------------------


def _safety_settings() -> list[types.SafetySetting]:
    return [
        types.SafetySetting(category=category, threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE)
        for category in SAFETY_CATEGORIES
    ]


def _retry_options() -> types.HttpRetryOptions:
    return types.HttpRetryOptions(attempts=RETRY_ATTEMPTS, initial_delay=1)


# --- Public factories --------------------------------------------------------------------


def thinking_budget(kind: ModelKind, settings: AgentSettings | None = None) -> int:
    """The output room a thinking measurement grants `kind` on Claude; 0 keeps its thinking off.

    Only the root and the adapter take one (`AGENT_ROOT_THINKING_BUDGET`,
    `AGENT_ADAPTER_THINKING_BUDGET`); the reviewer and every Gemini kind have 0.
    """
    settings = settings or get_settings()
    if settings.provider != "anthropic-vertex":
        return 0
    budgets: dict[ModelKind, int] = {"root": settings.root_thinking_budget, "adapter": settings.adapter_thinking_budget}
    return budgets.get(kind, 0)


_CLI_CLIENTS: dict[tuple[str, str, int, str | None], Any] = {}


def cli_client(settings: AgentSettings | None = None, *, fallback: bool = True) -> Any:
    """The shared `claude-cli` client (one per configuration, so its concurrency gate is shared).

    With `fallback`, a call the CLI cannot answer (the root's chat with tools) goes to Claude on
    Vertex AI for the configured project and location; without it, such a call raises.
    """
    from .cli_transport import ClaudeCliClient

    settings = settings or get_settings()
    key = (settings.project if fallback else "", settings.location, settings.cli_concurrency, settings.cli_call_log)
    client = _CLI_CLIENTS.get(key)
    if client is None:
        vertex = make_anthropic_client(settings.project, settings.location, max_retries=2) if fallback else None
        log = Path(settings.cli_call_log) if settings.cli_call_log else None
        client = ClaudeCliClient(fallback=vertex, concurrency=settings.cli_concurrency, call_log=log)
        _CLI_CLIENTS[key] = client
    return client


def model_for(kind: ModelKind, settings: AgentSettings | None = None) -> str:
    """The model id of one agent kind: `AGENT_MODEL`, or an experiment's per-kind model on `claude-cli`."""
    settings = settings or get_settings()
    per_kind = {"adapter": settings.adapter_model, "reviewer": settings.reviewer_model}.get(kind)
    return per_kind or settings.model


def make_model(kind: ModelKind, settings: AgentSettings | None = None) -> BaseLlm:
    """The ADK model of one agent kind for the configured provider (and transport)."""
    settings = settings or get_settings()
    if kind not in MODEL_KINDS:
        raise ValueError(f"unknown model kind {kind!r}")
    if settings.provider == "anthropic-vertex":
        return VertexClaude(
            model=model_for(kind, settings),
            max_tokens=MAX_OUTPUT_TOKENS[kind] + thinking_budget(kind, settings),
            vertex_project=settings.project,
            vertex_region=settings.location,
            transport_client=cli_client(settings) if settings.transport == "claude-cli" else None,
        )
    return Gemini(
        model=settings.model,
        client_kwargs={"enterprise": True, "project": settings.project, "location": settings.location},
        retry_options=_retry_options(),
    )


def make_content_config(kind: ModelKind, settings: AgentSettings | None = None) -> types.GenerateContentConfig:
    """The generation config of one agent kind for the configured provider."""
    settings = settings or get_settings()
    if kind not in MODEL_KINDS:
        raise ValueError(f"unknown model kind {kind!r}")
    if settings.provider == "anthropic-vertex":
        budget = thinking_budget(kind, settings)
        return AnthropicGenerateContentConfig(
            max_output_tokens=MAX_OUTPUT_TOKENS[kind] + budget,
            effort=CLAUDE_EFFORT[kind],
            # thinking_budget 0 is ADK's `thinking: {type: "disabled"}`; unset, Haiku 5.5 thinks.
            # A measurement's budget turns on adaptive thinking (Haiku 5.5 refuses `budget_tokens`).
            thinking_config=types.ThinkingConfig(thinking_budget=ADAPTIVE_THINKING if budget else 0),
            labels=_labels(kind),
        )
    return types.GenerateContentConfig(
        max_output_tokens=GEMINI_ADAPTER_MAX_OUTPUT_TOKENS if kind == "adapter" else MAX_OUTPUT_TOKENS[kind],
        thinking_config=types.ThinkingConfig(thinking_level=GEMINI_THINKING[kind]),
        safety_settings=_safety_settings(),
        labels=_labels(kind),
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM if kind == "reviewer" else None,
    )


def allow_full_file(config: types.GenerateContentConfig, settings: AgentSettings | None = None) -> None:
    """Widen one adapter request's config for an answer that may be a full file.

    The cap becomes `ADAPTER_FULL_MAX_OUTPUT_TOKENS` on Claude, which keeps its thinking
    as it was (the default adaptive thinking with the adapter's thinking budget added to
    the cap again, or off at a budget of 0), and `GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS` on
    Gemini, whose thinking level drops to `GEMINI_ADAPTER_FULL_THINKING`. The provider
    is read from the config's type, not from the settings, so the request decides. ADK
    copies the agent's config per request only shallowly (`_copy_request_scoped_fields`),
    so the thinking config is replaced, never mutated: a change to the shared object
    would reach every later run.
    """
    if isinstance(config, AnthropicGenerateContentConfig):
        thinking = config.thinking_config.thinking_budget if config.thinking_config else 0
        room = thinking_budget("adapter", settings) if thinking else 0
        config.max_output_tokens = ADAPTER_FULL_MAX_OUTPUT_TOKENS + room
        return
    config.max_output_tokens = GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS
    config.thinking_config = types.ThinkingConfig(thinking_level=GEMINI_ADAPTER_FULL_THINKING)


# --- Judge -------------------------------------------------------------------------------

Verdict = Literal["in_scope", "out_of_scope", "attack", "needs_data"]
"""`needs_data`: a request for data the service would have to fetch (owner rule of 2026-10-10)."""
_LANG = re.compile(r"^[a-z]{2}$")


class JudgeVerdict(BaseModel):
    """What the judge decided, the language of what it read (for the scope judge, the message's), and the tokens.

    `tokens` is the plain total, which the `done` event and the attribution line report;
    `input_tokens` and `output_tokens` split it, so the eval harness can price the judge
    at the input and output rates (output includes thinking tokens on Gemini) and the
    budgets can weigh it against the main model's input token (`ledger.judge_budget_tokens`
    with `JUDGE_WEIGHTS`: 1 and 5 on the Claude arm, 0.2 and 1.67 for the Flash-Lite judge on
    the Gemini arm; it falls back to the plain total when there is no split).
    """

    model_config = ConfigDict(extra="ignore")

    verdict: Verdict
    lang: str = "en"
    tokens: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @field_validator("lang", mode="before")
    @classmethod
    def _two_letters(cls, value: Any) -> str:
        text = str(value or "").strip().lower()[:2]
        return text if _LANG.match(text) else "en"


class _JudgeAnswer(BaseModel):
    """The schema the judge model answers in."""

    verdict: Verdict
    lang: str = Field(description="ISO 639-1 code of the language the user writes in, for example en or de")


class JudgeUnavailable(Exception):
    """No verdict within the budget: timeout, transport error or an unparseable answer."""


class Transcription(BaseModel):
    """A table the transcriber read out of free text, and the tokens it cost (split like a verdict)."""

    model_config = ConfigDict(extra="ignore")

    table: TranscribedTable
    tokens: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)


class JudgeClient(Protocol):
    """The judge model's two jobs, both failing closed with `JudgeUnavailable`.

    `judge` classifies one fenced text against a rubric. `transcribe` reads one fenced
    text as a `TranscribedTable` (the data panel's free-text path): the same cheap model
    and structured answer, with a larger output cap and a longer budget
    (`TRANSCRIBE_TIMEOUT_S`).
    """

    async def judge(self, text: str, rubric: str) -> JudgeVerdict: ...

    async def transcribe(self, text: str, rubric: str) -> Transcription: ...


TRANSCRIBE_MAX_OUTPUT_TOKENS = 8_192
"""The transcriber's output cap: `MAX_TRANSCRIBE_CHARS` of text written back as a table of
at most 200 rows and 20 columns is well under it, and a cut-off answer is a failed attempt."""
TRANSCRIBE_TIMEOUT_S = 30.0
"""The transcriber's wall-clock budget for its attempt and retry: a table of a few hundred
cells takes the judge model several seconds to write, far more than a verdict."""

JUDGE_RETRY_BACKOFF_S = 0.5
"""Seconds the judge waits before its one retry, inside the same budget (`AGENT_JUDGE_TIMEOUT_S`).

A 429 or a transport error retried in the same instant meets the same cause, and on a
per-minute quota a failed call counts as well, so an instant retry doubles the burn. A
judge call takes about one to two seconds, so the wait still leaves the retry room in
the default 4 s budget.
"""


async def _within_budget[Answer](
    attempt: Callable[[str, str], Awaitable[Answer]], text: str, rubric: str, timeout_s: float
) -> Answer:
    """One attempt plus one retry after `JUDGE_RETRY_BACKOFF_S`, all inside one wall-clock budget.

    Fails closed with `JudgeUnavailable`, whose message names the type of the last
    failure (for example `RateLimitError`), also when the budget ran out during the wait
    or the retry, so a caller can tell a quota from a timeout without the exception text.
    """
    last: BaseException | None = None
    try:
        async with asyncio.timeout(timeout_s):
            for number in range(2):
                if number:
                    await asyncio.sleep(JUDGE_RETRY_BACKOFF_S)
                try:
                    return await attempt(text, rubric)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # any transport, API or parse failure gets the one retry
                    last = exc
    except TimeoutError as exc:
        after = f" (after {type(last).__name__})" if last is not None else ""
        raise JudgeUnavailable(f"the judge did not answer in time{after}") from exc
    raise JudgeUnavailable(f"the judge failed twice ({type(last).__name__})") from last


@dataclass
class AnthropicJudge:
    """The judge on Claude through Vertex AI, answering under a structured-output format."""

    model: str
    project: str
    region: str
    timeout_s: float
    client: Any = None
    """A client to use instead of Vertex AI's (the `claude-cli` transport)."""
    transcribe_timeout_s: float = TRANSCRIBE_TIMEOUT_S

    @cached_property
    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        from anthropic import AsyncAnthropicVertex

        return AsyncAnthropicVertex(project_id=self.project, region=self.region, max_retries=0)

    async def _structured[Schema: BaseModel](
        self, text: str, rubric: str, schema: type[Schema], max_tokens: int
    ) -> tuple[Schema, int, int]:
        """One call answered under `schema`'s format: the answer, its input tokens and its output tokens."""
        message = await self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            thinking={"type": "disabled"},
            system=rubric,
            messages=[{"role": "user", "content": text}],
            output_config={"format": structured_output_format(schema)},
        )
        # A refusal or a cut-off answer need not match the format; it is a failed attempt, not an answer.
        if message.stop_reason != "end_turn":
            raise ValueError(f"the judge stopped with {message.stop_reason}")
        answer = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        usage = message.usage
        input_tokens = sum(
            int(getattr(usage, name, 0) or 0)
            for name in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        )
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        return schema.model_validate_json(answer), input_tokens, output_tokens

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        answer, input_tokens, output_tokens = await self._structured(
            text, rubric, _JudgeAnswer, JUDGE_MAX_OUTPUT_TOKENS
        )
        return JudgeVerdict(
            **answer.model_dump(),
            tokens=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def _attempt_transcribe(self, text: str, rubric: str) -> Transcription:
        table, input_tokens, output_tokens = await self._structured(
            text, rubric, TranscribedTable, TRANSCRIBE_MAX_OUTPUT_TOKENS
        )
        return Transcription(
            table=table, tokens=input_tokens + output_tokens, input_tokens=input_tokens, output_tokens=output_tokens
        )

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)

    async def transcribe(self, text: str, rubric: str) -> Transcription:
        return await _within_budget(self._attempt_transcribe, text, rubric, self.transcribe_timeout_s)


@dataclass
class GeminiJudge:
    """The judge on Gemini through Vertex AI, answering under a response schema."""

    model: str
    project: str
    location: str
    timeout_s: float

    @cached_property
    def _client(self) -> Any:
        from google import genai

        return genai.Client(enterprise=True, project=self.project, location=self.location)

    async def _structured[Schema: BaseModel](
        self, text: str, rubric: str, schema: type[Schema], max_tokens: int
    ) -> tuple[Schema, int, int, int]:
        """One call answered under `schema`: the answer, its total, input and output tokens."""
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=rubric,
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
                # The judge must see attacks to classify them, so its own filters are off.
                safety_settings=[
                    types.SafetySetting(category=category, threshold=types.HarmBlockThreshold.OFF)
                    for category in SAFETY_CATEGORIES
                ],
                labels=_labels("judge"),
            ),
        )
        answer = schema.model_validate_json(response.text or "")
        usage = response.usage_metadata

        def count(name: str) -> int:
            return int(getattr(usage, name, 0) or 0) if usage else 0

        input_tokens = count("prompt_token_count") + count("tool_use_prompt_token_count")
        output_tokens = count("candidates_token_count") + count("thoughts_token_count")
        return answer, count("total_token_count"), input_tokens, output_tokens

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        answer, total, input_tokens, output_tokens = await self._structured(
            text, rubric, _JudgeAnswer, JUDGE_MAX_OUTPUT_TOKENS
        )
        return JudgeVerdict(**answer.model_dump(), tokens=total, input_tokens=input_tokens, output_tokens=output_tokens)

    async def _attempt_transcribe(self, text: str, rubric: str) -> Transcription:
        table, total, input_tokens, output_tokens = await self._structured(
            text, rubric, TranscribedTable, TRANSCRIBE_MAX_OUTPUT_TOKENS
        )
        return Transcription(table=table, tokens=total, input_tokens=input_tokens, output_tokens=output_tokens)

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)

    async def transcribe(self, text: str, rubric: str) -> Transcription:
        return await _within_budget(self._attempt_transcribe, text, rubric, TRANSCRIBE_TIMEOUT_S)


class FakeJudge:
    """A scripted judge for tests: each call pops the next verdict or raises the next exception.

    `delay_s` makes every attempt sleep first, so a test can drive the budget into a timeout.
    `transcriptions` scripts `transcribe` the same way; without a script it reads nothing
    and fails closed, so a test that expects a table must script one.
    """

    def __init__(
        self,
        script: Sequence[JudgeVerdict | Exception] = (),
        *,
        delay_s: float = 0.0,
        timeout_s: float = 4.0,
        transcriptions: Sequence[Transcription | Exception] = (),
    ):
        self.script = list(script)
        self.transcriptions = list(transcriptions)
        self.delay_s = delay_s
        self.timeout_s = timeout_s
        self.calls: list[tuple[str, str]] = []
        self.transcribe_calls: list[tuple[str, str]] = []

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        self.calls.append((text, rubric))
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        item = self.script.pop(0) if self.script else JudgeVerdict(verdict="in_scope", lang="en")
        if isinstance(item, Exception):
            raise item
        return item

    async def _attempt_transcribe(self, text: str, rubric: str) -> Transcription:
        self.transcribe_calls.append((text, rubric))
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        if not self.transcriptions:
            raise ValueError("no transcription scripted")
        item = self.transcriptions.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)

    async def transcribe(self, text: str, rubric: str) -> Transcription:
        return await _within_budget(self._attempt_transcribe, text, rubric, self.timeout_s)


def make_judge_client(settings: AgentSettings | None = None) -> JudgeClient:
    """The judge for the configured provider, on `AGENT_JUDGE_MODEL` at `AGENT_LOCATION`."""
    settings = settings or get_settings()
    if settings.provider == "anthropic-vertex":
        if settings.transport == "claude-cli":
            # A CLI call starts a process, so the live 4 s budget would fail every verdict closed.
            return AnthropicJudge(
                model=settings.judge_model,
                project=settings.project,
                region=settings.location,
                timeout_s=max(settings.judge_timeout_s, CLI_JUDGE_TIMEOUT_S),
                client=cli_client(settings),
                transcribe_timeout_s=max(TRANSCRIBE_TIMEOUT_S, CLI_JUDGE_TIMEOUT_S),
            )
        return AnthropicJudge(
            model=settings.judge_model,
            project=settings.project,
            region=settings.location,
            timeout_s=settings.judge_timeout_s,
        )
    return GeminiJudge(
        model=settings.judge_model,
        project=settings.project,
        location=settings.location,
        timeout_s=settings.judge_timeout_s,
    )


def make_anthropic_client(project: str, location: str, *, max_retries: int = 0) -> Any:
    """A bare Claude-on-Vertex client for a caller outside the ADK agents (the offline scorer,
    `agents/evals/score.py`). No SDK retries by default, so a 429 reaches the caller."""
    from anthropic import AsyncAnthropicVertex

    return AsyncAnthropicVertex(project_id=project, region=location, max_retries=max_retries)


def parse_judge_answer(text: str) -> JudgeVerdict:
    """Parse a judge answer given as JSON text (used by fakes and the eval harness)."""
    try:
        return JudgeVerdict.model_validate(json.loads(text))
    except (ValueError, ValidationError) as exc:
        raise JudgeUnavailable("the judge answer does not parse") from exc
