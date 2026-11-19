"""The guard on a role the turn's own change of the data left without its column (`data/emptied.py`).

The prep eval's `de-tagesmittel-pro-sensor`: the daily mean of the temperature per sensor drops the humidity, so the
scatter plot's y axis loses its column and no column is left for it. The root then added the timestamps as days since
the first date, which nobody asked for, and the column landed on an axis. With the guard no date turned into numbers
and no row number made in that turn lands on a role, whichever way it comes in (the same data step, a second one, a
binding call), the table keeps only what was asked for, the session block names the role that lost its column, and
the next turn lists what the server can compute for it. A refused call costs none of the turn's two data steps, and a
column the request derives or converts from text itself still takes the axis it names.
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import CONVERSIONS_HEADING, EMPTIED_HEADING
from agents.anyplot.data.emptied import ADDING_OPS
from agents.anyplot.plugins.ledger import ledger_for
from agents.anyplot.render.contract import DataOutput
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import DATASET_ID, SUMMARY_PENDING, read_session
from agents.anyplot.tools.session import (
    COLUMN_HELD_FILLED_MESSAGE,
    COLUMN_HELD_MESSAGE,
    LOSING_LINE,
    LOST_LINE,
    MADE_BEFORE_LINE,
    MADE_NOW_LINE,
    ROWS_REPLACE_MESSAGE,
    set_bindings,
)
from agents.main import Runtime, app, get_runtime

from .fakes import FakeAnthropic, default_script
from .test_from_version import context_for
from .test_paste_conversions import block_now, open_spec, paste, say
from .test_service_flow import HEADERS, USER, create_plot, permissive_queue, prepare_call


SENSORS = (
    "Zeitpunkt,Sensor,Temperatur,Feuchte\n2026-01-01 00:00,S1,14.9,74.8\n2026-01-01 00:13,S2,15.1,78.0\n"
    "2026-01-01 00:26,S1,14.1,55.9\n2026-01-01 12:39,S2,18.2,61.0\n2026-01-02 00:52,S1,13.4,70.2\n"
    "2026-01-02 09:05,S2,16.8,64.5\n2026-01-02 17:18,S1,17.5,58.1\n2026-01-03 01:31,S2,12.9,80.3\n"
)
"""The prep eval's `de-tagesmittel-pro-sensor` table: on `scatter-basic`, x takes Temperatur and y Feuchte."""
DAILY_MEAN = {"op": "aggregate", "by": ["Zeitpunkt", "Sensor"], "column": "Temperatur", "how": "mean", "period": "day"}
DAYS = {"op": "date_number", "column": "Zeitpunkt", "unit": "days", "name": "Tag"}
ROWS = {"op": "row_number", "name": "index"}
CANDIDATES = CONVERSIONS_HEADING.split("{", 1)[0]
LOST_Y = "<user_data>\ny: Feuchte\n</user_data>"
REPLY = {"text": "Daily mean per sensor: 8 readings became 5 rows. Feuchte is gone, so y has no column now."}
HELD = COLUMN_HELD_MESSAGE.format(roles="y")
"""The guard's refusal for the emptied y, as the root reads it in the call's answer."""
HELD_FILLED = COLUMN_HELD_FILLED_MESSAGE.format(roles="y")
"""The same refusal once y holds a column again: nothing about a role that waits."""
ATTRIBUTION = "anyplot.agents.attribution"
FAHRENHEIT = {"op": "compute", "name": "Fahrenheit", "expression": "t * 1.8 + 32", "inputs": {"t": "Temperatur"}}


def bindings_call(**pairs: str) -> dict[str, Any]:
    return {"call": "set_bindings", "args": {"bindings": [{"role": r, "column": c} for r, c in pairs.items()]}}


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


async def summarized(
    client: httpx.AsyncClient, runtime: Runtime, text: str = SENSORS, spec: str = "scatter-basic"
) -> str:
    """A session of `spec` with `text` pasted and summarized, as the page leaves it after the summary turn."""
    sid = await open_spec(client, spec)
    await paste(client, sid, text)
    await runtime.write_state(await runtime.session(USER, sid), {SUMMARY_PENDING: None})
    return sid


async def outcome(runtime: Runtime, sid: str) -> tuple[dict[str, str], list[str]]:
    """The bindings in force, as role: column, and the columns of the current table."""
    state = (await runtime.session(USER, sid)).state
    view = read_session(state)
    assert view is not None
    stored = get_services().datasets.get(state[DATASET_ID], sid)
    assert stored is not None
    return {b.role: b.column for b in view.bindings}, [column.name for column in stored.profile.columns]


