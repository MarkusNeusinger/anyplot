"""The marks of a turn that changed the table (`agents/anyplot/turn_marks.py`): what it did to the plot's roles.

The prep eval's `de-tagesmittel-pro-sensor` asked for a daily mean of the temperature on a plot of humidity against
temperature, and in one run of five the root also turned the dates into days since the first one and put that column
on x and the temperature on y. The page learned the new bindings silently from the turn's `done`. The server now
names every role such a turn reassigned, as a line after the turn's change lines, and counts the marks' codes in the
`chat_turn` telemetry line; it blocks nothing, and the root reads none of it. The unit tests drive `turn_marks` on
facts; the flow tests drive whole turns through the `/v1` routes with scripted models.
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, get_args

import httpx
import pytest

from agents.anyplot import pipeline, telemetry, turn_marks
from agents.anyplot.plugins.ledger import RequestLedger, ToolCall
from agents.anyplot.plugins.tool_safety import DATA_CODE_TOOL, GENERATE_TOOL
from agents.anyplot.schemas import MAX_COLUMN_NAME_CHARS, MAX_NOTE_CHARS, Binding
from agents.anyplot.services import Services
from agents.anyplot.session_state import SUMMARY_PENDING, confirmation_fingerprint, read_session
from agents.anyplot.tools.session import DATA_CODE_CHANGE, EXAMPLE_DATA_CHANGE
from agents.anyplot.turn_marks import RoleMark, TableFacts, mark_codes, table_facts
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_data_code_tool import SNIPPET
from .test_paste_conversions import SID, block_now, open_spec, paste, pasted, say
from .test_service_flow import HEADERS, SINE_LINE, USER, _session_state, generate_call, permissive_queue, prepare_call


def facts(dataset_id: str, columns: str, **bindings: str) -> TableFacts:
    """The facts of version `dataset_id` with the comma-separated `columns` and `bindings` as role=column."""
    return TableFacts(dataset_id, frozenset(columns.split(",")), tuple(bindings.items()))


def marks(start: TableFacts | None, end: TableFacts | None) -> list[tuple[tuple[str, ...], str]]:
    return [(mark.codes, mark.line) for mark in turn_marks.turn_marks(start, end)]


class TestTheMarks:
    def test_a_role_that_takes_a_column_the_table_had_is_moved(self) -> None:
        start = facts("v1", "Day,Temp,Humid", x="Temp", y="Humid")

        found = marks(start, facts("v2", "Day,Temp,Humid", x="Temp", y="Day"))

        assert found == [(("axis_moved",), "y takes 'Day' instead of 'Humid'")]

    def test_an_open_role_that_takes_a_column_the_table_had_is_filled(self) -> None:
        start = facts("v1", "Name,Score,Hours", x="Score")

        found = marks(start, facts("v2", "Name,Score,Hours", x="Score", y="Hours"))

        assert found == [(("axis_filled",), "y takes 'Hours'")]

    def test_an_open_role_that_takes_a_column_the_turn_made_is_a_new_column_bound(self) -> None:
        start = facts("v1", "Name,Score", x="Score")

        found = marks(start, facts("v2", "Name,Score,index", x="Score", y="index"))

        assert found == [(("new_column_bound",), "y takes the new column 'index'")]

    def test_a_role_that_moved_to_a_new_column_gets_one_line_that_says_both(self) -> None:
        start = facts("v1", "Time,Temp,Humid", x="Temp", y="Humid")

        found = marks(start, facts("v2", "Time,Temp,Humid,Day", x="Day", y="Temp"))

        assert found == [
            (("axis_moved", "new_column_bound"), "x takes the new column 'Day' instead of 'Temp'"),
            (("axis_moved",), "y takes 'Temp' instead of 'Humid'"),
        ]

    def test_a_role_that_lost_its_column_with_nothing_in_its_place(self) -> None:
        start = facts("v1", "Name,Hours,Score", x="Hours", y="Score")

        found = marks(start, facts("v2", "Name,Hours,Score", x="Hours"))

        assert found == [(("axis_moved",), "y lost its column 'Score' and holds none now")]

    def test_two_roles_that_swapped_their_columns(self) -> None:
        start = facts("v1", "Hours,Score", x="Hours", y="Score")

        found = marks(start, facts("v2", "Hours,Score", x="Score", y="Hours"))

        assert found == [
            (("axis_moved",), "x takes 'Score' instead of 'Hours'"),
            (("axis_moved",), "y takes 'Hours' instead of 'Score'"),
        ]

    def test_a_changed_table_that_leaves_the_roles_alone_has_none(self) -> None:
        start = facts("v1", "Hours,Score", x="Hours", y="Score")

        assert marks(start, facts("v2", "Hours,Score,Rank", x="Hours", y="Score")) == []

    def test_a_turn_that_changed_no_table_has_none_whatever_its_bindings_did(self) -> None:
        """A turn that only re-binds keeps its version: no line, even for a role that moved."""
        start = facts("v1", "Hours,Score", x="Hours", y="Score")

        assert marks(start, facts("v1", "Hours,Score", x="Score", y="Hours")) == []

    def test_a_turn_in_which_a_step_replaced_the_data_has_none_whatever_else_it_did(self) -> None:
        """A new table puts its own columns on every role: the step's change line says so, a mark would repeat it. A
        replacing call that stored nothing replaced nothing, and a change of the table is marked as before."""
        start = facts("v1", "Hours,Score", x="Hours", y="Score")
        end = facts("v3", "x,y", x="x", y="y")
        moved = marks(start, end)

        for tool in turn_marks.REPLACING_TOOLS:
            assert turn_marks.turn_marks(start, end, [ToolCall(tool, outcome="changed")]) == []
            assert len(turn_marks.turn_marks(start, end, [ToolCall(tool, outcome="error")])) == len(moved) == 2
        prepared = [ToolCall("prepare_data", outcome="changed"), ToolCall("set_bindings", outcome="changed")]
        assert len(turn_marks.turn_marks(start, end, prepared)) == 2

    def test_the_replacing_tools_are_the_tools_that_store_a_new_table(self) -> None:
        assert turn_marks.REPLACING_TOOLS == {GENERATE_TOOL, DATA_CODE_TOOL}
        assert turn_marks.REPLACING_TOOLS < telemetry.TOOL_NAMES

    def test_a_turn_without_a_table_at_either_end_has_none(self) -> None:
        """No role held a column it could have moved: the first table's bindings are the defaults the card shows."""
        end = facts("v1", "x,y", x="x", y="y")

        assert marks(None, end) == []
        assert marks(end, None) == []

    def test_a_renamed_column_is_still_itself_and_a_new_column_under_its_old_name_is_new(self) -> None:
        start = facts("v1", "Hours,Score", x="Hours", y="Score").renamed(
            lambda name: "Points" if name == "Score" else name
        )

        assert marks(start, facts("v2", "Hours,Points", x="Hours", y="Points")) == []
        moved = marks(start, facts("v2", "Hours,Points,Score", x="Hours", y="Score"))
        assert moved == [(("axis_moved", "new_column_bound"), "y takes the new column 'Score' instead of 'Points'")]

    def test_the_lines_follow_the_start_roles_then_the_new_ones(self) -> None:
        start = facts("v1", "a,b,c", y="b", x="a")

        found = marks(start, facts("v2", "a,b,c,d", x="c", size="d"))

        assert [line for _, line in found] == [
            "y lost its column 'b' and holds none now",
            "x takes 'c' instead of 'a'",
            "size takes the new column 'd'",
        ]

    def test_a_line_fits_a_change_line_and_is_cut_like_one(self) -> None:
        """At the schema's caps (a role of 32 characters, column names of 64) a line stays whole within the change
        lines' cap; a longer one is cut as theirs are, so the `done` event's bound holds whatever reaches here."""
        old, new = "o" * MAX_COLUMN_NAME_CHARS, "n" * MAX_COLUMN_NAME_CHARS
        start = facts("v1", old, **{"r" * 32: old})

        (found,) = turn_marks.turn_marks(start, facts("v2", new, **{"r" * 32: new}))
        (cut,) = turn_marks.turn_marks(facts("v1", old, **{"r" * 300: old}), facts("v2", new, **{"r" * 300: new}))

        assert found.line == f"{'r' * 32} takes the new column '{new}' instead of '{old}'"
        assert len(found.line) < MAX_NOTE_CHARS
        assert len(cut.line) == MAX_NOTE_CHARS and cut.line.endswith("…")

    def test_the_codes_are_distinct_and_sorted(self) -> None:
        both = RoleMark(("axis_moved", "new_column_bound"), "x")
        moved = RoleMark(("axis_moved",), "y")
        filled = RoleMark(("axis_filled",), "size")

        assert mark_codes([moved, both, filled]) == ["axis_filled", "axis_moved", "new_column_bound"]
        assert mark_codes([]) == []

    def test_the_telemetry_codes_are_the_marks(self) -> None:
        assert get_args(telemetry.TurnMark) == get_args(turn_marks.TurnMark)
        assert telemetry.TURN_MARKS == {code for code, _ in turn_marks.MARKS}


