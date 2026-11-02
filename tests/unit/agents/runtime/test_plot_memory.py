"""The plot memory and the library switch that carries it (owner decisions of 2026-11-02).

Pure checks of `memory.py` and `switch.py` first, then whole turns through `/v1` with scripted
models: a change hands its lasting decisions over with the run and the memory keeps them only once
the plot ships; a switch keeps the memory and writes the carry, which the first run in the new
library takes from that library's catalogue code; `.start_over()` stays fresh and starts the memory
over; switching back counts the decisions the older plot misses; the page lists and removes entries.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot import telemetry
from agents.anyplot.memory import (
    MAX_ENTRIES,
    MEMORY,
    MEMORY_SEQ,
    MemoryEntry,
    MemoryRefused,
    decision_lines,
    expected_texts,
    forget,
    kind_counts,
    memory_delta,
    newer_than,
    next_seq,
    plan,
    read_memory,
    remember,
)
from agents.anyplot.opening import assess
from agents.anyplot.pipeline import DECISIONS_HEADING, EARLIER_REQUESTS_HEADING, EXPECTED_HEADING
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.schemas import PipelineArgs, PlotResult, RememberItem
from agents.anyplot.services import CodeVersion, Services, get_services
from agents.anyplot.session_state import PENDING_EXPECTED_TEXTS, PENDING_REMEMBER, PENDING_REQUEST
from agents.anyplot.settings import get_settings
from agents.anyplot.switch import CARRY, Carry, SourcePlot, Target, carry_for, read_carry, summary
from agents.main import ActiveRun, Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    adapter_inputs,
    create_plot,
    open_session,
    parse_sse,
    permissive_queue,
    snapshot_body,
)


LINE = RememberItem(kind="reference_line", text="horizontal reference line at y = 7")
FORMULA = RememberItem(kind="annotation", text="annotation top left: the formula $y = ax^2 + b$ typeset as LaTeX")
STARS = RememberItem(kind="marker", text="outliers as red star markers")
LABEL = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (h)'", expected_text="Zeit (h)")
LIMITS = RememberItem(kind="limits", target="x", text="x limits 0 to 100")
OWNER_EXAMPLES = [LINE, FORMULA, STARS, LABEL, LIMITS]
"""The owner's own examples of tuning the memory must hold (2026-11-02)."""


def entries(*items: RememberItem, turn: int = 1) -> list[MemoryEntry]:
    return plan([], items, seq=1, turn=turn).entries


# --- memory.py ------------------------------------------------------------------------------


