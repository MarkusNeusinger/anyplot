"""Tests for the NumberProvenance plugin: a figure in the root's final reply must stand in a source; an unsourced one
is asked for once, then the reply is withheld. Every value, column and sentence here is invented for the test."""

import json
import re
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from google.adk.events.event import Event
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agents.anyplot import figures as figures_module
from agents.anyplot.agent import MEMORY_HEADING, add_session_context, memory_block
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.query import QueryArgs, run_query
from agents.anyplot.figures import Figure, Sources, figures
from agents.anyplot.memory import MEMORY, MemoryEntry
from agents.anyplot.plugins import reply_language
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, session_hash
from agents.anyplot.plugins.number_provenance import (
    HOOK,
    REASK_LINE,
    UNVERIFIED_FIGURE,
    FigureCheck,
    NumberProvenancePlugin,
    collect_figures,
    replacement_allowed,
    request_sources,
    service_limits,
    session_part,
)
from agents.anyplot.plugins.scope_guard import ScopeGuardPlugin
from agents.anyplot.plugins.tool_safety import NOTES_KEY, SHOWS_KEY, SHOWS_PREAMBLE
from agents.anyplot.policy import DATA_PREAMBLE, fence, refusal
from agents.anyplot.services import Services
from agents.anyplot.session_state import LANGUAGE, LANGUAGE_SOURCE
from agents.anyplot.settings import get_settings
from agents.anyplot.tools.session import query_result
from agents.main import Runtime, app, get_runtime

from .fakes import ScriptedRoot, gemini_response, kind_of
from .test_service_flow import HEADERS, open_session, parse_sse, permissive_queue


STATIC = "The static policy: never state 777.5 as a figure."
SESSION = "Session (set by the server):\n- Dataset: 48 rows, 3 columns"
QUESTION = "how many loans did the branches make in all?"


@dataclass
class FakeSession:
    id: str = "s1"
    user_id: str = "adm_1"
    state: dict[str, Any] = field(default_factory=dict)
    events: list[Any] = field(default_factory=list)


@dataclass
class FakeContext:
    invocation_id: str = "inv-1"
    agent_name: str = "anyplot"
    session: FakeSession = field(default_factory=FakeSession)

    @property
    def state(self) -> dict[str, Any]:
        return self.session.state


@pytest.fixture
def ledger() -> Any:
    current = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1")
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


def user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def model(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


def response_of(name: str, response: dict[str, Any]) -> types.Content:
    part = types.Part(function_response=types.FunctionResponse(name=name, response=response))
    return types.Content(role="user", parts=[part])


def call_of(name: str, args: dict[str, Any]) -> types.Content:
    return types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])


def root_request(*contents: types.Content, session: str | None = SESSION) -> LlmRequest:
    parts = [types.Part(text=STATIC)] + ([types.Part(text=session)] if session is not None else [])
    return LlmRequest(
        model="m",
        contents=list(contents) or [user(QUESTION)],
        config=types.GenerateContentConfig(
            system_instruction=types.Content(parts=parts),
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(name="query_data")])],
        ),
    )


def lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    records = [record for record in caplog.records if record.name == "anyplot.agents.attribution"]
    return [line for line in (json.loads(record.getMessage()) for record in records) if line["hook"] == HOOK]


