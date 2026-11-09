"""What a new paste does to the plot memory, the switch's carry and a plot wish pasted with it (owner decisions of
2026-11-08).

- The memory stays: only the user clears it (2026-11-02). The paste answer says when a column the old data was
  plotted by is not in the new data (`columns_changed`), so the page can show the decisions there.
- The switch's carry drops with every new data version, as the kept first-plot note does (F): its texts, theme and
  requests were taken from a plot of the data before. A switch or the fan-out's copy after the data changed carries
  no plot of the earlier data either.
- A plot wish sent with the new data is kept for the first plot of that data (E): a plot of data a new paste
  replaced is no plot of the current data.
"""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import EARLIER_DATA_LINE
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.store import DatasetStore
from agents.anyplot.dataset_versions import push_version, undo_version
from agents.anyplot.memory import MEMORY_SEQ, memory_delta, plan, read_memory
from agents.anyplot.opening import store_dataset
from agents.anyplot.schemas import PlotResult, RememberItem
from agents.anyplot.services import CodeVersion, Services, get_services
from agents.anyplot.session_state import PENDING_REQUEST
from agents.anyplot.switch import CARRY, read_carry, source_plot
from agents.main import Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK, default_script
from .test_dataset_versions import SID, SNAPSHOT, opened, view_of
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    adapter_inputs,
    create_plot,
    open_session,
    permissive_queue,
    snapshot_body,
)
from .test_service_flow import tool_responses as tool_answers


LINE = RememberItem(kind="reference_line", text="horizontal reference line at y = 7")
LABEL = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (h)'", expected_text="Zeit (h)")
SAME_COLUMNS = "Student,Study Hours,Exam Score\nT01,4.5,71\nT02,5.0,77\nT03,6.5,80\n"
"""New rows under the columns the session's plot was made by: every binding carries."""
OTHER_COLUMNS = "Length (m),Period (s)\n0.25,1.003\n0.5,1.419\n1.0,2.006\n"
"""A table about something else: no binding of the scatter data carries."""
NOTE = "title: Pendulum 2026"


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


async def paste(client: httpx.AsyncClient, sid: str, text: str) -> dict[str, Any]:
    response = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": text})
    assert response.status_code == 200, response.text
    return dict(response.json())


async def seed_memory(runtime: Runtime, sid: str) -> None:
    held = plan([], [LINE, LABEL], seq=1, turn=1).entries
    await runtime.write_state(await runtime.session(USER, sid), memory_delta(held, 3))


async def switch(client: httpx.AsyncClient, sid: str, library: str) -> dict[str, Any]:
    body = {"library": library, "snapshot": snapshot_body(library=library)}
    response = await client.post(f"/v1/sessions/{sid}/library", headers=HEADERS, json=body)
    assert response.status_code == 200, response.text
    return dict(response.json())