def answers(fake: Any, call: int) -> str:
    """Everything the root's `call`-th request carries in its messages, the tools' answers among them."""
    return json.dumps(fake.calls[call]["messages"], default=str, ensure_ascii=False)


def block_of(fake: Any, call: int) -> str:
    """The session block of the root's `call`-th request."""
    return str(fake.calls[call]["system"][-1]["text"])


GUARD_WORDS = {
    "tool": {"prepare_data", "set_bindings"},
    "outcome": {"refused", "kept_off", "bound", "refilled"},
    "role": {"x", "y"},
    "kind": set(ADDING_OPS),
}
"""Every value an `emptied_role` line may hold on `scatter-basic`: closed words, the spec's role names and operation
names, so no column of the user's can stand in one."""


def guard_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    """The guard's log lines (hook `emptied_role`) the turn wrote, without the envelope every attribution line has,
    each checked to be content-free: every value one of `GUARD_WORDS`."""
    lines = [json.loads(record.getMessage()) for record in caplog.records if record.name == ATTRIBUTION]
    envelope = {"severity", "hook", "request_id", "user", "session", "llm_calls", "tokens"}
    found = [{k: v for k, v in line.items() if k not in envelope} for line in lines if line["hook"] == "emptied_role"]
    for line in found:
        for key, value in line.items():
            words = GUARD_WORDS[key.rstrip("s")]  # `roles` and `kinds` hold lists of the same words
            assert set(value if isinstance(value, list) else [value]) <= words, line
    return found


