"""The page's "plot the new data" (`plot_new_data`, owner decision of 2026-11-08): the latest version as its base
behind a code guard, else the fresh start.

When the data comes from the paste the library's latest plot drew and the bindings are the same, role for role, the
run changes that version with one server-written request (`DATA_CHANGE_REQUEST`), which the stored lineage leaves
out. Otherwise (a new paste, other bindings, no plot yet) it starts from the catalogue code as `.start_over()` does,
with the remembered decisions and the theme the user asked for. The result and the plot event say which
(`new_data`).
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest

from agents.anyplot import telemetry
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.dataset_versions import push_version
from agents.anyplot.pipeline import (
    DATA_CHANGE_REQUEST,
    KEPT_CHANGE_LINE,
    PENDING_KEYS,
    Run,
    change_waits,
    hold_request,
    keep_pending_request,
    lineage_requests,
    new_data_base,
    new_data_request,
    pending_fate,
    run_theme,
    settle_pending_request,
    take_pending_request,
    users_request,
)
from agents.anyplot.plugins.tool_safety import DATA_CHANGED
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.schemas import MAX_CHANGE_REQUEST_CHARS, MAX_RUN_REQUEST_CHARS, Binding, PipelineArgs, PlotResult
from agents.anyplot.services import CodeVersion, Services, get_services
from agents.anyplot.session_state import (
    BINDINGS,
    PENDING_BASE,
    PENDING_CLEARED,
    PENDING_EXPECTED_TEXTS,
    PENDING_REQUEST,
    read_session,
)
from agents.main import ACTION_MESSAGES, PLOT_ACTIONS, Runtime, app, get_runtime

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
    tool_responses,
)


X = Binding(role="x", column="Study Hours")
Y = Binding(role="y", column="Exam Score")
KEEP_PLAN: dict[str, Any] = {"edits": [], "title": "Exam Score by Study Hours", "changes": ["Kept the plot"]}
PREVIOUS_MARK = 'title = "Exam Score by Study Hours"'
"""A line of the shipped version's working code (`SCATTER_PLAN`) that the catalogue code lacks."""
WISH = "log scale on y"
"""A change of the plot the user asks for in a message that also changes the data."""


def version(**overrides: Any) -> CodeVersion:
    fields: dict[str, Any] = {
        "number": 1,
        "working": "w",
        "run_form": "r",
        "export": "e",
        "data_csv": "a\n1\n",
        "render_id": "r1",
        "result": PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
        "library": "matplotlib",
        "spec_id": "scatter-basic",
        "data_version": 2,
        "bindings": [X, Y],
    }
    return CodeVersion(**{**fields, **overrides})


class FakeView:
    """The two fields of a `SessionView` the guard reads."""

    def __init__(self, bindings: list[Binding]) -> None:
        self.bindings = bindings


# --- the guard, the theme and the lineage ----------------------------------------------------


def test_the_latest_version_is_the_base_only_for_the_same_paste_and_bindings() -> None:
    same = FakeView([Y, X])  # the same assignments in another order
    assert new_data_base(version(), same, 1, None) == "previous"  # data v2 of the paste numbered 1
    assert new_data_base(version(data_version=1), same, 1, None) == "previous"  # the paste itself
    assert new_data_base(None, same, 1, None) == "no_plot"
    assert new_data_base(version(data_version=2), same, 3, None) == "other_paste"  # a new paste, numbered 3
    assert new_data_base(version(data_version=None), same, 1, None) == "other_paste"  # no stamp: other data
    rebound = FakeView([Binding(role="x", column="Exam Score"), Binding(role="y", column="Study Hours")])
    assert new_data_base(version(), rebound, 1, None) == "bindings_changed"
    assert new_data_base(version(), FakeView([X]), 1, None) == "bindings_changed"  # a role left open
    assert new_data_base(version(bindings=None), same, 1, None) == "bindings_changed"