HOURS = "Student,Study Hours,Exam Score\n" + "".join(f"S{i:02d},{2 + 2 * (i % 4)},{50 + 3 * i}\n" for i in range(12))
"""12 invented students over 4 study hours, three per hour, so a line plot's key repeats."""


LINE_BOUND = [Binding(role="x", column="Study Hours"), Binding(role="y", column="Exam Score")]
MOVED_Y = [LINE_BOUND[0], Binding(role="y", column="Student")]
"""The bindings a turn began with when it moved y onto the scores before the plot run."""


def combined(*, after_a_data_step: bool) -> tuple[RequestLedger, TableFacts, TableFacts]:
    """A plot run that combines the repeated hours of a confirmed `line-basic` table, in a turn that began with y on
    another column (`MOVED_Y`): on the version the run combines, or on a version before a data step of the root's own.
    The ledger after the step, the turn's start, and the facts of the version the step left."""
    store, view = pasted(HOURS, "line-basic")
    view = replace(view, bindings=LINE_BOUND, confirmed=confirmation_fingerprint(view.dataset_id, LINE_BOUND))
    dataset = store.get(view.dataset_id, SID)
    assert dataset is not None
    start = table_facts("before the root's step" if after_a_data_step else view.dataset_id, dataset.profile, MOVED_Y)
    ledger = RequestLedger(marks_from=start)
    ctx = SimpleNamespace(state={}, session=SimpleNamespace(id=SID))

    _, drawn, line = pipeline._combine_repeated_key(
        ctx,  # type: ignore[arg-type]
        SimpleNamespace(datasets=store),  # type: ignore[arg-type]
        view,
        dataset,
        ledger,
        "mean",
    )

    assert line is not None and drawn.dataset_id != view.dataset_id
    return ledger, start, table_facts(drawn.dataset_id, drawn.profile, LINE_BOUND)  # the combine keeps the bindings


