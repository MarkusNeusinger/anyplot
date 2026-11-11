"""The root's turn guards: the per-turn caps, the plot refused before the run after the turn's own data change or on
the summary turn of an unconfirmed paste, the session line of the plot buttons' turns, and what Budget counts.

The caps and the bounds are ToolSafety's code, counted from the turn's allowed calls (`RequestLedger.calls_of`), so
root.md no longer repeats them. The two refusals before the run leave what the run's own `not_ready` would (the kept
request, the `pipeline_run` line, the last run) and tell the root why in a fixed message (owner decision of 2026-11-08:
refuse before the run, so the turn of a data change or of a paste's summary never shows the page a plot card).
"""

import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from agents.anyplot import telemetry
from agents.anyplot.agent import PLOT_ACTION_LINE
from agents.anyplot.models import JudgeVerdict
from agents.anyplot.plugins.budget import BudgetPlugin
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, ToolCall
from agents.anyplot.plugins.tool_safety import (
    CAP_MESSAGE,
    DATA_CHANGED,
    STOP_MESSAGES,
    SUMMARY_TURN,
    TURN_CAPS,
    ToolSafetyPlugin,
    TurnCap,
    pipeline_bound,
)
from agents.anyplot.services import Services
from agents.anyplot.session_state import LAST_RUN, PENDING_REQUEST, SUMMARY_PENDING, read_session
from agents.main import Runtime, app, get_runtime

from .conftest import CASES
from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    open_session,
    parse_sse,
    permissive_queue,
    request_text,
    requests_of,
    snapshot_body,
)


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


@dataclass
class FakeSession:
    id: str = "s1"
    user_id: str = USER


@dataclass
class FakeContext:
    invocation_id: str = "inv-1"
    agent_name: str = "anyplot"
    function_call_id: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    session: FakeSession = field(default_factory=FakeSession)


@dataclass
class FakeTool:
    name: str


@contextmanager
def turn(**fields: Any) -> Iterator[RequestLedger]:
    """One turn's ledger, as the `/messages` route binds it."""
    ledger = RequestLedger(request_id="req-1", user_id=USER, session_id="s1", **fields)
    token = CURRENT_LEDGER.set(ledger)
    try:
        yield ledger
    finally:
        CURRENT_LEDGER.reset(token)


async def before(name: str, args: dict[str, Any], agent: str = "anyplot") -> dict[str, Any] | None:
    return await ToolSafetyPlugin().before_tool_callback(
        tool=FakeTool(name),  # type: ignore[arg-type]
        tool_args=args,
        tool_context=FakeContext(agent_name=agent),  # type: ignore[arg-type]
    )


VALID: dict[str, dict[str, Any]] = {
    "prepare_data": {"operations": [{"op": "sort", "column": "Exam Score"}]},
    "generate_data": {
        "variables": [{"name": "x", "start": "0", "stop": "1"}],
        "series": [{"name": "y", "expression": "x**2"}],
    },
    "query_data": {"operations": []},
    "run_data_code": {"code": "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2]})", "source_language": "python"},
    "plot_pipeline": {},
}
"""A valid call of every capped tool, so a refusal is the cap's and never the arguments'."""
SNIPPET = "import numpy as np\nimport pandas as pd\nx = np.arange(4)\ndf = pd.DataFrame({'x': x, 'y': x**2})\n"
TITLE = "Title: Scores by hours"


def answers(fake: object, name: str) -> list[dict[str, Any]]:
    """What the root read back from each call of `name` in its last request, in order."""
    last = requests_of(fake, "root")[-1]
    return [
        part.function_response.response or {}
        for content in last.contents
        for part in content.parts or []
        if part.function_response is not None and part.function_response.name == name
    ]


def lines_of(caplog: pytest.LogCaptureFixture, event: str) -> list[dict[str, Any]]:
    records = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
    return [line for line in records if line["event"] == event]


