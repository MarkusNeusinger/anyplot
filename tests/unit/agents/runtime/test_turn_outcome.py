"""What a turn changed (`done.turn`), the memory a version stands on (`plot.memory`) and the round cap on `status`.

The record of the root's tool calls (`RequestLedger.tool_calls`) comes first, as ToolSafety writes it; then the
outcome derived from it (`stream.turn_outcome`) and the translator's fields; then whole turns through `/v1` with
scripted models, one per outcome value.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
from google.adk.events.event import Event

from agents.anyplot.memory import MemoryEntry, memory_delta, plan
from agents.anyplot.models import JudgeVerdict
from agents.anyplot.pipeline import STATUS_KEY
from agents.anyplot.plugins.budget import BudgetPlugin
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger, ToolCall
from agents.anyplot.plugins.tool_safety import ToolSafetyPlugin, call_outcome
from agents.anyplot.schemas import RememberItem
from agents.anyplot.services import Services
from agents.anyplot.settings import get_settings
from agents.main import ActiveRun, Runtime, app, ended_well, get_runtime
from agents.stream import CALL_CHANGES, TURN_ORDER, Translator, plot_memory, turn_outcome

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import HEADERS, USER, open_session, parse_sse, permissive_queue, set_max_attempts


LINE = RememberItem(kind="reference_line", text="horizontal reference line at y = 7")
STARS = RememberItem(kind="marker", text="outliers as red star markers")
LIMITS = RememberItem(kind="limits", target="x", text="x limits 0 to 100")
LABEL = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (h)'", expected_text="Zeit (h)")
DERIVE = {"op": "derive", "name": "Score per Hour", "how": "ratio", "columns": ["Exam Score", "Study Hours"]}


def calls(*pairs: tuple[str, str]) -> RequestLedger:
    ledger = RequestLedger()
    ledger.tool_calls = [ToolCall(tool, outcome=outcome) for tool, outcome in pairs]  # type: ignore[arg-type]
    return ledger


# --- the record of the root's calls ---------------------------------------------------------


@dataclass
class FakeContext:
    invocation_id: str = "inv-1"
    agent_name: str = "anyplot"
    function_call_id: str | None = None
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeTool:
    name: str


@pytest.fixture
def ledger() -> Iterator[RequestLedger]:
    current = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1")
    token = CURRENT_LEDGER.set(current)
    yield current
    CURRENT_LEDGER.reset(token)


async def call(
    plugin: ToolSafetyPlugin, name: str, args: dict[str, Any], result: dict[str, Any], call_id: str | None = None
) -> None:
    context = FakeContext(function_call_id=call_id)
    refusal = await plugin.before_tool_callback(tool=FakeTool(name), tool_args=args, tool_context=context)
    await plugin.after_tool_callback(
        tool=FakeTool(name), tool_args=args, tool_context=context, result=refusal or result
    )


class TestRecord:
    async def test_every_call_is_noted_in_order_with_its_verdict_and_what_it_did(self, ledger: RequestLedger) -> None:
        plugin = ToolSafetyPlugin()
        await call(plugin, "get_dataset_profile", {}, {"status": "ok", "rows": 3})
        await call(plugin, "set_bindings", {"bindings": "not a list"}, {})
        await call(plugin, "set_bindings", {"bindings": [{"role": "x", "column": "a"}]}, {"status": "ok"})
        await call(plugin, "plot_pipeline", {}, {"status": "ok", "attempts": 1, "artifacts": []})
        await call(plugin, "plot_pipeline", {}, {"status": "ok"})

        assert ledger.tool_calls == [
            ToolCall("get_dataset_profile", "allowed", "ok"),
            ToolCall("set_bindings", "invalid_arguments", "refused"),
            ToolCall("set_bindings", "allowed", "changed"),
            ToolCall("plot_pipeline", "allowed", "shipped"),
            ToolCall("plot_pipeline", "one_pipeline_per_turn", "refused"),
        ]
        # The allowed names stay as EmptyReply and the usage telemetry read them.
        assert ledger.tools == ["get_dataset_profile", "set_bindings", "plot_pipeline"]
        assert ledger.open_calls == {}

    async def test_parallel_calls_close_by_their_call_id(self, ledger: RequestLedger) -> None:
        plugin = ToolSafetyPlugin()
        first, second = FakeContext(function_call_id="c1"), FakeContext(function_call_id="c2")
        for context in (first, second):
            await plugin.before_tool_callback(
                tool=FakeTool("set_language"), tool_args={"language": "de"}, tool_context=context
            )
        await plugin.after_tool_callback(
            tool=FakeTool("set_language"), tool_args={}, tool_context=second, result={"status": "error", "code": "x"}
        )
        await plugin.after_tool_callback(
            tool=FakeTool("set_language"), tool_args={}, tool_context=first, result={"status": "ok"}
        )

        assert [c.outcome for c in ledger.tool_calls] == ["changed", "error"]

    async def test_a_call_the_budget_answered_first_is_refused_by_budget(
        self, ledger: RequestLedger, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_DAILY_PIPELINE_RUNS", "1")
        get_settings.cache_clear()
        services.usage.add_pipeline_run("adm_1")  # the day's one run is spent
        context = FakeContext(function_call_id="c1")
        refusal = await BudgetPlugin().before_tool_callback(
            tool=FakeTool("plot_pipeline"),
            tool_args={},
            tool_context=context,  # type: ignore[arg-type]
        )
        assert refusal == {"status": "error", "code": "budget"}  # the chain ends: ToolSafety's before never runs
        # A parallel call of the same model answer that closes first stays after it, where the root made it.
        await call(ToolSafetyPlugin(), "set_language", {"language": "de"}, {"status": "ok"}, call_id="c2")

        await ToolSafetyPlugin().after_tool_callback(
            tool=FakeTool("plot_pipeline"),
            tool_args={},
            tool_context=context,
            result=refusal,  # type: ignore[arg-type]
        )

        assert ledger.tool_calls == [
            ToolCall("plot_pipeline", "budget", "refused"),
            ToolCall("set_language", "allowed", "changed"),
        ]
        assert ledger.tools == ["set_language"]
        assert ledger.open_calls == {}

    async def test_a_name_the_model_made_up_is_kept_as_other(self, ledger: RequestLedger) -> None:
        await call(ToolSafetyPlugin(), "mail_my_boss@example.com", {}, {})

        assert ledger.tool_calls == [ToolCall("other", "tool_not_allowed", "refused")]

    async def test_a_plot_buttons_turn_records_the_refused_change(self, ledger: RequestLedger) -> None:
        """B3's guard reads the ledger as before: the refused change never enters `tools`."""
        ledger.plot_action = True
        plugin = ToolSafetyPlugin()
        await call(plugin, "prepare_data", {"operations": [DERIVE]}, {"status": "ok"})
        await call(plugin, "plot_pipeline", {}, {"status": "ok"})

        assert ledger.tool_calls == [
            ToolCall("prepare_data", "plot_as_confirmed", "refused"),
            ToolCall("plot_pipeline", "allowed", "shipped"),
        ]
        assert ledger.tools == ["plot_pipeline"]

    async def test_other_agents_calls_are_not_the_roots(self, ledger: RequestLedger) -> None:
        context = FakeContext(agent_name="adapter_matplotlib")
        await ToolSafetyPlugin().before_tool_callback(
            tool=FakeTool("get_spec_brief"), tool_args={}, tool_context=context
        )
        await ToolSafetyPlugin().after_tool_callback(
            tool=FakeTool("get_spec_brief"), tool_args={}, tool_context=context, result={"status": "ok"}
        )

        assert ledger.tool_calls == []

    async def test_a_call_still_running_at_the_end_stays_unfinished(self, ledger: RequestLedger) -> None:
        await ToolSafetyPlugin().before_tool_callback(
            tool=FakeTool("run_data_code"),
            tool_args={"code": "df = 1", "source_language": "python"},
            tool_context=FakeContext(),
        )

        assert ledger.tool_calls == [ToolCall("run_data_code", "allowed", "unfinished")]
        assert turn_outcome(ledger) == "answer"

    @pytest.mark.parametrize(
        ("setup", "name", "args", "verdict"),
        [
            ({"switch_request": {"library": "seaborn", "plot": True}}, "plot_pipeline", {}, "switch_requested"),
            ({"tools": ["plot_pipeline"]}, "switch_plot", {"library": "seaborn"}, "plot_already_run"),
            ({"tools": ["plot_pipeline"]}, "plot_pipeline", {}, "one_pipeline_per_turn"),
            (
                {"tools": ["run_data_code"] * 2},
                "run_data_code",
                {"code": "df = 1", "source_language": "python"},
                "too_many_data_runs",
            ),
            ({"tools": ["prepare_data"] * 2}, "prepare_data", {"operations": [DERIVE]}, "too_many_prepare_calls"),
            (
                {"tools": ["generate_data"] * 2},
                "generate_data",
                {"variables": [{"name": "x", "start": "0", "stop": "1"}], "series": [{"name": "y", "expression": "x"}]},
                "too_many_generate_calls",
            ),
            ({"tools": ["query_data"] * 3}, "query_data", {"operations": []}, "too_many_query_calls"),
            ({}, "plot_pipeline", {"change_request": "as on https://example.com/chart"}, "url_or_path_not_allowed"),
        ],
    )
    async def test_every_refusal_is_a_closed_verdict(
        self, ledger: RequestLedger, setup: dict[str, Any], name: str, args: dict[str, Any], verdict: str
    ) -> None:
        for key, value in setup.items():
            setattr(ledger, key, value)

        await call(ToolSafetyPlugin(), name, args, {"status": "ok"})

        assert ledger.tool_calls == [ToolCall(name, verdict, "refused")]  # type: ignore[arg-type]

    async def test_a_readers_answer_the_checks_refused_is_an_error_and_a_stored_change_still_counts(
        self, ledger: RequestLedger
    ) -> None:
        plugin = ToolSafetyPlugin()
        await call(plugin, "get_dataset_profile", {}, {"status": "ok", "unexpected": 1})
        await call(plugin, "prepare_data", {"operations": [DERIVE]}, {"status": "ok", "unexpected": 1})

        assert ledger.tool_calls == [
            ToolCall("get_dataset_profile", "allowed", "error"),  # the root got `invalid_result`
            ToolCall("prepare_data", "allowed", "changed"),  # the version is stored all the same
        ]

    def test_a_code_outside_the_verdicts_reads_unknown(self) -> None:
        ledger = RequestLedger()
        ledger.open_call("c1", "forget", "a_refusal_added_later")
        assert ledger.tool_calls == [ToolCall("forget", "unknown", "refused")]

    def test_a_call_that_ran_without_its_note_still_counts(self) -> None:
        """Only an error answer without a note is a refusal from before ToolSafety; a change the tool stored counts."""
        ledger = RequestLedger()
        ledger.close_call("c1", "prepare_data", "changed", early_verdict="unknown")
        ledger.close_call("c2", "plot_pipeline", "error", early_verdict="budget")

        assert ledger.tool_calls == [
            ToolCall("prepare_data", "allowed", "changed"),
            ToolCall("plot_pipeline", "budget", "refused"),
        ]
        assert turn_outcome(ledger) == "data"