def test_a_combined_key_moves_the_start_past_the_servers_step() -> None:
    """A plot run's combined key is the server's own step, announced with the plot: the turn's marks start from the
    version it left, so what the turn did to the roles before it (a narrowing `set_bindings`) is not marked."""
    ledger, start, end = combined(after_a_data_step=False)

    assert ledger.marks_from == end
    assert turn_marks.turn_marks(ledger.marks_from, end) == []
    assert turn_marks.turn_marks(start, end) != []  # what the turn's start alone would have marked


def test_a_combined_key_after_a_data_step_of_the_roots_keeps_that_steps_marks() -> None:
    """The other order: the root changed the table and moved y, then a plot run combined a key. No route reaches it
    today: a version the turn stored is unconfirmed, a combine needs confirmed data, and ToolSafety refuses a plot
    after a data step of the turn. Built here, the start stays where the root's steps began, and their marks stay."""
    ledger, start, end = combined(after_a_data_step=True)

    assert ledger.marks_from == start
    assert marks(ledger.marks_from, end) == [(("axis_moved",), "y takes 'Exam Score' instead of 'Student'")]


# --- Whole turns -------------------------------------------------------------------------------------------------


TIME, STATION, TEMP, HUMID, DAYS = "Reading time", "Station", "Air temp", "Rel humidity", "Day no"
"""Invented column names of a table of timed readings, and the name of the date number the root makes."""
READINGS = f"{TIME},{STATION},{TEMP},{HUMID}\n" + "".join(
    f"2026-03-{day:02d} {hour:02d}:00,{station},{10 + day + hour / 10 + index},{60 + 2 * day - index}\n"
    for day in (1, 2, 3)
    for index, station in enumerate(("North", "South"))
    for hour in (8, 16)
)
"""Two stations, two readings a day for three days: humidity against temperature on `scatter-basic`."""
DAILY_MEAN = {"op": "aggregate", "by": [TIME, STATION], "columns": [TEMP, HUMID], "how": "mean", "period": "day"}
DAY_NUMBERS = {"op": "date_number", "column": TIME, "unit": "days", "name": DAYS}


