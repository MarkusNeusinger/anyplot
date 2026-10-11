"""Tests for agents/anyplot/models.py: factories per provider, Claude structured output, the judge."""

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import pytest
from google.adk.models.anthropic_llm import AnthropicGenerateContentConfig
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.anyplot import models
from agents.anyplot.models import (
    ADAPTER_FULL_MAX_OUTPUT_TOKENS,
    GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS,
    GEMINI_ADAPTER_MAX_OUTPUT_TOKENS,
    JUDGE_MAX_OUTPUT_TOKENS,
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
    structured_output_format,
    thinking_budget,
)
from agents.anyplot.schemas import MAX_FULL_CODE_CHARS, AdaptPlan, Verdict
from agents.anyplot.settings import MAX_THINKING_BUDGET, AgentSettings

from .fakes import SCATTER_PLAN, FakeAnthropic


GEMINI = AgentSettings(provider="gemini", model="gemini-3.8-flash", judge_model="gemini-3.5-flash-lite")
# Thinking off, so the caps below are the bare ones; the defaults (root 1,024, adapter 2,048) are tested apart.
CLAUDE = AgentSettings(location="global", project="anyplot-eval", root_thinking_budget=0, adapter_thinking_budget=0)
CLAUDE_DEFAULTS = AgentSettings(location="global", project="anyplot-eval")
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
        assert model.max_tokens == {"root": 4096, "adapter": 8192, "reviewer": 4096}[kind]

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
        """Every cap leaves ample headroom above the spike-X rerun's largest answer of its kind.

        At 2,048, 23 of 244 first Claude adapter calls were cut off; the largest finished plan
        took 2,606 tokens, a review 600, a root reply 259, a judge answer 59.
        """
        gemini = {kind: make_content_config(kind, GEMINI).max_output_tokens for kind in ("root", "adapter", "reviewer")}
        claude = {kind: make_content_config(kind, CLAUDE).max_output_tokens for kind in ("root", "adapter", "reviewer")}

        assert gemini == {"root": 4096, "adapter": GEMINI_ADAPTER_MAX_OUTPUT_TOKENS, "reviewer": 4096}
        assert GEMINI_ADAPTER_MAX_OUTPUT_TOKENS == 8_192  # bounded by the soft deadline, not by the answers
        assert claude == {"root": 4096, "adapter": 8192, "reviewer": 4096}
        assert make_model("adapter", CLAUDE).max_tokens == 8192
        assert JUDGE_MAX_OUTPUT_TOKENS == 256

    def test_allow_full_file_on_gemini_lowers_thinking_without_touching_the_agent_config(self) -> None:
        agent_config = make_content_config("adapter", GEMINI)
        request = LlmRequest(config=agent_config.model_copy())  # ADK's per-request copy is shallow like this

        allow_full_file(request.config)

        assert request.config.max_output_tokens == GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS
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
        assert agent_config.max_output_tokens == 8192

    def test_claude_defaults_think_adaptively_with_the_budgets_added_to_the_caps(self) -> None:
        """Since 2026-10-11 the root thinks with 1,024 and the adapter with 2,048 extra output tokens."""
        from agents.anyplot.models import ADAPTIVE_THINKING

        configs = {kind: make_content_config(kind, CLAUDE_DEFAULTS) for kind in ("root", "adapter", "reviewer")}

        assert {kind: config.max_output_tokens for kind, config in configs.items()} == {
            "root": 4096 + 1024,
            "adapter": 8192 + 2048,
            "reviewer": 4096,
        }
        assert configs["root"].thinking_config.thinking_budget == ADAPTIVE_THINKING
        assert configs["adapter"].thinking_config.thinking_budget == ADAPTIVE_THINKING
        assert configs["reviewer"].thinking_config.thinking_budget == 0  # the reviewer never thinks
        assert make_model("adapter", CLAUDE_DEFAULTS).max_tokens == 8192 + 2048
        request = LlmRequest(config=configs["adapter"].model_copy())
        allow_full_file(request.config)
        assert request.config.max_output_tokens == ADAPTER_FULL_MAX_OUTPUT_TOKENS + 2048

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

    async def test_schema_becomes_an_output_format_next_to_the_effort(self) -> None:
        responses, client = await self.run(self.request(AdaptPlan), SCATTER_PLAN)

        call = client.calls[0]
        assert call["output_config"] == {"effort": "medium", "format": structured_output_format(AdaptPlan)}
        assert not isinstance(call.get("tools"), list) and not isinstance(call.get("tool_choice"), dict)
        assert "thinking" not in call or call["thinking"] is None or not isinstance(call["thinking"], dict)
        assert len(responses) == 1
        parts = responses[0].content.parts
        assert [part.function_call for part in parts] == [None]
        assert AdaptPlan.model_validate_json(parts[0].text).title == SCATTER_PLAN["title"]

    async def test_a_request_with_tools_gets_no_format(self) -> None:
        client = FakeAnthropic({"unknown": [{"text": "chat"}]})
        model = make_model("root", CLAUDE)
        model.__dict__["_anthropic_client"] = client

        responses = [response async for response in model.generate_content_async(self.request(AdaptPlan, tools=True))]

        assert responses[0].content.parts[0].text == "chat"
        assert "format" not in (client.calls[0].get("output_config") or {})

    async def test_adaptive_thinking_asks_the_api_to_drop_a_rebound_thinking_block(self) -> None:
        """The root replays its thinking block after a tool result while the session block moved,
        so without the binding control the API answers 400 'Invalid signature in thinking block'."""
        from agents.anyplot.models import ADAPTIVE_THINKING, THINKING_BINDING_BETA

        thinking = self.request(AdaptPlan, tools=True)
        thinking.config.thinking_config = types.ThinkingConfig(thinking_budget=ADAPTIVE_THINKING)
        disabled = self.request(AdaptPlan, tools=True)
        disabled.config.thinking_config = types.ThinkingConfig(thinking_budget=0)
        client = FakeAnthropic({"unknown": [{"text": "chat"}, {"text": "chat"}]})
        model = make_model("root", CLAUDE_DEFAULTS)
        model.__dict__["_anthropic_client"] = client

        for request in (thinking, disabled):
            [_ async for _ in model.generate_content_async(request)]

        with_thinking, without = client.calls
        assert with_thinking["thinking"]["type"] != "disabled"
        assert with_thinking["thinking"]["block_binding"] == {"prefix_mismatch_behavior": "drop_block"}
        assert THINKING_BINDING_BETA in with_thinking["extra_headers"]["anthropic-beta"]
        assert without["thinking"] == {"type": "disabled"}
        assert "extra_headers" not in without

    async def test_verdict_schema_round_trip(self) -> None:
        responses, _ = await self.run(self.request(Verdict), {"ok": True, "defects": []})

        assert Verdict.model_validate_json(responses[0].content.parts[0].text).ok is True

    def test_inlined_schema_has_no_definitions(self) -> None:
        schema = response_json_schema(Verdict)

        assert "$defs" not in schema
        assert schema["properties"]["defects"]["items"]["properties"]["id"]["enum"][0] == "VQ-01"

    @pytest.mark.parametrize("schema", [AdaptPlan, Verdict])
    def test_the_format_is_strict_and_keeps_the_limits_as_hints(self, schema: type) -> None:
        """Constrained decoding needs `additionalProperties: false` and refuses length and count keywords."""
        output_format = structured_output_format(schema)
        text = json.dumps(output_format)

        assert output_format["type"] == "json_schema"
        assert "$ref" not in text and "$defs" not in text

        def objects(node: object) -> list[dict]:
            if isinstance(node, dict):
                found = [node] if node.get("type") == "object" else []
                return found + [item for value in node.values() for item in objects(value)]
            if isinstance(node, list):
                return [item for value in node for item in objects(value)]
            return []

        assert all(item["additionalProperties"] is False for item in objects(output_format["schema"]))
        for keyword in ("minLength", "maxLength", "maxItems", "minimum", "maximum"):
            assert f'"{keyword}"' not in text
        assert "maxItems: 5" in text  # the limit stays as a hint in the description


