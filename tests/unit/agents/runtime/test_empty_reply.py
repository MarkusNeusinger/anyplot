"""Tests for the EmptyReply plugin: a final root response without text is asked for once more, else `no_reply`."""

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot.plugins import reply_language
from agents.anyplot.plugins.empty_reply import (
    NO_REPLY,
    RETRY_LINE,
    EmptyReplyPlugin,
    carries_answer,
    is_empty,
    stored_in_turn,
)
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, ToolCall
from agents.anyplot.plugins.tool_safety import ToolSafetyPlugin
from agents.anyplot.services import Services

from .fakes import ScriptedRoot, gemini_response


@dataclass
class FakeSession:
    id: str = "s1"
    user_id: str = "adm_1"
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeContext:
    invocation_id: str = "inv-1"
    agent_name: str = "anyplot"
    session: FakeSession = field(default_factory=FakeSession)


@pytest.fixture
def ledger() -> Any:
    current = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1")
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


def root_request() -> LlmRequest:
    return LlmRequest(
        model="m",
        contents=[types.Content(role="user", parts=[types.Part(text="only 2024")])],
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(name="get_dataset_profile")])]
        ),
    )


EMPTY = [
    LlmResponse(content=None, finish_reason=types.FinishReason.STOP),
    LlmResponse(content=types.Content(role="model", parts=[]), finish_reason=types.FinishReason.STOP),
    LlmResponse(content=types.Content(role="model", parts=[types.Part(text="")])),
    LlmResponse(content=types.Content(role="model", parts=[types.Part(text="  \n")])),
    LlmResponse(content=types.Content(role="model", parts=[types.Part(text="Reading the table.", thought=True)])),
    LlmResponse(content=None, finish_reason=types.FinishReason.MALFORMED_FUNCTION_CALL),
]
"""What the root's final response looked like when the user saw no reply: no content, no part, an empty or blank
text, a thought only, a call the model could not form."""


def lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    records = [record for record in caplog.records if record.name == "anyplot.agents.attribution"]
    return [line for line in (json.loads(record.getMessage()) for record in records) if line["hook"] == "empty_reply"]


async def check(response: LlmResponse, context: FakeContext | None = None) -> LlmResponse | None:
    return await EmptyReplyPlugin().after_model_callback(
        callback_context=context or FakeContext(),  # type: ignore[arg-type]
        llm_response=response,
    )