def test_a_computed_table_that_replaced_the_data_is_other_data() -> None:
    """`generate_data` and `run_data_code` keep the paste's original (`push_version(rebind=True)`), so the number
    alone would take a formula's table named like the paste's columns for a change of the paste."""
    same = FakeView([X, Y])
    assert new_data_base(version(), same, 1, "formula: y = sin(x)") == "other_data"  # a paste's plot, a formula now
    computed = version(data_source="formula: y = sin(x)")
    assert new_data_base(computed, same, 1, "formula: y = sin(x)") == "previous"  # a change of the computed table
    assert new_data_base(computed, same, 1, "formula: y = x**2") == "other_data"  # another formula


def test_a_waiting_first_plot_note_makes_it_a_first_plot() -> None:
    """A note kept for a first plot is taken only by a fresh run; from the latest version it would wait unseen."""
    same = FakeView([X, Y])
    assert new_data_base(version(), same, 1, None, note_kept=True) == "kept_note"
    assert new_data_base(version(data_version=1), same, 3, None, note_kept=True) == "other_paste"


def test_the_fresh_start_of_new_data_keeps_the_theme_the_user_asked_for() -> None:
    asked = version(theme="dark", theme_asked=True)
    assert run_theme(None, "light", None, None, asked) == ("dark", True)
    assert run_theme(None, "light", None, None, version(theme="dark")) == ("light", False)  # the site's, not asked
    assert run_theme("light", "dark", None, None, asked) == ("light", True)  # a theme asked for now wins
    assert run_theme(None, "light", None) == ("light", False)  # `.start_over()` passes no latest version


def test_the_server_request_stays_out_of_the_lineage() -> None:
    standing = ["title: Scores 2026"]
    ran = SimpleNamespace(user_requests=standing, change_request=DATA_CHANGE_REQUEST)
    assert lineage_requests(cast(Run, ran)) == standing
    ran.change_request = "red markers"
    assert lineage_requests(cast(Run, ran)) == [*standing, "red markers"]
    # A kept change of the plot that joined the server's request: only the user's part is a standing request.
    ran.change_request = new_data_request(WISH)
    assert lineage_requests(cast(Run, ran)) == [*standing, WISH]


# --- a change of the plot kept while the data waited -------------------------------------------


def previous(request: str = WISH, **fields: Any) -> PipelineArgs:
    return PipelineArgs(change_request=request, base="previous", **fields)


def test_the_kept_change_stands_after_the_servers_request_and_reads_back() -> None:
    joined = new_data_request(WISH)

    assert joined.startswith(DATA_CHANGE_REQUEST) and joined.endswith(f"{KEPT_CHANGE_LINE}\n{WISH}")
    assert users_request(joined) == WISH and users_request(WISH) == WISH
    assert new_data_request("  ") == DATA_CHANGE_REQUEST and users_request(DATA_CHANGE_REQUEST) == ""
    # Only the two forms the server builds are the server's: a request that merely begins with its sentence stays.
    begun = f"{DATA_CHANGE_REQUEST} Also make the markers red."
    assert users_request(begun) == begun and users_request(f"{DATA_CHANGE_REQUEST}\n{WISH}") != WISH
    # The user's part is never cut to make room: the longest one still fits what the adapter and the reviewer take.
    assert len(new_data_request("x" * MAX_CHANGE_REQUEST_CHARS)) <= MAX_RUN_REQUEST_CHARS


@pytest.mark.parametrize("reason", ["data_unconfirmed", "incomplete_bindings"])
def test_a_change_of_the_plot_is_kept_as_one_while_the_data_waits(reason: Any) -> None:
    state: dict[str, Any] = {BINDINGS: [X.model_dump(), Y.model_dump()]}

    assert keep_pending_request(state, previous(expected_texts=["Scores 2026"]), reason)

    assert (state[PENDING_REQUEST], state[PENDING_BASE]) == (WISH, "previous")
    assert state[PENDING_EXPECTED_TEXTS] == ["Scores 2026"] and change_waits(state)
    # On data that is ready nothing waits: the run draws the change at once.
    assert not keep_pending_request({}, previous(), None)


def test_a_first_plots_note_stays_one_when_a_change_joins_it() -> None:
    """A fresh start the user asked for stays one: the note is taken by the fresh run, with the change in it."""
    state: dict[str, Any] = {}
    hold_request(state, PipelineArgs(change_request="title: Cohort 2026"))
    hold_request(state, previous())

    assert state[PENDING_REQUEST] == f"title: Cohort 2026\n{WISH}" and state.get(PENDING_BASE) is None
    assert not change_waits(state)
    # And a change that waits first becomes a first plot's note with the fresh start asked for after it.
    later: dict[str, Any] = {}
    hold_request(later, previous())
    hold_request(later, PipelineArgs(change_request="start again, title: Cohort 2026"))
    assert later.get(PENDING_BASE) is None and not change_waits(later)