class TestCaps:
    def test_the_caps(self) -> None:
        """A data call and one retry after its error, a third question, one plot run, the "one repair round" bound."""
        assert TURN_CAPS == {
            "prepare_data": TurnCap(2, "too_many_prepare_calls"),
            "generate_data": TurnCap(2, "too_many_generate_calls"),
            "query_data": TurnCap(3, "too_many_query_calls", spare=3),
            "run_data_code": TurnCap(2, "too_many_data_runs"),
            "plot_pipeline": TurnCap(1, "one_pipeline_per_turn"),
        }
        assert set(VALID) == set(TURN_CAPS)

    @pytest.mark.parametrize(
        ("errors", "answered", "allowed"),
        [(3, 0, True), (3, 2, True), (3, 3, False), (2, 1, True), (5, 0, True), (6, 0, False), (4, 2, False)],
    )
    async def test_a_question_that_answered_an_error_is_no_question_answered(
        self, errors: int, answered: int, allowed: bool
    ) -> None:
        """Persona round of 2026-11-11: three `query_data` calls answered errors, and the fourth, the one that would
        have worked, met the cap of three. Up to three errored calls come on top; six calls bound the turn."""
        calls = [ToolCall("query_data", outcome="error")] * errors + [ToolCall("query_data", outcome="ok")] * answered
        with turn(tools=["query_data"] * len(calls), tool_calls=list(calls)):
            refusal = await before("query_data", VALID["query_data"])

        assert (refusal is None) is allowed
        assert allowed or (refusal or {}).get("code") == "too_many_query_calls"

    async def test_a_data_writers_error_still_counts(self) -> None:
        """`prepare_data`'s cap is the change and one retry after its error: no call comes on top."""
        calls = [ToolCall("prepare_data", outcome="error")] * 2
        with turn(tools=["prepare_data"] * 2, tool_calls=list(calls)):
            refusal = await before("prepare_data", VALID["prepare_data"])

        assert (refusal or {}).get("code") == "too_many_prepare_calls"

    def test_the_cap_message_names_no_tool_and_no_limit(self) -> None:
        """The first wording named both, and the root told the user that "the query tool hit its call limit"."""
        for name, cap in TURN_CAPS.items():
            message = CAP_MESSAGE.format(tool=name, calls=cap.calls)
            assert name not in message and "per turn" not in message and not re.search(r"\d", message)

    @pytest.mark.parametrize("tier", ["public", "admin"])
    @pytest.mark.parametrize("name", sorted(TURN_CAPS))
    async def test_the_call_after_a_cap_is_refused_with_a_fixed_message(self, name: str, tier: str) -> None:
        """The same caps and codes for every tier; the message names the tool and the cap, never a word of the
        user's."""
        cap = TURN_CAPS[name]
        with turn(tier=tier) as ledger:
            allowed = [await before(name, VALID[name]) for _ in range(cap.calls)]
            refused = await before(name, VALID[name])

        assert allowed == [None] * cap.calls
        assert refused == {
            "status": "error",
            "code": cap.code,
            "message": CAP_MESSAGE.format(tool=name, calls=cap.calls),
        }
        assert ledger.calls_of(name) == cap.calls and ledger.tools == [name] * cap.calls
        assert ledger.tool_calls[-1] == ToolCall(name, cap.code, "refused")  # type: ignore[arg-type]

    @pytest.mark.parametrize("name", sorted(TURN_CAPS))
    async def test_a_refused_call_never_counts_and_a_new_turn_starts_at_zero(self, name: str) -> None:
        cap = TURN_CAPS[name]
        with turn() as ledger:
            assert (await before(name, {"bogus": 1}) or {}).get("code") == "invalid_arguments"
            for _ in range(cap.calls):
                assert await before(name, VALID[name]) is None
            for _ in range(2):  # a refusal of the cap counts no more than any other
                assert (await before(name, VALID[name]) or {}).get("code") == cap.code
            assert ledger.calls_of(name) == cap.calls
        with turn():
            assert await before(name, VALID[name]) is None

    async def test_the_checks_run_allowlist_plot_action_arguments_then_the_caps(self) -> None:
        """A later check of the module plan (`rules_loaded`) can go before every counter."""
        spent = ["prepare_data"] * 2
        with turn(plot_action=True, tools=list(spent)):
            assert await before("prepare_data", VALID["prepare_data"]) == {
                "status": "error",
                "code": "plot_as_confirmed",
            }
            assert await before("google_search", {}) == {"status": "error", "code": "tool_not_allowed"}
        with turn(tools=list(spent)):
            assert await before("prepare_data", VALID["prepare_data"], agent="adapter_matplotlib") == {
                "status": "error",
                "code": "tool_not_allowed",
            }
            broken = await before("prepare_data", {"operations": [{"op": "sort"}]})
            assert broken is not None and broken["code"] == "invalid_arguments" and "errors" in broken
            link = {"operations": [{"op": "rename", "column": "https://example.org/a", "name": "b"}]}
            assert await before("prepare_data", link) == {"status": "error", "code": "url_or_path_not_allowed"}
            assert (await before("prepare_data", VALID["prepare_data"]) or {}).get("code") == "too_many_prepare_calls"
        # A bound before the run comes after the arguments too: an invalid call keeps no request and writes no run.
        with turn(summary_turn=True) as ledger:
            linked = {"change_request": "as on https://example.org/chart"}
            assert await before("plot_pipeline", linked) == {"status": "error", "code": "url_or_path_not_allowed"}
            assert ledger.kept_note is None

    async def test_the_pipelines_bounds_keep_their_shape(self) -> None:
        with turn(switch_request={"library": "seaborn", "plot": True}):
            assert await before("plot_pipeline", {}) == {"status": "error", "code": "switch_requested"}
        with turn(tools=["plot_pipeline"]):
            assert await before("switch_plot", {"library": "seaborn"}) == {
                "status": "error",
                "code": "plot_already_run",
            }

    async def test_a_third_data_change_runs_no_tool_body(self, client: httpx.AsyncClient, swap_models) -> None:
        def sort(descending: bool) -> dict[str, Any]:
            operation = {"op": "sort", "column": "Exam Score", "descending": descending}
            return {"call": "prepare_data", "args": {"operations": [operation]}}

        fake = swap_models("gemini", {"root": [sort(True), sort(False), sort(True), {"text": "Sorted: 24 rows."}]})
        sid = await open_session(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "sort it"})

        found = answers(fake, "prepare_data")
        assert [answer["status"] for answer in found] == ["ok", "ok", "error"]
        assert found[-1] == {
            "status": "error",
            "code": "too_many_prepare_calls",
            "message": CAP_MESSAGE.format(tool="prepare_data", calls=2),
        }
        assert parse_sse(response.text)[-1][1]["dataset"]["version"] == 3  # the original and two changes