class TestRemember:
    def test_a_single_valued_kind_replaces_the_entry_of_its_kind_and_target(self) -> None:
        before = entries(LABEL, RememberItem(kind="axis_label", target="y", text="y-axis label: 'Wert'"))
        relabelled = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (min)'")

        after = remember(before, relabelled, seq=3, turn=2)

        assert [(entry.id, entry.target, entry.text) for entry in after] == [
            ("m2", "y", "y-axis label: 'Wert'"),  # another target stays
            ("m3", "x", "x-axis label: 'Zeit (min)'"),
        ]

    def test_a_multi_valued_kind_adds_beside_the_others(self) -> None:
        second = RememberItem(kind="reference_line", text="vertical reference line at x = 50")

        after = remember(entries(LINE), second, seq=2, turn=2)

        assert [entry.text for entry in after] == [LINE.text, second.text]

    def test_a_correction_replaces_the_entry_it_names(self) -> None:
        """A second reference line is added beside the first; one that `replaces` it takes its place (Copilot on
        #12520)."""
        moved = RememberItem(kind="reference_line", text="horizontal reference line at y = 8", replaces="m1")

        after = remember(entries(LINE, STARS), moved, seq=3, turn=2)

        assert [(entry.id, entry.text) for entry in after] == [("m2", STARS.text), ("m3", moved.text)]
        assert remember(entries(STARS), moved, seq=2, turn=2)[-1].text == moved.text  # m1 gone already: just added
        with pytest.raises(ValueError):
            RememberItem(kind="marker", text="x", replaces="title")

    def test_the_same_decision_twice_is_one_entry(self) -> None:
        once = entries(LINE)

        assert remember(once, LINE, seq=2, turn=3) == once
        assert plan(once, [LINE], seq=2, turn=3).seq == 2  # the id counter does not move either

    def test_the_caps_refuse_rather_than_drop_an_old_entry(self) -> None:
        full = plan([], [RememberItem(kind="other", text=f"decision {n}") for n in range(MAX_ENTRIES)], seq=1, turn=1)
        assert len(full.entries) == MAX_ENTRIES and full.refused == 0

        with pytest.raises(MemoryRefused) as refused:
            remember(full.entries, LINE, seq=full.seq, turn=2)
        assert refused.value.code == "memory_full"
        long = [RememberItem(kind="other", text=f"{n:02d}" + "x" * 198) for n in range(16)]  # 3,200 characters
        planned = plan([], long, seq=1, turn=1)
        assert (len(planned.entries), planned.refused) == (15, 1)

    def test_forget_removes_by_id_and_refuses_an_unknown_one(self) -> None:
        held = entries(LINE, STARS)

        assert [entry.id for entry in forget(held, "m1")] == ["m2"]
        with pytest.raises(MemoryRefused):
            forget(held, "m9")

    def test_a_text_is_one_line_without_control_characters(self) -> None:
        assert RememberItem(kind="title", text="  Title:\n'A'  ").text == "Title: 'A'"
        with pytest.raises(ValueError):
            RememberItem(kind="title", text="bad\x00text")
        with pytest.raises(ValueError):
            RememberItem.model_validate({"kind": "unknown", "text": "a"})


class TestReadMemory:
    def test_a_corrupt_item_never_reaches_a_prompt(self) -> None:
        good = entries(LINE)[0].model_dump()
        state = {MEMORY: [good, {"id": "m2", "kind": "title"}, "text", dict(good), {**good, "id": "x"}]}

        assert [entry.id for entry in read_memory(state)] == ["m1"]  # the second copy of m1 is dropped too

    def test_ids_are_never_reused(self) -> None:
        held = entries(LINE, STARS)

        assert next_seq({MEMORY_SEQ: 7}, held) == 7
        assert next_seq({MEMORY_SEQ: 1}, held) == 3  # never below one past the highest id in use
        assert next_seq({}, []) == 1


class TestForgetTool:
    """`forget` refuses before it writes: no session, a run in flight, a malformed or unknown id."""

    @staticmethod
    def context(state: dict[str, Any], invocation_id: str) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(state=state, invocation_id=invocation_id, session=SimpleNamespace(id="s1"))

    @staticmethod
    def opened(**extra: Any) -> dict[str, Any]:
        from agents.anyplot.dev_fixture import snapshot_from_repo
        from agents.anyplot.session_state import initial_state

        state = initial_state(
            spec_id="scatter-basic",
            library="matplotlib",
            locale="en",
            snapshot=snapshot_from_repo("scatter-basic", "matplotlib"),
            normalised="x = 1",
            readiness={},
        )
        return {**state, **extra}

    async def test_each_refusal_leaves_the_memory_as_it_was(self) -> None:
        from agents.anyplot.plugins.ledger import ledger_for
        from agents.anyplot.tools.session import forget as forget_tool

        held = memory_delta(entries(LINE, STARS), 3)
        assert await forget_tool("m1", self.context({}, "inv-forget-1")) == {
            "status": "error",
            "code": "session_not_open",
        }
        state = self.opened(**held)
        for entry_id, code in (("title", "invalid_arguments"), ("m9", "unknown_entry")):
            assert await forget_tool(entry_id, self.context(state, "inv-forget-2")) == {"status": "error", "code": code}
        ledger_for("inv-forget-3").pipeline_active = True
        try:
            refused = await forget_tool("m1", self.context(state, "inv-forget-3"))
        finally:
            ledger_for("inv-forget-3").pipeline_active = False
        assert refused == {"status": "error", "code": "run_active"}
        assert state[MEMORY] == held[MEMORY]

        assert await forget_tool("m1", self.context(state, "inv-forget-4")) == {"status": "ok", "entries": 1}
        assert [entry.id for entry in read_memory(state)] == ["m2"]