@pytest.mark.parametrize(
    ("tool", "result", "outcome"),
    [
        ("query_data", {"status": "ok", "rows": 2}, "ok"),
        ("get_current_code", {"status": "ok"}, "ok"),
        ("prepare_data", {"status": "ok", "version": 2}, "changed"),
        ("prepare_data", {"status": "error", "code": "invalid_operations"}, "error"),
        ("prepare_data", {"status": "not_ready", "reason": "no_dataset"}, "not_ready"),
        ("generate_data", {"status": "ok"}, "changed"),
        ("run_data_code", {"status": "ok"}, "changed"),
        ("set_bindings", {"status": "ok"}, "changed"),
        ("set_language", {"status": "ok", "changed": False}, "changed"),
        ("forget", {"status": "ok", "entries": 1}, "changed"),
        ("forget", {"status": "error", "code": "unknown_entry"}, "error"),
        ("keep_plot_request", {"status": "ok", "request_kept": True}, "kept"),
        ("keep_plot_request", {"status": "ok", "request_kept": False, "reason": "plot_exists"}, "ok"),
        ("switch_plot", {"status": "ok", "switch_requested": True}, "changed"),
        ("plot_pipeline", {"status": "needs_attention"}, "shipped"),
        ("plot_pipeline", {"status": "failed", "reason": "render"}, "failed"),
        ("plot_pipeline", {"status": "not_ready", "reason": "incomplete_bindings"}, "not_ready"),
        # A stop with a failed plot card is the plot turn the page shows, a wish it kept or not.
        ("plot_pipeline", {"status": "not_ready", "reason": "incomplete_bindings", "request_kept": True}, "not_ready"),
        ("plot_pipeline", {"status": "not_ready", "reason": "data_unconfirmed"}, "unconfirmed"),
        ("plot_pipeline", {"status": "not_ready", "reason": "data_unconfirmed", "request_kept": True}, "kept"),
        ("plot_pipeline", {"status": "error", "code": "budget"}, "error"),
        ("plot_pipeline", None, "error"),
    ],
)
def test_call_outcome_reads_the_tools_own_answer(tool: str, result: Any, outcome: str) -> None:
    assert call_outcome(tool, result) == outcome