THINKING = AgentSettings(
    location="global", project="anyplot-eval", root_thinking_budget=2048, adapter_thinking_budget=4096
)
NON_STREAMING_LIMIT = 128_000 * 600 // 3600
"""The largest `max_tokens` the Anthropic SDK sends without streaming (`_calculate_nonstreaming_timeout`)."""


class TestThinkingMeasurement:
    """`AGENT_*_THINKING_BUDGET`: adaptive Claude thinking with its room added to the cap; 0 turns it off."""

    def test_zero_turns_thinking_off(self) -> None:
        assert [thinking_budget(kind, CLAUDE) for kind in ("root", "adapter", "reviewer")] == [0, 0, 0]
        assert thinking_budget("adapter", GEMINI) == 0

    def test_a_budget_turns_on_adaptive_thinking_and_adds_its_room_to_the_cap(self) -> None:
        configs = {kind: make_content_config(kind, THINKING) for kind in ("root", "adapter", "reviewer")}

        assert {kind: config.max_output_tokens for kind, config in configs.items()} == {
            "root": 4096 + 2048,
            "adapter": 8192 + 4096,
            "reviewer": 4096,
        }
        assert {kind: config.thinking_config.thinking_budget for kind, config in configs.items()} == {
            "root": -1,
            "adapter": -1,
            "reviewer": 0,
        }
        assert make_model("adapter", THINKING).max_tokens == 8192 + 4096

    def test_a_full_file_keeps_the_thinking_room_below_the_sdk_limit(self) -> None:
        request = LlmRequest(config=make_content_config("adapter", THINKING).model_copy())

        allow_full_file(request.config, THINKING)

        assert request.config.max_output_tokens == ADAPTER_FULL_MAX_OUTPUT_TOKENS + 4096
        assert request.config.thinking_config is not None and request.config.thinking_config.thinking_budget == -1
        assert ADAPTER_FULL_MAX_OUTPUT_TOKENS + MAX_THINKING_BUDGET < NON_STREAMING_LIMIT

    async def test_the_adapter_thinks_before_its_structured_answer(self) -> None:
        client = FakeAnthropic({"unknown": [{"thought": "plan the edits first", "json": SCATTER_PLAN}]})
        model = make_model("adapter", THINKING)
        model.__dict__["_anthropic_client"] = client
        config = make_content_config("adapter", THINKING)
        config.response_schema = AdaptPlan
        request = LlmRequest(
            model="claude-haiku-5-5",
            contents=[types.Content(role="user", parts=[types.Part(text="adapt this")])],
            config=config,
        )

        responses = [response async for response in model.generate_content_async(request)]

        call = client.calls[0]
        assert call["thinking"] == {
            "type": "adaptive",
            "display": "summarized",
            "block_binding": {"prefix_mismatch_behavior": "drop_block"},  # a rebound block is dropped, not a 400
        }
        assert call["max_tokens"] == 8192 + 4096
        assert call["output_config"]["effort"] == "medium" and call["output_config"]["format"]["type"] == "json_schema"
        parts = responses[0].content.parts
        assert parts[0].thought and parts[0].text == "plan the edits first"
        answer = "".join(part.text for part in parts if part.text and not part.thought)
        assert AdaptPlan.model_validate_json(answer).title == SCATTER_PLAN["title"]