def verdicts(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [line["verdict"] for line in lines(caplog)]


async def check(response: LlmResponse, context: FakeContext | None = None) -> LlmResponse | None:
    return await NumberProvenancePlugin().after_model_callback(
        callback_context=cast(Any, context or FakeContext()), llm_response=response
    )


def one(written: str) -> Figure:
    (figure,) = figures(written)
    return figure


def text(response: LlmResponse) -> str | None:
    return reply_language.reply_text(response)


def mode(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AGENT_NUMBER_PROVENANCE", value)
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def enforced(development_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here runs the check under `enforce` unless it sets another mode. The default is `log`, under which
    no reply is asked for again or withheld, so a test of a figure that may stand would pass without the check."""
    mode(monkeypatch, "enforce")


# --- the sources --------------------------------------------------------------------------------------------------


class TestSources:
    def test_tool_results_user_messages_and_the_session_block_are_sources(self) -> None:
        request = root_request(
            user("the branches lent 9,876 books last year"),
            call_of("query_data", {"operations": [{"op": "aggregate", "value": 1234.5}]}),
            response_of("query_data", {"rows": [["all", "4321.25"]], "total_rows": 1}),
        )
        sources = request_sources(request, {})

        assert sources.kind_of(one("4,321.25")) == "tool_result"
        assert sources.kind_of(one("9876")) == "user"
        assert sources.kind_of(one("48")) == "session"

    def test_never_the_static_policy_the_roots_own_text_or_its_tool_arguments(self) -> None:
        request = root_request(
            user(QUESTION),
            model("Earlier I said 5,555.5 loans."),
            call_of("query_data", {"operations": [{"op": "aggregate", "value": 1234.5}]}),
            response_of("query_data", {"rows": [["all", "4321.25"]]}),
        )
        sources = request_sources(request, {})

        for figure in ("777.5", "5,555.5", "1234.5"):
            assert sources.kind_of(one(figure)) is None, figure

    def test_another_agents_relayed_message_is_no_source(self) -> None:
        relayed = types.Content(
            role="user",
            parts=[types.Part(text="For context: below is a transcript."), types.Part(text="[adapter] said:\n31.5")],
        )
        assert request_sources(root_request(relayed), {}).kind_of(one("31.5")) is None

    def test_a_plots_drawn_texts_count_as_drawn_text_and_its_requested_texts_as_none(self) -> None:
        shown = {
            "texts": {"title": {"count": 1, "texts": ["Loans 2024: 6,120"]}},
            "score": 87,
            "requested_not_found": ["Mean 4.75"],
        }
        result = {
            "status": "ok",
            "attempts": 1,
            SHOWS_KEY: SHOWS_PREAMBLE + "\n" + fence("tool_notes", json.dumps(shown)),
        }
        sources = request_sources(root_request(response_of("plot_pipeline", result)), {})

        assert sources.kind_of(one("6,120")) == "drawn_text"
        assert sources.kind_of(one("87")) == "tool_result"
        assert sources.kind_of(one("4.75")) is None

    def test_a_roles_ends_count_as_drawn_text_and_its_count_is_no_source(self) -> None:
        shown = {
            "texts": {
                "y tick labels": {
                    "count": 12,
                    "texts": ["Loans: 6,120", *(f"Category {chr(65 + idx)}" for idx in range(11))],
                },
                "x tick labels": {"count": 30, "first": ["1995"], "last": ["2024"]},
            },
            "review": "passed",
        }
        result = {
            "status": "ok",
            "attempts": 1,
            SHOWS_KEY: SHOWS_PREAMBLE + "\n" + fence("tool_notes", json.dumps(shown)),
        }
        sources = request_sources(root_request(response_of("plot_pipeline", result)), {})

        for figure in ("6,120", "1995", "2024"):
            assert sources.kind_of(one(figure)) == "drawn_text", figure
        for count in ("12", "30"):
            assert sources.kind_of(one(count)) is None, count

    def test_an_axis_limit_stated_with_fewer_decimals_counts_as_tool_result(self) -> None:
        shown = {
            "texts": {"title": {"count": 1, "texts": ["Loans: 6,120"]}},
            "axes": [
                {
                    "x": {"scale": "linear", "min": 0.0, "max": 12.5},
                    "y": {"scale": "linear", "min": 2.5, "max": 105.32541},
                }
            ],
            "review": "passed",
        }
        result = {
            "status": "ok",
            "attempts": 1,
            SHOWS_KEY: SHOWS_PREAMBLE + "\n" + fence("tool_notes", json.dumps(shown)),
        }
        sources = request_sources(root_request(response_of("plot_pipeline", result)), {})

        assert sources.kind_of(one("105.3")) == "tool_result"
        assert sources.kind_of(one("105.32541")) == "tool_result"

    def test_a_plots_notes_count_as_plot_notes(self) -> None:
        """The adapter's `changes` and the reviewer's `residual_defects` are model-written: a kind of their own, so the
        measurement tells them from a server's result."""
        notes = {"changes": ["dashed line at y = 47.5"], "residual_defects": ["two tick labels collide near 3.75"]}
        result = {
            "status": "ok",
            "attempts": 2,
            NOTES_KEY: DATA_PREAMBLE + "\n" + fence("tool_notes", json.dumps(notes)),
        }
        sources = request_sources(root_request(response_of("plot_pipeline", result)), {})

        assert sources.kind_of(one("47.5")) == "plot_notes"
        assert sources.kind_of(one("3.75")) == "plot_notes"
        assert sources.kind_of(one("2.0")) == "tool_result"  # the result's own `attempts`, an exact 2

    def test_the_plot_code_counts_as_plot_code(self) -> None:
        code = {
            "status": "ok",
            "version": 3,
            "code": DATA_PREAMBLE + "\n" + fence("catalogue_code", "ax.axhline(3.75)"),
        }
        sources = request_sources(root_request(response_of("get_current_code", code)), {})

        assert sources.kind_of(one("3.75")) == "plot_code"
        assert sources.kind_of(one("3.0")) == "tool_result"

    def test_the_plot_memory_is_a_source_of_its_own_kind(self) -> None:
        """The root writes the memory itself (`remember`), from the user's decision; once the context window has dropped
        the message that set it, the memory is where the figure still stands."""
        entry = MemoryEntry(id="m1", kind="reference_line", target="y", text="horizontal line at y = 61.5", turn=3)
        state = {MEMORY: [entry.model_dump()]}
        session = f"{SESSION}\n{memory_block([entry])}\n- Plot versions: 2; latest result: ok, theme light"
        sources = request_sources(root_request(session=session), state)

        assert MEMORY_HEADING.split("{", 1)[0] in session
        assert sources.kind_of(one("61.5")) == "memory"
        assert sources.kind_of(one("61.50")) is None  # a model-written source keeps the strict rule
        assert sources.kind_of(one("48")) == "session"

    def test_the_services_limits_are_a_source_and_never_a_share(self) -> None:
        sources = request_sources(root_request(), {})

        assert sources.kind_of(one("20,000")) == "service"
        assert sources.kind_of(one("600")) == "service"
        assert sources.kind_of(one("50 %")) is None  # a limit of 50 columns is no share

    def test_the_session_part_is_the_last_part_beside_the_policy(self) -> None:
        assert session_part(root_request()) == SESSION
        assert session_part(root_request(session=None)) is None

    async def test_the_kept_request_holds_the_session_block_after_the_real_callbacks(
        self, ledger: RequestLedger
    ) -> None:
        """ReplyLanguage keeps the request object, and `add_session_context` puts the block into that object after
        it, as ADK runs the plugins before the agent's own callback: so the kept request holds the block the root
        read."""
        context = FakeContext()
        request = LlmRequest(model="m", contents=[user(QUESTION)], config=types.GenerateContentConfig())
        request.config.system_instruction = STATIC

        await reply_language.ReplyLanguagePlugin().before_model_callback(
            callback_context=cast(Any, context), llm_request=request
        )
        await add_session_context(cast(Any, context), request)

        kept = session_part(ledger.root_request)
        assert kept is not None and kept.startswith("Session: no plot is open")


# --- the check ----------------------------------------------------------------------------------------------------


TOTAL = response_of("query_data", {"rows": [["all", "4321.25"]], "total_rows": 1})


class TestCheck:
    async def test_a_sourced_reply_passes_and_leaves_a_clean_line(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request(user(QUESTION), call_of("query_data", {}), TOTAL)
        ledger.tools = ["query_data"]
        response = gemini_response({"text": "The branches lent 4,321.25 books, about 4,321."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert await check(response) is None

        assert text(response) == "The branches lent 4,321.25 books, about 4,321."
        (line,) = lines(caplog)
        assert line["verdict"] == "clean"
        assert (line["figures"], line["unsourced"], line["from_tool_result"]) == (2, 0, 2)

    async def test_a_versions_row_counts_are_a_tool_result_beside_its_code(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`get_current_code`'s `data` holds counts the server took from the stored version (`session.version_data`):
        a tool result, while the code text beside them stays `plot_code`. The file holds fewer rows than the view drew
        (rows that share the plot's key were combined), so each count stands in one field only."""
        result = {
            "status": "ok",
            "version": 3,
            "code": DATA_PREAMBLE + "\n" + fence("catalogue_code", "ax.axhline(3.75)"),
            "data": {"rows_in_file": {"data.csv": 13, "plot.html": 13}, "view": {"rows": 15, "of_rows": 248}},
        }
        ledger.root_request = root_request(
            user("how many rows does the file of version 3 hold?"),
            call_of("get_current_code", {"version": 3}),
            response_of("get_current_code", result),
        )
        ledger.tools = ["get_current_code"]
        sources = request_sources(ledger.root_request, {})
        reply = "The data.csv of version 3 holds 13 rows; the plot drew 15 of the 248, under a line at 3.75."
        response = gemini_response({"text": reply})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert await check(response) is None

        assert [sources.kind_of(one(count)) for count in ("13", "15", "248")] == ["tool_result"] * 3
        assert sources.kind_of(one("3.75")) == "plot_code"
        (line,) = lines(caplog)
        assert (line["verdict"], line["unsourced"], line["from_tool_result"], line["from_plot_code"]) == (
            "clean",
            0,
            3,
            1,
        )

    async def test_a_fit_and_a_grand_total_are_tool_results(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The answers of a `fit` and of an `aggregate` without `by`, as the server writes them: a reply that states the
        slope as the result writes it, the intercept rounded and the total is clean."""
        dataset = parse_dataset("week,signups\n1,112\n2,135\n3,149\n4,171\n5,198\n6,214\n")
        fit = [{"op": "fit", "x": "week", "y": "signups"}]
        total = [{"op": "aggregate", "column": "signups", "how": "sum"}]
        fitted = run_query(dataset, QueryArgs.model_validate({"operations": fit}).operations)
        summed = run_query(dataset, QueryArgs.model_validate({"operations": total}).operations)
        assert fitted.columns == ["slope", "intercept", "r_squared", "n"] and summed.columns == ["signups"]
        (row,) = fitted.rows
        slope, intercept = row[0], row[1]
        ledger.root_request = root_request(
            user("how fast do the signups grow, and how many are there in all?"),
            call_of("query_data", {"operations": fit}),
            response_of("query_data", query_result(fitted)),
            call_of("query_data", {"operations": total}),
            response_of("query_data", query_result(summed)),
        )
        ledger.tools = ["query_data", "query_data"]
        reply = f"The signups grow by {slope} a week from {Decimal(intercept):.2f}, {summed.rows[0][0]} in all."
        response = gemini_response({"text": reply})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert await check(response) is None

        assert text(response) == reply
        (line,) = lines(caplog)
        assert (line["verdict"], line["figures"], line["unsourced"], line["from_tool_result"]) == ("clean", 3, 0, 3)

    async def test_a_reply_without_a_figure_leaves_no_line(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(gemini_response({"text": "The bars are blue now."}))

        assert lines(caplog) == [] and ledger.guards == []

    async def test_the_line_names_no_figure(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        ledger.tools = ["query_data"]
        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(gemini_response({"text": "The total is 8,642.13 books."}))

        (line,) = lines(caplog)
        counts = {"figures", "unsourced", "exempt", "unread", "magnitude_only"} | {
            f"from_{kind}"
            for kind in ("tool_result", "session", "user", "service", "memory", "plot_notes", "plot_code", "drawn_text")
        }
        base = {"severity", "hook", "request_id", "user", "session", "llm_calls", "tokens", "verdict"}
        assert set(line) == base | counts
        assert all(isinstance(line[key], int) for key in counts) and "8,642" not in json.dumps(line)
        # The counts never take the place of the line's own caller and session hash.
        assert (line["user"], line["session"]) == ("adm_1", session_hash("s1"))
        assert line["verdict"] == "unsourced_logged" and ledger.guards == [(HOOK, "unsourced_logged")]

    async def test_a_tool_turn_is_only_logged(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request(user(QUESTION), call_of("query_data", {}), TOTAL)
        ledger.tools = ["query_data"]
        response = gemini_response({"text": "The branches lent 4,321.25 books, 8 % more than the 4,001.2 before."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The branches lent 4,321.25 books, 8 % more than the 4,001.2 before."
        assert not answers.requests and not ledger.figures_reasked and ledger.error is None
        (line,) = lines(caplog)
        assert (line["verdict"], line["figures"], line["unsourced"], line["from_tool_result"]) == (
            "unsourced_logged",
            3,
            2,
            1,
        )

    async def test_a_no_tool_turn_is_asked_once_more_with_the_tools(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([gemini_response({"text": "I can compute the total with a query; shall I?"})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        first = "The branches lent 8,642.13 books, 3.5 % of the 48 rows' total."
        response = gemini_response({"text": first})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert await check(response) is None

        assert text(response) == "I can compute the total with a query; shall I?"
        (asked,) = answers.requests
        assert asked.contents[:-2] == ledger.root_request.contents
        assert asked.contents[-2] == model(first)
        assert asked.contents[-1].parts[0].text == REASK_LINE.format(figures='"8,642.13", "3.5 %"')
        assert asked.config.tools  # the answer may compute the figure with a tool
        assert ledger.figures_reasked and ledger.error is None and ledger.llm_calls == 1
        assert verdicts(caplog) == ["reasked", "clean"]
        assert ledger.guards == [(HOOK, "reasked"), (HOOK, "clean")]

    async def test_an_answer_that_still_states_the_figure_is_withheld(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([gemini_response({"text": "The total is about 8,642 books."})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert ledger.error == UNVERIFIED_FIGURE
        assert response.content is not None and response.content.parts == [] and text(response) is None
        assert verdicts(caplog) == ["reasked", "withheld"]
        assert lines(caplog)[-1]["reason"] == "unsourced"

    async def test_after_a_tool_call_the_turns_next_reply_is_checked_under_the_flag(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The second ask answers with a tool call, which goes on in ADK's flow; the reply after the tool is checked
        against the sources as they are then, and still withheld for a figure no tool gave, although a tool ran."""
        answers = ScriptedRoot([gemini_response({"call": "query_data"})])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        first = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(first)
            assert first.content is not None and first.content.parts[0].function_call is not None
            # ADK runs the tool and calls the root again with its result in the request.
            ledger.tools = ["query_data"]
            ledger.root_request = root_request(user(QUESTION), call_of("query_data", {}), TOTAL)
            sourced = gemini_response({"text": "The total is 4,321.25 books."})
            await check(sourced)
            # A closing reply without any figure still leaves the line that shows how the asked turn ended.
            plain = gemini_response({"text": "No total could be worked out from these rows."})
            await check(plain)
            invented = gemini_response({"text": "The total is 8,642.13 books."})
            await check(invented)

        assert text(sourced) == "The total is 4,321.25 books."
        assert text(plain) == "No total could be worked out from these rows."
        assert text(invented) is None and ledger.error == UNVERIFIED_FIGURE
        assert len(answers.requests) == 1  # never a second re-ask
        assert verdicts(caplog) == ["reasked", "clean", "clean", "withheld"]
        assert lines(caplog)[2]["figures"] == 0

    async def test_a_limit_of_the_service_passes_on_a_turn_without_a_tool(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The limits the root's instructions state are facts of the service: no re-ask, also with every small whole
        number read."""
        monkeypatch.setattr(figures_module, "SMALL_WHOLE_MAX", None)
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        said = "Pasted text is capped at 1 MB and a workbook at 5 MB; a table holds at most 20,000 rows."
        response = gemini_response({"text": said})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == said and not answers.requests
        (line,) = lines(caplog)
        assert (line["verdict"], line["figures"], line["from_service"]) == ("clean", 3, 3)

    async def test_a_remembered_figure_passes_after_the_context_window(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        entry = MemoryEntry(id="m1", kind="reference_line", target="y", text="horizontal line at y = 61.5", turn=3)
        context = FakeContext(session=FakeSession(state={MEMORY: [entry.model_dump()]}))
        ledger.root_request = root_request(session=f"{SESSION}\n{memory_block([entry])}")
        response = gemini_response({"text": "The line at y = 61.5 is still part of every plot."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response, context)

        assert not answers.requests
        (line,) = lines(caplog)
        assert (line["verdict"], line["from_memory"]) == ("clean", 1)

    async def test_an_evals_collector_alone_receives_the_unsourced_figures(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        ledger.tools = ["query_data"]
        collected: list[FigureCheck] = []

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            with collect_figures(collected.append):
                await check(gemini_response({"text": "The total is 8,642.13 books, 48 rows."}))
            await check(gemini_response({"text": "And 9,753.24 more."}))

        (seen,) = collected
        assert (seen.request_id, seen.verdict, seen.tools, seen.unsourced) == (
            "req-1",
            "unsourced_logged",
            True,
            ("8,642.13",),
        )
        first = lines(caplog)[0]
        assert all(first[key] == value for key, value in seen.counts.items()) and seen.counts["from_session"] == 1
        assert "8,642" not in caplog.text and "9,753" not in caplog.text

    async def test_an_unread_token_is_counted_and_never_asked_for(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A token whose marks fit no number is no figure the check can verify: the line counts it, and the turn
        without a tool is not asked again."""
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": "The plot was drawn with release 4.12.7 of the library."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The plot was drawn with release 4.12.7 of the library." and ledger.error is None
        assert not answers.requests and not ledger.figures_reasked
        (line,) = lines(caplog)
        assert (line["verdict"], line["figures"], line["unsourced"], line["unread"]) == ("clean", 1, 0, 1)

    async def test_a_second_ask_after_a_tool_never_happens(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        ledger.tools = ["prepare_data"]

        await check(gemini_response({"text": "Renamed; the total is 8,642.13."}))

        assert not answers.requests and not ledger.figures_reasked

    @pytest.mark.parametrize(
        ("setup", "reason"),
        [("no_request", "no_request"), ("budget", "budget"), ("raises", "error"), ("empty", "empty")],
    )
    async def test_a_second_ask_that_cannot_be_made_withholds_the_reply(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        setup: str,
        reason: str,
    ) -> None:
        """Without a second ask, a reply that states an unsourced figure is withheld, with its reason."""
        answer: LlmResponse | Exception = (
            RuntimeError("the model is away") if setup == "raises" else LlmResponse(content=None)
        )
        answers = ScriptedRoot([answer])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = None if setup == "no_request" else root_request()
        if setup == "budget":
            ledger.llm_calls = get_settings().max_llm_calls
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert ledger.error == UNVERIFIED_FIGURE and text(response) is None
        (line,) = lines(caplog)
        assert (line["verdict"], line["reason"]) == ("withheld", reason)

    async def test_what_is_no_final_reply_of_the_root_is_not_checked(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(gemini_response({"call": "query_data", "args": {"limit": 25}}))
            await check(gemini_response({"text": "8,642.13"}), FakeContext(agent_name="adapter"))
            partial = gemini_response({"text": "8,642.13"})
            partial.partial = True
            await check(partial)
            await check(gemini_response({"text": refusal("out_of_scope", "en")}))
            ledger.refuse("budget", "spent")
            await check(gemini_response({"text": "8,642.13"}))

        assert lines(caplog) == [] and not ledger.figures_reasked

    async def test_a_failure_of_the_check_keeps_the_reply(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def broken(*args: Any) -> Any:
            raise ValueError("bug")

        monkeypatch.setattr("agents.anyplot.plugins.number_provenance.provenance", broken)
        ledger.root_request = root_request()
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The total is 8,642.13 books." and ledger.error is None
        assert verdicts(caplog) == ["error"]


class TestModes:
    async def test_off_checks_nothing(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mode(monkeypatch, "off")
        ledger.root_request = root_request()
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The total is 8,642.13 books." and lines(caplog) == []

    async def test_log_never_asks_again_and_never_withholds(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mode(monkeypatch, "log")
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The total is 8,642.13 books." and ledger.error is None
        assert not answers.requests and verdicts(caplog) == ["unsourced_logged"]

    async def test_log_is_the_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AGENT_NUMBER_PROVENANCE")
        get_settings.cache_clear()

        assert get_settings().number_provenance == "log"

    async def test_the_default_asks_nothing_again_and_withholds_nothing(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("AGENT_NUMBER_PROVENANCE")
        get_settings.cache_clear()
        answers = ScriptedRoot([])
        monkeypatch.setattr(reply_language, "root_model", lambda: answers)
        ledger.root_request = root_request()
        response = gemini_response({"text": "The total is 8,642.13 books."})

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            await check(response)

        assert text(response) == "The total is 8,642.13 books." and ledger.error is None
        assert not answers.requests and verdicts(caplog) == ["unsourced_logged"]


# --- the replies of the other plugins' re-asks --------------------------------------------------------------------


ENGLISH_REPLY = "The table has 48 rows and 3 columns, and the loans spread across the branches of the city."
GERMAN_ADDED = "Die Tabelle hat 48 Zeilen und 3 Spalten, und die Ausleihen ergeben zusammen 8.642,13 Bücher der Stadt."
GERMAN_SAME = "Die Tabelle hat 48 Zeilen und 3 Spalten, und die Ausleihen verteilen sich auf die Filialen der Stadt."
LONG_REPLY = " ".join(["The bars now show the monthly loans per branch, sorted by amount."] * 25)
SHORT_ADDED = "The bars show 8,642.13 loans per branch, sorted by amount."
SHORT_SAME = "The bars show the monthly loans per branch, sorted by amount."


def german() -> FakeContext:
    return FakeContext(session=FakeSession(state={LANGUAGE: "de", LANGUAGE_SOURCE: "chosen"}))


def reply_event(text: str) -> Event:
    return Event(author="anyplot", content=types.Content(role="model", parts=[types.Part(text=text)]))


def all_lines(caplog: pytest.LogCaptureFixture, hook: str) -> list[dict[str, Any]]:
    records = [record for record in caplog.records if record.name == "anyplot.agents.attribution"]
    return [line for line in (json.loads(record.getMessage()) for record in records) if line["hook"] == hook]


class TestReplacement:
    def test_a_replacement_that_adds_an_unsourced_figure_is_not_used_on_a_turn_without_a_tool(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            allowed = replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="reply_language")

        assert not allowed
        (line,) = lines(caplog)
        assert (line["verdict"], line["replacement"], line["unsourced"]) == ("kept", "reply_language", 1)
        assert ledger.guards == [(HOOK, "kept")] and "8.642" not in caplog.text

    def test_a_figure_the_replaced_reply_held_may_stay(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The check failed open on the first reply, or a reply already stated it: a translation that keeps it adds
        nothing, so it is only logged."""
        ledger.root_request = root_request()

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            allowed = replacement_allowed(
                ledger, {}, "The loans add up to 8,642.13 books.", GERMAN_ADDED, of="reply_language"
            )

        assert allowed and verdicts(caplog) == ["unsourced_logged"]

    @pytest.mark.parametrize("setup", ["tool_turn", "log"])
    def test_elsewhere_the_check_of_a_replacement_only_logs(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        setup: str,
    ) -> None:
        ledger.root_request = root_request()
        if setup == "tool_turn":
            ledger.tools = ["query_data"]
        else:
            mode(monkeypatch, "log")

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            allowed = replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="output_guard")

        assert allowed
        (line,) = lines(caplog)
        assert (line["verdict"], line["replacement"]) == ("unsourced_logged", "output_guard")

    def test_an_unread_token_never_refuses_a_replacement(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        replacement = "Die Tabelle hat 48 Zeilen und 3 Spalten, gezeichnet mit Version 4.12.7 der Bibliothek."

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            allowed = replacement_allowed(ledger, {}, ENGLISH_REPLY, replacement, of="reply_language")

        assert allowed
        (line,) = lines(caplog)
        assert (line["verdict"], line["unsourced"], line["unread"]) == ("clean", 0, 1)

    def test_a_halted_turn_checks_no_replacement(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        """On a turn already failed or refused the check stays out, as it does for the turn's own reply."""
        ledger.root_request = root_request()
        ledger.fail("deadline")

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="reply_language")

        assert lines(caplog) == []

    def test_an_evals_collector_receives_a_refused_replacement(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        collected: list[FigureCheck] = []

        with collect_figures(collected.append):
            assert not replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="output_guard")

        (seen,) = collected
        assert (seen.verdict, seen.replacement, seen.tools, seen.unsourced) == (
            "kept",
            "output_guard",
            False,
            ("8.642,13",),
        )

    def test_after_the_figures_were_asked_for_a_tool_turn_is_held_too(
        self, ledger: RequestLedger, services: Services, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger.root_request = root_request()
        ledger.tools = ["query_data"]
        ledger.figures_reasked = True

        assert not replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="reply_language")

    def test_off_checks_no_replacement(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mode(monkeypatch, "off")
        ledger.root_request = root_request()

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            assert replacement_allowed(ledger, {}, ENGLISH_REPLY, GERMAN_ADDED, of="reply_language")

        assert lines(caplog) == []

    @pytest.mark.parametrize(
        ("tools", "answer", "used"),
        [([], GERMAN_ADDED, False), ([], GERMAN_SAME, True), (["query_data"], GERMAN_ADDED, True)],
        ids=["added_on_a_turn_without_a_tool", "nothing_added", "added_on_a_tool_turn"],
    )
    async def test_reply_languages_reask(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        tools: list[str],
        answer: str,
        used: bool,
    ) -> None:
        monkeypatch.setattr(reply_language, "root_model", lambda: ScriptedRoot([gemini_response({"text": answer})]))
        ledger.tools = list(tools)
        plugin = reply_language.ReplyLanguagePlugin()
        context = cast(Any, german())
        await plugin.before_model_callback(callback_context=context, llm_request=root_request())

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            result = await plugin.after_model_callback(
                callback_context=context, llm_response=gemini_response({"text": ENGLISH_REPLY})
            )

        language = [line["verdict"] for line in all_lines(caplog, "reply_language")]
        if used:
            assert result is not None and text(result) == answer
            assert language == ["mismatch", "reasked"]
        else:
            assert result is None  # the first reply stays, as for any failed re-ask
            assert language == ["mismatch", "reask_failed"] and verdicts(caplog) == ["kept"]

    @pytest.mark.parametrize(
        ("tools", "answer", "used"),
        [([], SHORT_ADDED, False), ([], SHORT_SAME, True), (["query_data"], SHORT_ADDED, True)],
        ids=["added_on_a_turn_without_a_tool", "nothing_added", "added_on_a_tool_turn"],
    )
    async def test_the_output_guards_reask(
        self,
        ledger: RequestLedger,
        services: Services,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
        tools: list[str],
        answer: str,
        used: bool,
    ) -> None:
        monkeypatch.setattr(reply_language, "root_model", lambda: ScriptedRoot([gemini_response({"text": answer})]))
        ledger.root_request = root_request()
        ledger.tools = list(tools)

        with caplog.at_level("INFO", logger="anyplot.agents.attribution"):
            replaced = await ScopeGuardPlugin().on_event_callback(
                invocation_context=cast(Any, FakeContext()), event=reply_event(LONG_REPLY)
            )

        assert replaced is not None and replaced.content is not None
        guard = all_lines(caplog, "output_guard")[-1]
        if used:
            assert replaced.content.parts[0].text == answer and guard["verdict"] == "shortened"
        else:
            # The long reply, cut at the cap: the shorter answer added a figure no source holds.
            assert replaced.content.parts[0].text != answer
            assert (guard["verdict"], guard["reason"]) == ("reply_cut", "figures")


# --- the limits the root's instructions state ---------------------------------------------------------------------


ROOT_PROMPT = Path(__file__).resolve().parents[4] / "agents" / "anyplot" / "prompts" / "root.md"
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”|„[^“”\n]*[“”]')
"""A quoted passage of the prompt: what a user says or a text the plot shows, never a fact of the service."""
EXAMPLES: dict[str, str] = {
    "12": "a lag or a window of monthly rows, the months of a date, a range of example dates",
    "16": "the characters a float takes at full precision",
    "19": "the characters a float takes at full precision",
    "27": "a repeated key: 27 rows over 9 values",
    "31": "a day of a month in a date example",
    "36": "a range of example dates",
    "53": "the weeks of an ISO year, a fact of the calendar",
    "100": "a share's whole, an index's base, a condition's value",
    "500": "a range of example values for a distribution",
    "1200": "the number `extract` reads from an example cell",
    "1234": "an example cell of a number column",
    "2020": "an example year of a condition",
    "2021": "an example date's year",
    "2021.25": "an example decimal year",
    "7000": "an example cell of a number column",
    "-3.5": "the number `extract` reads from an example cell",
    "-5": "a part `split` reads from an example cell",
    "-50": "an example range of values to round",
}
"""Every figure of `root.md`'s prose that is no limit of the service, with why it stands there: an example, or a fact
outside the service. A new figure in the prompt fails `test_every_figure_of_the_prompt_is_a_limit_or_an_example`
until it is a limit in `service_limits` or listed here."""


def prompt_figures() -> list[Figure]:
    """The figures of `root.md`'s prose that the check reads: outside code and quoted passages, none exempt."""
    text = figures_module._CODE.sub(lambda match: " " * len(match.group(0)), ROOT_PROMPT.read_text(encoding="utf-8"))
    text = QUOTED.sub(lambda match: " " * len(match.group(0)), text)
    return [figure for figure in figures(text) if not figure.small]


class TestServiceLimits:
    def test_every_figure_of_the_prompt_is_a_limit_or_an_example(self) -> None:
        limits = Sources()
        for limit in service_limits():
            limits.add_number(limit, 0, "service")

        unlisted = sorted({f.text for f in prompt_figures() if limits.kind_of(f) is None and f.text not in EXAMPLES})

        assert unlisted == []

    def test_every_listed_example_still_stands_in_the_prompt(self) -> None:
        assert set(EXAMPLES) <= {figure.text for figure in prompt_figures()}

    def test_the_file_limits_count_in_megabytes(self) -> None:
        assert {Decimal(1), Decimal(2), Decimal(5)} <= set(service_limits())

    def test_no_prompt_example_launders_a_figure(self) -> None:
        """The prompt's text is no source: its example values stay unsourced."""
        sources = request_sources(root_request(), {})

        for example in ("1234", "7000", "2021.25", "-3.5"):
            assert sources.kind_of(one(example)) is None, example


# --- through the service ------------------------------------------------------------------------------------------


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


async def say(client: httpx.AsyncClient, sid: str, words: str) -> list[tuple[str, dict[str, Any]]]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": words})
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


async def bundle(client: httpx.AsyncClient, sid: str) -> dict[str, Any]:
    response = await client.get(f"/v1/sessions/{sid}/bundle?version=0", headers=HEADERS)
    assert response.status_code == 200, response.text
    return cast(dict[str, Any], response.json())


INVENTED = "The scores add up to 1,618.03."
"""A reply whose figure no source of the scatter session holds (its table has 24 rows of hours and scores)."""


async def test_a_reply_that_states_an_unsourced_figure_twice_is_withheld(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The turn ends with `error{code:"unverified_figure"}` and no message; the withheld reply is in no transcript
    and no later request, so neither the user, nor the root, nor the scope judge ever reads the figure."""
    fake = swap_models(
        "gemini", {"root": [{"text": INVENTED}, {"text": "About 1,618."}, {"text": "The table has 24 rows."}]}
    )
    sid = await open_session(client)

    withheld = await say(client, sid, "what do the scores add up to?")
    later = await say(client, sid, "and how many rows?")

    assert [name for name, _ in withheld] == ["ready", "error", "done"]
    assert withheld[1][1] == {"code": UNVERIFIED_FIGURE, "ref": "req-1"} and "turn" not in withheld[-1][1]
    assert [name for name, _ in later] == ["ready", "message", "done"]
    assert later[1][1] == {"text": "The table has 24 rows."}
    asked = fake.requests[1]
    assert asked.contents[-2] == model(INVENTED) and '"1,618.03"' in (asked.contents[-1].parts[0].text or "")
    assert asked.config.tools
    assert "1,618" not in json.dumps([content.model_dump(mode="json") for content in fake.requests[-1].contents])
    case = await bundle(client, sid)
    assert all("1,618" not in item["text"] for item in case["transcript"])
    first, second = case["turns"]["records"]
    assert (first["kind"], first["error"]) == ("error", UNVERIFIED_FIGURE)
    assert [(line["guard"], line["verdict"]) for line in first["guards"]] == [
        ("scope_guard", "in_scope"),
        (HOOK, "reasked"),
        (HOOK, "withheld"),
    ]
    assert (HOOK, "clean") in [(line["guard"], line["verdict"]) for line in second["guards"]]


@pytest.mark.parametrize(
    ("closing", "events"),
    [("The table has 24 rows.", ["ready", "message", "done"]), (INVENTED, ["ready", "error", "done"])],
    ids=["sourced_after_the_tool", "still_unsourced_after_the_tool"],
)
async def test_a_second_ask_that_calls_a_tool_is_checked_again_after_it(
    client: httpx.AsyncClient, swap_models, closing: str, events: list[str]
) -> None:
    """The second ask reads the data with a tool; the reply after it passes when the tool's result holds its figure,
    and is withheld when it still states one no source holds, although a tool ran."""
    fake = swap_models("gemini", {"root": [{"text": INVENTED}, {"call": "get_dataset_profile"}, {"text": closing}]})
    sid = await open_session(client)

    turn = await say(client, sid, "what do the scores add up to?")

    assert [name for name, _ in turn] == events
    assert len([request for request in fake.requests if kind_of(request) == "root"]) == 3


QUERY = {"operations": [], "columns": ["Exam Score"], "limit": 3}
"""A question of the data that returns three scores, none of them the invented total."""


def shape(request: LlmRequest) -> list[tuple[str | None, list[str]]]:
    """Each content of a request as its role and the kinds of its parts."""
    kinds = []
    for content in request.contents:
        parts = []
        for part in content.parts or []:
            if part.function_call is not None:
                parts.append(f"call:{part.function_call.name}")
            elif part.function_response is not None:
                parts.append(f"result:{part.function_response.name}")
            elif part.text:
                parts.append("text")
        kinds.append((content.role, parts))
    return kinds


async def test_the_reask_line_never_reaches_the_request_after_its_tool_call(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The re-ask line quotes the reply's unsourced figures in a user-role turn, and the check reads every user turn of
    the root's request as the user's own words. Were the line to reach the request ADK builds after the tool the second
    ask called, the figure it quotes would source itself, and a reply that repeats it would pass. The line and the
    first reply live only in the second ask's copy of the request; the event ADK stores is the answer's tool call, so
    the next request holds the user's message, that call and its result, and the repeated figure is withheld."""
    script = [{"text": INVENTED}, {"call": "query_data", "args": QUERY}, {"text": INVENTED}]
    fake = swap_models("gemini", {"root": script})
    sid = await open_session(client)

    turn = await say(client, sid, "what do the scores add up to?")

    first, reask, after = [request for request in fake.requests if kind_of(request) == "root"]
    assert shape(reask)[-2:] == [("model", ["text"]), ("user", ["text"])]
    assert '"1,618.03"' in (reask.contents[-1].parts[0].text or "")
    assert shape(after) == [*shape(first), ("model", ["call:query_data"]), ("user", ["result:query_data"])]
    (result,) = [part.function_response for part in after.contents[-1].parts or [] if part.function_response]
    assert result.response is not None and result.response.get("status") != "error"
    held = json.dumps([content.model_dump(mode="json") for content in after.contents])
    assert REASK_LINE.split("{figures}")[0] not in held and "1,618" not in held
    assert request_sources(after, {}).kind_of(one("1,618.03")) is None
    assert [name for name, _ in turn] == ["ready", "error", "done"]
    assert turn[1][1] == {"code": UNVERIFIED_FIGURE, "ref": "req-1"}
    (record,) = (await bundle(client, sid))["turns"]["records"]
    assert [(line["guard"], line["verdict"]) for line in record["guards"]] == [
        ("scope_guard", "in_scope"),
        (HOOK, "reasked"),
        (HOOK, "withheld"),
    ]
