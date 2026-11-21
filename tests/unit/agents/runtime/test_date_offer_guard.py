"""The guard's second trigger (`data/emptied.py`): a date column refused on a role that takes numbers.

The prep eval's runs of 2026-11-21: in `en-date-from-year-month-text` the root read `period` as dates, put it on the
scatter plot's x, which takes numbers, was refused, and turned the dates into a decimal year by itself; in
`de-tagesmittel-pro-sensor` it kept every column through the daily mean, put the timestamps on x, was refused, and
added the days since the first date. Nobody had asked for either column. Which numbers a date becomes is the user's
choice, so after such a refusal the turn makes no date number and no row numbers, the refusal says so at once, and a
root asked for the numbers, which makes them before it binds them, never meets the trigger.
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import DATASET_ID
from agents.anyplot.tools.session import (
    DATE_OFFER_FILLED_MESSAGE,
    DATE_OFFER_MESSAGE,
    MADE_NOW_LINE,
    OFFER_HELD_MESSAGE,
)
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_empty_axis_guard import ATTRIBUTION, answers, bindings_call, outcome, summarized
from .test_paste_conversions import say
from .test_service_flow import USER, permissive_queue, prepare_call


MONTHS = "period,orders\n01/2024,120\n02/2024,135\n03/2024,128\n04/2024,150\n05/2024,162\n06/2024,171\n"
"""The prep eval's `en-date-from-year-month-text` table: `period` is text until the user says how to read it."""
READ_MONTHS = {"op": "set_type", "column": "period", "type": "datetime", "date_format": "MM/YYYY"}
DECIMAL_YEAR = {"op": "date_number", "column": "period", "unit": "decimal_year", "name": "period (decimal year)"}
BOTH_MEANS = {
    "op": "aggregate",
    "by": ["Zeitpunkt", "Sensor"],
    "columns": ["Feuchte", "Temperatur"],
    "how": "mean",
    "period": "day",
}
DAYS = {"op": "date_number", "column": "Zeitpunkt", "unit": "days", "name": "Tag"}
ROWS = {"op": "row_number", "name": "index"}
REPLY = {"text": "Done."}
OFFER_WORDS = {
    "tool": {"prepare_data", "set_bindings"},
    "outcome": {"misfit", "offer_held"},
    "role": {"x", "y"},
    "kind": {"date_number", "row_number"},
}
"""Every value a line of the second trigger may hold on `scatter-basic`: no column of the user's can stand in one."""


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


def offer_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    """The guard's lines (hook `emptied_role`) without their envelope, each checked to be content-free."""
    lines = [json.loads(record.getMessage()) for record in caplog.records if record.name == ATTRIBUTION]
    envelope = {"severity", "hook", "request_id", "user", "session", "llm_calls", "tokens"}
    found = [{k: v for k, v in line.items() if k not in envelope} for line in lines if line["hook"] == "emptied_role"]
    for line in found:
        for key, value in line.items():
            assert set(value if isinstance(value, list) else [value]) <= OFFER_WORDS[key.rstrip("s")], line
    return found


class TestTheEvalRuns:
    async def test_a_decimal_year_after_the_refusal_is_never_made(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [
            prepare_call(READ_MONTHS),
            bindings_call(x="period", y="orders"),
            prepare_call(DECIMAL_YEAR),
            bindings_call(x="period (decimal year)", y="orders"),
            REPLY,
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime, MONTHS)
        before, _ = await outcome(runtime, sid)

        await say(client, sid, {"text": "period is month and year (MM/YYYY); read it as dates."})

        bound, columns = await outcome(runtime, sid)
        # The change the user asked for is stored; the column nobody asked for is not, and the bindings stay.
        assert columns == ["period", "orders"] and bound == before
        message = DATE_OFFER_FILLED_MESSAGE if "x" in before else DATE_OFFER_MESSAGE
        assert message.format(roles="x") in answers(fake, 2)
        held = answers(fake, 3)
        assert (
            OFFER_HELD_MESSAGE.format(roles="x") in held and MADE_NOW_LINE.format(name="period (decimal year)") in held
        )
        assert offer_lines(caplog) == [
            {"tool": "set_bindings", "outcome": "misfit", "roles": ["x"]},
            {"tool": "prepare_data", "outcome": "offer_held", "roles": ["x"], "kinds": ["date_number"]},
        ]

    async def test_days_after_the_refusal_are_never_made_while_x_keeps_its_column(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The daily mean of both columns takes no role, so the guard on a taken role never fires; the refusal of the
        timestamps on x does."""
        script = default_script()
        script["root"] = [
            prepare_call(BOTH_MEANS),
            bindings_call(x="Zeitpunkt", y="Temperatur"),
            prepare_call(DAYS),
            bindings_call(x="Tag", y="Temperatur"),
            REPLY,
        ]
        fake = swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Bilde das Tagesmittel der Temperatur pro Sensor."})

        bound, columns = await outcome(runtime, sid)
        assert "Tag" not in columns and bound == {"x": "Temperatur", "y": "Feuchte"}
        # x holds a column, so the refusal says nothing about a role that waits.
        assert DATE_OFFER_FILLED_MESSAGE.format(roles="x") in answers(fake, 2)
        assert OFFER_HELD_MESSAGE.format(roles="x") in answers(fake, 3)


class TestTheBoundary:
    async def test_numbers_made_before_any_refusal_bind_as_before(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A root asked for the days on x makes them first and binds them after: the trigger never sees it."""
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [prepare_call(DAYS), bindings_call(x="Tag", y="Temperatur"), REPLY]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Put the days since the first reading on x."})

        bound, columns = await outcome(runtime, sid)
        assert "Tag" in columns and bound["x"] == "Tag"
        assert offer_lines(caplog) == []

    async def test_row_numbers_after_the_refusal_are_never_made(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger=ATTRIBUTION)
        script = default_script()
        script["root"] = [bindings_call(x="Zeitpunkt", y="Temperatur"), prepare_call(ROWS), REPLY]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Plot it over time."})

        _, columns = await outcome(runtime, sid)
        assert "index" not in columns
        assert offer_lines(caplog)[-1] == {
            "tool": "prepare_data",
            "outcome": "offer_held",
            "roles": ["x"],
            "kinds": ["row_number"],
        }

    async def test_a_change_without_such_a_column_is_stored_after_the_refusal(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        script = default_script()
        script["root"] = [bindings_call(x="Zeitpunkt", y="Temperatur"), prepare_call(BOTH_MEANS), REPLY]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Daily means, please."})

        _, columns = await outcome(runtime, sid)
        # The daily means were stored: the table holds the means of the eight readings, not the readings.
        state = (await runtime.session(USER, sid)).state
        stored = get_services().datasets.get(state[DATASET_ID], sid)
        assert stored is not None and stored.profile.rows == 5
        assert sorted(columns) == ["Feuchte", "Sensor", "Temperatur", "Zeitpunkt"]

    async def test_the_next_turn_makes_the_numbers_the_user_asks_for(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The trigger holds for its own turn: the user who then names the unit gets the column and the binding."""
        script = default_script()
        script["root"] = [
            bindings_call(x="Zeitpunkt", y="Temperatur"),
            REPLY,
            prepare_call(DAYS),
            bindings_call(x="Tag", y="Temperatur"),
            REPLY,
        ]
        swap_models("anthropic-vertex", script)
        sid = await summarized(client, runtime)

        await say(client, sid, {"text": "Plot it over time."})
        await say(client, sid, {"text": "Yes, the days since the first reading on x."})

        bound, columns = await outcome(runtime, sid)
        assert "Tag" in columns and bound["x"] == "Tag"