def bind_call(**roles: str) -> dict[str, Any]:
    """The root's `set_bindings` call with `roles` as role=column."""
    return {"call": "set_bindings", "args": {"bindings": [{"role": r, "column": c} for r, c in roles.items()]}}


REBIND = bind_call(x=DAYS, y=TEMP)
OBSERVED_MARKS = [f"x takes the new column '{DAYS}' instead of '{TEMP}'", f"y takes '{TEMP}' instead of '{HUMID}'"]


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


def chat_turns(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
    return [line for line in lines if line["event"] == "chat_turn"]


async def readings_session(client: httpx.AsyncClient, runtime: Runtime, **roles: str) -> str:
    """A `scatter-basic` session on the readings, its paste summarized, bound as `roles` say (role=column) or, without
    them, humidity against temperature."""
    sid = await open_spec(client, "scatter-basic")
    await paste(client, sid, READINGS)
    await runtime.write_state(await runtime.session(USER, sid), {SUMMARY_PENDING: None})
    bindings = [{"role": role, "column": column} for role, column in (roles or {"x": TEMP, "y": HUMID}).items()]
    bound = await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=bindings)
    assert bound.status_code == 200, bound.text
    return sid


async def test_the_observed_turn_ends_with_a_line_per_moved_role_after_its_own_change_lines(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The eval's case: a daily mean, the dates as days since the first one, x and y reassigned. The page shows a line
    per role after the data step's own; the telemetry counts the codes alone; the root reads none of it."""
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [prepare_call(DAILY_MEAN, DAY_NUMBERS), REBIND, {"text": "Daily means per station."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime)

    events = await say(client, sid, {"text": "the daily mean of the temperature per station"})

    name, done = events[-1]
    assert name == "done" and done["bindings"] == [{"role": "x", "column": DAYS}, {"role": "y", "column": TEMP}]
    steps, lines = done["dataset"]["changes"][:-2], done["dataset"]["changes"][-2:]
    assert lines == OBSERVED_MARKS
    assert len(steps) == 2 and steps[0].startswith("averaged") and steps[1].startswith(f"new column {DAYS}:")
    # Only the page reads the lines: the version keeps the data step's own, and the session block of the next turn,
    # which lists each version with its change lines, holds none of the marks.
    view = read_session(await _session_state(client, sid))
    stored = services.datasets.get(view.dataset_id, sid) if view is not None and view.dataset_id else None
    assert stored is not None and stored.changes == steps
    block = await block_now(client, sid)
    assert steps[0] in block and all(line not in block for line in OBSERVED_MARKS)
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == ["axis_moved", "new_column_bound"]
    assert all(name not in json.dumps(turn) for name in (TIME, STATION, TEMP, HUMID, DAYS))


async def test_a_data_turn_that_leaves_the_roles_alone_has_no_mark(
    client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [prepare_call({"op": "sort", "column": TEMP}), {"text": "Sorted."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime)

    events = await say(client, sid, {"text": "sort by temperature"})

    assert events[-1][1]["dataset"]["changes"] == [f"sorted by {TEMP}, ascending"]
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == []


async def test_an_open_axis_the_turn_filled_with_a_column_the_table_had_is_marked(
    client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """y was open; the turn sorted the table and put the humidity, there all along, on it: a reassignment too."""
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [prepare_call({"op": "sort", "column": TEMP}), bind_call(x=TEMP, y=HUMID), {"text": "Sorted."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime, x=TEMP)

    events = await say(client, sid, {"text": "sort by temperature"})

    name, done = events[-1]
    assert name == "done" and done["bindings"] == [{"role": "x", "column": TEMP}, {"role": "y", "column": HUMID}]
    assert done["dataset"]["changes"] == [f"sorted by {TEMP}, ascending", f"y takes '{HUMID}'"]
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == ["axis_filled"]


async def test_a_turn_that_only_re_binds_has_no_dataset_and_no_mark(
    client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The table is the same version at both ends: the roles moved, but no data step of the turn moved them."""
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [bind_call(x=HUMID, y=TEMP), {"text": "Swapped the axes."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime)

    events = await say(client, sid, {"text": "swap the axes"})

    name, done = events[-1]
    assert name == "done" and "dataset" not in done
    assert done["bindings"] == [{"role": "x", "column": HUMID}, {"role": "y", "column": TEMP}]
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == []


async def test_a_formula_over_a_paste_replaced_the_table_and_has_no_mark_whatever_else_the_turn_did(
    client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The generated table puts its own columns on both roles, and the turn swaps them after: its change line says the
    table is new, and no line repeats it for each role."""
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [generate_call(("y", "sin(x)")), bind_call(x="y", y="x"), {"text": "A sine, axes swapped."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime)

    events = await say(client, sid, {"text": "plot a sine instead, with the axes swapped"})

    name, done = events[-1]
    assert name == "done" and done["bindings"] == [{"role": "x", "column": "y"}, {"role": "y", "column": "x"}]
    assert done["dataset"]["changes"] == [SINE_LINE]
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == []


@pytest.mark.parametrize(("source", "change"), [("python", DATA_CODE_CHANGE), ("example", EXAMPLE_DATA_CHANGE)])
async def test_a_table_computed_from_code_over_a_paste_replaced_it_and_has_no_mark(
    client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture, source: str, change: str
) -> None:
    """The user's code, or example data, makes a new table with its own columns on both roles: no line per role."""
    caplog.set_level(logging.INFO)
    script = default_script()
    run = {"call": "run_data_code", "args": {"code": SNIPPET, "source_language": source}}
    script["root"] = [run, {"text": "4 rows, 2 columns from the code."}]
    swap_models("anthropic-vertex", script)
    sid = await readings_session(client, runtime)

    events = await say(client, sid, {"text": "use this code for the data instead"})

    name, done = events[-1]
    assert name == "done" and done["bindings"] == [{"role": "x", "column": "x"}, {"role": "y", "column": "y"}]
    assert done["dataset"]["changes"] == [f"{change}: 4 rows, 2 columns"]
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == []


ONE_COLUMN = "value\n1\n3\n5\n4\n6\n2\n"
"""`line-basic`'s x open beside one number column: the summary turn's server makes the row numbers for it."""


async def test_the_servers_own_row_numbers_on_the_summary_turn_get_no_mark(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    script = default_script()
    script["root"] = [{"text": "6 rows; x takes the new row numbers in index."}]
    swap_models("anthropic-vertex", script)
    sid = await open_spec(client, "line-basic")
    await paste(client, sid, ONE_COLUMN)

    events = await say(client, sid, {"action": "summarize_data"})

    name, done = events[-1]
    assert name == "done" and done["bindings"] == [{"role": "x", "column": "index"}, {"role": "y", "column": "value"}]
    (server,) = done["dataset"]["changes"]
    assert server.startswith("new first column index")
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == []


async def test_a_root_step_after_the_servers_conversions_is_marked_against_what_they_left(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The server bound its row numbers to x; the root then made a column and put it on y. Only the root's step is
    marked, and against the table the server's step left, so x, which held nothing at the paste, gets no line."""
    caplog.set_level(logging.INFO)
    double = {"op": "compute", "name": "double", "expression": "v * 2", "inputs": {"v": "value"}}
    script = default_script()
    script["root"] = [prepare_call(double), bind_call(x="index", y="double"), {"text": "6 rows; y doubled."}]
    swap_models("anthropic-vertex", script)
    sid = await open_spec(client, "line-basic")
    await paste(client, sid, ONE_COLUMN)

    events = await say(client, sid, {"action": "summarize_data"})

    changes = events[-1][1]["dataset"]["changes"]
    assert len(changes) == 3 and changes[0].startswith("new first column index")
    assert changes[1].startswith("added column double:")
    assert changes[2] == "y takes the new column 'double' instead of 'value'"
    (turn,) = chat_turns(caplog)
    assert turn["turn_marks"] == ["axis_moved", "new_column_bound"]