def test_stored_values_that_fail_their_checks_are_dropped() -> None:
    from agents.anyplot.pipeline import merged_remember, take_carried_texts

    assert merged_remember([{"kind": "title"}, LINE.model_dump(), "x"], [STARS]) == [LINE, STARS]
    assert merged_remember("not a list", []) == []
    carry = Carry(source=MATPLOTLIB, target=SEABORN)
    assert take_carried_texts(PipelineArgs(change_request="c"), carry) == PipelineArgs(change_request="c")
    assert read_carry({CARRY: "text"}, SEABORN.pair()) is None
    assert read_carry({CARRY: {"source": {"spec_id": "x"}}}, SEABORN.pair()) is None
    with pytest.raises(ValueError):
        Target(spec_id="scatter-basic", library="excel")
    with pytest.raises(ValueError):
        RememberItem(kind="title", text=" \n ")  # nothing left once the whitespace is collapsed


def test_the_owner_examples_become_decisions_and_texts() -> None:
    held = entries(*OWNER_EXAMPLES)

    assert decision_lines(held) == [item.text for item in OWNER_EXAMPLES]
    assert expected_texts(held) == ["Zeit (h)"]  # the formula is no verbatim text
    assert kind_counts(held) == {"annotation": 1, "axis_label": 1, "limits": 1, "marker": 1, "reference_line": 1}
    assert newer_than(held, None) == 5 and newer_than(held, 1) == 0 and newer_than(held, 0) == 5


# --- switch.py ------------------------------------------------------------------------------

MATPLOTLIB = Target(spec_id="scatter-basic", library="matplotlib")
SEABORN = Target(spec_id="scatter-basic", library="seaborn")
PLOTLY = Target(spec_id="scatter-basic", library="plotly")


class TestCarry:
    def test_a_plot_carries_its_asked_theme_its_requests_and_the_memory_texts(self) -> None:
        plot = SourcePlot(theme="dark", theme_asked=True, expected_texts=["Old"], requests=["add a line at 7"])

        carry = carry_for(source=MATPLOTLIB, target=SEABORN, plot=plot, pending=None, memory=entries(LABEL))

        assert carry is not None and carry.from_plot
        assert (carry.theme, carry.expected_texts, carry.requests) == ("dark", ["Zeit (h)"], ["add a line at 7"])

    def test_without_memory_the_versions_own_texts_carry_and_a_site_theme_does_not(self) -> None:
        plot = SourcePlot(theme="dark", theme_asked=False, expected_texts=["Zeit (h)", "\x00"], requests=[])

        carry = carry_for(source=MATPLOTLIB, target=SEABORN, plot=plot, pending=None, memory=[])

        assert carry is not None and (carry.theme, carry.expected_texts) == (None, ["Zeit (h)"])

    def test_a_carry_not_run_yet_moves_on_to_the_next_target(self) -> None:
        pending = Carry(source=MATPLOTLIB, target=SEABORN, from_plot=True, theme="dark", requests=["r"])

        carry = carry_for(source=SEABORN, target=PLOTLY, plot=None, pending=pending, memory=[])

        assert carry is not None and carry.source == MATPLOTLIB and carry.target == PLOTLY and carry.theme == "dark"
        assert read_carry({CARRY: carry.model_dump(mode="json")}, PLOTLY.pair()) == carry
        assert read_carry({CARRY: carry.model_dump(mode="json")}, SEABORN.pair()) is None  # made for another pair

    def test_nothing_carries_without_a_plot_a_pending_carry_or_memory(self) -> None:
        assert carry_for(source=MATPLOTLIB, target=SEABORN, plot=None, pending=None, memory=[]) is None

    def test_the_offer_needs_something_to_carry_and_a_target_that_misses_it(self) -> None:
        carry = Carry(source=MATPLOTLIB, target=SEABORN, from_plot=True)
        held = entries(LINE, turn=4)

        assert summary(carry, held, None).offer  # no plot in the target yet
        assert summary(carry, held, 3).body() == {
            "decisions": 1,
            "newer": 1,
            "target_has_plot": True,
            "from_plot": True,
            "offer": True,
        }
        assert not summary(carry, held, 4).offer  # the target's plot already has every decision
        assert not summary(None, [], None).offer


