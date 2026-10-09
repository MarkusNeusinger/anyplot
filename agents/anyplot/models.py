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

ADK 2.11 sends no response schema to Claude: `basic.py` sets
`config.response_schema` for a tool-less agent with an `output_schema`, and
`anthropic_llm.py` never reads it, so the adapter and reviewer would get free text.
`VertexClaude` closes that gap with a forced tool call: when a request carries a
response schema and no tools, it adds one tool whose input schema is the response
schema, forces `tool_choice` to it, and turns the returned `tool_use` input back
into the JSON text ADK's `validate_schema` parses. Forced tool use excludes extended
thinking, which this module never enables for Claude.

**Gemini** (`gemini`). `google.adk.models.google_llm.Gemini` with
`client_kwargs={"enterprise": True, "project": ..., "location": ...}`, HTTP retries
(3 attempts), explicit safety settings at `BLOCK_MEDIUM_AND_ABOVE`, and a thinking
level per kind; no temperature, top_p or thinking budget, which Gemini 3 does not
want.

Per kind: the root chats (2,048 output tokens, low effort), the adapter edits code
(2,048 tokens for edits, raised to `ADAPTER_FULL_MAX_OUTPUT_TOKENS` by the adapter's
callback when a full file is allowed; medium effort), the reviewer judges two images
(2,048 tokens, low effort, medium media resolution on Gemini).
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Literal, Protocol

from google.adk.models.anthropic_llm import AnthropicGenerateContentConfig, Claude
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .settings import AgentSettings, get_settings


ModelKind = Literal["root", "adapter", "reviewer"]
MODEL_KINDS: tuple[ModelKind, ...] = ("root", "adapter", "reviewer")

MAX_OUTPUT_TOKENS: dict[ModelKind, int] = {"root": 2048, "adapter": 2048, "reviewer": 2048}
ADAPTER_FULL_MAX_OUTPUT_TOKENS = 12_288
GEMINI_THINKING: dict[ModelKind, types.ThinkingLevel] = {
    "root": types.ThinkingLevel.LOW,
    "adapter": types.ThinkingLevel.MEDIUM,
    "reviewer": types.ThinkingLevel.LOW,
}
ClaudeEffort = Literal["low", "medium", "high", "xhigh", "max"]
CLAUDE_EFFORT: dict[ModelKind, ClaudeEffort] = {"root": "low", "adapter": "medium", "reviewer": "low"}
SAFETY_CATEGORIES: tuple[types.HarmCategory, ...] = (
    types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
)
RETRY_ATTEMPTS = 3

STRUCTURED_TOOL = "submit_result"
"""Name of the forced tool that carries a Claude structured answer."""

JUDGE_MAX_OUTPUT_TOKENS = 64
JUDGE_TOOL = "submit_verdict"


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


def _has_tools(llm_request: LlmRequest) -> bool:
    return bool(llm_request.config and llm_request.config.tools)


class VertexClaude(Claude):
    """ADK's `Claude` with a client from the settings and structured output through a forced tool."""

    vertex_project: str
    vertex_region: str

    @cached_property
    def _anthropic_client(self) -> Any:
        """The Vertex AI client for the configured project and location, built on first use."""
        if self.client is not None:
            return self.client
        from anthropic import AsyncAnthropicVertex

        return AsyncAnthropicVertex(project_id=self.vertex_project, region=self.vertex_region)

    def _build_anthropic_kwargs(
        self, llm_request: LlmRequest, messages: Any, tools: Any, tool_choice: Any, thinking: Any
    ) -> dict[str, Any]:
        """ADK's request arguments, plus the forced structured-answer tool when a response schema is set."""
        kwargs: dict[str, Any] = super()._build_anthropic_kwargs(llm_request, messages, tools, tool_choice, thinking)
        schema = llm_request.config.response_schema if llm_request.config else None
        if schema is not None and not _has_tools(llm_request):
            kwargs["tools"] = [
                {
                    "name": STRUCTURED_TOOL,
                    "description": "Submit the final answer. Call this exactly once with the complete answer.",
                    "input_schema": response_json_schema(schema),
                }
            ]
            kwargs["tool_choice"] = {"type": "tool", "name": STRUCTURED_TOOL}
        return kwargs

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        structured = bool(llm_request.config and llm_request.config.response_schema) and not _has_tools(llm_request)
        # A structured answer is read whole, so it never streams.
        async for response in super().generate_content_async(llm_request, stream=stream and not structured):
            yield _structured_text(response) if structured else response


def _structured_text(response: LlmResponse) -> LlmResponse:
    """Replace the forced tool call with the JSON text of its input, as a schema-bound Gemini answer reads."""
    if response.content is None or not response.content.parts:
        return response
    parts: list[types.Part] = []
    for part in response.content.parts:
        call = part.function_call
        if call is not None and call.name == STRUCTURED_TOOL:
            parts.append(types.Part(text=json.dumps(call.args or {}, ensure_ascii=False)))
        elif call is None:
            parts.append(part)
    response.content = types.Content(role=response.content.role or "model", parts=parts)
    return response


# --- Gemini ------------------------------------------------------------------------------


def _safety_settings() -> list[types.SafetySetting]:
    return [
        types.SafetySetting(category=category, threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE)
        for category in SAFETY_CATEGORIES
    ]


def _retry_options() -> types.HttpRetryOptions:
    return types.HttpRetryOptions(attempts=RETRY_ATTEMPTS, initial_delay=1)


# --- Public factories --------------------------------------------------------------------