# --- the turn's outcome ---------------------------------------------------------------------


class TestTurnOutcome:
    @pytest.mark.parametrize(
        ("record", "outcome"),
        [
            ([], "answer"),
            ([("query_data", "ok"), ("get_dataset_profile", "ok")], "answer"),
            ([("prepare_data", "error"), ("set_bindings", "refused")], "answer"),  # a write that stored nothing
            ([("plot_pipeline", "unconfirmed")], "answer"),  # no round, no plot card
            ([("prepare_data", "changed")], "data"),
            ([("set_bindings", "changed")], "data"),
            ([("run_data_code", "changed")], "data"),
            ([("plot_pipeline", "shipped")], "plot"),
            ([("plot_pipeline", "failed")], "plot"),
            ([("plot_pipeline", "not_ready")], "plot"),  # the page shows it as a failed plot card
            ([("keep_plot_request", "kept")], "kept"),
            ([("plot_pipeline", "kept")], "kept"),
            ([("switch_plot", "changed")], "switch"),
            ([("set_language", "changed")], "language"),
            ([("forget", "changed")], "memory"),
            # Several changes: the first in TURN_ORDER, the page's own order.
            ([("keep_plot_request", "kept"), ("prepare_data", "changed")], "data"),
            ([("prepare_data", "changed"), ("plot_pipeline", "shipped")], "data"),
            ([("forget", "changed"), ("plot_pipeline", "shipped")], "plot"),
            ([("set_language", "changed"), ("keep_plot_request", "kept")], "language"),
            ([("forget", "changed"), ("keep_plot_request", "kept")], "kept"),
        ],
    )
    def test_from_the_record(self, record: list[tuple[str, str]], outcome: str) -> None:
        assert turn_outcome(calls(*record)) == outcome

    def test_the_paste_conversions_of_a_summary_change_the_data_without_a_call(self) -> None:
        ledger = calls(("get_dataset_profile", "ok"))
        ledger.conversions_made = "ds-2"
        assert turn_outcome(ledger) == "data"

    def test_every_change_has_its_place_in_the_order(self) -> None:
        assert set(CALL_CHANGES.values()) == set(TURN_ORDER)
        assert len(TURN_ORDER) == len(set(TURN_ORDER))


