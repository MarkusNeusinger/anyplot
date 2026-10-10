"""Fakes for the runtime tests: scripted LLMs for both providers and canned agent answers.

`ScriptedLlm` stands in for any ADK model and answers from a per-kind queue (the kind
comes from the `agent_kind` label every generation config carries). `FakeAnthropic`
stands in for the `AsyncAnthropicVertex` client behind the real `VertexClaude`, so
the Claude arm exercises the forced-tool structured output end to end.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

from anthropic.types import Message
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import Field


# A plan that adapts the normalised scatter-basic matplotlib file to the fixture's columns.
SCATTER_PLAN: dict[str, Any] = {
    "edits": [
        {
            "find": (
                "np.random.seed(42)\n"
                "study_hours = np.random.uniform(1, 12, 180)\n"
                "exam_scores = np.clip(38 + study_hours * 4.5 + np.random.normal(0, 12, 180), 35, 100)\n"
            ),
            "replace": (
                "df = load_user_data()\n"
                'study_hours = df["Study Hours"].to_numpy(dtype=float)\n'
                'exam_scores = df["Exam Score"].to_numpy(dtype=float)\n'
            ),
        },
        {"find": 'title = ""', "replace": 'title = "Exam Score by Study Hours"'},
        {"find": '"Study Hours per Week"', "replace": '"Study Hours"'},
        {"find": '"Exam Score (%)"', "replace": '"Exam Score"'},
    ],
    "title": "Exam Score by Study Hours",
    "changes": ["Plotted Exam Score against Study Hours from your data", "Set a title for your data"],
}
VERDICT_OK: dict[str, Any] = {"ok": True, "defects": []}
VERDICT_REJECT: dict[str, Any] = {
    "ok": False,
    "defects": [
        {
            "id": "VQ-03",
            "theme": "both",
            "observed": "24 sparse markers at s=130 look small",
            "target": "s=250 (+120)",
            "likely_cause": "the scatter marker size",
        }
    ],
}
ROOT_REPLY = "Your plot is ready: Exam Score against Study Hours."

GEMINI_CALL_OVERHEAD_S = 1.83
GEMINI_S_PER_OUTPUT_TOKEN = 0.00681
"""Spike X's least-squares fit of a Gemini 3.8 Flash run's model time over its output tokens.

Fitted on the 122 runs of the Gemini arm (2026-10-10), with thinking tokens counted as
output: R² 0.74, RMSE 10.6 s. It reproduced the one-case probe run within 0.1 s."""


def gemini_call_s(output_tokens: int) -> float:
    """The fitted seconds of a Gemini call that produced `output_tokens` (thinking included)."""
    return GEMINI_CALL_OVERHEAD_S + GEMINI_S_PER_OUTPUT_TOKEN * output_tokens


def kind_of(llm_request: LlmRequest) -> str:
    labels = (llm_request.config.labels or {}) if llm_request.config else {}
    return labels.get("agent_kind", "unknown")


class ScriptedLlm(BaseLlm):
    """A Gemini-like model: answers from queues per agent kind and records every request."""

    model: str = "gemini-scripted"
    script: dict[str, list[Any]] = Field(default_factory=dict)
    requests: list[LlmRequest] = Field(default_factory=list)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        self.requests.append(llm_request)
        queue = self.script.get(kind_of(llm_request), [])
        item = queue.pop(0) if queue else {"text": "fallback"}
        yield gemini_response(item)


def gemini_response(item: dict[str, Any]) -> LlmResponse:
    """A scripted answer; `finish_reason` (an enum name such as `MAX_TOKENS`) marks a cut-off one, `STOP` by default."""
    usage = types.GenerateContentResponseUsageMetadata(prompt_token_count=100, candidates_token_count=20)
    if "call" in item:
        part = types.Part(function_call=types.FunctionCall(name=item["call"], args=item.get("args", {})))
    elif "json" in item:
        part = types.Part(text=json.dumps(item["json"]))
    else:
        part = types.Part(text=item["text"])
    return LlmResponse(
        content=types.Content(role="model", parts=[part]),
        usage_metadata=usage,
        model_version="gemini-scripted",
        finish_reason=types.FinishReason[item.get("finish_reason", "STOP")],
    )


def default_script(
    verdict: dict[str, Any] | None = None, plans: list[dict[str, Any]] | None = None
) -> dict[str, list[Any]]:
    """Root calls the pipeline then replies; one adapter plan per attempt; one reviewer verdict."""
    return {
        "root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}],
        "adapter": [{"json": plan} for plan in (plans or [SCATTER_PLAN])],
        "reviewer": [{"json": verdict or VERDICT_OK}],
    }


class _Messages:
    def __init__(self, owner: "FakeAnthropic") -> None:
        self.owner = owner

    async def create(self, **kwargs: Any) -> Message:
        self.owner.calls.append(kwargs)
        return self.owner.respond(kwargs)


class FakeAnthropic:
    """An `AsyncAnthropicVertex` stand-in: `respond(kwargs)` builds the next `Message`."""

    def __init__(self, script: dict[str, list[Any]]) -> None:
        self.script = script
        self.calls: list[dict[str, Any]] = []
        self.messages = _Messages(self)

    @staticmethod
    def kind(kwargs: dict[str, Any]) -> str:
        system = kwargs.get("system")
        text = system if isinstance(system, str) else json.dumps(system, default=str)
        for marker, kind in (("# Adapter", "adapter"), ("# Reviewer", "reviewer"), ("# anyplot assistant", "root")):
            if marker in text:
                return kind
        return "unknown"

    def respond(self, kwargs: dict[str, Any]) -> Message:
        """The next scripted answer; `stop` overrides its stop reason (`max_tokens` marks a cut-off answer)."""
        kind = self.kind(kwargs)
        queue = self.script.get(kind, [])
        item = queue.pop(0) if queue else {"text": "fallback"}
        if "json" in item:
            choice = kwargs.get("tool_choice") or {}
            assert choice.get("type") == "tool", "a structured answer must be a forced tool call"
            block = {
                "type": "tool_use",
                "id": f"toolu_{len(self.calls)}",
                "name": choice["name"],
                "input": item["json"],
            }
            stop = "tool_use"
        elif "call" in item:
            block = {
                "type": "tool_use",
                "id": f"toolu_{len(self.calls)}",
                "name": item["call"],
                "input": item.get("args", {}),
            }
            stop = "tool_use"
        else:
            block = {"type": "text", "text": item["text"]}
            stop = "end_turn"
        stop = item.get("stop", stop)
        return Message.model_validate(
            {
                "id": f"msg_{len(self.calls)}",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "content": [block],
                "stop_reason": stop,
                "stop_sequence": None,
                "usage": {"input_tokens": 100, "output_tokens": 20},
            }
        )