class TestDataChangedThisTurn:
    @pytest.mark.parametrize(
        ("calls", "outcome"),
        [
            ([ToolCall("prepare_data", outcome="changed")], DATA_CHANGED),
            ([ToolCall("generate_data", outcome="changed")], DATA_CHANGED),
            ([ToolCall("run_data_code", outcome="changed")], DATA_CHANGED),
            # Still running when the plot call comes in the same model answer: it would race the change.
            ([ToolCall("run_data_code")], DATA_CHANGED),
            ([ToolCall("prepare_data", outcome="error")], None),  # a failed call changed nothing
            ([ToolCall("prepare_data", "plot_as_confirmed", "refused")], None),
            ([ToolCall("set_bindings", outcome="changed")], None),  # no new version: the run answers for itself
            ([ToolCall("query_data", outcome="ok")], None),
        ],
    )
    def test_the_marker_reads_the_record_of_the_turns_calls(self, calls: list[ToolCall], outcome: str | None) -> None:
        with turn(tool_calls=list(calls)) as ledger:
            assert pipeline_bound(ledger, FakeContext()) == outcome  # type: ignore[arg-type]

    async def test_a_change_still_under_way_stops_the_plot_on_confirmed_data_too(
        self, client: httpx.AsyncClient, services: Services
    ) -> None:
        """The old version stays confirmed until the change stores the new one: a run in the same model answer would
        draw the version the change replaces (Flash review, 2026-11-08)."""
        sid = await open_session(client)  # pasted and confirmed
        state = await _session_state(client, sid)
        context = FakeContext(state=state, session=FakeSession(id=sid))
        assert read_session(state).data_confirmed  # type: ignore[union-attr]

        with turn(tool_calls=[ToolCall("run_data_code")]) as ledger:
            assert pipeline_bound(ledger, context) == DATA_CHANGED  # type: ignore[arg-type]
            refusal = await ToolSafetyPlugin().before_tool_callback(
                tool=FakeTool("plot_pipeline"),  # type: ignore[arg-type]
                tool_args={},
                tool_context=context,  # type: ignore[arg-type]
            )
        assert refusal is not None and (refusal["code"], refusal["reason"]) == (DATA_CHANGED, "data_unconfirmed")
        with turn(summary_turn=True) as ledger:
            assert pipeline_bound(ledger, context) is None  # a summary turn on confirmed data plots

    @pytest.mark.parametrize("change", ["prepare_data", "rebuild", "generate_data", "run_data_code"])
    async def test_a_plot_after_the_turns_own_change_is_refused_before_the_run(
        self, client: httpx.AsyncClient, swap_models, services: Services, caplog: pytest.LogCaptureFixture, change: str
    ) -> None:
        """No `plot` event, the request kept, the records of a `not_ready` run, no daily run counted; the turn's
        `done` carries the new data unconfirmed, which drops the page's confirmation."""
        caplog.set_level(logging.INFO)
        plot = {"call": "plot_pipeline", "args": {"change_request": TITLE}}
        calls = {
            "prepare_data": {"operations": [{"op": "sort", "column": "Exam Score", "descending": True}]},
            "rebuild": {"operations": [], "from_version": "original"},
            "generate_data": VALID["generate_data"],
            "run_data_code": {"code": SNIPPET, "source_language": "python"},
        }
        tool = "prepare_data" if change == "rebuild" else change
        root: list[dict[str, Any]] = [{"call": tool, "args": calls[change]}, plot, {"text": "Changed: 24 rows."}]
        if change == "rebuild":
            first = {"call": "prepare_data", "args": calls["prepare_data"]}
            root = [first, {"text": "Sorted."}, *root]
        fake = swap_models("gemini", {"root": root})
        sid = await open_session(client)
        if change == "rebuild":
            await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "sort by score"})
            caplog.clear()

        response = await client.post(
            f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "change it and plot it, title it please"}
        )
        events = parse_sse(response.text)

        assert [name for name, _ in events] == ["ready", "message", "done"]
        refusal = answers(fake, "plot_pipeline")[-1]
        assert refusal == {
            "status": "error",
            "code": DATA_CHANGED,
            "message": STOP_MESSAGES[DATA_CHANGED],
            "reason": refusal["reason"],
            "request_kept": True,
        }
        assert refusal["reason"] in ("data_unconfirmed", "incomplete_bindings")
        done = events[-1][1]
        assert done["data_confirmed"] is False and done["dataset"]["version"] >= 2 and done["turn"] == "data"
        state = await _session_state(client, sid)
        assert state[PENDING_REQUEST] == TITLE and state[LAST_RUN]["status"] == "not_ready"
        (run,) = lines_of(caplog, "pipeline_run")
        assert (run["status"], run["reason"]) == ("not_ready", refusal["reason"])
        (chat,) = lines_of(caplog, "chat_turn")
        assert "plot_pipeline" not in chat["tools"] and chat["kind"] in ("prep", "formula", "code")
        assert services.usage.user_runs(USER) == 0  # refused within the turn's bounds: no daily run

    async def test_after_a_failed_data_call_the_plot_runs(self, client: httpx.AsyncClient, swap_models) -> None:
        ghost = {"op": "rename", "column": "No Such Column", "name": "x"}
        script = {
            "root": [
                {"call": "prepare_data", "args": {"operations": [ghost]}},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Your plot is ready."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        }
        fake = swap_models("gemini", script)
        sid = await open_session(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "rename and plot"})

        assert answers(fake, "prepare_data")[-1]["status"] == "error"
        shipped = answers(fake, "plot_pipeline")[-1]
        assert shipped["status"] == "ok" and "code" not in shipped and "message" not in shipped
        assert next(data for name, data in parse_sse(response.text) if name == "plot")["status"] == "ok"

    async def test_a_plot_after_bindings_that_voided_the_confirmation_still_runs_into_not_ready(
        self, client: httpx.AsyncClient, swap_models, services: Services
    ) -> None:
        """root.md's `set_bindings` path: no data version, so the run itself answers `not_ready` `data_unconfirmed`
        with `request_kept`, sends its `plot` event, carries no code, and counts as a daily run as before."""
        swapped = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
        script = {
            "root": [
                {"call": "set_bindings", "args": {"bindings": swapped}},
                {"call": "plot_pipeline", "args": {"change_request": TITLE}},
                {"text": "The new bindings wait for your check; the title is kept."},
            ]
        }
        fake = swap_models("gemini", script)
        sid = await open_session(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "swap the axes"})

        assert answers(fake, "set_bindings")[-1]["data_confirmed"] is False
        result = answers(fake, "plot_pipeline")[-1]
        assert (result["status"], result["reason"], result["request_kept"]) == ("not_ready", "data_unconfirmed", True)
        assert "code" not in result and "message" not in result
        plot = next(data for name, data in parse_sse(response.text) if name == "plot")
        assert (plot["status"], plot["reason"]) == ("not_ready", "data_unconfirmed")
        assert services.usage.user_runs(USER) == 1