class TestEndedWell:
    """Only a turn that ended well says what it changed: the page marks no refused, failed or stopped turn."""

    def run(self, *, aborted: bool = False, deadline: bool = False) -> ActiveRun:
        run = ActiveRun(abort=asyncio.Event(), deadline_hit=deadline)
        if aborted:
            run.abort.set()
        return run

    def test_a_plain_turn(self) -> None:
        assert ended_well(RequestLedger(), self.run(), None)

    def test_an_error_or_a_refusal(self) -> None:
        refused = RequestLedger()
        refused.refuse("out_of_scope", "Only plots.")
        assert not ended_well(RequestLedger(), self.run(), "internal")
        assert not ended_well(refused, self.run(), None)

    def test_the_users_stop(self) -> None:
        assert not ended_well(RequestLedger(), self.run(aborted=True), None)

    def test_a_deadline_after_a_shipped_plot(self) -> None:
        """The route fails a deadline only before a plot went out; after one, the turn ended well."""
        assert ended_well(RequestLedger(), self.run(aborted=True, deadline=True), None)


# --- the translator's fields ----------------------------------------------------------------


@pytest.fixture
def translator() -> Translator:
    return Translator(RequestLedger(request_id="req-7", llm_calls=3, tokens=900), run_id="run-1")


def status_event(**status: Any) -> Event:
    return Event(custom_metadata={STATUS_KEY: status})