# --- Turns through /v1 ----------------------------------------------------------------------


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


KEEP_PLAN: dict[str, Any] = {"edits": [], "title": "Exam Score by Study Hours", "changes": ["Kept the plot"]}
CHANGE = {
    "change_request": "add a horizontal reference line at y = 7 and label the x axis 'Zeit (h)'",
    "base": "previous",
    "expected_texts": ["Zeit (h)"],
    "remember": [LINE.model_dump(exclude_none=True), LABEL.model_dump(exclude_none=True)],
}


def seaborn_plan() -> dict[str, Any]:
    """An adaptation of seaborn's scatter-basic: its generated data block replaced by the user's columns."""
    _, normalised = assess(snapshot_body_model("seaborn"), "seaborn", get_settings())
    start = normalised.index("np.random.seed(42)")
    end = normalised.index("\n", normalised.index("df = pd.DataFrame(", start))
    replace = (
        "df = load_user_data()\n"
        'marketing_spend = df["Study Hours"].to_numpy(dtype=float)\n'
        'sales_revenue = df["Exam Score"].to_numpy(dtype=float)\n'
        'df = pd.DataFrame({"Marketing Spend ($ thousands)": marketing_spend, '
        '"Quarterly Revenue ($ thousands)": sales_revenue})'
    )
    return {"edits": [{"find": normalised[start:end], "replace": replace}], "changes": ["Used your columns"]}


def snapshot_body_model(library: str) -> Any:
    from agents.anyplot.dev_fixture import snapshot_from_repo

    return snapshot_from_repo("scatter-basic", library)


async def say(client: httpx.AsyncClient, sid: str, body: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json=body)
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


async def switch(client: httpx.AsyncClient, sid: str, library: str, **extra: Any) -> httpx.Response:
    body = {"library": library, "snapshot": snapshot_body(library=library), **extra}
    return await client.post(f"/v1/sessions/{sid}/library", headers=HEADERS, json=body)


async def seed_memory(sid: str, held: list[MemoryEntry]) -> None:
    runtime = app.dependency_overrides[get_runtime]()
    seq = max((int(entry.id[1:]) for entry in held), default=0) + 1
    await runtime.write_state(await runtime.session(USER, sid), memory_delta(held, seq))