class TestSummaryTurn:
    async def paste(self, client: httpx.AsyncClient) -> str:
        sid = await open_session(client, with_data=False)
        data = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text()
        pasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": data})
        assert pasted.status_code == 200, pasted.text
        return sid

    async def test_the_summary_action_gets_no_plot_run(
        self, client: httpx.AsyncClient, swap_models, services: Services
    ) -> None:
        fake = swap_models("gemini", {"root": [{"call": "plot_pipeline", "args": {}}, {"text": "24 rows, 3 columns."}]})
        sid = await self.paste(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "summarize_data"})

        events = parse_sse(response.text)
        assert [name for name, _ in events] == ["ready", "message", "done"]
        # An action brings no request, so nothing is kept.
        assert answers(fake, "plot_pipeline")[-1] == {
            "status": "error",
            "code": SUMMARY_TURN,
            "message": STOP_MESSAGES[SUMMARY_TURN],
            "reason": "data_unconfirmed",
        }
        assert events[-1][1]["turn"] == "answer" and services.usage.user_runs(USER) == 0
        assert read_session(await _session_state(client, sid)).summary_pending is False  # type: ignore[union-attr]

    async def test_the_note_sent_with_the_paste_keeps_its_wish_once(
        self, client: httpx.AsyncClient, swap_models, judge
    ) -> None:
        """Twice refused, kept once (`merged_request`); the record names the refusal, with the outcome `kept`."""
        plot = {"call": "plot_pipeline", "args": {"change_request": TITLE, "expected_texts": ["Scores by hours"]}}
        fake = swap_models("gemini", {"root": [plot, plot, {"text": "24 rows; the title is kept for the first plot."}]})
        judge.script = [JudgeVerdict(verdict="in_scope", lang="en")]
        sid = await self.paste(client)

        response = await client.post(
            f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "title it Scores by hours"}
        )

        refused = answers(fake, "plot_pipeline")
        assert [answer["code"] for answer in refused] == [SUMMARY_TURN, SUMMARY_TURN]
        assert all(answer["request_kept"] is True for answer in refused)
        state = await _session_state(client, sid)
        assert state[PENDING_REQUEST] == TITLE
        assert parse_sse(response.text)[-1][1]["turn"] == "kept"

    @pytest.mark.parametrize("reply", ["", "https://example.org"])
    async def test_an_empty_or_sanitised_reply_after_the_refusal_is_no_reply(
        self, client: httpx.AsyncClient, swap_models, reply: str
    ) -> None:
        """No `plot` event sets `plot_sent`, and a refused run is no stored change: the turn fails with `no_reply` and
        the paste stays unsummarized, so the next message still summarizes it."""
        fake = swap_models(
            "gemini", {"root": [{"call": "plot_pipeline", "args": {}}, {"text": reply}, {"text": reply}]}
        )
        sid = await self.paste(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "summarize_data"})

        events = parse_sse(response.text)
        assert ("error", {"code": "no_reply", "ref": "req-1"}) in events and not any(n == "plot" for n, _ in events)
        assert answers(fake, "plot_pipeline")[-1]["code"] == SUMMARY_TURN
        assert read_session(await _session_state(client, sid)).summary_pending is True  # type: ignore[union-attr]

    async def test_a_summary_turn_on_confirmed_data_still_plots(
        self, client: httpx.AsyncClient, swap_models, runtime: Runtime, judge
    ) -> None:
        """The data the click confirmed is the user's own check: the plot runs, with no code."""
        script = {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Your plot is ready."}],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        }
        fake = swap_models("gemini", script)
        judge.script = [JudgeVerdict(verdict="in_scope", lang="en")]
        sid = await open_session(client)  # pasted and confirmed
        session = await runtime.session(USER, sid)
        view = read_session(session.state)
        assert view is not None and view.data_confirmed
        await runtime.write_state(session, {SUMMARY_PENDING: view.dataset_id})  # the summary is owed again

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "plot it"})

        shipped = answers(fake, "plot_pipeline")[-1]
        assert shipped["status"] == "ok" and "code" not in shipped
        assert next(data for name, data in parse_sse(response.text) if name == "plot")["status"] == "ok"

    async def test_budget_counts_no_run_for_the_turns_bounds(self, services: Services) -> None:
        """A second call, a switch, a call after the turn's data change or on an unconfirmed summary turn: no run.
        A call the run itself answers `not_ready` (unconfirmed data on any other turn) counts as before."""
        plugin = BudgetPlugin()
        bounded: list[dict[str, Any]] = [
            {"tools": ["plot_pipeline"]},
            {"switch_request": {"library": "seaborn", "plot": True}},
            {"tool_calls": [ToolCall("prepare_data", outcome="changed")]},
            {"summary_turn": True},
        ]
        for fields in bounded:
            with turn(**fields):
                answer = await plugin.before_tool_callback(
                    tool=FakeTool("plot_pipeline"),  # type: ignore[arg-type]
                    tool_args={},
                    tool_context=FakeContext(),  # type: ignore[arg-type]
                )
            assert answer is None and services.usage.user_runs(USER) == 0, fields
        with turn():
            await plugin.before_tool_callback(
                tool=FakeTool("plot_pipeline"),  # type: ignore[arg-type]
                tool_args={},
                tool_context=FakeContext(),  # type: ignore[arg-type]
            )
        assert services.usage.user_runs(USER) == 1

    async def test_a_refusal_that_kept_nothing_is_recorded_as_refused(self, services: Services) -> None:
        with turn(summary_turn=True) as ledger:
            refusal = await before("plot_pipeline", {})
        assert refusal is not None and refusal["code"] == SUMMARY_TURN and "request_kept" not in refusal
        assert refusal["reason"] == "no_dataset"
        assert ledger.tool_calls == [ToolCall("plot_pipeline", SUMMARY_TURN, "refused")]  # type: ignore[arg-type]
        assert ledger.tools == []