def pipeline_event(**output: Any) -> Event:
    return Event(author="plot_pipeline", output=output)


class TestTranslator:
    def test_done_carries_the_turn_last_and_reads_as_before_without_it(self, translator: Translator) -> None:
        before = translator.done(bindings=[], data_confirmed=True)
        assert before == 'event: done\ndata: {"llm_calls":3,"tokens":900,"bindings":[],"data_confirmed":true}\n\n'
        after = translator.done(bindings=[], data_confirmed=True, turn="answer")
        assert after == before.removesuffix("}\n\n") + ',"turn":"answer"}\n\n'

    def test_a_steps_status_carries_the_round_cap(self, translator: Translator) -> None:
        (chunk,) = translator.translate(status_event(step="adapting", attempt=1, max_attempts=3))
        assert chunk == 'event: status\ndata: {"step":"adapting","attempt":1,"max_attempts":3}\n\n'

    @pytest.mark.parametrize("cap", [None, 0, True, "3", 2.5])
    def test_a_missing_or_malformed_cap_reads_as_before(self, translator: Translator, cap: object) -> None:
        status: dict[str, Any] = {"step": "rendering", "attempt": 2}
        if cap is not None:
            status["max_attempts"] = cap
        (chunk,) = translator.translate(status_event(**status))
        assert chunk == 'event: status\ndata: {"step":"rendering","attempt":2}\n\n'

    def test_the_queue_statuses_are_unchanged(self, translator: Translator) -> None:
        assert translator.queued(2, 3) == 'event: status\ndata: {"step":"queued","position":2,"waiting":3}\n\n'
        assert translator.started() == 'event: status\ndata: {"step":"started"}\n\n'

    def test_a_stored_version_carries_its_memory(self, translator: Translator) -> None:
        translator.ledger.shipped_memory = {"kept": ["m1", "m2", "m3"], "added": ["m4"]}
        (chunk,) = translator.translate(pipeline_event(status="ok", attempts=1, artifacts=[], version=4))
        assert chunk == (
            'event: plot\ndata: {"status":"ok","attempts":1,"artifacts":[],"version":4,'
            '"memory":{"kept":["m1","m2","m3"],"added":["m4"]}}\n\n'
        )

    def test_a_plot_without_a_stored_version_carries_no_memory(self, translator: Translator) -> None:
        translator.ledger.shipped_memory = {"kept": ["m1"], "added": []}  # never read without a version
        (chunk,) = translator.translate(pipeline_event(status="failed", reason="render", attempts=2, artifacts=[]))
        assert chunk == 'event: plot\ndata: {"status":"failed","reason":"render","attempts":2,"artifacts":[]}\n\n'

    def test_a_version_whose_memory_the_server_does_not_hold_carries_none(self, translator: Translator) -> None:
        """Never two empty lists that would read as "kept 0" for a memory nobody settled."""
        (chunk,) = translator.translate(pipeline_event(status="ok", attempts=1, artifacts=[], version=2))
        assert chunk == 'event: plot\ndata: {"status":"ok","attempts":1,"artifacts":[],"version":2}\n\n'

    def test_only_entry_ids_pass(self) -> None:
        assert plot_memory({"kept": ["m1", "title: 'Lernzeit'", 7], "added": ["m12"]}) == {
            "kept": ["m1"],
            "added": ["m12"],
        }
        assert plot_memory({"kept": ["m1"]}) is None
        assert plot_memory(None) is None