def plot_of(events: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    return next(data for name, data in events if name == "plot")


async def test_a_change_hands_its_decisions_over_and_the_memory_keeps_them_once_it_ships(
    client: httpx.AsyncClient, swap_models
) -> None:
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here it is."},
                {"call": "plot_pipeline", "args": CHANGE},
                {"text": "Line and label added."},
                {"text": "It shows two decisions."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    events = await say(client, sid, {"text": "add a line at 7 and call the x axis 'Zeit (h)'"})

    # The fake render draws no 'Zeit (h)', so the plot ships with that note: shipped all the same.
    assert plot_of(events)["status"] == "needs_attention"
    change = adapter_inputs(fake)[1]
    assert DECISIONS_HEADING in change and EARLIER_REQUESTS_HEADING not in change  # what stands once it ships
    assert LINE.text in change and LABEL.text in change
    memory = (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json()
    assert memory["max_entries"] == MAX_ENTRIES
    assert [
        (entry["id"], entry["kind"], entry["target"], entry["expect"], entry["turn"]) for entry in memory["entries"]
    ] == [("m1", "reference_line", None, None, 2), ("m2", "axis_label", "x", "Zeit (h)", 2)]
    version = get_services().versions.latest_rendered(sid)
    assert version is not None and (version.spec_id, version.library, version.turn) == (
        "scatter-basic",
        "matplotlib",
        2,
    )
    assert version.expected_texts == ["Zeit (h)"]

    await say(client, sid, {"text": "what do you keep for me?"})
    system = json.dumps([request.config.system_instruction for request in fake.requests][-1], default=str)
    assert "Plot memory: 2 entries" in system and "m2 axis_label/x: x-axis label: 'Zeit (h)'" in system


async def test_a_change_that_ships_nothing_is_never_remembered(client: httpx.AsyncClient, swap_models) -> None:
    broken = {"edits": [{"find": "no such line", "replace": "x"}], "changes": ["Tried"]}
    swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": CHANGE},
            ]
            + [{"text": "That failed."}],
            "adapter": [{"json": SCATTER_PLAN}] + [{"json": broken}] * 6,
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    events = await say(client, sid, {"text": "add a line at 7"})

    assert plot_of(events)["status"] == "failed"
    assert (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json()["entries"] == []


async def test_the_switch_carries_the_memory_and_the_theme_into_the_new_library(
    client: httpx.AsyncClient, swap_models, backend: FakeBackend, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {"theme": "dark"}},
                {"text": "Dark plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "The plot in seaborn, with your decisions."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": seaborn_plan()}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(*OWNER_EXAMPLES, turn=1))

    switched = await switch(client, sid, "seaborn")

    assert switched.status_code == 200, switched.text
    assert switched.json()["target"] == {"spec_id": "scatter-basic", "library": "seaborn"}
    assert switched.json()["carry"] == {
        "decisions": 5,
        "newer": 5,
        "target_has_plot": False,
        "from_plot": True,
        "offer": True,
    }
    state = await _session_state(client, sid)
    assert state[CARRY]["theme"] == "dark" and state[CARRY]["expected_texts"] == ["Zeit (h)"]
    assert len(read_memory(state)) == 5  # the memory stays

    events = await say(client, sid, {"action": "carry_plot"})

    plot = plot_of(events)
    assert (plot["status"], plot["version"]) == ("needs_attention", 2), plot
    # The carried label went to the render's check: the fake render draws no texts, so the check says so.
    assert any("the requested texts could not be checked" in line for line in plot["residual_defects"])
    carried = adapter_inputs(fake)[1]
    assert "Library: seaborn" in carried and "sns." in carried  # the new library's catalogue code, no previous
    assert DECISIONS_HEADING in carried and all(item.text in carried for item in OWNER_EXAMPLES)
    assert EXPECTED_HEADING in carried and "Zeit (h)" in carried
    assert backend.jobs[-1].themes == ("dark",)  # the theme the user asked for in matplotlib
    version = get_services().versions.latest_rendered(sid, target=("scatter-basic", "seaborn"))
    assert version is not None and version.expected_texts == ["Zeit (h)"] and version.theme_asked
    state = await _session_state(client, sid)
    assert state.get(CARRY) is None and len(read_memory(state)) == 5  # taken; the memory goes on
    switch_line = next(line for line in telemetry_lines(caplog) if line["event"] == "plot_switch")
    assert switch_line["memory_kinds"] == kind_counts(entries(*OWNER_EXAMPLES))
    assert (switch_line["carried_count"], switch_line["offered"], switch_line["switch_source"]) == (5, True, "menu")
    runs = [line for line in telemetry_lines(caplog) if line["event"] == "pipeline_run"]
    assert [(run["carried"], run["fresh"], run["memory_entries"]) for run in runs] == [
        (False, True, 0),  # the first `.create_plot()`
        (True, False, 5),
    ]


async def test_start_over_is_fresh_and_starts_the_memory_over(client: httpx.AsyncClient, swap_models) -> None:
    fake = swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}] * 2,
            "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(LINE, STARS))

    events = await create_plot(client, sid)  # `.start_over()` sends the same action

    assert plot_of(events)["status"] == "ok"
    assert DECISIONS_HEADING not in adapter_inputs(fake)[1]
    state = await _session_state(client, sid)
    assert state[MEMORY] == [] and state[MEMORY_SEQ] == 3  # emptied; the ids go on