async def test_a_paste_keeps_the_memory_and_drops_the_carry(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    swap_models("gemini", default_script())
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(runtime, sid)
    await switch(client, sid, "seaborn")
    assert read_carry(await _session_state(client, sid), ("scatter-basic", "seaborn")) is not None
    before = await _session_state(client, sid)

    pasted = await paste(client, sid, SAME_COLUMNS)

    state = await _session_state(client, sid)
    assert state.get(CARRY) is None  # the carry was taken from a plot of the data before
    assert read_memory(state) == read_memory(before) and state[MEMORY_SEQ] == before[MEMORY_SEQ] == 3
    assert pasted["columns_changed"] is False  # every binding found its column again


def test_every_new_data_version_drops_the_carry() -> None:
    """A paste, a change of the data and an undo each write `CARRY: None`, as they drop the kept note."""
    store = DatasetStore()
    state = opened(store)
    assert store_dataset(store, SID, parse_dataset("a,b\n5,6\n"), SNAPSHOT).state_delta()[CARRY] is None
    state[CARRY] = {"stale": True}

    changed = push_version(store, SID, view_of(state), parse_dataset("a,b\n1,2\n"), SNAPSHOT)
    assert changed.delta[CARRY] is None and changed.delta[PENDING_REQUEST] is None
    state.update(changed.delta)
    state[CARRY] = {"stale": True}

    undone = undo_version(store, SID, view_of(state), SNAPSHOT)
    assert undone is not None and undone.delta[CARRY] is None


async def test_a_switch_after_new_data_carries_only_the_asked_theme_of_the_earlier_plot(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    """Owner decision of 2026-11-09: the dark theme the user asked for on the plot of the data before carries, as "plot
    the new data" keeps it; that plot's texts and requests stay behind, and the memory still travels."""
    script = default_script()
    script["root"][0] = {"call": "plot_pipeline", "args": {"theme": "dark"}}
    swap_models("gemini", script)
    sid = await open_session(client)
    await create_plot(client, sid)
    await seed_memory(runtime, sid)
    await paste(client, sid, SAME_COLUMNS)

    switched = await switch(client, sid, "seaborn")

    assert switched["carry"]["from_plot"] is True and switched["carry"]["decisions"] == 2
    carry = read_carry(await _session_state(client, sid), ("scatter-basic", "seaborn"))
    assert carry is not None and carry.theme == "dark" and carry.requests == []
    assert carry.expected_texts == ["Zeit (h)"]  # the memory's own text, which only the user removes


def test_a_plot_of_another_data_version_gives_its_theme_and_no_texts_or_requests() -> None:
    version = CodeVersion(
        number=1,
        working="w",
        run_form="r",
        export="e",
        data_csv="a\n1\n",
        render_id="r1",
        result=PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
        theme="dark",
        theme_asked=True,
        expected_texts=["Exam 2025"],
        requests=["title: Exam 2025"],
        data_version=1,
    )

    earlier = source_plot(version, data_version=2)
    same = source_plot(version, data_version=1)

    assert earlier is not None and (earlier.theme, earlier.theme_asked) == ("dark", True)
    assert (earlier.expected_texts, earlier.requests) == ([], [])
    assert same is not None and (same.expected_texts, same.requests) == (["Exam 2025"], ["title: Exam 2025"])


async def test_a_switch_on_the_data_of_the_plot_still_carries_it(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    script = default_script()
    script["root"][0] = {"call": "plot_pipeline", "args": {"theme": "dark"}}
    swap_models("gemini", script)
    sid = await open_session(client)
    await create_plot(client, sid)

    switched = await switch(client, sid, "seaborn")

    assert switched["carry"]["from_plot"] is True
    carry = read_carry(await _session_state(client, sid), ("scatter-basic", "seaborn"))
    assert carry is not None and carry.theme == "dark"


async def test_a_wish_pasted_with_new_data_reaches_the_plot_of_that_data(
    client: httpx.AsyncClient, swap_models
) -> None:
    """Persona case 06: the title typed with the second paste never reached its plot, since the library had a plot of
    the first data and `keep_plot_request` answered `plot_exists`."""
    keep = {"call": "keep_plot_request", "args": {"change_request": NOTE, "expected_texts": ["Pendulum 2026"]}}
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                keep,
                {"text": "24 rows; the title is kept for the first plot."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await paste(client, sid, SAME_COLUMNS)

    noted = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": NOTE})

    assert noted.status_code == 200, noted.text
    assert tool_answers(fake, "keep_plot_request")[-1] == {"status": "ok", "request_kept": True}
    system = json.dumps([request.config.system_instruction for request in fake.requests][-1], default=str)
    assert EARLIER_DATA_LINE in system  # the root learns that the plot shows the replaced data
    assert (await _session_state(client, sid))[PENDING_REQUEST] == NOTE
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).is_success

    events = await create_plot(client, sid)

    assert next(data for name, data in events if name == "plot")["version"] == 2
    second = adapter_inputs(fake)[1]
    assert NOTE in second and "Pendulum 2026" in second
    assert (await _session_state(client, sid)).get(PENDING_REQUEST) is None  # the shipped plot used it
    latest = get_services().versions.latest_rendered(sid)
    assert latest is not None and latest.data_version == 2  # the paste's number


async def test_a_change_of_the_plot_of_replaced_data_is_kept_for_the_new_data(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The live eval of 2026-11-08: the root sent the title pasted with the new data as a change of the old plot
    (`base: previous`) on unconfirmed data. That plot shows the replaced data, so the request is the first plot's."""
    change = {"change_request": NOTE, "base": "previous", "expected_texts": ["Pendulum 2026"]}
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": change},
                {"text": "Kept for the plot of the new data."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    await paste(client, sid, SAME_COLUMNS)

    noted = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": NOTE})

    assert noted.status_code == 200, noted.text
    assert tool_answers(fake, "plot_pipeline")[-1]["request_kept"] is True
    assert (await _session_state(client, sid))[PENDING_REQUEST] == NOTE


async def test_a_change_of_the_plot_of_this_paste_stays_unkept(client: httpx.AsyncClient, swap_models) -> None:
    """The same change on unconfirmed data of the plot's own paste names a plot that is there: not kept, as before."""
    change = {"change_request": NOTE, "base": "previous"}
    fake = swap_models(
        "gemini",
        {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here."},
                {"call": "plot_pipeline", "args": change},
                {"text": "Confirm the data first."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)
    swapped = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=swapped)).is_success

    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "title: Pendulum 2026"})

    assert tool_answers(fake, "plot_pipeline")[-1].get("request_kept") is None
    assert (await _session_state(client, sid)).get(PENDING_REQUEST) is None


async def test_the_paste_answer_says_when_a_plotted_column_is_gone(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", default_script())
    sid = await open_session(client)

    other = await paste(client, sid, OTHER_COLUMNS)
    back = await paste(client, sid, SAME_COLUMNS)

    assert other["columns_changed"] is True  # neither Study Hours nor Exam Score is in the pendulum table
    assert back["columns_changed"] is True  # the pendulum columns the defaults bound are gone again
    first = await paste(client, await open_session(client, with_data=False), SAME_COLUMNS)
    assert first["columns_changed"] is False  # nothing was replaced


async def test_a_plotted_column_that_no_longer_fits_its_role_is_no_column_gone(
    client: httpx.AsyncClient, swap_models
) -> None:
    """Copilot on #12834: `Exam Score` is in the new table as text, so the y binding does not carry, but the column
    the plot was drawn by is there; the line would wrongly say the earlier data had other columns."""
    swap_models("gemini", default_script())
    sid = await open_session(client)

    texts = await paste(client, sid, "Student,Study Hours,Exam Score\nT01,4.5,good\nT02,5.0,fair\nT03,6.5,good\n")

    assert texts["columns_changed"] is False
    assert {binding["role"]: binding["column"] for binding in texts["bindings"]}.get("y") != "Exam Score"
