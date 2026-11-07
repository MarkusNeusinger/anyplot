"""After the root's own data change in a turn, the session block lists no conversion candidates for the rest of it.

Prep eval of 2026-11-07: on `scatter-basic` with one number column, `y` stays open, and the session block lists the
row-number fallback for it, worded as `certain`. In a turn that asked for a drop, an aggregate and a sort, the block was
recomputed on the new version after the root's `prepare_data`, the row-number line came back on the next call, and the
root added a `row_number` nobody asked for in about half the runs, also after #12595 had scoped the prompt's rule. The
guard is code (owner rule of 2026-11-07: code before prompt): once `ledger.prep_ops` holds the turn's own change, the
candidates stay out of the block until the turn ends. The lines of the conversions the server made stay, since the
summary names them, and the next turn lists the candidates again.
"""

from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import CONVERSIONS_HEADING
from agents.anyplot.services import Services
from agents.anyplot.session_state import SUMMARY_PENDING
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_paste_conversions import MADE_HEADING, YEARS, block_now, open_spec, paste, say
from .test_service_flow import USER, permissive_queue, prepare_call


TOTALS = "Category,Revenue\nTotal,245\nShoes,120\nHats,80\nBags,45\n"
"""The prep eval's `en-drop-total-row`: one number column on `scatter-basic`, so `y` stays open."""
CANDIDATES = CONVERSIONS_HEADING.split("{", 1)[0]
DROP_TOTAL = prepare_call({"op": "drop_rows", "where": [{"column": "Category", "test": "eq", "value": "Total"}]})


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


async def summarized(client: httpx.AsyncClient, runtime: Runtime, text: str, spec: str = "scatter-basic") -> str:
    """A session with `text` pasted and summarized, as the page leaves it after the summary turn (the prep eval's
    message cases): the server made no conversion, and the block lists the candidates for the open role."""
    sid = await open_spec(client, spec)
    await paste(client, sid, text)
    await runtime.write_state(await runtime.session(USER, sid), {SUMMARY_PENDING: None})
    return sid


def blocks(fake: Any) -> list[str]:
    """The session block of every root call, in order."""
    return [call["system"][-1]["text"] for call in fake.calls]


async def test_after_the_turns_own_change_no_candidate_is_listed(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    script = default_script()
    script["root"] = [DROP_TOTAL, {"text": "Dropped the Total row; 3 rows remain."}]
    fake = swap_models("anthropic-vertex", script)
    sid = await summarized(client, runtime, TOTALS)
    assert CANDIDATES in await block_now(client, sid)  # the open y has its row-number line

    events = await say(client, sid, {"text": "Drop the Total row, it is not a category."})

    before, after = blocks(fake)
    assert CANDIDATES in before
    assert CANDIDATES not in after and "row_number" not in after
    assert events[-1][1]["dataset"]["version"] == 2


async def test_a_new_turn_lists_the_candidates_again(client: httpx.AsyncClient, runtime: Runtime, swap_models) -> None:
    """The guard holds for the turn: a later message about the open role gets the conversion line, as before."""
    script = default_script()
    script["root"] = [
        DROP_TOTAL,
        {"text": "Dropped the Total row; 3 rows remain."},
        {"text": "y has no column yet; the row numbers 1 to 3 can fill it."},
    ]
    fake = swap_models("anthropic-vertex", script)
    sid = await summarized(client, runtime, TOTALS)

    await say(client, sid, {"text": "Drop the Total row, it is not a category."})
    await say(client, sid, {"text": "What goes on the y axis?"})

    first_turn, second_turn = blocks(fake)[:2], blocks(fake)[2:]
    assert CANDIDATES not in first_turn[1]
    assert len(second_turn) == 1 and CANDIDATES in second_turn[0]
    assert CANDIDATES in await block_now(client, sid)


async def test_a_turn_without_a_change_keeps_the_candidates_in_every_call(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    """Only the turn's own `prepare_data` takes them out: a read of the profile is no change."""
    script = default_script()
    script["root"] = [{"call": "get_dataset_profile", "args": {}}, {"text": "4 rows, y is open."}]
    fake = swap_models("anthropic-vertex", script)
    sid = await summarized(client, runtime, TOTALS)

    await say(client, sid, {"text": "How many rows are there?"})

    assert all(CANDIDATES in block for block in blocks(fake))


async def test_the_server_made_conversions_stay_listed_after_the_roots_change(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The summary names what the server made, in the reply after the root's own `prepare_data` too."""
    script = default_script()
    script["root"] = [
        prepare_call({"op": "rename", "column": "Emissions", "name": "Tonnes"}),
        {"text": "5 rows; Year read as dates in Year (date), 5 of 5 cells; Emissions renamed to Tonnes."},
    ]
    fake = swap_models("anthropic-vertex", script)
    sid = await open_spec(client, "line-timeseries-rolling")
    await paste(client, sid, YEARS)

    await say(client, sid, {"text": "call the Emissions column Tonnes"})

    after = blocks(fake)[-1]
    assert MADE_HEADING in after and CANDIDATES not in after