async def test_start_over_stays_fresh_when_the_root_asks_for_the_previous_version(
    client: httpx.AsyncClient, swap_models
) -> None:
    """`create_plot` is the catalogue plot whatever `base` the root passes (Flash review, 2026-11-02)."""
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": {"base": "previous"}},
                {"text": "Here again."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(LINE))

    events = await create_plot(client, sid)

    assert plot_of(events)["status"] == "ok"  # SCATTER_PLAN applies to the catalogue code only
    assert DECISIONS_HEADING not in adapter_inputs(fake)[1]
    assert (await _session_state(client, sid))[MEMORY] == []


async def test_a_note_of_decisions_alone_is_kept_for_the_first_plot() -> None:
    from agents.anyplot.pipeline import hold_request, settle_pending_request, take_pending_request
    from agents.anyplot.schemas import KeepRequestArgs

    state: dict[str, Any] = {}
    kept = KeepRequestArgs(remember=[LINE])  # no request text: still something to keep
    hold_request(state, PipelineArgs(**kept.model_dump()))
    assert state[PENDING_REMEMBER] == [LINE.model_dump(mode="json")]

    taken = take_pending_request(state, PipelineArgs())
    assert taken.remember == [LINE]
    settle_pending_request(state, taken, shipped=False)  # a failed first plot keeps it
    assert state[PENDING_REMEMBER] == [LINE.model_dump(mode="json")]
    settle_pending_request(state, taken, shipped=True)
    assert state[PENDING_REMEMBER] is None


async def test_a_carry_run_that_ships_nothing_keeps_the_carry(client: httpx.AsyncClient, swap_models) -> None:
    broken = {"edits": [{"find": "no such line", "replace": "x"}], "changes": ["Tried"]}
    swap_models(
        "gemini",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}] * 2,
            "adapter": [{"json": SCATTER_PLAN}] + [{"json": broken}] * 6,
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(sid, entries(LINE, LABEL))
    assert (await switch(client, sid, "seaborn")).status_code == 200

    events = await say(client, sid, {"action": "carry_plot"})

    assert plot_of(events)["status"] == "failed"
    state = await _session_state(client, sid)
    assert read_carry(state, ("scatter-basic", "seaborn")) is not None and len(read_memory(state)) == 2
    # The carried label fed the run's checks only: it never became a text of the user's kept note (Copilot on #12520).
    assert state.get(PENDING_EXPECTED_TEXTS) is None and state.get(PENDING_REQUEST) is None


async def test_switching_back_counts_the_decisions_the_older_plot_misses(
    client: httpx.AsyncClient, swap_models
) -> None:
    swap_models(
        "gemini",
        {"root": [{"call": "plot_pipeline", "args": {}}, {"text": "Here."}]}
        | {"adapter": [{"json": SCATTER_PLAN}], "reviewer": [{"json": VERDICT_OK}]},
    )
    sid = await open_session(client)
    await create_plot(client, sid)  # matplotlib's version 1, turn 1
    assert (await switch(client, sid, "seaborn")).status_code == 200

    await seed_memory(sid, entries(LINE, turn=1))
    back = await switch(client, sid, "matplotlib")
    assert back.json()["carry"]["newer"] == 0 and not back.json()["carry"]["offer"]  # its plot is current

    assert (await switch(client, sid, "seaborn")).status_code == 200
    await seed_memory(sid, [*entries(LINE, turn=1), *plan([], [STARS], seq=2, turn=3).entries])
    back = await switch(client, sid, "matplotlib")
    assert back.json()["carry"] == {
        "decisions": 2,
        "newer": 1,
        "target_has_plot": True,
        "from_plot": True,  # the carry seaborn never ran moved on, with matplotlib's plot behind it
        "offer": True,
    }


async def test_another_spec_stays_refused_until_the_plot_type_switch(client: httpx.AsyncClient) -> None:
    sid = await open_session(client)
    body = {"library": "matplotlib", "snapshot": snapshot_body(spec_id="bar-basic")}

    response = await client.post(f"/v1/sessions/{sid}/library", headers=HEADERS, json=body)

    assert response.status_code == 422 and response.json()["detail"] == "invalid"