def test_plot_the_new_data_takes_the_kept_change_after_the_servers_request() -> None:
    state: dict[str, Any] = {}
    hold_request(state, previous(expected_texts=["Scores 2026"]))
    action = PipelineArgs(base="previous").model_copy(update={"change_request": DATA_CHANGE_REQUEST})

    taken = take_pending_request(state, action)

    assert taken.change_request == new_data_request(WISH) and taken.expected_texts == ["Scores 2026"]
    assert pending_fate(state, action) == "used" and state[PENDING_REQUEST] == WISH  # kept until the run ends
    # An undo back to the plotted data brings no request of the server's: the kept change stands alone.
    assert take_pending_request(state, PipelineArgs(base="previous")).change_request == WISH
    # A typed change of the plot takes it in front of its own; a fresh start takes it as any note.
    assert take_pending_request(state, previous("blue markers")).change_request == f"{WISH}\nblue markers"
    assert take_pending_request(state, PipelineArgs()).change_request == WISH


def test_a_change_of_the_plot_takes_no_first_plots_note() -> None:
    state: dict[str, Any] = {}
    hold_request(state, PipelineArgs(change_request="title: Cohort 2026"))
    change = previous("blue markers")

    assert take_pending_request(state, change) == change and pending_fate(state, change) is None
    settle_pending_request(state, change, shipped=True)
    assert state[PENDING_REQUEST] == "title: Cohort 2026"


def test_the_kept_change_goes_with_the_plot_that_drew_it_and_stays_with_one_that_did_not() -> None:
    state: dict[str, Any] = {}
    hold_request(state, previous())
    found = {key: state.get(key) for key in PENDING_KEYS}
    ran = take_pending_request(state, previous("blue markers"))

    settle_pending_request(state, ran, shipped=False, kept_change=found)
    assert (state[PENDING_REQUEST], state[PENDING_BASE]) == (WISH, "previous")  # not the run's joined request
    # The run's own data step stored a new version, which drops a kept note: the run puts it back.
    state.update(PENDING_CLEARED)
    settle_pending_request(state, ran, shipped=False, kept_change=found)
    assert (state[PENDING_REQUEST], state[PENDING_BASE]) == (WISH, "previous")

    settle_pending_request(state, ran, shipped=True, kept_change=found)
    assert all(state.get(key) is None for key in PENDING_KEYS)


def test_only_a_first_plots_note_makes_the_new_data_a_fresh_start() -> None:
    """`note_kept` is a first plot's note; a kept change of the plot leaves the latest version as the base."""
    same = FakeView([X, Y])
    assert new_data_base(version(), same, 1, None, note_kept=False) == "previous"
    assert new_data_base(version(), same, 1, None, note_kept=True) == "kept_note"


def test_the_action_is_a_plot_button_with_its_own_message() -> None:
    assert "plot_new_data" in PLOT_ACTIONS
    assert ACTION_MESSAGES["plot_new_data"].startswith("[action] Create the plot")


# --- turns through /v1 -----------------------------------------------------------------------


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


def script(*plans: dict[str, Any], theme: str | None = None) -> dict[str, list[Any]]:
    """The first plot (with `theme` when given), then one bare plot per further plan."""
    first = {"call": "plot_pipeline", "args": {"theme": theme} if theme else {}}
    root: list[Any] = [first, {"text": "Here."}]
    for _ in plans[1:]:
        root += [{"call": "plot_pipeline", "args": {}}, {"text": "Here is the new data."}]
    return {
        "root": root,
        "adapter": [{"json": plan} for plan in plans],
        "reviewer": [{"json": VERDICT_OK} for _ in plans],
    }


