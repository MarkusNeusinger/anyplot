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
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import CONVERSIONS_HEADING, EMPTIED_HEADING
from agents.anyplot.plugins.ledger import ledger_for
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import DATASET_ID, SUMMARY_PENDING, read_session
from agents.anyplot.tools.session import (
    COLUMN_HELD_MESSAGE,
    LOSING_LINE,
    LOST_LINE,
    MADE_BEFORE_LINE,
    MADE_NOW_LINE,
    set_bindings,
)
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_from_version import context_for
from .test_paste_conversions import block_now, open_spec, paste, say
from .test_service_flow import USER, permissive_queue, prepare_call


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


async def summarized(client: httpx.AsyncClient, runtime: Runtime, text: str = SENSORS) -> str:
    """A `scatter-basic` session with `text` pasted and summarized, as the page leaves it after the summary turn."""
    sid = await open_spec(client, "scatter-basic")
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


class TestTheWaysIn:
    async def test_the_same_data_step_stores_nothing_and_the_column_lands_nowhere(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The daily mean and the days since the first date in one call: the carry would bind `Tag` to the y that
        the same call emptied, so the call is refused, whole."""
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
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The row numbers would take x and move Temperatur to the emptied y: no column made in the turn lands on
        any role, not only on the emptied one."""
        script = default_script()
        script["root"] = [prepare_call(DAILY_MEAN), prepare_call(ROWS), REPLY]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur"} and "index" not in columns
        assert HELD in answers(fake, 2)

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

    async def test_a_column_made_before_the_change_that_empties_the_axis_lands_nowhere(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """Made first, while every role was bound, the row numbers take no role; the drop of Feuchte would then let
        the carry put them on y. That call is refused, so y keeps Feuchte."""
        script = default_script()
        script["root"] = [prepare_call(ROWS), prepare_call({"op": "drop_columns", "columns": ["Feuchte"]}), REPLY]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Drop the humidity."})

        bound, _ = await outcome(runtime, sid)
        refused = answers(fake, 2)
        assert bound == {"x": "Temperatur", "y": "Feuchte"} and HELD in refused
        assert LOSING_LINE.format(role="y", column="Feuchte") in refused
        assert MADE_BEFORE_LINE.format(name="index") in refused

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
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """A computed column is the request's own, no conversion: in the turn that emptied y, the root binds it."""
        fahrenheit = {
            "op": "compute",
            "name": "Fahrenheit",
            "expression": "t * 1.8 + 32",
            "inputs": {"t": "Temperatur"},
        }
        script = default_script()
        script["root"] = [
            prepare_call(DAILY_MEAN),
            prepare_call(fahrenheit),
            bindings_call(x="Temperatur", y="Fahrenheit"),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Tagesmittel pro Sensor, und dieselben Werte in Fahrenheit auf y."})

        bound, columns = await outcome(runtime, sid)
        assert bound == {"x": "Temperatur", "y": "Fahrenheit"} and columns[-1] == "Fahrenheit"


class TestSetBindings:
    async def test_it_refuses_the_turns_date_numbers_only_once_the_turn_emptied_a_role(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The binding call alone: a column of dates turned into numbers that the turn made, once a role it emptied is
        open; the same binding before that is the user's offer taken."""
        sid = await summarized(client, runtime, SENSORS.replace("Feuchte", "Tag"))
        context = await context_for(client, sid, "inv-e-1")
        ledger = ledger_for("inv-e-1")
        ledger.made_columns = ["Tag"]

        before = await set_bindings([{"role": "x", "column": "Temperatur"}, {"role": "y", "column": "Tag"}], context)
        ledger.emptied_roles["y"] = "Feuchte"
        refused = await set_bindings([{"role": "x", "column": "Tag"}, {"role": "y", "column": "Temperatur"}], context)

        assert before["status"] == "ok"
        assert (refused["code"], refused["message"]) == ("invalid_bindings", HELD)
        assert ledger.guard_held == ["set_bindings"]
        view = read_session(context.state)
        assert view is not None and {b.role: b.column for b in view.bindings} == {"x": "Temperatur", "y": "Tag"}