async def test_the_page_lists_and_removes_entries(client: httpx.AsyncClient, runtime: Runtime) -> None:
    sid = await open_session(client)
    assert (await client.get(f"/v1/sessions/{sid}/memory", headers=HEADERS)).json() == {
        "entries": [],
        "max_entries": MAX_ENTRIES,
    }
    await seed_memory(sid, entries(LINE, STARS))

    removed = await client.delete(f"/v1/sessions/{sid}/memory/m1", headers=HEADERS)

    assert removed.status_code == 200
    assert [entry["id"] for entry in removed.json()["entries"]] == ["m2"]
    assert (await client.delete(f"/v1/sessions/{sid}/memory/m1", headers=HEADERS)).status_code == 404
    assert (await client.delete(f"/v1/sessions/{sid}/memory/x1", headers=HEADERS)).status_code == 422
    runtime.active[sid] = ActiveRun(abort=asyncio.Event(), user=USER, started=runtime.now())  # a turn in flight
    try:
        assert (await client.delete(f"/v1/sessions/{sid}/memory/m2", headers=HEADERS)).status_code == 409
    finally:
        runtime.active.pop(sid, None)


async def test_forget_removes_an_entry_before_the_run(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", {"root": [{"call": "forget", "args": {"entry_id": "m1"}}, {"text": "Forgotten."}]})
    sid = await open_session(client)
    await seed_memory(sid, entries(LINE, STARS))

    await say(client, sid, {"text": "no reference line after all"})

    assert [entry.id for entry in read_memory(await _session_state(client, sid))] == ["m2"]


async def test_a_kept_first_plot_note_brings_its_decisions_to_the_memory(
    client: httpx.AsyncClient, swap_models
) -> None:
    swap_models(
        "gemini",
        {
            "root": [
                {
                    "call": "keep_plot_request",
                    "args": {
                        "change_request": "title 'Lernzeit'",
                        "expected_texts": ["Lernzeit"],
                        "remember": [{"kind": "title", "text": "title: 'Lernzeit'", "expected_text": "Lernzeit"}],
                    },
                },
                {"text": "Kept for the first plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await say(client, sid, {"text": "Titel 'Lernzeit' bitte"})
    assert (await _session_state(client, sid))[PENDING_REMEMBER] == [
        {"kind": "title", "text": "title: 'Lernzeit'", "target": None, "expected_text": "Lernzeit", "replaces": None}
    ]

    await create_plot(client, sid)

    state = await _session_state(client, sid)
    assert [(entry.kind, entry.expect) for entry in read_memory(state)] == [("title", "Lernzeit")]
    assert state[PENDING_REMEMBER] is None


async def test_the_bundle_names_each_versions_spec_and_library(client: httpx.AsyncClient, swap_models) -> None:
    from .fakes import default_script

    swap_models("gemini", default_script())
    sid = await open_session(client)
    await create_plot(client, sid)

    bundle = (await client.get(f"/v1/sessions/{sid}/bundle", headers=HEADERS)).json()

    assert [(item["spec_id"], item["library"]) for item in bundle["versions"]] == [("scatter-basic", "matplotlib")]


def test_a_full_memory_is_reported_on_the_result() -> None:
    result = PlotResult(status="ok", attempts=1, artifacts=["plot.py"], memory_full=True)
    assert result.memory_full is True
    assert PipelineArgs(remember=OWNER_EXAMPLES).remember == OWNER_EXAMPLES
    with pytest.raises(ValueError):
        PipelineArgs(remember=[*OWNER_EXAMPLES, LINE])  # at most five per run


def test_a_version_is_filed_under_its_pair() -> None:
    version = CodeVersion(
        number=1,
        working="w",
        run_form="r",
        export="e",
        data_csv="a\n1\n",
        render_id="r1",
        result=PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
        library="seaborn",
        spec_id="scatter-basic",
    )
    assert version.target == ("scatter-basic", "seaborn")


def telemetry_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
