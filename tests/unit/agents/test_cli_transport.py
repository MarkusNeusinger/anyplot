"""Tests for agents/anyplot/cli_transport.py and its settings and factories; no CLI, no model."""

import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot import models
from agents.anyplot.cli_transport import ClaudeCliClient, CliTransportError, CliUnsupported, plan_call, to_message
from agents.anyplot.settings import CLI_JUDGE_TIMEOUT_S, AgentSettings, get_settings


SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
IMAGE = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}}


def structured_call(**overrides: Any) -> dict[str, Any]:
    call: dict[str, Any] = {
        "model": "claude-haiku-5-5",
        "max_tokens": 4096,
        "system": [{"type": "text", "text": "RULES", "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": [{"type": "text", "text": "look", "cache_control": {}}, IMAGE]}],
        "thinking": {"type": "disabled"},
        "output_config": {"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
    }
    return {**call, **overrides}


def result_line(**fields: Any) -> str:
    return json.dumps({"type": "result", "is_error": False, **fields})


class Recorder:
    """A fake CLI runner: records each call and answers with the next scripted stdout."""

    def __init__(self, *answers: str) -> None:
        self.answers = list(answers)
        self.calls: list[tuple[list[str], dict[str, Any], str]] = []

    async def __call__(self, argv: list[str], stdin: bytes, cwd: str) -> str:
        self.calls.append((argv, json.loads(stdin), cwd))
        return self.answers.pop(0)


class TestPlan:
    def test_a_structured_call_keeps_text_and_image_and_drops_cache_control(self) -> None:
        plan = plan_call(structured_call())
        assert plan is not None
        assert plan["system"] == "RULES"
        assert plan["effort"] == "low"
        assert plan["schema"] == SCHEMA
        assert plan["tool"] is None
        assert plan["blocks"] == [{"type": "text", "text": "look"}, IMAGE]

    def test_a_single_tool_call_answers_with_the_tool_schema_from_the_first_user_turn(self) -> None:
        tool = {"name": "submit_score", "input_schema": SCHEMA, "strict": True}
        retry = [
            {"role": "user", "content": "score this"},
            {"role": "assistant", "content": [{"type": "tool_use", "id": "x", "name": "submit_score", "input": {}}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "incomplete"}]},
        ]
        plan = plan_call(structured_call(tools=[tool], tool_choice={"type": "auto"}, messages=retry, output_config={}))
        assert plan is not None
        assert (plan["tool"], plan["schema"]) == ("submit_score", SCHEMA)
        assert plan["blocks"] == [{"type": "text", "text": "score this"}]

    @pytest.mark.parametrize(
        "overrides",
        [
            {"tools": [{"name": "a", "input_schema": SCHEMA}, {"name": "b", "input_schema": SCHEMA}]},
            {"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]},
            {"messages": [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x", "content": "r"}]}]},
            {"messages": []},
        ],
    )
    def test_chat_with_tools_or_history_is_not_for_the_cli(self, overrides: dict[str, Any]) -> None:
        assert plan_call(structured_call(**overrides)) is None


class TestMessage:
    def test_structured_output_becomes_the_text_block_and_usage_is_kept(self) -> None:
        plan = plan_call(structured_call())
        assert plan is not None
        usage = {"input_tokens": 3, "output_tokens": 7, "cache_creation_input_tokens": 11, "cache_read_input_tokens": 0}
        message = to_message(plan, {"structured_output": {"ok": True}, "usage": usage})
        assert message.stop_reason == "end_turn"
        assert json.loads(message.content[0].text) == {"ok": True}
        assert (message.usage.input_tokens, message.usage.output_tokens) == (3, 7)
        assert message.usage.cache_creation_input_tokens == 11

    def test_a_tool_plan_answers_with_a_tool_use_block(self) -> None:
        plan = plan_call(structured_call(tools=[{"name": "submit", "input_schema": SCHEMA}], output_config={}))
        assert plan is not None
        message = to_message(plan, {"structured_output": {"ok": False}})
        assert message.stop_reason == "tool_use"
        assert (message.content[0].name, message.content[0].input) == ("submit", {"ok": False})

    def test_a_missing_structured_output_is_an_error(self) -> None:
        plan = plan_call(structured_call())
        assert plan is not None
        with pytest.raises(CliTransportError):
            to_message(plan, {"result": "plain text"})


class TestClient:
    def test_the_cli_gets_model_effort_schema_and_a_clean_working_directory(self, tmp_path: Path) -> None:
        runner = Recorder(result_line(structured_output={"ok": True}))
        log = tmp_path / "calls.jsonl"
        client = ClaudeCliClient(runner=runner, executable="claude", call_log=log)
        message = asyncio.run(client.messages.create(**structured_call()))
        argv, stdin, cwd = runner.calls[0]
        assert argv[argv.index("--model") + 1] == "claude-haiku-5-5"
        assert argv[argv.index("--effort") + 1] == "low"
        assert json.loads(argv[argv.index("--json-schema") + 1]) == SCHEMA
        assert argv[argv.index("--tools") + 1] == ""
        assert stdin["message"]["content"][1] == IMAGE
        assert not Path(cwd).exists()  # the scratch directory is gone after the call
        assert json.loads(message.content[0].text) == {"ok": True}
        assert json.loads(log.read_text())["ok"] is True

    def test_a_call_the_cli_cannot_answer_goes_to_the_fallback(self) -> None:
        sent: list[dict[str, Any]] = []

        async def create(**kwargs: Any) -> str:
            sent.append(kwargs)
            return "from vertex"

        client = ClaudeCliClient(fallback=SimpleNamespace(messages=SimpleNamespace(create=create)), runner=Recorder())
        root_call = structured_call(tools=[{"name": "a"}, {"name": "b"}])
        assert asyncio.run(client.messages.create(**root_call)) == "from vertex"
        assert sent == [root_call]

    def test_without_a_fallback_such_a_call_raises(self) -> None:
        client = ClaudeCliClient(runner=Recorder())
        with pytest.raises(CliUnsupported):
            asyncio.run(client.messages.create(**structured_call(tools=[{"name": "a"}, {"name": "b"}])))

    def test_an_error_result_raises_and_is_logged(self, tmp_path: Path) -> None:
        log = tmp_path / "calls.jsonl"
        runner = Recorder(json.dumps({"type": "result", "is_error": True, "result": "usage limit"}))
        client = ClaudeCliClient(runner=runner, executable="claude", call_log=log)
        with pytest.raises(CliTransportError, match="usage limit"):
            asyncio.run(client.messages.create(**structured_call()))
        assert json.loads(log.read_text())["ok"] is False


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.upper().startswith("AGENT_") or name.upper() in ("ENVIRONMENT", "K_SERVICE"):
            monkeypatch.delenv(name)
    get_settings.cache_clear()


@pytest.mark.usefixtures("clean_env")
class TestSettingsAndFactories:
    def test_the_cli_transport_is_refused_outside_development_and_test(self) -> None:
        with pytest.raises(ValidationError, match="claude-cli"):
            AgentSettings(transport="claude-cli", environment="production")
        assert AgentSettings(transport="claude-cli", environment="development").transport == "claude-cli"

    def test_per_kind_models_need_the_cli_transport_and_a_cli_model(self) -> None:
        with pytest.raises(ValidationError, match="AGENT_ADAPTER_MODEL"):
            AgentSettings(adapter_model="claude-sonnet-5-5", environment="development")
        with pytest.raises(ValidationError, match="claude-cli transport"):
            AgentSettings(transport="claude-cli", environment="development", reviewer_model="claude-x")

    def test_make_model_uses_the_kind_model_and_the_cli_client(self) -> None:
        settings = AgentSettings(transport="claude-cli", environment="development", adapter_model="claude-sonnet-5-5")
        adapter = models.make_model("adapter", settings)
        root = models.make_model("root", settings)
        assert (adapter.model, root.model) == ("claude-sonnet-5-5", "claude-haiku-5-5")
        assert isinstance(adapter.transport_client, ClaudeCliClient)
        assert adapter.transport_client is root.transport_client  # one shared concurrency gate
        assert models.make_model("adapter", AgentSettings()).transport_client is None

    def test_the_judge_gets_the_cli_client_and_a_longer_budget(self) -> None:
        judge = models.make_judge_client(AgentSettings(transport="claude-cli", environment="test"))
        assert isinstance(judge, models.AnthropicJudge)
        assert isinstance(judge.client, ClaudeCliClient)
        assert judge.timeout_s == CLI_JUDGE_TIMEOUT_S