async def change_data(runtime: Runtime, services: Services, sid: str) -> None:
    """A change of the paste's data, as `prepare_data` stores it: the last row dropped, the bindings carried."""
    session = await runtime.session(USER, sid)
    view = read_session(session.state)
    assert view is not None and view.dataset_id is not None
    stored = services.datasets.get(view.dataset_id, sid)
    assert stored is not None
    fewer = parse_dataset("\n".join(stored.csv.strip().splitlines()[:-1]) + "\n")
    await runtime.write_state(session, push_version(services.datasets, sid, view, fewer, view.snapshot).delta)


async def plot_new_data(client: httpx.AsyncClient, sid: str) -> dict[str, Any]:
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).is_success
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "plot_new_data"})
    assert response.status_code == 200, response.text
    return next(data for name, data in parse_sse(response.text) if name == "plot")


def runs(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
    return [line for line in lines if line["event"] == "pipeline_run"]


async def test_a_change_of_the_same_paste_starts_from_the_latest_version(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    fake = swap_models("gemini", script(SCATTER_PLAN, KEEP_PLAN))
    sid = await open_session(client)
    await create_plot(client, sid)
    await change_data(runtime, services, sid)

    plot = await plot_new_data(client, sid)

    assert (plot["status"], plot["version"], plot["new_data"]) == ("ok", 2, "previous")
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK in second  # the shipped version's code, not the catalogue's
    assert DATA_CHANGE_REQUEST in second
    stored = get_services().versions.latest_rendered(sid)
    assert stored is not None and stored.requests == [] and stored.data_version == 2
    assert stored.bindings == [X, Y]
    assert [(run["base"], run["fresh"], run.get("new_data")) for run in runs(caplog)] == [
        ("catalogue", True, None),
        ("previous", False, "previous"),
    ]


async def test_other_bindings_start_from_the_catalogue_plot_in_the_theme_asked_for(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models, backend: FakeBackend
) -> None:
    fake = swap_models("gemini", script(SCATTER_PLAN, SCATTER_PLAN, theme="dark"))
    sid = await open_session(client)
    await create_plot(client, sid)
    swapped = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=swapped)).is_success

    plot = await plot_new_data(client, sid)

    assert plot["new_data"] == "bindings_changed"
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK not in second and DATA_CHANGE_REQUEST not in second  # the catalogue code, no request
    assert backend.jobs[-1].themes == ("dark",)  # the theme the user asked for on the plot before
    stored = get_services().versions.latest_rendered(sid)
    assert stored is not None and stored.theme_asked


async def test_a_new_paste_starts_fresh_and_takes_the_wish_sent_with_it(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    fake = swap_models("gemini", script(SCATTER_PLAN, SCATTER_PLAN))
    sid = await open_session(client)
    await create_plot(client, sid)
    pasted = "Student,Study Hours,Exam Score\nT01,4.5,71\nT02,5.0,77\nT03,6.5,80\n"
    assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": pasted})).is_success
    await runtime.write_state(await runtime.session(USER, sid), {PENDING_REQUEST: "title: Cohort 2026"})

    plot = await plot_new_data(client, sid)

    assert plot["new_data"] == "other_paste"
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK not in second and "title: Cohort 2026" in second
    assert (await _session_state(client, sid)).get(PENDING_REQUEST) is None


async def test_an_undo_back_to_the_plotted_data_says_nothing_changed(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models
) -> None:
    """Paste, plot, change, undo: the data is the one the plot drew again, so the run starts from that version
    without the server's data-change request."""
    fake = swap_models("gemini", script(SCATTER_PLAN, KEEP_PLAN))
    sid = await open_session(client)
    await create_plot(client, sid)
    await change_data(runtime, services, sid)
    assert (await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)).is_success

    plot = await plot_new_data(client, sid)

    assert plot["new_data"] == "previous"
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK in second and DATA_CHANGE_REQUEST not in second


async def test_a_waiting_note_starts_fresh_and_reaches_the_plot(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models
) -> None:
    fake = swap_models("gemini", script(SCATTER_PLAN, SCATTER_PLAN))
    sid = await open_session(client)
    await create_plot(client, sid)
    await change_data(runtime, services, sid)
    await runtime.write_state(await runtime.session(USER, sid), {PENDING_REQUEST: "title: Cohort 2026"})

    plot = await plot_new_data(client, sid)

    assert plot["new_data"] == "kept_note"
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK not in second and "title: Cohort 2026" in second
    assert (await _session_state(client, sid)).get(PENDING_REQUEST) is None


