"""Tests for the refused turns in the root's request and for the RootRefusal plugin: a fixed refusal the root sends
for a message the scope judge passed is asked for once more."""

import json
from dataclasses import dataclass, field
from typing import Any

import pytest
from google.adk.events.event import Event
from google.adk.flows.llm_flows.context import _fencing
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot.plugins import reply_language
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.plugins.root_refusal import JUDGE_PASSED, RETRY_LINE, RootRefusalPlugin, is_fixed_refusal
from agents.anyplot.plugins.scope_guard import (
    GUARD_UNAVAILABLE_TEXT,
    HALT_AUTHOR,
    is_refused_turn,
    withheld_messages,
    withheld_text,
    without_refused_turns,
)
from agents.anyplot.policy import fixed_replies, refusal
from agents.anyplot.services import Services

from .fakes import ScriptedRoot, gemini_response


REFUSAL = refusal("out_of_scope", "en")


def user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def model(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def halt(text: str) -> types.Content:
    """A halt event's text as ADK itself hands it to the root: the event's author is `model`, another agent."""
    event = Event(author=HALT_AUTHOR, content=types.Content(role="model", parts=[types.Part(text=text)]))
    shown = _fencing._present_other_agent_message(event)
    assert shown is not None and shown.content is not None
    return shown.content


class TestRefusedTurns:
    def test_adk_hands_a_halt_event_over_as_the_quote_the_filter_knows(self) -> None:
        """Pins ADK's form: a user content with a preamble part and one quoted part that starts `[model] said:`."""
        content = halt(REFUSAL)

        assert content.role == "user" and len(content.parts or []) == 2
        assert is_refused_turn(content)
        assert is_refused_turn(halt(GUARD_UNAVAILABLE_TEXT))

    @pytest.mark.parametrize("code", [None, "out_of_scope", "needs_data", "other_library"])
    def test_every_placeholder_of_a_withheld_message_is_a_refused_turn(self, code: str | None) -> None:
        assert is_refused_turn(user(withheld_text(code)))

    @pytest.mark.parametrize(
        "content",
        [
            user("make the bars blue"),
            user("[model] said: nothing of the kind"),  # a user's own words, one part and no preamble
            user("[message withheld by scope policy: out_of_scope] is what the page showed, why?"),
            model(REFUSAL),
            types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(name="query_data", response={"rows": 3}))],
            ),
        ],
    )
    def test_what_the_user_the_root_and_the_tools_wrote_stays(self, content: types.Content) -> None:
        assert not is_refused_turn(content)

    def test_the_request_loses_the_refused_turns_and_nothing_else(self) -> None:
        first, reply, asked = user("which columns?"), model("Two columns."), user("make the bars blue")
        contents = [first, reply, user(withheld_text("out_of_scope")), halt(REFUSAL), asked]

        assert without_refused_turns(contents) == [first, reply, asked]
        assert without_refused_turns([first, reply, asked]) == [first, reply, asked]

    def test_a_request_of_refused_turns_alone_stays_as_it_is(self) -> None:
        """Never an empty request: the root is not called for a refused turn, so this is no case of the service."""
        contents = [user(withheld_text("needs_data")), halt(refusal("needs_data", "en"))]

        assert without_refused_turns(contents) == contents

    def test_the_withheld_messages_are_counted_from_the_sessions_events(self) -> None:
        events = [
            Event(author="user", content=user("which columns?")),
            Event(author="user", content=user(withheld_text("out_of_scope"))),
            Event(author=HALT_AUTHOR, content=model(REFUSAL)),
            Event(author="user", content=user(withheld_text())),
            Event(author="user", content=user("make the bars blue")),
        ]

        assert withheld_messages(events) == 2 and withheld_messages(events[:1]) == 0


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
    current.guards.append(JUDGE_PASSED)
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


def root_request() -> LlmRequest:
    return LlmRequest(
        model="m",
        contents=[user("what is the slope of the fitted line?")],
        config=types.GenerateContentConfig(
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(name="query_data")])]
        ),
    )


def lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    records = [record for record in caplog.records if record.name == "anyplot.agents.attribution"]
    found = [json.loads(record.getMessage()) for record in records]
    return [line["verdict"] for line in found if line["hook"] == "root_refusal"]