class TestTheWaysIn:
    async def test_the_same_data_step_stores_nothing_and_the_column_lands_nowhere(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The daily mean and the days since the first date in one call: the carry would bind `Tag` to the y that
        the same call emptied, so the call is refused, whole."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [prepare_call(DAILY_MEAN, DAYS), REPLY]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert "Tag" not in bound.values() and "Tag" not in columns
        refused = answers(fake, 1)
        assert '\\"code\\": \\"invalid_operation\\"' in refused and HELD in refused
        # Nothing was stored, so y still holds Feuchte: the refusal says it would lose it, never that it lost it.
        assert LOSING_LINE.format(role="y", column="Feuchte") in refused and MADE_NOW_LINE.format(name="Tag") in refused
        assert LOST_LINE.format(role="y", column="Feuchte") not in refused
        # One content-free line: the role and the operation, no column of the user's.
        lines = guard_lines(caplog)
        assert lines == [{"tool": "prepare_data", "outcome": "refused", "roles": ["y"], "kinds": ["date_number"]}]
        assert "Feuchte" not in json.dumps(lines) and "Tag" not in json.dumps(lines)

    async def test_a_second_data_step_stores_nothing_and_the_reply_names_the_axis(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        script = default_script()
        script["root"] = [prepare_call(DAILY_MEAN), prepare_call(DAYS), REPLY]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur"} and columns == ["Zeitpunkt", "Sensor", "Temperatur"]
        refused = answers(fake, 2)
        assert HELD in refused and LOST_LINE.format(role="y", column="Feuchte") in refused
        # The facts the reply states: the role that lost its column and that column, for every call after the change.
        for call in (1, 2):
            assert f"- {EMPTIED_HEADING.format(count=1)}\n{LOST_Y}" in block_of(fake, call)
        assert EMPTIED_HEADING.split("{", 1)[0] not in block_of(fake, 0)

    async def test_an_unasked_row_number_through_a_second_step_lands_nowhere(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The row numbers would take x and move Temperatur to the emptied y: no column made in the turn lands on
        any role, not only on the emptied one."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [prepare_call(DAILY_MEAN), prepare_call(ROWS), REPLY]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur"} and "index" not in columns
        assert HELD in answers(fake, 2)
        assert guard_lines(caplog) == [
            {"tool": "prepare_data", "outcome": "refused", "roles": ["y"], "kinds": ["row_number"]}
        ]

    async def test_a_binding_call_never_puts_such_a_column_on_an_axis(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The eval run's order of calls: the change, a binding, the days, a binding that puts them on x. The days are
        refused at the data step, so the binding finds no such column; y holds Temperatur by the root's own binding of
        a column that was there, which the guard leaves alone."""
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN),
            bindings_call(x="Temperatur", y="Temperatur"),
            prepare_call(DAYS),
            bindings_call(x="Tag", y="Temperatur"),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur", "y": "Temperatur"} and "Tag" not in columns

    async def test_a_column_made_before_the_change_that_empties_the_axis_is_kept_off_it(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Made first, while every role was bound, the row numbers take no role; the drop of Feuchte would then let
        the carry put them on y. The drop is the user's change and is stored; the row numbers stay in the table,
        unbound, kept off y, and y waits for the user, as after any change that empties it. A binding that puts them
        on a role in the same turn is still refused, and the next turn offers them."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call(ROWS),
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            bindings_call(x="Temperatur", y="index"),
            REPLY,
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Drop the humidity."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur"} and columns == ["index", "Zeitpunkt", "Sensor", "Temperatur"]
        assert HELD not in answers(fake, 2) and f"- {EMPTIED_HEADING.format(count=1)}\n{LOST_Y}" in block_of(fake, 2)
        refused = answers(fake, 3)
        assert '\\"code\\": \\"invalid_bindings\\"' in refused and MADE_BEFORE_LINE.format(name="index") in refused
        assert guard_lines(caplog) == [
            {"tool": "prepare_data", "outcome": "kept_off", "roles": ["y"], "kinds": ["row_number"]},
            {"tool": "set_bindings", "outcome": "refused", "roles": ["y"], "kinds": ["row_number"]},
        ]
        listed = await block_now(client, sid)
        assert CANDIDATES in listed and '"op": "row_number", "name": "index"' in listed and "takes x" in listed

    async def test_a_drop_that_takes_the_earlier_row_numbers_with_it_keeps_nothing_off(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """With the row numbers dropped too, nothing of the turn's is left that could take y: a plain emptying."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call(ROWS),
            prepare_call({"op": "drop_columns", "columns": ["Feuchte", "index"]}),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Drop the humidity."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur"} and columns == ["Zeitpunkt", "Sensor", "Temperatur"]
        assert guard_lines(caplog) == []

    async def test_the_plot_button_after_such_a_turn_answers_that_y_is_open(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The kept-off column leaves y bound to nothing: confirmed as shown, the plot run stops before the adapter
        with `incomplete_bindings`."""
        script = default_script()
        script["root"] = [
            prepare_call(ROWS),
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            REPLY,
            {"call": "plot_pipeline", "args": {}},
            {"text": "y has no column yet, so no plot was made."},
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)
        await say(client, sid, {"text": "Drop the humidity."})
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200

        events = await create_plot(client, sid)

        assert '\\"reason\\": \\"incomplete_bindings\\"' in answers(fake, len(fake.calls) - 1)
        assert all(FakeAnthropic.kind(call) == "root" for call in fake.calls)  # no adapter, no reviewer
        assert not any(name == "plot" and data.get("status") == "ok" for name, data in events)

    async def test_a_text_column_the_request_converts_and_sums_is_its_own(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The price read from text and summed per region in one call: the aggregate takes both axes' columns and the
        new column fills x, as the request means. A conversion of a text column is no fill the guard holds."""
        prices = "Region,Qty,Weight,Price\nNord,3,1.5,12 Stk à CHF\nSüd,5,2.5,20 Stk à CHF\nNord,2,1.0,8 Stk à CHF\n"
        extract = {"op": "extract", "column": "Price", "keep": "number", "name": "Preis"}
        total = {"op": "aggregate", "by": ["Region"], "column": "Preis", "how": "sum"}
        script = default_script()
        script["root"] = [prepare_call(extract, total), {"text": "Preis summed per region: 2 rows."}]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime, prices)

        await say(client, sid, {"text": "Total price per region, the price is the number in Price."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Preis"} and columns == ["Region", "Preis"]
        assert HELD not in answers(fake, 1)
        # y lost Weight to the aggregate, with nothing left to take it: the block says so.
        assert f"- {EMPTIED_HEADING.format(count=1)}\n<user_data>\ny: Weight\n</user_data>" in block_of(fake, 1)


class TestWhatTheGuardLeaves:
    async def test_a_refused_call_costs_none_of_the_turns_two_data_steps(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """After the refusal the root still makes its two changes: the daily mean, then a rename."""
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN, DAYS),
            prepare_call(DAILY_MEAN),
            prepare_call({"op": "rename", "column": "Sensor", "name": "Fühler"}),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        events = await say(client, sid, {"text": "Tagesmittel pro Sensor, und nenne Sensor Fühler."})

        _, columns = await outcome(runtime, sid)
        assert columns == ["Zeitpunkt", "Fühler", "Temperatur"]
        assert events[-1][1]["dataset"]["version"] == 3

    async def test_the_next_turn_lists_what_the_server_can_compute_and_takes_the_users_pick(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The row numbers first, as a number axis is offered them before any date; the days, asked for in the next turn,
        take y as an offer the user took."""
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN),
            prepare_call(DAYS),
            REPLY,
            prepare_call(DAYS),
            {"text": "Tag holds the days since 2026-01-01 and takes y."},
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)
        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        listed = await block_now(client, sid)
        await say(client, sid, {"text": "Nimm die Tage seit dem ersten Datum für y."})

        assert CANDIDATES in listed and '"op": "row_number"' in listed and "takes x" in listed
        assert CANDIDATES in block_of(fake, 3) and EMPTIED_HEADING.split("{", 1)[0] not in block_of(fake, 3)
        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur", "y": "Tag"} and columns[-1] == "Tag"

    async def test_a_derived_column_the_request_names_takes_the_axis_it_names(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A computed column is the request's own, no conversion: in the turn that emptied y, the root binds it. The
        same calls without the request are the known gap below, so the binding writes its log line either way."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN),
            prepare_call(FAHRENHEIT),
            bindings_call(x="Temperatur", y="Fahrenheit"),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Tagesmittel pro Sensor, und dieselben Werte in Fahrenheit auf y."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur", "y": "Fahrenheit"} and columns[-1] == "Fahrenheit"
        assert guard_lines(caplog) == [{"tool": "set_bindings", "outcome": "bound", "role": "y", "kind": "compute"}]

    async def test_residual_a_date_number_asked_with_the_change_that_empties_the_axis_comes_in_the_next_turn(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """Accepted residual: one message that asks for the daily mean and for the days since the first date reads,
        by the typed records, as the fault. The days wait: the root makes the daily mean alone, and the same request
        in the next turn goes through and takes y, as an offer the user took."""
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN, DAYS),
            prepare_call(DAILY_MEAN),
            {"text": "Daily mean per sensor: 5 rows. y lost Feuchte; the days can be made in the next turn."},
            prepare_call(DAYS),
            {"text": "Tag holds the days since 2026-01-01 and takes y."},
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Tagesmittel pro Sensor, und gib mir die Tage seit Beginn als Spalte."})
        after_first = await outcome(runtime, sid)
        await say(client, sid, {"text": "Gib mir die Tage seit Beginn als Spalte."})

        assert after_first == ({"x": "Temperatur"}, ["Zeitpunkt", "Sensor", "Temperatur"])
        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Tag"},
            ["Zeitpunkt", "Sensor", "Temperatur", "Tag"],
        )


class TestTheReviewedCases:
    async def test_a_column_read_as_dates_and_numbered_in_the_emptying_call_is_held(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """`Zeitpunkt` is text when the turn begins (read as text in an earlier turn); one call reads it as dates,
        turns it into days and drops it with Feuchte. The column is a date only in the middle of the call, so the
        record comes from the operation as it runs: refused, nothing stored, the table as it was."""
        as_text = {"op": "set_type", "column": "Zeitpunkt", "type": "text"}
        as_dates = {"op": "set_type", "column": "Zeitpunkt", "type": "datetime"}
        drop = {"op": "drop_columns", "columns": ["Zeitpunkt", "Feuchte"]}
        script = default_script()
        script["root"] = [
            prepare_call(as_text),
            {"text": "Zeitpunkt is text now."},
            prepare_call(as_dates, DAYS, drop),
            REPLY,
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)
        await say(client, sid, {"text": "Read Zeitpunkt as text."})
        before = await outcome(runtime, sid)

        await say(client, sid, {"text": "Days since the start instead of the time, and drop Feuchte."})

        assert (
            await outcome(runtime, sid)
            == before
            == ({"x": "Temperatur", "y": "Feuchte"}, ["Zeitpunkt", "Sensor", "Temperatur", "Feuchte"])
        )
        refused = answers(fake, 3)
        assert HELD in refused and LOSING_LINE.format(role="y", column="Feuchte") in refused
        assert MADE_NOW_LINE.format(name="Tag") in refused

    async def test_residual_an_asked_row_number_after_the_emptied_role_was_filled_again_waits_a_turn(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """Accepted residual: the turn stays armed after the root put a column that was there on the emptied y, since
        typed records cannot tell that refill from the root's own unasked one, which would let a date number nobody
        asked for into the table. The refusal then says only what holds, nothing of a role that waits; the same call in
        the next turn is stored and lands on no role."""
        rows = prepare_call({"op": "row_number", "name": "RowID"})
        script = default_script()
        script["root"] = [
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            bindings_call(x="Temperatur", y="Temperatur"),
            rows,
            {"text": "Feuchte dropped; RowID can be made in the next turn."},
            rows,
            {"text": "RowID numbers the rows 1 to 8."},
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Drop Feuchte, put Temperatur on y too, and add row numbers as RowID."})
        refused = answers(fake, 3)
        after_first = await outcome(runtime, sid)
        await say(client, sid, {"text": "Add row numbers as RowID."})

        assert HELD_FILLED in refused and HELD not in refused
        assert after_first == ({"x": "Temperatur", "y": "Temperatur"}, ["Zeitpunkt", "Sensor", "Temperatur"])
        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Temperatur"},
            ["RowID", "Zeitpunkt", "Sensor", "Temperatur"],
        )


class TestRefilled:
    """A column that was there before the turn, put on a role the turn emptied, writes `refilled`: it counts, it does
    not judge, so an asked refill writes it too."""

    async def test_the_root_binding_temperatur_to_the_emptied_y_logs_refilled(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            bindings_call(x="Temperatur", y="Temperatur"),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Drop Feuchte."})

        assert (await outcome(runtime, sid))[0] == {"x": "Temperatur", "y": "Temperatur"}
        assert guard_lines(caplog) == [{"tool": "set_bindings", "outcome": "refilled", "role": "y"}]

    async def test_the_carry_of_a_later_call_putting_a_column_that_was_there_on_y_logs_refilled(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`Akku`, read as text in an earlier turn, is read as numbers in place after the drop emptied y: the carry
        puts it on the open y (`carry_bindings`, a conversion for an open role), with no new column."""
        akku = SENSORS.replace("Feuchte\n", "Feuchte,Akku\n").replace("\n2026", ",9\n2026").rstrip("\n") + ",9\n"
        script = default_script()
        script["root"] = [
            prepare_call({"op": "set_type", "column": "Akku", "type": "text"}),
            {"text": "Akku is text now."},
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            prepare_call({"op": "set_type", "column": "Akku", "type": "number"}),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime, akku)
        await say(client, sid, {"text": "Read Akku as text."})
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)

        await say(client, sid, {"text": "Drop Feuchte and read Akku as numbers."})

        assert (await outcome(runtime, sid))[0] == {"x": "Temperatur", "y": "Akku"}
        assert guard_lines(caplog) == [{"tool": "prepare_data", "outcome": "refilled", "role": "y"}]


SERIES = (
    "Datum,Wert,Ort\n2025-01-01,4,Bern\n2025-01-02,6,Bern\n2025-01-03,5,Thun\n2025-01-04,9,Thun\n2025-01-05,7,Bern\n"
)
"""A daily series on `line-basic`: x Datum, y Wert."""
SALES = (
    "Region,Umsatz,Kosten,Jahr,Monat\nNord,120,80,2025,1\nSued,90,60,2025,1\nNord,130,85,2025,2\nSued,95,66,2025,2\n"
    "Nord,140,90,2025,3\n"
)
"""Sales by month in parts on `scatter-basic`: x Umsatz, y Kosten (the year, one value in five rows, is a constant no
axis takes), and the year and the month as spare numbers."""
TAGE = {"op": "date_number", "column": "Datum", "unit": "days", "name": "Tage"}
DROP_DATUM = {"op": "drop_columns", "columns": ["Datum"]}
NR = {"op": "row_number", "name": "Nr"}


async def turn_of(
    client: httpx.AsyncClient,
    runtime: Runtime,
    swap_models: Any,
    steps: list[dict[str, Any]],
    *,
    text: str = SENSORS,
    spec: str = "scatter-basic",
) -> tuple[Any, str]:
    """One turn that makes the scripted calls `steps`, then replies."""
    script = default_script()
    script["root"] = [*steps, REPLY]
    fake = swap_models("anthropic-vertex", script)
    sid = await summarized(client, runtime, text, spec)
    await say(client, sid, {"text": "Do as I asked."})
    return fake, sid


class TestTheTurnsStart:
    """A role is taken when the column it held at the start of the turn is gone, whatever the bindings in force say:
    a `set_bindings` before the data step no longer disarms the guard, and a spare column the carry could put on the
    taken role does not make the made column harmless."""

    async def test_unbinding_y_first_does_not_free_the_days(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        fake, sid = await turn_of(
            client, runtime, swap_models, [bindings_call(x="Temperatur"), prepare_call(DAILY_MEAN), prepare_call(DAYS)]
        )

        assert await outcome(runtime, sid) == ({"x": "Temperatur"}, ["Zeitpunkt", "Sensor", "Temperatur"])
        assert HELD in answers(fake, 3)

    async def test_unbinding_y_first_does_not_free_the_row_numbers(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        fake, sid = await turn_of(
            client, runtime, swap_models, [bindings_call(x="Temperatur"), prepare_call(DAILY_MEAN), prepare_call(ROWS)]
        )

        assert await outcome(runtime, sid) == ({"x": "Temperatur"}, ["Zeitpunkt", "Sensor", "Temperatur"])
        assert HELD in answers(fake, 3)

    async def test_moving_y_onto_x_first_does_not_free_the_days(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """y holds Temperatur when the aggregate drops Feuchte, its column of the turn's start: still taken. The days
        are refused with the sentence for a filled role, and the binding of them finds no such column."""
        steps = [
            bindings_call(x="Temperatur", y="Temperatur"),
            prepare_call(DAILY_MEAN),
            prepare_call(DAYS),
            bindings_call(x="Temperatur", y="Tag"),
        ]
        fake, sid = await turn_of(client, runtime, swap_models, steps)

        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Temperatur"},
            ["Zeitpunkt", "Sensor", "Temperatur"],
        )
        assert HELD_FILLED in answers(fake, 3)

    @pytest.mark.parametrize("keep_date", [True, False])
    async def test_a_date_built_numbered_and_y_dropped_in_one_call_is_refused(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, keep_date: bool
    ) -> None:
        """The year and the month could fill y; the days would take it. The days come from the built date, not from
        Kosten, y's column of the start: refused, with the built date kept or dropped."""
        dropped = ["Kosten"] if keep_date else ["Datum", "Kosten"]
        built = [
            {"op": "make_date", "name": "Datum", "year": "Jahr", "month": "Monat"},
            TAGE,
            {"op": "drop_columns", "columns": dropped},
        ]
        fake, sid = await turn_of(client, runtime, swap_models, [prepare_call(*built)], text=SALES)

        assert await outcome(runtime, sid) == (
            {"x": "Umsatz", "y": "Kosten"},
            ["Region", "Umsatz", "Kosten", "Jahr", "Monat"],
        )
        assert HELD in answers(fake, 1)


class TestTheReplacement:
    """A date number made from the very column a taken role held at the turn's start replaces it, on that role and no
    other. The original fault stays refused, because there the days come from another column than y lost."""

    async def test_the_days_instead_of_the_dates_in_one_call_take_x(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        fake, sid = await turn_of(
            client, runtime, swap_models, [prepare_call(TAGE, DROP_DATUM)], text=SERIES, spec="line-basic"
        )

        assert await outcome(runtime, sid) == ({"x": "Tage", "y": "Wert"}, ["Wert", "Ort", "Tage"])
        assert EMPTIED_HEADING.split("{", 1)[0] not in block_of(fake, 1)  # x holds its replacement: nothing waits

    async def test_the_days_then_the_drop_in_two_calls_take_x(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        _, sid = await turn_of(
            client, runtime, swap_models, [prepare_call(TAGE), prepare_call(DROP_DATUM)], text=SERIES, spec="line-basic"
        )

        assert await outcome(runtime, sid) == ({"x": "Tage", "y": "Wert"}, ["Wert", "Ort", "Tage"])

    async def test_the_days_bound_to_x_then_the_drop_stay(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The order of the review's t02 with the replacement: the drop takes x while x holds its own date's days."""
        steps = [prepare_call(TAGE), bindings_call(x="Tage", y="Wert"), prepare_call(DROP_DATUM)]
        _, sid = await turn_of(client, runtime, swap_models, steps, text=SERIES, spec="line-basic")

        assert await outcome(runtime, sid) == ({"x": "Tage", "y": "Wert"}, ["Wert", "Ort", "Tage"])

    async def test_the_days_do_not_replace_another_roles_column(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The days of the dates are x's replacement, never y's: the drop of Wert with them is refused."""
        fake, sid = await turn_of(
            client,
            runtime,
            swap_models,
            [prepare_call(TAGE, {"op": "drop_columns", "columns": ["Wert"]})],
            text=SERIES,
            spec="line-basic",
        )

        assert await outcome(runtime, sid) == ({"x": "Datum", "y": "Wert"}, ["Datum", "Wert", "Ort"])
        assert COLUMN_HELD_MESSAGE.format(roles="y") in answers(fake, 1)

    async def test_the_original_fault_stays_refused(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        fake, sid = await turn_of(client, runtime, swap_models, [prepare_call(DAILY_MEAN, DAYS)])

        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Feuchte"},
            ["Zeitpunkt", "Sensor", "Temperatur", "Feuchte"],
        )
        assert HELD in answers(fake, 1)


class TestRowNumbersNeverReplace:
    """Row numbers have no source: "the row numbers on x instead of the dates" takes two turns in every order, and the
    refusal says which ones work."""

    async def test_rows_instead_of_the_dates_in_one_call_are_refused_with_what_works(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        fake, sid = await turn_of(
            client, runtime, swap_models, [prepare_call(DROP_DATUM, NR)], text=SERIES, spec="line-basic"
        )

        assert await outcome(runtime, sid) == ({"x": "Datum", "y": "Wert"}, ["Datum", "Wert", "Ort"])
        assert ROWS_REPLACE_MESSAGE in answers(fake, 1)

    async def test_what_the_refusal_says_works_does_work(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """Made and bound while Datum stays, in this turn; Datum removed in the next one, where x's column of the start
        is Nr."""
        script = default_script()
        script["root"] = [prepare_call(NR), bindings_call(x="Nr", y="Wert"), REPLY, prepare_call(DROP_DATUM), REPLY]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime, SERIES, "line-basic")

        await say(client, sid, {"text": "Number the rows and put them on x."})
        first = await outcome(runtime, sid)
        await say(client, sid, {"text": "Now remove the dates."})

        assert first == ({"x": "Nr", "y": "Wert"}, ["Nr", "Datum", "Wert", "Ort"])
        assert await outcome(runtime, sid) == ({"x": "Nr", "y": "Wert"}, ["Nr", "Wert", "Ort"])

    async def test_rows_bound_to_x_then_the_drop_in_one_turn_refuse_the_drop(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The review's t02 with row numbers: the drop would take x while x holds a held column the root bound there,
        so the drop is refused; the row numbers and their binding stay."""
        steps = [prepare_call(NR), bindings_call(x="Nr", y="Wert"), prepare_call(DROP_DATUM)]
        fake, sid = await turn_of(client, runtime, swap_models, steps, text=SERIES, spec="line-basic")

        assert await outcome(runtime, sid) == ({"x": "Nr", "y": "Wert"}, ["Nr", "Datum", "Wert", "Ort"])
        refused = answers(fake, 3)
        assert ROWS_REPLACE_MESSAGE in refused  # what works: the drop of the dates in the next turn
        assert MADE_BEFORE_LINE.format(name="Nr") in refused


class TestARenameTakesNoRole:
    async def test_after_a_rename_of_ys_column_the_days_are_made_and_take_nothing(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The turn's start follows the rename: y still holds its column, under the new name, so nothing is taken and
        the days are stored, on no role, since none is open."""
        rename = {"op": "rename", "column": "Feuchte", "name": "Humidity"}
        _, sid = await turn_of(client, runtime, swap_models, [prepare_call(rename), prepare_call(DAYS)])

        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Humidity"},
            ["Zeitpunkt", "Sensor", "Temperatur", "Humidity", "Tag"],
        )


class TestWhatIsNoHeldColumn:
    async def test_a_reformatted_copy_of_a_date_is_stored(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """`replace` of "-" by "/" in the dates makes dates again, no numbers: no held column, also after y's column
        was taken."""
        reformat = {"op": "replace", "column": "Zeitpunkt", "old": "-", "new": "/", "name": "Zeit"}
        fake, sid = await turn_of(
            client,
            runtime,
            swap_models,
            [prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}), prepare_call(reformat)],
        )

        assert (await outcome(runtime, sid))[1] == ["Zeitpunkt", "Sensor", "Temperatur", "Zeit"]
        assert HELD not in answers(fake, 2) and HELD_FILLED not in answers(fake, 2)

    async def test_the_line_speaks_of_the_rest_of_the_turn_after_row_numbers_made_before(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """Row numbers made before y's column was taken stay in the table: the line says what holds from then on."""
        fake, _ = await turn_of(
            client,
            runtime,
            swap_models,
            [prepare_call(ROWS), prepare_call({"op": "drop_columns", "columns": ["Feuchte"]})],
        )

        assert "For the rest of this turn no date is turned into numbers and no row number is made" in block_of(fake, 2)


class TestNamedLimits:
    """What the guard does not cover, by name, as it stands; none of it is a promise."""

    async def test_known_limit_a_whole_new_table_from_code_is_not_guarded(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: Any
    ) -> None:
        """`run_data_code` (and `generate_data`) store a new table with the default bindings: the guard reads the
        changes of the table the turn started with, so the days in a computed table take y."""
        backend.data_script = lambda job: DataOutput(
            exit_code=0, csv_text="Sensor,Temperatur,Tag\nS1,14.5,0\nS2,16.6,0\nS1,15.5,1\n", wall_s=0.1
        )
        code = {"code": "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2]})", "source_language": "other"}
        _, sid = await turn_of(
            client, runtime, swap_models, [prepare_call(DAILY_MEAN), {"call": "run_data_code", "args": code}]
        )

        assert await outcome(runtime, sid) == ({"x": "Temperatur", "y": "Tag"}, ["Sensor", "Temperatur", "Tag"])

    @pytest.mark.parametrize("name", ["Zeile", "index"])
    async def test_known_limit_the_next_turns_carry_may_put_a_kept_off_column_on_x(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, name: str
    ) -> None:
        """After a turn that kept the row numbers off y, the next turn's rename of x's column lets the plain default
        carry bind the free columns again: the row-number column comes first in the table, x takes it and the renamed
        column goes to the open y. Main does the same with any spare number column when a binding goes."""
        script = default_script()
        script["root"] = [
            prepare_call({"op": "row_number", "name": name}),
            prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}),
            REPLY,
            prepare_call({"op": "rename", "column": "Temperatur", "name": "Temp"}),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Number the rows and drop Feuchte."})
        assert (await outcome(runtime, sid))[0] == {"x": "Temperatur"}
        await say(client, sid, {"text": "Call Temperatur Temp."})

        assert await outcome(runtime, sid) == ({"x": name, "y": "Temp"}, [name, "Zeitpunkt", "Sensor", "Temp"])


class TestTheKnownGap:
    async def test_known_gap_an_unasked_derived_column_still_takes_the_emptied_axis(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Not a promise, the state of things: a column a `compute` adds in the call that empties y fills y through
        the carry, whether the user asked for it or not, since nothing typed tells the two apart. What the guard does
        about it is the log line, which says how often it happens; a fix needs a decision of its own."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [prepare_call(DAILY_MEAN, FAHRENHEIT), REPLY]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur", "y": "Fahrenheit"} and columns[-1] == "Fahrenheit"
        lines = guard_lines(caplog)
        assert lines == [{"tool": "prepare_data", "outcome": "bound", "role": "y", "kind": "compute"}]
        assert "Fahrenheit" not in json.dumps(lines) and "Feuchte" not in json.dumps(lines)


class TestOtherTurns:
    """The guard reads only this turn's own calls: a paste's summary turn and the turn after an undo bind as before."""

    async def test_the_summary_turn_keeps_the_servers_row_numbers_and_the_roots_own_change(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The paste arrives with one number column, so y is open; the server makes the `certain` row numbers before
        the root runs (`paste_conversions.py`, not a call of the root's), x takes them and y the numbers, and the
        root's rename in the same turn carries them on. Nothing is refused."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call({"op": "rename", "column": "Wert", "name": "Messwert"}),
            {"text": "6 rows; x: row number 1 to 6; Wert renamed to Messwert."},
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, "Wert\n13\n27\n8\n19\n42\n5\n")

        await say(client, sid, {"text": "Nenne die Spalte Messwert."})

        bound, columns = await outcome(runtime, sid)
        assert (bound, columns) == ({"x": "index", "y": "Messwert"}, ["index", "Messwert"])
        assert HELD not in answers(fake, 1) and guard_lines(caplog) == []

    async def test_the_turn_after_an_undo_takes_the_offer_again(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """An undo is the page's, outside any turn, and its carry is the one it always was; the next turn starts with
        y open, not emptied by that turn, so the days asked for then take y."""
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN),
            REPLY,
            prepare_call(DAYS),
            {"text": "Tag takes y."},
            prepare_call(DAYS),
            {"text": "Tag takes y again."},
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)
        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})
        await say(client, sid, {"text": "Nimm die Tage seit dem ersten Datum für y."})

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)
        after_undo = await outcome(runtime, sid)
        await say(client, sid, {"text": "Doch, nimm die Tage für y."})

        assert undone.status_code == 200 and after_undo == ({"x": "Temperatur"}, ["Zeitpunkt", "Sensor", "Temperatur"])
        assert await outcome(runtime, sid) == (
            {"x": "Temperatur", "y": "Tag"},
            ["Zeitpunkt", "Sensor", "Temperatur", "Tag"],
        )


class TestSetBindings:
    async def test_it_refuses_a_held_column_on_a_taken_role_and_leaves_the_other_roles_alone(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The binding call alone, on a turn that made `Tag` from the dates and took y's column: `Tag` on x, which is
        not taken, binds; `Tag` on y is refused, and since y holds Temperatur then, with the sentence for a filled
        role."""
        sid = await summarized(client, runtime, SENSORS.replace("Feuchte", "Tag"))
        context = await context_for(client, sid, "inv-e-1")
        ledger = ledger_for("inv-e-1")
        ledger.made_columns = {"Tag": "Zeitpunkt"}
        ledger.taken_roles = {"y": "Feuchte"}

        on_x = await set_bindings([{"role": "x", "column": "Tag"}, {"role": "y", "column": "Temperatur"}], context)
        on_y = await set_bindings([{"role": "x", "column": "Temperatur"}, {"role": "y", "column": "Tag"}], context)

        assert on_x["status"] == "ok"
        assert (on_y["code"], on_y["message"]) == ("invalid_bindings", HELD_FILLED)
        assert ledger.guard_held == ["set_bindings"]
        view = read_session(context.state)
        assert view is not None and {b.role: b.column for b in view.bindings} == {"x": "Tag", "y": "Temperatur"}
