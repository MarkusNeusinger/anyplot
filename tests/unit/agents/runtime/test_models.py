"""Tests for agents/anyplot/models.py: factories per provider, Claude structured output, the judge."""

import asyncio
import json
import re
from pathlib import Path

import pytest
from google.adk.models.anthropic_llm import AnthropicGenerateContentConfig
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.anyplot.models import (
    ADAPTER_FULL_MAX_OUTPUT_TOKENS,
    GEMINI_ADAPTER_MAX_OUTPUT_TOKENS,
    STRUCTURED_TOOL,
    AnthropicJudge,
    FakeJudge,
    GeminiJudge,
    JudgeUnavailable,
    JudgeVerdict,
    VertexClaude,
    allow_full_file,
    make_content_config,
    make_judge_client,
    make_model,
    response_json_schema,
)
from agents.anyplot.schemas import AdaptPlan, Verdict
from agents.anyplot.settings import AgentSettings

from .fakes import SCATTER_PLAN, FakeAnthropic


GEMINI = AgentSettings(provider="gemini", model="gemini-3.8-flash", judge_model="gemini-3.5-flash-lite")
CLAUDE = AgentSettings(location="global", project="anyplot-eval")
PACKAGE = Path(__file__).resolve().parents[4] / "agents"


class TestFactories:
    @pytest.mark.parametrize("kind", ["root", "adapter", "reviewer"])
    def test_claude_model_comes_from_the_settings(self, kind: str) -> None:
        model = make_model(kind, CLAUDE)

        assert isinstance(model, VertexClaude)
        assert (model.model, model.vertex_project, model.vertex_region) == (
            "claude-haiku-5-5",
            "anyplot-eval",
            "global",
        )
        assert model.max_tokens == 2048

    @pytest.mark.parametrize("kind", ["root", "adapter", "reviewer"])
    def test_gemini_model_comes_from_the_settings(self, kind: str) -> None:
        model = make_model(kind, GEMINI)

        assert isinstance(model, Gemini)
        assert model.model == "gemini-3.8-flash"
        assert model.client_kwargs == {"enterprise": True, "project": "anyplot", "location": "eu"}
        assert model.retry_options is not None and model.retry_options.attempts == 3

    def test_claude_effort_per_kind_without_thinking_level(self) -> None:
        configs = {kind: make_content_config(kind, CLAUDE) for kind in ("root", "adapter", "reviewer")}

        assert all(isinstance(config, AnthropicGenerateContentConfig) for config in configs.values())
        assert {kind: config.effort for kind, config in configs.items()} == {
            "root": "low",
            "adapter": "medium",
            "reviewer": "low",
        }
        # Disabled explicitly: unset, Haiku 5.5 thinks and ADK round-trips the block malformed.
        assert all(
            config.thinking_config is not None
            and config.thinking_config.thinking_budget == 0
            and config.thinking_config.thinking_level is None
            for config in configs.values()
        )

    def test_gemini_config_thinking_safety_and_media(self) -> None:
        root = make_content_config("root", GEMINI)
        adapter = make_content_config("adapter", GEMINI)
        reviewer = make_content_config("reviewer", GEMINI)

        assert root.thinking_config.thinking_level == types.ThinkingLevel.LOW
        assert adapter.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM
        assert reviewer.media_resolution == types.MediaResolution.MEDIA_RESOLUTION_MEDIUM
        assert {setting.threshold for setting in root.safety_settings} == {
            types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        }
        for config in (root, adapter, reviewer):
            assert config.temperature is None and config.top_p is None
            assert config.thinking_config.thinking_budget is None
            assert config.labels["service"] == "anyplot-agents"

    def test_output_caps_per_provider(self) -> None:
        """Gemini's thinking counts toward the cap, so its edit-only adapter call gets room; Claude keeps 2,048."""
        gemini = {kind: make_content_config(kind, GEMINI).max_output_tokens for kind in ("root", "adapter", "reviewer")}
        claude = {kind: make_content_config(kind, CLAUDE).max_output_tokens for kind in ("root", "adapter", "reviewer")}

        assert gemini == {"root": 2048, "adapter": GEMINI_ADAPTER_MAX_OUTPUT_TOKENS, "reviewer": 2048}
        assert GEMINI_ADAPTER_MAX_OUTPUT_TOKENS == 10_240
        assert claude == {"root": 2048, "adapter": 2048, "reviewer": 2048}
        assert make_model("adapter", CLAUDE).max_tokens == 2048

    def test_allow_full_file_on_gemini_lowers_thinking_without_touching_the_agent_config(self) -> None:
        agent_config = make_content_config("adapter", GEMINI)
        request = LlmRequest(config=agent_config.model_copy())  # ADK's per-request copy is shallow like this

        allow_full_file(request.config)

        assert request.config.max_output_tokens == ADAPTER_FULL_MAX_OUTPUT_TOKENS
        assert request.config.thinking_config is not None
        assert request.config.thinking_config.thinking_level == types.ThinkingLevel.LOW
        assert agent_config.max_output_tokens == GEMINI_ADAPTER_MAX_OUTPUT_TOKENS
        assert agent_config.thinking_config is not None
        assert agent_config.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM

    def test_allow_full_file_on_claude_keeps_thinking_disabled(self) -> None:
        agent_config = make_content_config("adapter", CLAUDE)
        request = LlmRequest(config=agent_config.model_copy())

        allow_full_file(request.config)

        assert request.config.max_output_tokens == ADAPTER_FULL_MAX_OUTPUT_TOKENS
        assert request.config.thinking_config is not None
        assert request.config.thinking_config.thinking_budget == 0
        assert request.config.thinking_config.thinking_level is None
        assert agent_config.max_output_tokens == 2048

    def test_unknown_kind_is_refused(self) -> None:
        with pytest.raises(ValueError):
            make_model("judge", CLAUDE)

    def test_no_other_module_constructs_a_model_or_client(self) -> None:
        pattern = re.compile(r"\b(?:AsyncAnthropicVertex|AnthropicVertex|AsyncAnthropic|Gemini|Claude|genai\.Client)\(")
        offenders = [
            str(path.relative_to(PACKAGE))
            for path in PACKAGE.rglob("*.py")
            if path.name != "models.py" and pattern.search(path.read_text(encoding="utf-8"))
        ]
        assert offenders == []