# --- whole turns ----------------------------------------------------------------------------


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


async def say(client: httpx.AsyncClient, sid: str, text: str) -> list[tuple[str, dict[str, Any]]]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": text})
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


def done_of(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    assert events[-1][0] == "done"
    return events[-1][1]


def plot_of(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    return next(data for name, data in events if name == "plot")


async def seed_memory(sid: str, held: list[MemoryEntry]) -> None:
    runtime = app.dependency_overrides[get_runtime]()
    seq = max((int(entry.id[1:]) for entry in held), default=0) + 1
    await runtime.write_state(await runtime.session(USER, sid), memory_delta(held, seq))


def root(*steps: dict[str, Any], reply: str = "Okay.") -> dict[str, list[Any]]:
    return {"root": [*steps, {"text": reply}]}


def plotting(*steps: dict[str, Any]) -> dict[str, list[Any]]:
    return {
        "root": [*steps, {"text": "Here it is."}],
        "adapter": [{"json": SCATTER_PLAN}],
        "reviewer": [{"json": VERDICT_OK}],
    }


@pytest.mark.parametrize(
    ("script", "text"),
    [
        (root({"call": "query_data", "args": {"operations": [{"op": "sort", "column": "Exam Score"}]}}), "top score?"),
        (root({"call": "get_dataset_profile", "args": {}}), "which columns are numbers?"),
    ],
    ids=["query_data", "profile"],
)
async def test_a_question_is_an_answer(client: httpx.AsyncClient, swap_models, script: dict, text: str) -> None:
    swap_models("gemini", script)
    sid = await open_session(client)

    assert done_of(await say(client, sid, text))["turn"] == "answer"


async def test_a_data_change_is_data(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", root({"call": "prepare_data", "args": {"operations": [DERIVE]}}))
    sid = await open_session(client)

    done = done_of(await say(client, sid, "add the score per hour"))

    assert done["turn"] == "data" and done["dataset"]["version"] == 2


async def test_a_plot_is_plot_and_its_version_stands_on_no_memory(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", plotting({"call": "plot_pipeline", "args": {}}))
    sid = await open_session(client)

    events = await say(client, sid, "plot it")

    assert done_of(events)["turn"] == "plot"
    # A session without memory: known to be empty, so two empty lists, never a missing field.
    assert plot_of(events)["memory"] == {"kept": [], "added": []}
    steps = [data for name, data in events if name == "status"]
    assert steps and all(step["max_attempts"] == 2 for step in steps)  # the default AGENT_MAX_ATTEMPTS


async def test_the_round_cap_follows_the_setting(
    client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
) -> None:
    set_max_attempts(monkeypatch, "3")
    swap_models("gemini", plotting({"call": "plot_pipeline", "args": {}}))
    sid = await open_session(client)

    events = await say(client, sid, "plot it")

    assert {data["max_attempts"] for name, data in events if name == "status"} == {3}


async def test_a_version_names_the_decisions_it_kept_and_the_one_it_added(
    client: httpx.AsyncClient, swap_models
) -> None:
    swap_models(
        "gemini", plotting({"call": "plot_pipeline", "args": {"remember": [LABEL.model_dump(exclude_none=True)]}})
    )
    sid = await open_session(client)
    await seed_memory(sid, plan([], [LINE, STARS, LIMITS], seq=1, turn=0).entries)

    events = await say(client, sid, "plot it with the x axis called 'Zeit (h)'")

    assert plot_of(events)["memory"] == {"kept": ["m1", "m2", "m3"], "added": ["m4"]}
    assert done_of(events)["turn"] == "plot"


async def test_a_turn_that_fails_after_shipping_keeps_its_plots_memory_and_has_no_outcome(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The memory settles with the version, before the `plot` event: an error later in the turn cannot unsettle it,
    and the `done` after the error names no outcome, as the page marks no failed turn."""
    swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"raise": RuntimeError("model gone")}],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await seed_memory(sid, plan([], [LINE], seq=1, turn=0).entries)

    events = await say(client, sid, "plot it")

    assert plot_of(events)["memory"] == {"kept": ["m1"], "added": []}
    assert [name for name, _ in events][-2:] == ["error", "done"]
    assert "turn" not in done_of(events)


async def test_a_wish_kept_for_the_first_plot_is_kept(client: httpx.AsyncClient, swap_models) -> None:
    keep = {"call": "keep_plot_request", "args": {"change_request": "title 'Lernzeit'", "expected_texts": ["Lernzeit"]}}
    swap_models("gemini", root(keep, reply="Kept for the first plot."))
    sid = await open_session(client)

    events = await say(client, sid, "Titel 'Lernzeit' bitte")

    assert done_of(events)["turn"] == "kept"
    assert "plot" not in [name for name, _ in events]  # the stream itself shows nothing of it


async def test_a_switch_is_switch(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", root({"call": "switch_plot", "args": {"library": "seaborn"}}))
    sid = await open_session(client)

    done = done_of(await say(client, sid, "make it in seaborn"))

    assert done["turn"] == "switch" and done["switch"] == {"library": "seaborn", "plot": True}


async def test_a_language_choice_is_language(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", root({"call": "set_language", "args": {"language": "de"}}))
    sid = await open_session(client)

    assert done_of(await say(client, sid, "answer in German please"))["turn"] == "language"


async def test_a_forgotten_decision_is_memory(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", root({"call": "forget", "args": {"entry_id": "m1"}}, reply="Forgotten."))
    sid = await open_session(client)
    await seed_memory(sid, plan([], [LINE, STARS], seq=1, turn=0).entries)

    assert done_of(await say(client, sid, "no reference line after all"))["turn"] == "memory"


async def test_a_refused_turn_has_no_outcome(client: httpx.AsyncClient, swap_models, judge) -> None:
    swap_models("gemini", root())
    sid = await open_session(client)
    judge.script = [JudgeVerdict(verdict="out_of_scope", lang="en")]

    events = await say(client, sid, "write me a poem")

    assert [name for name, _ in events] == ["ready", "refusal", "done"]
    assert "turn" not in done_of(events)


async def test_a_plot_the_day_budget_refused_changed_nothing(
    client: httpx.AsyncClient, swap_models, services: Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through ADK's own flow: the Budget plugin answers the call before ToolSafety sees it, and the record still
    closes it as refused, so the turn reads as one that changed nothing."""
    monkeypatch.setenv("AGENT_DAILY_PIPELINE_RUNS", "1")
    get_settings.cache_clear()
    swap_models("gemini", root({"call": "plot_pipeline", "args": {}}, reply="Today's plots are used up."))
    sid = await open_session(client)
    services.usage.add_pipeline_run(USER)  # the day's one run is spent

    events = await say(client, sid, "plot it")

    assert "plot" not in [name for name, _ in events]
    assert done_of(events)["turn"] == "answer"