async def check(response: LlmResponse, context: FakeContext | None = None) -> LlmResponse | None:
    return await RootRefusalPlugin().after_model_callback(
        callback_context=context or FakeContext(),  # type: ignore[arg-type]
        llm_response=response,
    )


class TestRootRefusal:
    def test_a_fixed_refusal_is_the_whole_reply_in_any_language(self) -> None:
        assert all(is_fixed_refusal(gemini_response({"text": text})) for text in fixed_replies())
        assert is_fixed_refusal(gemini_response({"text": f"  {REFUSAL}\n"}))
        assert not is_fixed_refusal(gemini_response({"text": f"{REFUSAL} But the slope is 0.07."}))
        assert not is_fixed_refusal(gemini_response({"call": "query_data"}))
        assert not is_fixed_refusal(LlmResponse(content=None))

    async def test_the_refusal_of_a_passed_message_is_asked_once_more(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([gemini_response({"text": "The slope is 0.07 per degree."})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": REFUSAL})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            returned = await check(response)

        # Edited in place, never returned: ShippedReply and ReplyLanguage after it check the answer.
        assert returned is None and reply_language.reply_text(response) == "The slope is 0.07 per degree."
        (asked,) = answers.requests
        assert asked.contents[:-1] == ledger.root_request.contents
        assert asked.contents[-1].role == "user" and asked.contents[-1].parts[0].text == RETRY_LINE
        assert asked.config.tools  # the answer may need to read the data
        assert ledger.refusal_reasked and ledger.error is None and ledger.llm_calls == 1
        assert lines(caplog) == ["reasked"]

    async def test_after_a_tool_the_second_ask_has_no_tools(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        answers = ScriptedRoot([gemini_response({"text": "Renamed: Hours."})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        ledger.tools = ["prepare_data"]

        await check(gemini_response({"text": REFUSAL}))

        (asked,) = answers.requests
        assert asked.config.tools is None and asked.tools_dict == {}

    @pytest.mark.parametrize(
        "second", [gemini_response({"text": REFUSAL}), LlmResponse(content=None), RuntimeError("the model is away")]
    )
    async def test_a_second_refusal_an_empty_answer_or_a_failed_call_keeps_the_reply(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        second: LlmResponse | Exception,
    ) -> None:
        answers = ScriptedRoot([second])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": REFUSAL})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert reply_language.reply_text(response) == REFUSAL and ledger.error is None
        assert lines(caplog) == ["kept"]

    async def test_the_root_is_asked_once_per_turn(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([gemini_response({"call": "query_data"})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        first, later = gemini_response({"text": REFUSAL}), gemini_response({"text": REFUSAL})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(first)  # the answer calls a tool, so ADK calls the root again
            await check(later)

        assert first.content is not None and first.content.parts[0].function_call is not None
        assert reply_language.reply_text(later) == REFUSAL and len(answers.requests) == 1
        assert lines(caplog) == ["reasked", "kept"]

    async def test_without_a_kept_request_the_reply_stays(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        response = gemini_response({"text": REFUSAL})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert reply_language.reply_text(response) == REFUSAL and lines(caplog) == ["kept"]

    @pytest.mark.parametrize(
        "guards",
        [
            [],  # an action of the page: no judge ran
            [("scope_guard", "out_of_scope"), ("scope_guard", "paste_note_in_scope")],
            [("scope_guard", "needs_data"), ("scope_guard", "paste_note_in_scope")],
            [("scope_guard", "other_library"), ("scope_guard", "served_library_in_scope")],
        ],
    )
    async def test_where_the_judge_passed_nothing_the_roots_refusal_stands(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        guards: list[tuple[str, str]],
    ) -> None:
        answers = ScriptedRoot([gemini_response({"text": "unused"})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.guards[:] = guards
        ledger.root_request = root_request()
        response = gemini_response({"text": REFUSAL})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert reply_language.reply_text(response) == REFUSAL and not answers.requests and lines(caplog) == []

    async def test_an_ordinary_reply_a_tool_call_and_another_agent_pass(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(gemini_response({"text": "Two columns."}))
            await check(gemini_response({"call": "query_data"}))
            await check(gemini_response({"text": REFUSAL}), FakeContext(agent_name="adapter"))

        assert lines(caplog) == [] and not ledger.refusal_reasked