class TestClaudeStructuredOutput:
    def request(self, schema: type, tools: bool = False) -> LlmRequest:
        config = AnthropicGenerateContentConfig(max_output_tokens=100, effort="medium")
        config.response_schema = schema
        config.response_mime_type = "application/json"
        if tools:
            config.tools = [types.Tool(function_declarations=[types.FunctionDeclaration(name="other_tool")])]
        return LlmRequest(
            model="claude-haiku-5-5",
            contents=[types.Content(role="user", parts=[types.Part(text="adapt this")])],
            config=config,
        )

    async def run(self, request: LlmRequest, answer: dict) -> tuple[list, FakeAnthropic]:
        client = FakeAnthropic({"unknown": [{"json": answer}]})
        model = make_model("adapter", CLAUDE)
        model.__dict__["_anthropic_client"] = client
        responses = [response async for response in model.generate_content_async(request, stream=True)]
        return responses, client

    async def test_schema_becomes_a_forced_tool_and_the_answer_json_text(self) -> None:
        responses, client = await self.run(self.request(AdaptPlan), SCATTER_PLAN)

        call = client.calls[0]
        assert call["tool_choice"] == {"type": "tool", "name": STRUCTURED_TOOL}
        assert call["tools"][0]["input_schema"] == response_json_schema(AdaptPlan)
        assert "$ref" not in json.dumps(call["tools"][0]["input_schema"])
        assert call["output_config"] == {"effort": "medium"}
        assert "thinking" not in call or call["thinking"] is None or not isinstance(call["thinking"], dict)
        assert len(responses) == 1
        parts = responses[0].content.parts
        assert [part.function_call for part in parts] == [None]
        assert AdaptPlan.model_validate_json(parts[0].text).title == SCATTER_PLAN["title"]

    async def test_verdict_schema_round_trip(self) -> None:
        responses, _ = await self.run(self.request(Verdict), {"ok": True, "defects": []})

        assert Verdict.model_validate_json(responses[0].content.parts[0].text).ok is True

    def test_inlined_schema_has_no_definitions(self) -> None:
        schema = response_json_schema(Verdict)

        assert "$defs" not in schema
        assert schema["properties"]["defects"]["items"]["properties"]["id"]["enum"][0] == "VQ-01"


class TestJudge:
    async def test_retry_once_then_answer(self) -> None:
        judge = FakeJudge([RuntimeError("transient"), JudgeVerdict(verdict="attack", lang="DE-ch")])

        verdict = await judge.judge("<user_message>x</user_message>", "rubric")

        assert (verdict.verdict, verdict.lang) == ("attack", "de")
        assert len(judge.calls) == 2

    async def test_two_failures_are_unavailable(self) -> None:
        judge = FakeJudge([ValueError("bad json"), ValueError("bad json")])

        with pytest.raises(JudgeUnavailable):
            await judge.judge("text", "rubric")

    async def test_budget_timeout_is_unavailable(self) -> None:
        judge = FakeJudge(delay_s=0.2, timeout_s=0.05)

        with pytest.raises(JudgeUnavailable, match="in time"):
            await judge.judge("text", "rubric")

    def test_factory_follows_the_provider(self) -> None:
        claude = make_judge_client(CLAUDE)
        gemini = make_judge_client(GEMINI)

        assert isinstance(claude, AnthropicJudge)
        assert (claude.model, claude.project, claude.region, claude.timeout_s) == (
            "claude-haiku-5-5",
            "anyplot-eval",
            "global",
            4.0,
        )
        assert isinstance(gemini, GeminiJudge)
        assert (gemini.model, gemini.location) == ("gemini-3.5-flash-lite", "eu")

    async def test_anthropic_judge_parses_the_forced_tool(self) -> None:
        judge = make_judge_client(CLAUDE)
        assert isinstance(judge, AnthropicJudge)
        client = FakeAnthropic({"unknown": [{"json": {"verdict": "out_of_scope", "lang": "en"}}]})
        judge.__dict__["_client"] = client

        verdict = await judge.judge("<user_message>poem</user_message>", "# Scope judge")

        assert verdict.verdict == "out_of_scope"
        assert verdict.tokens == 120
        assert (verdict.input_tokens, verdict.output_tokens) == (100, 20)  # the split the eval harness prices
        assert client.calls[0]["tool_choice"]["type"] == "tool"

    def test_adapter_full_cap(self) -> None:
        assert ADAPTER_FULL_MAX_OUTPUT_TOKENS == 12_288

    async def test_cancellation_is_not_swallowed(self) -> None:
        judge = FakeJudge(delay_s=1.0)
        task = asyncio.create_task(judge.judge("text", "rubric"))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
