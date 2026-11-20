"""On the summary turn of a paste that replaced data, the root's request keeps the discussion and loses the replaced
table's facts (`plugins/replaced_table.py`).

Production, 2026-11-19 and 2026-11-20: a session held a table whose `day` column held dates and the root's summary of
it; the user pasted a table whose `day` held text, with the note "Convert the column day to dates.", and the root
answered from the first table's `get_dataset_profile` result and its own summary that the column already held dates.
The request of that turn now holds every user message and every text reply, none of the first table's tool exchanges
and none of the root's thinking about them, and the note starts with a fixed server line that marks the switch. The
stored events, the scope judge and every other turn stay as they were.
"""

import logging
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from agents.anyplot.agent import REPLACED_DATA_LINE
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.models import FakeJudge, JudgeVerdict
from agents.anyplot.plugins import replaced_table
from agents.anyplot.plugins.number_provenance import FigureCheck, _relayed, collect_figures
from agents.anyplot.plugins.replaced_table import (
    DISCUSSION_TOOLS,
    REPLACED_TABLE_LINE,
    TABLE_TOOLS,
    ReplacedTablePlugin,
    replacing_summary_turn,
    without_replaced_table,
)
from agents.anyplot.plugins.scope_guard import withheld_text, without_refused_turns
from agents.anyplot.policy import refusal
from agents.anyplot.services import Services
from agents.anyplot.session_state import (
    BINDINGS,
    DATASET_ID,
    DATASET_ORIGINAL,
    DATASET_TOP,
    DATASET_VERSION,
    SUMMARY_PENDING,
    initial_state,
)
from agents.anyplot.tools.session import ROOT_TOOL_NAMES
from agents.main import ACTION_MESSAGES, Runtime, app, get_runtime

from .fakes import FakeAnthropic, kind_of
from .test_paste_conversions import open_spec, paste, say
from .test_root_refusal import halt
from .test_service_flow import PROVIDERS, USER, permissive_queue


SPEC = "line-timeseries-rolling"
FIRST = "day,visitors\n8 Nov 2026,1403\n9 Nov 2026,1527\n10 Nov 2026,1496\n11 Nov 2026,1618\n"
"""An invented week of visitors whose `day` reads as dates at the paste."""
SECOND = "day,visitors\n1st March 2026,87\n2nd March 2026,93\n3rd March 2026,78\n4th March 2026,102\n"
"""Its replacement: the same column names, `day` in a form no date reading takes, so it stays text."""
ACTION = ACTION_MESSAGES["summarize_data"]
NOTE = "Convert the column day to dates."
SUMMARY = "4 rows; day holds dates from 8 to 11 November 2026, visitors per day."
PROFILE = {"call": "get_dataset_profile", "args": {}}
MARKED_NOTE = f"text:{REPLACED_TABLE_LINE}\n\n{NOTE}"

Turn = tuple[str, list[str]]

DISCUSSION: list[Turn] = [("user", [f"text:{ACTION}"]), ("assistant", [f"text:{SUMMARY}"]), ("user", [MARKED_NOTE])]
"""The note's request after the first table's summary turn: the action, the summary and the marked note."""


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


def user(*texts: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text) for text in texts])