class TestEmptyReply:
    @pytest.mark.parametrize("response", EMPTY)
    def test_these_responses_carry_nothing_for_the_user(self, response: LlmResponse) -> None:
        assert is_empty(response)

    @pytest.mark.parametrize(
        "response", [gemini_response({"text": "4 rows; hours on x."}), gemini_response({"call": "get_dataset_profile"})]
    )
    def test_a_text_or_a_tool_call_is_no_empty_reply(self, response: LlmResponse) -> None:
        assert not is_empty(response)

    @pytest.mark.parametrize("index", range(len(EMPTY)))
    async def test_an_empty_reply_is_asked_once_more_and_the_answer_takes_its_place(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        index: int,
    ) -> None:
        model = ScriptedRoot([gemini_response({"text": "4 rows; hours on x."})])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        ledger.root_request = root_request()
        response = EMPTY[index].model_copy(deep=True)

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            returned = await check(response)

        # Edited in place, never returned: ShippedReply and ReplyLanguage after it check the answer.
        assert returned is None and reply_language.reply_text(response) == "4 rows; hours on x."
        assert response.finish_reason == types.FinishReason.STOP and response.error_code is None
        (asked,) = model.requests
        assert asked.contents[:-1] == ledger.root_request.contents
        assert asked.contents[-1].role == "user" and asked.contents[-1].parts[0].text == RETRY_LINE
        assert asked.config.tools  # the second ask may still call a tool, to read the data
        assert ledger.empty_reasked and ledger.error is None and ledger.llm_calls == 1 and ledger.tokens == 120
        assert [line["verdict"] for line in lines(caplog)] == ["reasked"]

    async def test_after_a_tool_the_second_ask_has_no_tools(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A second call of a tool that stores something would apply its change twice, within its per-turn cap or
        without one (`set_bindings`)."""
        model = ScriptedRoot([gemini_response({"text": "Renamed: Hours."})])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        ledger.root_request = root_request()
        ledger.tools = ["prepare_data"]

        await check(EMPTY[2].model_copy(deep=True))

        (asked,) = model.requests
        assert asked.config.tools is None and asked.tools_dict == {}
        assert ledger.root_request.config.tools  # the kept request itself keeps them

    @pytest.mark.parametrize(
        ("tool", "result", "agent", "stored"),
        [
            ("prepare_data", {"status": "ok", "rows": 3}, "anyplot", True),
            ("generate_data", {"status": "ok"}, "anyplot", True),
            ("run_data_code", {"status": "ok"}, "anyplot", True),
            ("set_bindings", {"status": "ok"}, "anyplot", True),
            ("set_language", {"status": "ok", "changed": False}, "anyplot", True),
            ("keep_plot_request", {"status": "ok", "request_kept": True}, "anyplot", True),
            ("forget", {"status": "ok", "entries": 0}, "anyplot", True),
            ("keep_plot_request", {"status": "ok", "request_kept": False}, "anyplot", False),
            ("prepare_data", {"status": "error", "code": "invalid_operations"}, "anyplot", False),
            ("get_dataset_profile", {"status": "ok", "rows": 3}, "anyplot", False),
            ("query_data", {"status": "ok"}, "anyplot", False),
            ("prepare_data", {"status": "ok"}, "adapter_matplotlib", False),
            # ToolSafety refuses the result for its size, but the version was stored before: still a change.
            ("prepare_data", {"status": "ok", "rows": 3, "profile": "x" * 20_000}, "anyplot", True),
            ("get_dataset_profile", {"status": "ok", "rows": 3, "profile": "x" * 40_000}, "anyplot", False),
            # A plot run that kept the first plot's request is no stored change: a summary turn still owes its reply.
            (
                "plot_pipeline",
                {"status": "not_ready", "reason": "data_unconfirmed", "request_kept": True},
                "anyplot",
                False,
            ),
        ],
    )
    async def test_a_tool_that_stored_a_change_is_noted(
        self, ledger: RequestLedger, tool: str, result: dict[str, Any], agent: str, stored: bool
    ) -> None:
        """Read from the record of the turn's calls, which ToolSafety closes from each tool's own answer, also when it
        then refuses the result (6a's finding: such a change used to miss EmptyReply's own note)."""
        context = SimpleNamespace(agent_name=agent, invocation_id="inv-1")

        await ToolSafetyPlugin().after_tool_callback(
            tool=SimpleNamespace(name=tool),  # type: ignore[arg-type]
            tool_args={},
            tool_context=context,  # type: ignore[arg-type]
            result=result,
        )

        assert stored_in_turn(ledger) is stored and carries_answer(ledger) is stored

    async def test_an_answer_that_calls_a_tool_goes_on_in_the_flow(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            reply_language, "root_model", lambda: ScriptedRoot([gemini_response({"call": "get_dataset_profile"})])
        )
        ledger.root_request = root_request()
        response = EMPTY[0].model_copy(deep=True)

        await check(response)

        assert response.content is not None and response.content.parts[0].function_call.name == "get_dataset_profile"
        assert ledger.error is None

    @pytest.mark.parametrize(
        ("answer", "reason"), [(gemini_response({"text": ""}), "empty"), (RuntimeError("down"), "error")]
    )
    async def test_still_empty_fails_the_turn_as_no_reply(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        answer: Any,
        reason: str,
    ) -> None:
        monkeypatch.setattr(reply_language, "root_model", lambda: ScriptedRoot([answer]))
        ledger.root_request = root_request()

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[2].model_copy(deep=True))

        assert ledger.error == NO_REPLY and ledger.refusal is None
        assert [(line["verdict"], line["reason"]) for line in lines(caplog)] == [(NO_REPLY, reason)]
        assert "only 2024" not in caplog.text

    async def test_a_failing_check_still_ends_an_empty_turn_as_no_reply(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        async def broken(*args: Any) -> str | None:
            raise RuntimeError("bug")

        monkeypatch.setattr(EmptyReplyPlugin, "_ask_again", staticmethod(broken))

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[0].model_copy(deep=True))

        assert ledger.error == NO_REPLY
        assert [(line["verdict"], line["reason"]) for line in lines(caplog)] == [(NO_REPLY, "check_failed")]

    async def test_one_ask_per_turn(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """The second ask called a tool, and the root's reply after the tool was empty again: no third call."""
        model = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        ledger.root_request = root_request()
        ledger.empty_reasked = True

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[0].model_copy(deep=True))

        assert model.requests == [] and ledger.error == NO_REPLY
        assert lines(caplog)[-1]["reason"] == "empty"

    async def test_without_a_kept_request_or_budget_the_turn_fails_at_once(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        model = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[0].model_copy(deep=True))
        assert ledger.error == NO_REPLY and lines(caplog)[-1]["reason"] == "no_request"

        ledger.error = None
        ledger.root_request = root_request()
        ledger.budget_tokens = 10**12  # the request's token budget is spent
        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[0].model_copy(deep=True))
        assert ledger.error == NO_REPLY and lines(caplog)[-1]["reason"] == "budget" and model.requests == []

    @pytest.mark.parametrize("carried", ["shipped", "switch", "stored"])
    async def test_a_turn_that_carries_its_answer_keeps_an_empty_closing_reply(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        carried: str,
    ) -> None:
        """A shipped plot is on the page, a switch the page carries out, a stored change reaches it with `done`: no
        error after any, so the user is never told to send a message whose change already happened."""
        model = ScriptedRoot([gemini_response({"text": ""})])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        ledger.root_request = root_request()
        if carried == "shipped":
            ledger.shipped_in_turn = True
        elif carried == "switch":
            ledger.switch_request = {"library": "plotly", "plot": True}
        else:
            ledger.tool_calls.append(ToolCall("set_bindings", outcome="changed"))

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(EMPTY[2].model_copy(deep=True))

        assert len(model.requests) == 1 and ledger.error is None
        assert [(line["verdict"], line["reason"]) for line in lines(caplog)] == [("empty_kept", "empty")]

    @pytest.mark.parametrize(
        ("context", "response", "halted"),
        [
            (FakeContext(), gemini_response({"text": "4 rows; hours on x."}), False),
            (FakeContext(), gemini_response({"call": "get_dataset_profile"}), False),
            (FakeContext(agent_name="adapter_matplotlib"), EMPTY[0], False),
            (FakeContext(), EMPTY[2].model_copy(update={"partial": True}), False),
            (FakeContext(), EMPTY[0], True),
        ],
    )
    async def test_other_responses_are_left_alone(
        self,
        ledger: RequestLedger,
        services: Services,
        monkeypatch: pytest.MonkeyPatch,
        context: FakeContext,
        response: LlmResponse,
        halted: bool,
    ) -> None:
        """A reply, a tool call, another agent's answer, a partial chunk, and a turn the scope guard already ended."""
        model = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: model)
        ledger.root_request = root_request()
        if halted:
            ledger.refuse("out_of_scope", "refused")

        assert await check(response.model_copy(deep=True), context) is None
        assert model.requests == [] and ledger.error is None