@pytest.mark.parametrize("tool", ["plot_pipeline", "keep_plot_request"])
async def test_a_change_asked_for_with_a_data_change_reaches_the_plot_of_the_new_data(
    client: httpx.AsyncClient, swap_models, tool: str
) -> None:
    """Persona round of 2026-11-11: one message changed the data and asked for a log scale. The plot of the new data
    came without it, since a change of an existing plot was never kept, and the root had said it was noted. Either
    call after the data tool keeps it now: the keep tool, which `root.md` names, or a plot call the server refuses
    in a turn that changed the data."""
    sort = {"call": "prepare_data", "args": {"operations": [{"op": "sort", "column": "Exam Score"}]}}
    args = {"change_request": WISH, "base": "previous"} if tool == "plot_pipeline" else {"change_request": WISH}
    change = {"call": tool, "args": args}
    plot = {"call": "plot_pipeline", "args": {}}
    fake = swap_models(
        "gemini",
        {
            "root": [
                plot,
                {"text": "Here."},
                sort,
                change,
                {"text": "Sorted."},
                plot,
                {"text": "Here is the new data."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    asked = await client.post(
        f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "sort by score and use a log scale on y"}
    )

    assert not any(name == "plot" for name, _ in parse_sse(asked.text))
    answer = tool_responses(fake, tool)[-1]
    if tool == "plot_pipeline":
        assert (answer["code"], answer["reason"], answer["request_kept"]) == (DATA_CHANGED, "data_unconfirmed", True)
    else:
        assert answer == {"status": "ok", "request_kept": True}
    state = await _session_state(client, sid)
    assert (state[PENDING_REQUEST], state[PENDING_BASE]) == (WISH, "previous")

    shown = await plot_new_data(client, sid)

    assert (shown["status"], shown["version"], shown["new_data"]) == ("ok", 2, "previous")
    second = adapter_inputs(fake)[1]
    assert PREVIOUS_MARK in second and DATA_CHANGE_REQUEST in second
    assert KEPT_CHANGE_LINE in second and WISH in second
    assert tool_responses(fake, "plot_pipeline")[-1]["kept_request"] == "used"
    stored = get_services().versions.latest_rendered(sid)
    assert stored is not None and stored.requests == [WISH] and stored.data_version == 2
    state = await _session_state(client, sid)
    assert state.get(PENDING_REQUEST) is None and state.get(PENDING_BASE) is None


async def test_the_keep_tool_keeps_a_change_of_the_plot_only_while_the_data_waits(
    client: httpx.AsyncClient, runtime: Runtime, services: Services, swap_models
) -> None:
    keep = {"call": "keep_plot_request", "args": {"change_request": WISH}}
    plot = {"call": "plot_pipeline", "args": {}}
    fake = swap_models(
        "gemini",
        {
            "root": [
                plot,
                {"text": "Here."},
                keep,
                {"text": "Not kept."},
                keep,
                {"text": "Kept."},
                plot,
                {"text": "."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": KEEP_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        },
    )
    sid = await open_session(client)
    await create_plot(client, sid)

    # On confirmed data the change runs at once, so the tool keeps nothing and says why.
    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "log scale on y please"})
    assert tool_responses(fake, "keep_plot_request")[-1] == {
        "status": "ok",
        "request_kept": False,
        "reason": "plot_exists",
    }

    await change_data(runtime, services, sid)
    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "log scale on y please"})

    assert tool_responses(fake, "keep_plot_request")[-1] == {"status": "ok", "request_kept": True}
    state = await _session_state(client, sid)
    assert (state[PENDING_REQUEST], state[PENDING_BASE]) == (WISH, "previous")
    shown = await plot_new_data(client, sid)
    assert shown["new_data"] == "previous" and WISH in adapter_inputs(fake)[1]


async def test_the_plot_event_of_every_other_run_names_no_base(client: httpx.AsyncClient, swap_models) -> None:
    swap_models("gemini", script(SCATTER_PLAN))
    sid = await open_session(client)

    events = await create_plot(client, sid)

    assert "new_data" not in next(data for name, data in events if name == "plot")