def reply(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def call(name: str, call_id: str, *, thought: str | None = None, text: str | None = None) -> types.Content:
    parts = []
    if thought is not None:
        parts.append(types.Part(text=thought, thought=True, thought_signature=b"sig"))
    if text is not None:
        parts.append(types.Part(text=text))
    parts.append(types.Part(function_call=types.FunctionCall(id=call_id, name=name, args={})))
    return types.Content(role="model", parts=parts)


def answer(name: str, call_id: str, **response: Any) -> types.Content:
    return answers((name, call_id), **response)


def answers(*calls: tuple[str, str], **response: Any) -> types.Content:
    """One user content with the answer of each `(name, call id)`, as ADK sends the answers of one model turn."""
    result = response or {"status": "ok"}
    parts = [
        types.Part(function_response=types.FunctionResponse(id=call_id, name=name, response=result))
        for name, call_id in calls
    ]
    return types.Content(role="user", parts=parts)


def shape(contents: list[types.Content]) -> list[Turn]:
    """Each content as its role and its parts: `text:<text>`, `thinking`, `call:<name>`, `result:<name>`, `signature`."""
    shown: list[Turn] = []
    for content in contents:
        parts: list[str] = []
        for part in content.parts or []:
            if part.function_call is not None:
                parts.append(f"call:{part.function_call.name}")
            elif part.function_response is not None:
                parts.append(f"result:{part.function_response.name}")
            elif part.thought:
                parts.append("thinking")
            elif part.text:
                parts.append(f"text:{part.text}")
            else:
                parts.append("signature")
        shown.append(("assistant" if content.role == "model" else "user", parts))
    return shown


def anthropic_shape(messages: list[dict[str, Any]]) -> list[Turn]:
    """The same for a Claude request as the API receives it; a result names its call's tool, `?` when no call has its
    id (an orphan the API refuses)."""
    names: dict[str, str] = {}
    shown: list[Turn] = []
    for message in messages:
        parts: list[str] = []
        for block in message["content"]:
            if block["type"] == "text":
                parts.append(f"text:{block['text']}")
            elif block["type"] == "thinking":
                parts.append("thinking")
            elif block["type"] == "tool_use":
                names[block["id"]] = block["name"]
                parts.append(f"call:{block['name']}")
            elif block["type"] == "tool_result":
                parts.append(f"result:{names.get(block['tool_use_id'], '?')}")
            else:
                parts.append(str(block["type"]))
        shown.append((message["role"], parts))
    return shown


def root_requests(fake: Any) -> list[list[Turn]]:
    """The contents of every root call the scripted model received, in order, on either provider."""
    if isinstance(fake, FakeAnthropic):
        return [anthropic_shape(kwargs["messages"]) for kwargs in fake.calls if FakeAnthropic.kind(kwargs) == "root"]
    return [shape(request.contents) for request in fake.requests if kind_of(request) == "root"]


def root_blocks(fake: Any) -> list[str]:
    """The session block of every root call, in order: the last part of its system instruction."""
    if isinstance(fake, FakeAnthropic):
        return [kwargs["system"][-1]["text"] for kwargs in fake.calls if FakeAnthropic.kind(kwargs) == "root"]
    return [request.config.system_instruction.parts[-1].text for request in fake.requests if kind_of(request) == "root"]


def marked(turns: list[Turn]) -> bool:
    return any(REPLACED_TABLE_LINE in part for _, parts in turns for part in parts)


def alternating(turns: list[Turn]) -> bool:
    """No two turns of one role follow each other, and in a user turn the tool answers come before any text."""
    roles = [role for role, _ in turns]
    if any(first == second for first, second in zip(roles, roles[1:], strict=False)):
        return False
    for role, parts in turns:
        answers = [index for index, part in enumerate(parts) if part.startswith("result:")]
        if role == "user" and answers and answers != list(range(len(answers))):
            return False
    return True


def thinking_kept(before: list[types.Content], after: list[types.Content]) -> bool:
    """Every content of `after` that holds a call holds the thinking of each content of `before` that held that call,
    the same parts, in front of its other parts."""
    for kept in after:
        held = kept.parts or []
        for source in before:
            calls = [part for part in source.parts or [] if part.function_call is not None]
            if not any(call is part for call in calls for part in held):
                continue
            thoughts = [
                part
                for part in source.parts or []
                if part.function_call is None and (part.thought or (part.thought_signature and not part.text))
            ]
            if not all(any(thought is part for part in held[: len(thoughts)]) for thought in thoughts):
                return False
    return True


def filtered(contents: list[types.Content]) -> list[types.Content]:
    """`without_replaced_table`, with the request's shape checked: the roles alternate, a user content holds its tool
    answers first, and a call that stays keeps its thinking."""
    result = without_replaced_table(contents)
    assert alternating(shape(result)), shape(result)
    assert thinking_kept(contents, result), shape(result)
    return result


def checked(requests: list[list[Turn]]) -> list[list[Turn]]:
    """Recorded requests, each checked to alternate as the API takes it."""
    for turns in requests:
        assert alternating(turns), turns
    return requests


def paired(turns: list[Turn]) -> bool:
    """Every call of the request has its answer right after it, and no answer stands without its call."""
    for index, (role, parts) in enumerate(turns):
        calls = sorted(part.removeprefix("call:") for part in parts if part.startswith("call:"))
        results = sorted(part.removeprefix("result:") for part in parts if part.startswith("result:"))
        if role == "user" and "?" in results:
            return False
        if calls:
            following = turns[index + 1][1] if index + 1 < len(turns) else []
            if sorted(part.removeprefix("result:") for part in following if part.startswith("result:")) != calls:
                return False
        if results and (index == 0 or not any(part.startswith("call:") for part in turns[index - 1][1])):
            return False
    return True


def script(provider: str, *answers: dict[str, Any]) -> dict[str, list[Any]]:
    """The root's answers; a `thought` stays only where the provider's fake writes one (Claude)."""
    keep_thought = provider == "anthropic-vertex"
    root = [{key: value for key, value in item.items() if keep_thought or key != "thought"} for item in answers]
    return {"root": root, "adapter": [], "reviewer": []}


async def replace_the_table(client: httpx.AsyncClient) -> str:
    """The production case up to the note: the first table pasted and summarized, then the second pasted."""
    sid = await open_spec(client, SPEC)
    await paste(client, sid, FIRST)
    await say(client, sid, {"action": "summarize_data"})
    await paste(client, sid, SECOND)
    return sid


class TestRequest:
    """`without_replaced_table` on the contents ADK builds for the root."""

    EARLIER = [
        user(ACTION),
        call("get_dataset_profile", "c1", thought="the profile shows dates"),
        answer("get_dataset_profile", "c1", rows=4),
        reply(SUMMARY),
    ]

    def test_the_first_tables_exchanges_go_and_the_discussion_stays(self) -> None:
        contents = [*self.EARLIER, user(NOTE)]

        kept = filtered(contents)

        assert shape(kept) == DISCUSSION

    def test_every_tool_that_describes_the_table_goes_and_every_other_stays(self) -> None:
        """Each tool's exchange in an earlier turn of its own: the ones in `TABLE_TOOLS` go with their answers, the
        ones in `DISCUSSION_TOOLS` stay with theirs, and every user message and reply stays."""
        contents: list[types.Content] = []
        for number, name in enumerate(sorted(ROOT_TOOL_NAMES)):
            exchange = [call(name, f"c{number}"), answer(name, f"c{number}")]
            contents += [user(f"ask {name}"), *exchange, reply(f"did {name}")]
        contents.append(user(NOTE))

        kept = shape(filtered(contents))

        called = {part.removeprefix("call:") for _, parts in kept for part in parts if part.startswith("call:")}
        assert called == set(DISCUSSION_TOOLS) and paired(kept)
        texts = [part for _, parts in kept for part in parts if part.startswith("text:")]
        assert texts == [
            *(text for name in sorted(ROOT_TOOL_NAMES) for text in (f"text:ask {name}", f"text:did {name}")),
            MARKED_NOTE,
        ]

    def test_the_two_lists_name_every_tool_of_the_root_once(self) -> None:
        """A new tool fails here until it is placed: its answer either describes the table or it does not."""
        assert set(TABLE_TOOLS) | set(DISCUSSION_TOOLS) == ROOT_TOOL_NAMES
        assert not set(TABLE_TOOLS) & set(DISCUSSION_TOOLS)
        assert all(TABLE_TOOLS.values()) and all(DISCUSSION_TOOLS.values())

    def test_a_call_and_its_answer_go_together_beside_a_call_that_stays(self) -> None:
        """Two calls of one answer: the table's goes with its answer, the other stays with its own, by name."""
        both = types.Content(
            role="model",
            parts=[
                types.Part(function_call=types.FunctionCall(id="a", name="get_dataset_profile", args={})),
                types.Part(function_call=types.FunctionCall(id="b", name="get_spec_brief", args={})),
            ],
        )
        both_answers = answers(("get_dataset_profile", "a"), ("get_spec_brief", "b"))
        contents = [user(ACTION), both, both_answers, reply(SUMMARY), user(NOTE)]

        kept = shape(filtered(contents))

        assert kept == [
            ("user", [f"text:{ACTION}"]),
            ("assistant", ["call:get_spec_brief"]),
            ("user", ["result:get_spec_brief"]),
            ("assistant", [f"text:{SUMMARY}"]),
            ("user", [MARKED_NOTE]),
        ]
        assert paired(kept)

    def test_a_kept_answer_before_a_removed_exchange_takes_the_turn_into_its_content(self) -> None:
        """An earlier turn that ended without a reply after a `get_spec_brief` and a `get_dataset_profile`: the kept
        answer and the marked turn would follow each other as two user contents, so they are one, the answer first,
        and the kept call keeps the thinking that led to it."""
        contents = [
            user(ACTION),
            call("get_spec_brief", "c1", thought="read the plot first"),
            answer("get_spec_brief", "c1"),
            call("get_dataset_profile", "c2", thought="now the table"),
            answer("get_dataset_profile", "c2"),
            user(NOTE),
        ]

        kept = filtered(contents)

        assert shape(kept) == [
            ("user", [f"text:{ACTION}"]),
            ("assistant", ["thinking", "call:get_spec_brief"]),
            ("user", ["result:get_spec_brief", MARKED_NOTE]),
        ]
        assert kept[1].parts is not None and kept[1].parts[0].thought_signature == b"sig"

    def test_user_turns_that_only_removed_exchanges_parted_become_one_text(self) -> None:
        """An earlier turn whose only answer was the first table's profile: its message and the next user turn are one
        user content with one text, so the reply check still reads both as the user's; a second text part that starts
        with `[server]` would read to it as another agent's relayed message."""
        contents = [user(ACTION), call("get_dataset_profile", "c1"), answer("get_dataset_profile", "c1"), user(NOTE)]

        kept = filtered(contents)

        assert shape(kept) == [("user", [f"text:{ACTION}\n\n{REPLACED_TABLE_LINE}\n\n{NOTE}"])]
        assert not _relayed(kept[0])
        middle = [user("only 2024"), call("prepare_data", "c2"), answer("prepare_data", "c2"), reply("Kept 2024.")]
        assert shape(filtered([*contents[:3], *middle, user(NOTE)])) == [
            ("user", [f"text:{ACTION}\n\nonly 2024"]),
            ("assistant", ["text:Kept 2024."]),
            ("user", [MARKED_NOTE]),
        ]

    def test_thinking_goes_only_where_no_call_stays(self) -> None:
        """A content with a call that stays keeps its thinking, the same parts in front: with extended thinking a kept
        `tool_use` stays with the thinking that led to it. One whose calls all go, or that holds a reply only, loses
        it."""
        both = types.Content(
            role="model",
            parts=[
                types.Part(text="profile and plot", thought=True, thought_signature=b"sig"),
                types.Part(function_call=types.FunctionCall(id="a", name="get_dataset_profile", args={})),
                types.Part(function_call=types.FunctionCall(id="b", name="get_spec_brief", args={})),
            ],
        )
        thought_reply = types.Content(
            role="model", parts=[types.Part(text="dates, so no change", thought=True), types.Part(text=SUMMARY)]
        )
        both_answers = answers(("get_dataset_profile", "a"), ("get_spec_brief", "b"))
        contents = [user(ACTION), both, both_answers, thought_reply, user(NOTE)]

        kept = filtered(contents)

        assert shape(kept) == [
            ("user", [f"text:{ACTION}"]),
            ("assistant", ["thinking", "call:get_spec_brief"]),
            ("user", ["result:get_spec_brief"]),
            ("assistant", [f"text:{SUMMARY}"]),
            ("user", [MARKED_NOTE]),
        ]
        assert kept[1].parts is not None and both.parts is not None and kept[1].parts[0] is both.parts[0]

    def test_a_text_beside_a_removed_call_joins_a_kept_call_behind_its_thinking(self) -> None:
        """Two contents of the root that now follow each other become one, its thinking first, where the model writes
        it."""
        contents = [
            user(ACTION),
            call("get_dataset_profile", "c1", text="Let me read the table."),
            answer("get_dataset_profile", "c1"),
            call("get_spec_brief", "c2", thought="and the plot"),
            answer("get_spec_brief", "c2"),
            reply(SUMMARY),
            user(NOTE),
        ]

        assert shape(filtered(contents)) == [
            ("user", [f"text:{ACTION}"]),
            ("assistant", ["thinking", "text:Let me read the table.", "call:get_spec_brief"]),
            ("user", ["result:get_spec_brief"]),
            ("assistant", [f"text:{SUMMARY}"]),
            ("user", [MARKED_NOTE]),
        ]

    def test_text_beside_a_call_that_goes_stays_and_joins_the_reply_after_it(self) -> None:
        """The two replies of the root that now follow each other become one content, so the turns still alternate."""
        contents = [
            user(ACTION),
            call("get_dataset_profile", "c1", text="Let me read the table."),
            answer("get_dataset_profile", "c1"),
            reply(SUMMARY),
            user(NOTE),
        ]

        kept = shape(filtered(contents))

        assert kept == [
            ("user", [f"text:{ACTION}"]),
            ("assistant", ["text:Let me read the table.", f"text:{SUMMARY}"]),
            ("user", [MARKED_NOTE]),
        ]

    def test_the_roots_thinking_before_the_turn_goes_and_a_reply_with_a_signature_stays(self) -> None:
        """A thought, and a signature with nothing beside it, are the root's reading of the replaced table; a reply part
        that carries a signature (Gemini puts one on the first part of an answer) is a reply and stays."""
        signed = types.Content(role="model", parts=[types.Part(text=SUMMARY, thought_signature=b"sig")])
        bare = types.Content(role="model", parts=[types.Part(thought_signature=b"sig")])
        thought = types.Content(role="model", parts=[types.Part(text="dates, so no change", thought=True)])
        contents = [user(ACTION), bare, thought, signed, user(NOTE)]

        kept = filtered(contents)

        assert shape(kept) == DISCUSSION
        assert kept[1].parts is not None and kept[1].parts[0].thought_signature == b"sig"

    def test_the_turns_own_calls_stay_after_the_marked_turn(self) -> None:
        own = [call("get_dataset_profile", "c2", thought="read the new table"), answer("get_dataset_profile", "c2")]
        contents = [*self.EARLIER, user(NOTE), *own]

        kept = filtered(contents)

        assert kept[3:] == own
        assert shape(kept)[:3] == DISCUSSION

    def test_nothing_before_the_turn_leaves_the_request_as_it_is(self) -> None:
        """Two pastes in a row: no earlier word describes a table, so there is no switch to mark."""
        alone = [user(NOTE)]
        own = [user(NOTE), call("get_dataset_profile", "c2"), answer("get_dataset_profile", "c2")]

        assert filtered(alone) is alone
        assert filtered(own) is own
        assert filtered([]) == []

    def test_the_line_stands_inside_the_users_own_first_part(self) -> None:
        """A part of its own would make the action line, which starts with `[action] `, read as another agent's relayed
        message to the reply check, which would then skip the notes pasted with it as a source of figures."""
        text = f"{ACTION}\n\nThe user pasted the notes below together with the data."
        contents = [*self.EARLIER, user(text)]

        current = filtered(contents)[-1]

        assert current.parts is not None and len(current.parts) == 1
        assert current.parts[0].text == f"{REPLACED_TABLE_LINE}\n\n{text}"
        assert not _relayed(current)

    def test_the_line_is_added_once_and_the_contents_are_copies(self) -> None:
        contents = [*self.EARLIER, user(NOTE)]
        before = [content.model_copy(deep=True) for content in contents]

        once = filtered(contents)

        assert filtered(once) == once
        assert contents == before  # the request's contents were read, never changed in place

    def test_the_line_is_fixed_english_without_a_figure(self) -> None:
        """It becomes part of the user's turn, which the reply check reads as a source of figures."""
        assert REPLACED_TABLE_LINE.startswith("[server] ") and REPLACED_TABLE_LINE.isascii()
        assert not any(character.isdigit() for character in REPLACED_TABLE_LINE)

    def test_the_refused_turns_and_the_replaced_table_go_together(self) -> None:
        """The context filter takes out the refused turns first, this filter the replaced table's exchanges after."""
        refused = [user(withheld_text("out_of_scope")), halt(refusal("out_of_scope", "en"))]
        contents = [*self.EARLIER, *refused, user(NOTE)]

        kept = filtered(without_refused_turns(contents))

        assert shape(kept) == DISCUSSION
        assert without_refused_turns(contents) == [*self.EARLIER, user(NOTE)]  # as it was without this filter


class TestPlugin:
    def request(self) -> LlmRequest:
        return LlmRequest(contents=[*TestRequest.EARLIER, user(NOTE)])

    async def test_only_the_roots_requests_change(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(replaced_table, "replacing_summary_turn", lambda state, session_id: True)
        plugin = ReplacedTablePlugin()
        for agent, changed in (("anyplot", True), ("adapter_matplotlib", False), ("reviewer", False)):
            request = self.request()
            before = list(request.contents)
            context = SimpleNamespace(agent_name=agent, state={}, session=SimpleNamespace(id="s1"))

            assert await plugin.before_model_callback(callback_context=cast(Any, context), llm_request=request) is None

            assert (request.contents != before) is changed, agent

    async def test_a_failure_leaves_the_request_and_logs_the_class_only(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        def broken(state: Any, session_id: str) -> bool:
            raise ValueError("a cell of the user's table")

        monkeypatch.setattr(replaced_table, "replacing_summary_turn", broken)
        request = self.request()
        before = list(request.contents)
        context = SimpleNamespace(agent_name="anyplot", state={}, session=SimpleNamespace(id="s1"))

        with caplog.at_level(logging.WARNING, logger=replaced_table.__name__):
            await ReplacedTablePlugin().before_model_callback(callback_context=cast(Any, context), llm_request=request)

        assert request.contents == before
        assert "ValueError" in caplog.text and "a cell" not in caplog.text

    async def test_an_original_that_left_the_store_replaced_nothing(self, services: Services) -> None:
        """The paste's own number decides, as for the session block: without its original nothing is marked."""
        store = services.datasets
        original = store.put("s1", parse_dataset(SECOND), number=2)
        current = store.put("s1", parse_dataset(SECOND), number=3)
        state = initial_state(
            spec_id=SPEC,
            library="matplotlib",
            locale="en",
            snapshot=snapshot_from_repo(SPEC, "matplotlib"),
            normalised="x = 1",
            readiness={},
        )
        state.update(
            {
                DATASET_ID: current,
                DATASET_ORIGINAL: original,
                DATASET_VERSION: 3,
                DATASET_TOP: 3,
                SUMMARY_PENDING: current,
                BINDINGS: [{"role": "value", "column": "visitors"}],
            }
        )

        assert replacing_summary_turn(state, "s1") is True
        # No summary turn: the paste was summarized, and no route marked this turn as its summary.
        assert replacing_summary_turn({**state, SUMMARY_PENDING: None}, "s1") is False
        assert store.delete(original, "s1")
        assert replacing_summary_turn(state, "s1") is False


@pytest.mark.parametrize("provider", PROVIDERS)
async def test_the_note_after_a_replacing_paste_keeps_the_talk_and_loses_the_first_table(
    client: httpx.AsyncClient, swap_models, provider: str
) -> None:
    """The production case. The first call of the note's turn holds the summary action, the root's summary and the
    marked note: no call or answer of the first table and no thinking about it. The second call, after the root's own
    `get_dataset_profile` of the turn, holds that exchange as well, after the marked note."""
    fake = swap_models(
        provider,
        script(
            provider,
            {**PROFILE, "thought": "the profile shows dates"},
            {"text": SUMMARY},
            PROFILE,
            {"text": "4 rows; day holds text such as 1st March 2026, which no date form reads."},
        ),
    )
    sid = await replace_the_table(client)

    await say(client, sid, {"text": NOTE})

    summary_first, summary_second, first, second = checked(root_requests(fake))
    assert first == DISCUSSION
    assert second == [*first, ("assistant", ["call:get_dataset_profile"]), ("user", ["result:get_dataset_profile"])]
    assert paired(first) and paired(second)
    thought = ["thinking"] if provider == "anthropic-vertex" else []
    # The summary turn of the first paste, a paste that replaced nothing: as ADK builds it.
    assert summary_first == [("user", [f"text:{ACTION}"])]
    assert summary_second == [
        *summary_first,
        ("assistant", [*thought, "call:get_dataset_profile"]),
        ("user", ["result:get_dataset_profile"]),
    ]
    # The filter and the session block read one condition.
    assert [REPLACED_DATA_LINE in block for block in root_blocks(fake)] == [False, False, True, True]


async def test_every_other_turn_reaches_the_root_as_adk_builds_it(client: httpx.AsyncClient, swap_models) -> None:
    """The turn after the marked one, and a summary action on data already summarized, hold every earlier exchange,
    the thinking and the note as stored, with no marker anywhere."""
    fake = swap_models(
        "anthropic-vertex",
        script(
            "anthropic-vertex",
            {**PROFILE, "thought": "the profile shows dates"},
            {"text": SUMMARY},
            {"text": "4 rows; day holds text."},
            {"text": "day is text."},
            {"text": "4 rows."},
        ),
    )
    sid = await replace_the_table(client)
    await say(client, sid, {"text": NOTE})

    await say(client, sid, {"text": "Which column is text?"})
    await say(client, sid, {"action": "summarize_data"})

    later, again = checked(root_requests(fake))[-2:]
    earlier = [
        ("user", [f"text:{ACTION}"]),
        ("assistant", ["thinking", "call:get_dataset_profile"]),
        ("user", ["result:get_dataset_profile"]),
        ("assistant", [f"text:{SUMMARY}"]),
        ("user", [f"text:{NOTE}"]),
        ("assistant", ["text:4 rows; day holds text."]),
        ("user", ["text:Which column is text?"]),
    ]
    assert later == earlier
    assert again == [*earlier, ("assistant", ["text:day is text."]), ("user", [f"text:{ACTION}"])]
    assert not marked(later) and not marked(again)
    assert [REPLACED_DATA_LINE in block for block in root_blocks(fake)[-2:]] == [False, False]


async def test_the_stored_turns_and_the_judges_context_stay_as_they_were(
    client: httpx.AsyncClient, swap_models, runtime: Runtime, services: Services
) -> None:
    """Only the request changes: the session keeps the first table's exchange and the note as typed, the scope judge
    read the note as typed, and its context of the next turn holds the note without the line."""
    swap_models(
        "anthropic-vertex",
        script("anthropic-vertex", PROFILE, {"text": SUMMARY}, {"text": "4 rows; day holds text."}, {"text": "Yes."}),
    )
    judge = cast(FakeJudge, services.judge)
    sid = await replace_the_table(client)
    await say(client, sid, {"text": NOTE})

    await say(client, sid, {"text": "Is visitors on the value axis?"})

    session = await runtime.session(USER, sid)
    stored = shape([event.content for event in session.events if event.content is not None and event.content.parts])
    assert stored[:5] == [
        ("user", [f"text:{ACTION}"]),
        ("assistant", ["call:get_dataset_profile"]),
        ("user", ["result:get_dataset_profile"]),
        ("assistant", [f"text:{SUMMARY}"]),
        ("user", [f"text:{NOTE}"]),
    ]
    judged = [text for text, _ in judge.calls]
    assert any(NOTE in text for text in judged[:-1])  # the note's own verdict, as typed
    assert NOTE in judged[-1] and "4 rows; day holds text." in judged[-1]
    assert not any(REPLACED_TABLE_LINE in text or "[server]" in text for text in judged)


async def test_a_refused_turn_and_the_first_table_both_leave_the_request(
    client: httpx.AsyncClient, swap_models, services: Services
) -> None:
    """The context filter and this one in their order on the live chain: neither the refused turn nor the first table's
    exchange reaches the root, and the note is marked."""
    fake = swap_models("anthropic-vertex", script("anthropic-vertex", PROFILE, {"text": SUMMARY}, {"text": "4 rows."}))
    judge = cast(FakeJudge, services.judge)
    in_scope = JudgeVerdict(verdict="in_scope", lang="en")
    # The first paste's data judge, the refused message, the second paste's data judge, the note.
    judge.script.extend([in_scope, JudgeVerdict(verdict="out_of_scope", lang="en"), in_scope, in_scope])
    sid = await open_spec(client, SPEC)
    await paste(client, sid, FIRST)
    await say(client, sid, {"action": "summarize_data"})
    await say(client, sid, {"text": "Write me a poem about the sea."})
    await paste(client, sid, SECOND)

    await say(client, sid, {"text": NOTE})

    assert checked(root_requests(fake))[-1] == [
        ("user", [f"text:{ACTION}"]),
        ("assistant", [f"text:{SUMMARY}"]),
        ("user", [MARKED_NOTE]),
    ]


async def test_the_reply_checks_sources_lose_the_first_tables_figures(client: httpx.AsyncClient, swap_models) -> None:
    """The check reads its sources from the request the root answered (`ledger.root_request`), which this filter edits
    in place: a figure only the first table's profile held is a source on the first table's summary turn and none on
    the note's. Under `log`, the default, the check only counts it."""
    stale = "The first day had 1403 visitors."
    swap_models("anthropic-vertex", script("anthropic-vertex", PROFILE, {"text": stale}, {"text": stale}))
    checks: list[FigureCheck] = []

    with collect_figures(checks.append):
        sid = await replace_the_table(client)
        await say(client, sid, {"text": NOTE})

    summary, note = checks
    assert "1403" not in summary.unsourced and summary.verdict == "clean"
    assert "1403" in note.unsourced and note.verdict == "unsourced_logged"