class TestJudge:
    async def test_retry_once_then_answer(self) -> None:
        judge = FakeJudge([RuntimeError("transient"), JudgeVerdict(verdict="attack", lang="DE-ch")])

        verdict = await judge.judge("<user_message>x</user_message>", "rubric")

        assert (verdict.verdict, verdict.lang) == ("attack", "de")
        assert len(judge.calls) == 2

    async def test_two_failures_are_unavailable(self) -> None:
        judge = FakeJudge([ValueError("bad json"), ValueError("bad json")])

        with pytest.raises(JudgeUnavailable, match=r"failed twice \(ValueError\)"):
            await judge.judge("text", "rubric")

    async def test_budget_timeout_is_unavailable(self) -> None:
        judge = FakeJudge(delay_s=0.2, timeout_s=0.05)

        with pytest.raises(JudgeUnavailable, match="in time$"):
            await judge.judge("text", "rubric")

    async def test_retry_waits_the_backoff(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A transient failure is not retried in the same instant: the retry starts a back-off later."""
        monkeypatch.setattr(models, "JUDGE_RETRY_BACKOFF_S", 0.05)
        judge = FakeJudge([RuntimeError("429"), JudgeVerdict(verdict="in_scope", lang="en")])
        loop = asyncio.get_running_loop()

        started = loop.time()
        verdict = await judge.judge("text", "rubric")

        assert verdict.verdict == "in_scope"
        assert len(judge.calls) == 2
        assert loop.time() - started >= 0.05

    async def test_first_answer_does_not_wait(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(models, "JUDGE_RETRY_BACKOFF_S", 1.0)
        judge = FakeJudge([JudgeVerdict(verdict="in_scope", lang="en")])
        loop = asyncio.get_running_loop()

        started = loop.time()
        await judge.judge("text", "rubric")

        assert loop.time() - started < 0.5

    async def test_budget_running_out_in_the_backoff_names_the_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Fail closed, and keep the cause: the budget ends during the wait, after one failed call."""
        monkeypatch.setattr(models, "JUDGE_RETRY_BACKOFF_S", 0.2)
        judge = FakeJudge([RuntimeError("quota")], timeout_s=0.05)

        with pytest.raises(JudgeUnavailable, match=r"in time \(after RuntimeError\)$"):
            await judge.judge("text", "rubric")
        assert len(judge.calls) == 1  # the retry never started

    def test_backoff_fits_the_default_budget(self) -> None:
        """Two judge calls of about 1.5 s each and the back-off fit the default 4 s budget."""
        assert 2 * 1.5 + models.JUDGE_RETRY_BACKOFF_S <= AgentSettings().judge_timeout_s

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

    async def test_anthropic_judge_answers_under_the_format(self) -> None:
        judge = make_judge_client(CLAUDE)
        assert isinstance(judge, AnthropicJudge)
        client = FakeAnthropic({"unknown": [{"json": {"verdict": "out_of_scope", "lang": "en"}}]})
        judge.__dict__["_client"] = client

        verdict = await judge.judge("<user_message>poem</user_message>", "# Scope judge")

        assert verdict.verdict == "out_of_scope"
        assert verdict.tokens == 120
        assert (verdict.input_tokens, verdict.output_tokens) == (100, 20)  # the split the eval harness prices
        call = client.calls[0]
        schema = call["output_config"]["format"]["schema"]
        assert schema["properties"]["verdict"]["enum"] == ["in_scope", "out_of_scope", "attack", "needs_data"]
        assert schema["additionalProperties"] is False and schema["required"] == ["verdict", "lang"]
        assert "tools" not in call and "tool_choice" not in call
        assert call["thinking"] == {"type": "disabled"}

    async def test_anthropic_judge_retries_a_refusal_then_fails_closed(self) -> None:
        judge = make_judge_client(CLAUDE)
        assert isinstance(judge, AnthropicJudge)
        refusal = {"json": {"verdict": "in_scope", "lang": "en"}, "stop": "refusal"}
        client = FakeAnthropic({"unknown": [refusal, dict(refusal)]})
        judge.__dict__["_client"] = client

        with pytest.raises(JudgeUnavailable, match="failed twice"):
            await judge.judge("<user_message>x</user_message>", "# Scope judge")
        assert len(client.calls) == 2

    async def test_anthropic_judge_transcribes_under_the_table_format(self) -> None:
        """The same client reads free text as a table: a larger cap, the table schema, thinking off."""
        from agents.anyplot.models import TRANSCRIBE_MAX_OUTPUT_TOKENS

        judge = make_judge_client(CLAUDE)
        assert isinstance(judge, AnthropicJudge)
        table = {"columns": ["Tier", "Anzahl"], "rows": [["Hund", "7"], ["Katze", "3"]], "note": ""}
        client = FakeAnthropic({"unknown": [{"json": table}]})
        judge.__dict__["_client"] = client

        reading = await judge.transcribe("<user_text>Hund 7 Katze 3</user_text>", "# Table transcriber")

        assert reading.table.columns == ["Tier", "Anzahl"] and reading.table.rows == [["Hund", "7"], ["Katze", "3"]]
        assert (reading.tokens, reading.input_tokens, reading.output_tokens) == (120, 100, 20)
        call = client.calls[0]
        assert call["max_tokens"] == TRANSCRIBE_MAX_OUTPUT_TOKENS and call["thinking"] == {"type": "disabled"}
        schema = call["output_config"]["format"]["schema"]
        assert set(schema["properties"]) == {"columns", "rows", "note"} and schema["additionalProperties"] is False
        assert call["system"] == "# Table transcriber" and "tools" not in call

    async def test_gemini_judge_transcribes_under_the_response_schema(self) -> None:
        """The Gemini judge reads a table too: the table schema, the larger cap, minimal thinking, its token split."""
        from agents.anyplot.data.transcribe import TranscribedTable
        from agents.anyplot.models import TRANSCRIBE_MAX_OUTPUT_TOKENS

        judge = make_judge_client(GEMINI)
        assert isinstance(judge, GeminiJudge)
        calls: list[dict[str, Any]] = []

        class _Usage:
            prompt_token_count = 300
            tool_use_prompt_token_count = 0
            candidates_token_count = 40
            thoughts_token_count = 5
            total_token_count = 345

        class _Response:
            text = '{"columns": ["Tier", "Anzahl"], "rows": [["Hund", "7"]], "note": "ok"}'
            usage_metadata = _Usage()

        class _Models:
            async def generate_content(self, **kwargs: Any) -> _Response:
                calls.append(kwargs)
                return _Response()

        class _Client:
            class aio:  # noqa: N801 - mirrors `genai.Client().aio.models`
                models = _Models()

        judge.__dict__["_client"] = _Client()

        reading = await judge.transcribe("<user_text>Hund 7</user_text>", "# Table transcriber")

        assert reading.table == TranscribedTable(columns=["Tier", "Anzahl"], rows=[["Hund", "7"]], note="ok")
        assert (reading.tokens, reading.input_tokens, reading.output_tokens) == (345, 300, 45)
        config = calls[0]["config"]
        assert calls[0]["model"] == "gemini-3.5-flash-lite" and calls[0]["contents"] == "<user_text>Hund 7</user_text>"
        assert config.response_schema is TranscribedTable and config.response_mime_type == "application/json"
        assert config.max_output_tokens == TRANSCRIBE_MAX_OUTPUT_TOKENS
        assert (
            config.thinking_config is not None and config.thinking_config.thinking_level == types.ThinkingLevel.MINIMAL
        )
        assert config.system_instruction == "# Table transcriber"

    def test_adapter_full_cap(self) -> None:
        """Claude's full-file cap holds a plan at the schema's 24 KB limit; Gemini's is bounded by the deadline."""
        assert ADAPTER_FULL_MAX_OUTPUT_TOKENS == 16_384
        assert GEMINI_ADAPTER_FULL_MAX_OUTPUT_TOKENS == 12_288
        assert MAX_FULL_CODE_CHARS / 2.5 < ADAPTER_FULL_MAX_OUTPUT_TOKENS  # 2.5 characters per Haiku 5.5 token

    async def test_cancellation_is_not_swallowed(self) -> None:
        judge = FakeJudge(delay_s=1.0)
        task = asyncio.create_task(judge.judge("text", "rubric"))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