class TestPlotActionLine:
    @pytest.mark.parametrize("action", ["create_plot", "carry_plot"])
    async def test_both_plot_buttons_name_the_call(self, client: httpx.AsyncClient, swap_models, action: str) -> None:
        script = {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Your plot is ready."}],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        }
        fake = swap_models("gemini", script)
        sid = await open_session(client)

        await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": action})

        assert all(PLOT_ACTION_LINE in request_text(request) for request in requests_of(fake, "root"))

    @pytest.mark.parametrize("body", [{"text": "what is on x?"}, {"action": "summarize_data"}])
    async def test_no_other_turn_has_the_line(
        self, client: httpx.AsyncClient, swap_models, judge, body: dict[str, str]
    ) -> None:
        fake = swap_models("gemini", {"root": [{"text": "Study Hours is on x."}]})
        judge.script = [JudgeVerdict(verdict="in_scope", lang="en")]
        sid = await open_session(client)

        await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json=body)

        assert PLOT_ACTION_LINE not in request_text(requests_of(fake, "root")[0])

    async def test_a_fanout_session_has_the_line_too(self, client: httpx.AsyncClient, swap_models) -> None:
        script = {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Your plot is ready."}],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        }
        fake = swap_models("gemini", script)
        body = {
            "user": USER,
            "spec_id": "scatter-basic",
            "library": "matplotlib",
            "locale": "en",
            "snapshot": snapshot_body(),
            "source": "fanout",
        }
        opened = await client.post("/v1/sessions", headers=HEADERS, json=body)
        assert opened.status_code == 200, opened.text
        sid = opened.json()["session_id"]
        data = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text()
        assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": data})).is_success
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).is_success

        await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "create_plot"})

        assert PLOT_ACTION_LINE in request_text(requests_of(fake, "root")[0])

    def test_the_line_names_no_page_control(self) -> None:
        assert not re.search(r"\.[a-z_]+\(", PLOT_ACTION_LINE)
        assert "button" not in PLOT_ACTION_LINE and "plot_pipeline with no arguments" in PLOT_ACTION_LINE