def make_model(kind: ModelKind, settings: AgentSettings | None = None) -> BaseLlm:
    """The ADK model of one agent kind for the configured provider."""
    settings = settings or get_settings()
    if kind not in MODEL_KINDS:
        raise ValueError(f"unknown model kind {kind!r}")
    if settings.provider == "anthropic-vertex":
        return VertexClaude(
            model=settings.model,
            max_tokens=MAX_OUTPUT_TOKENS[kind],
            vertex_project=settings.project,
            vertex_region=settings.location,
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
        return AnthropicGenerateContentConfig(
            max_output_tokens=MAX_OUTPUT_TOKENS[kind], effort=CLAUDE_EFFORT[kind], labels=_labels(kind)
        )
    return types.GenerateContentConfig(
        max_output_tokens=MAX_OUTPUT_TOKENS[kind],
        thinking_config=types.ThinkingConfig(thinking_level=GEMINI_THINKING[kind]),
        safety_settings=_safety_settings(),
        labels=_labels(kind),
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_MEDIUM if kind == "reviewer" else None,
    )


# --- Judge -------------------------------------------------------------------------------

Verdict = Literal["in_scope", "out_of_scope", "attack"]
_LANG = re.compile(r"^[a-z]{2}$")


class JudgeVerdict(BaseModel):
    """What the judge decided, the reply language it saw, and the tokens it cost."""

    model_config = ConfigDict(extra="ignore")

    verdict: Verdict
    lang: str = "en"
    tokens: int = Field(default=0, ge=0)

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


class JudgeClient(Protocol):
    """Classifies one fenced text against a rubric; fails closed with `JudgeUnavailable`."""

    async def judge(self, text: str, rubric: str) -> JudgeVerdict: ...


Attempt = Callable[[str, str], Awaitable[JudgeVerdict]]


async def _within_budget(attempt: Attempt, text: str, rubric: str, timeout_s: float) -> JudgeVerdict:
    """One attempt plus one retry, both inside one wall-clock budget."""
    last: BaseException | None = None
    try:
        async with asyncio.timeout(timeout_s):
            for _ in range(2):
                try:
                    return await attempt(text, rubric)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # any transport, API or parse failure gets the one retry
                    last = exc
    except TimeoutError as exc:
        raise JudgeUnavailable("the judge did not answer in time") from exc
    raise JudgeUnavailable(f"the judge failed twice ({type(last).__name__})") from last


@dataclass
class AnthropicJudge:
    """The judge on Claude through Vertex AI, answering through a forced tool call."""

    model: str
    project: str
    region: str
    timeout_s: float

    @cached_property
    def _client(self) -> Any:
        from anthropic import AsyncAnthropicVertex

        return AsyncAnthropicVertex(project_id=self.project, region=self.region, max_retries=0)

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        message = await self._client.messages.create(
            model=self.model,
            max_tokens=JUDGE_MAX_OUTPUT_TOKENS,
            system=rubric,
            messages=[{"role": "user", "content": text}],
            tools=[
                {
                    "name": JUDGE_TOOL,
                    "description": "Submit the verdict.",
                    "input_schema": response_json_schema(_JudgeAnswer),
                }
            ],
            tool_choice={"type": "tool", "name": JUDGE_TOOL},
        )
        answer = next((block.input for block in message.content if getattr(block, "type", "") == "tool_use"), None)
        if not isinstance(answer, dict):
            raise ValueError("the judge answered without a verdict")
        usage = message.usage
        tokens = int(getattr(usage, "input_tokens", 0) or 0) + int(getattr(usage, "output_tokens", 0) or 0)
        return JudgeVerdict(**_JudgeAnswer.model_validate(answer).model_dump(), tokens=tokens)

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)


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

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=rubric,
                response_mime_type="application/json",
                response_schema=_JudgeAnswer,
                max_output_tokens=JUDGE_MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
                # The judge must see attacks to classify them, so its own filters are off.
                safety_settings=[
                    types.SafetySetting(category=category, threshold=types.HarmBlockThreshold.OFF)
                    for category in SAFETY_CATEGORIES
                ],
                labels=_labels("judge"),
            ),
        )
        answer = _JudgeAnswer.model_validate_json(response.text or "")
        usage = response.usage_metadata
        tokens = int(getattr(usage, "total_token_count", 0) or 0) if usage else 0
        return JudgeVerdict(**answer.model_dump(), tokens=tokens)

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)


class FakeJudge:
    """A scripted judge for tests: each call pops the next verdict or raises the next exception.

    `delay_s` makes every attempt sleep first, so a test can drive the budget into a timeout.
    """

    def __init__(
        self, script: Sequence[JudgeVerdict | Exception] = (), *, delay_s: float = 0.0, timeout_s: float = 4.0
    ):
        self.script = list(script)
        self.delay_s = delay_s
        self.timeout_s = timeout_s
        self.calls: list[tuple[str, str]] = []

    async def _attempt(self, text: str, rubric: str) -> JudgeVerdict:
        self.calls.append((text, rubric))
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        item = self.script.pop(0) if self.script else JudgeVerdict(verdict="in_scope", lang="en")
        if isinstance(item, Exception):
            raise item
        return item

    async def judge(self, text: str, rubric: str) -> JudgeVerdict:
        return await _within_budget(self._attempt, text, rubric, self.timeout_s)


def make_judge_client(settings: AgentSettings | None = None) -> JudgeClient:
    """The judge for the configured provider, on `AGENT_JUDGE_MODEL` at `AGENT_LOCATION`."""
    settings = settings or get_settings()
    if settings.provider == "anthropic-vertex":
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


def parse_judge_answer(text: str) -> JudgeVerdict:
    """Parse a judge answer given as JSON text (used by fakes and the eval harness)."""
    try:
        return JudgeVerdict.model_validate(json.loads(text))
    except (ValueError, ValidationError) as exc:
        raise JudgeUnavailable("the judge answer does not parse") from exc
