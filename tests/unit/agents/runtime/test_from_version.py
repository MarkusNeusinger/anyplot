"""The root reads and rebuilds from the original or an earlier data version (`from_version`).

Persona tests of 2026-11-06: the chat sent users to `.undo()` or a new paste three times, because `prepare_data` and
`query_data` read only the current version: run 01 needed the raw rows for categories after an aggregate, run 02 the
pace column after a weekly sum, run 10 "all 20 teams" after a top 10. Owner decision of 2026-11-06: the chat may read or
rebuild from the original paste or an earlier version and says so ("from your original table: kept 20 of 487 rows");
`.undo()` stays the user's button. The tables here are invented. The tools are called as ADK calls them, on sessions
opened through the real `/v1` routes; one flow drives a whole turn with a scripted root.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import VERSIONS_HEADING, session_context
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.store import DatasetStore
from agents.anyplot.dataset_versions import (
    MAX_DATASET_HISTORY,
    MAX_VERSION_LINE_CHARS,
    KeptVersion,
    VersionRefused,
    kept_versions,
    push_version,
    rebuilt_changes,
    resolve_version,
    undo_version,
    version_lines,
)
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.opening import store_dataset
from agents.anyplot.plugins.ledger import ledger_for
from agents.anyplot.plugins.tool_safety import PLOT_ACTION_REFUSAL, ToolSafetyPlugin
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import (
    CONFIRMED,
    DATASET_HISTORY,
    DATASET_ID,
    DATASET_ORIGINAL,
    DATASET_TOP,
    DATASET_VERSION,
    SessionView,
    initial_state,
    read_session,
)
from agents.anyplot.tools.session import VERSION_MESSAGES, prepare_data, query_data
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_paste_conversions import open_spec, paste, say
from .test_plot_action_guard import before, plot_turn
from .test_service_flow import HEADERS, USER, _session_state, permissive_queue


SID = "s1"
SNAPSHOT = snapshot_from_repo("scatter-basic", "matplotlib")
TEAMS = "Team,Points,Goals\n" + "".join(f"Team {chr(65 + i)},{(i * 37) % 61 + 10},{i + 3}\n" for i in range(24))
"""24 invented teams with distinct points, in no order: a top 10 and a top 20 by points differ in every place."""
RUNS = (
    "Date,Distance (km),Time (min),Pace (min/km)\n"
    "2026-09-01,5.0,27.5,5.5\n2026-09-03,8.0,46.4,5.8\n2026-09-05,10.0,52.0,5.2\n"
    "2026-09-08,6.0,31.2,5.2\n2026-09-10,12.0,72.0,6.0\n2026-09-12,4.0,19.6,4.9\n"
    "2026-09-15,7.0,39.9,5.7\n2026-09-17,15.0,93.0,6.2\n"
)
"""Eight invented runs over three weeks; the fastest pace (4.9) is the run of 2026-09-12."""
TOP_10 = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 10}]
TOP_20 = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 20}]
WEEKLY = [
    {"op": "aggregate", "by": ["Date"], "columns": ["Distance (km)", "Time (min)"], "how": "sum", "period": "week"}
]


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


async def pasted_session(client: httpx.AsyncClient, text: str) -> str:
    sid = await open_spec(client, "scatter-basic")
    await paste(client, sid, text)
    return sid


async def context_for(client: httpx.AsyncClient, sid: str, invocation: str) -> SimpleNamespace:
    """A tool context on the session's state, which the tools write their delta into."""
    context = SimpleNamespace(state=await _session_state(client, sid), session=SimpleNamespace(id=sid))
    context.invocation_id = invocation
    return context


async def write_back(runtime: Runtime, sid: str, context: SimpleNamespace) -> None:
    """What ADK does with a tool's state writes at the end of the call."""
    await runtime.write_state(await runtime.session(USER, sid), dict(context.state))


def fenced(text: str, tag: str) -> Any:
    match = re.search(rf"<{tag}>\n?(.*?)\n?</{tag}>", text, re.DOTALL)
    assert match is not None, text
    return json.loads(match.group(1))


def points_of(sid: str, state: dict[str, Any]) -> list[int]:
    stored = get_services().datasets.get(state[DATASET_ID], sid)
    assert stored is not None
    lines = stored.csv.strip().splitlines()[1:]
    return [int(line.split(",")[1]) for line in lines]


def all_points() -> list[int]:
    return [int(line.split(",")[1]) for line in TEAMS.strip().splitlines()[1:]]


class TestRebuild:
    async def test_the_first_20_after_all_comes_from_the_sorted_original_in_one_call(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-r-1")
        original = context.state[DATASET_ID]
        top10 = await prepare_data(TOP_10, context)
        assert top10["status"] == "ok" and top10["rows"] == 10 and top10["version"] == 2
        second = context.state[DATASET_ID]

        top20 = await prepare_data(TOP_20, context, from_version="original")

        assert top20["status"] == "ok" and top20["rows"] == 20 and top20["version"] == 3
        assert points_of(sid, context.state) == sorted(all_points(), reverse=True)[:20]
        changes = fenced(top20["changes"], "tool_notes")
        assert changes == [
            "from your original table: sorted by Points, descending",
            "kept the first 20 of 24 rows, 4 dropped",
        ]
        assert ledger_for("inv-r-1").dataset_changes[-2:] == changes  # what the `done` event shows the page
        assert ledger_for("inv-r-1").rebuilt_from == [1]
        # Append-only: the top 10 and the original stay, in order, and the rebuild is the next version on top.
        assert context.state[DATASET_HISTORY] == [original, second]
        assert context.state[DATASET_VERSION] == 3 and context.state[DATASET_TOP] == 3
        assert context.state[DATASET_ORIGINAL] == original
        assert get_services().datasets.get(second, sid) is not None

    async def test_a_number_from_the_session_block_starts_there(self, client: httpx.AsyncClient) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-r-2")
        await prepare_data([{"op": "sort", "column": "Points", "descending": True}], context)
        await prepare_data([{"op": "keep_rows", "n": 3}], context)

        answer = await prepare_data([{"op": "keep_rows", "n": 5}], context, from_version="2")

        assert answer["rows"] == 5 and answer["version"] == 4
        assert fenced(answer["changes"], "tool_notes") == ["from version 2: kept the first 5 of 24 rows, 19 dropped"]
        assert points_of(sid, context.state) == sorted(all_points(), reverse=True)[:5]

    async def test_without_operations_an_earlier_version_comes_back_as_it_was(self, client: httpx.AsyncClient) -> None:
        """All 24 teams again (persona run 10): the original as the next version, without an operation to make up."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-r-3")
        await prepare_data(TOP_10, context)

        answer = await prepare_data([], context, from_version="original")

        assert answer["status"] == "ok" and answer["rows"] == 24 and answer["version"] == 3
        assert fenced(answer["changes"], "tool_notes") == ["from your original table, as it was: 24 rows, 3 columns"]
        assert points_of(sid, context.state) == all_points()
        assert ledger_for("inv-r-3").prep_ops == ["sort", "keep_rows"]  # the empty call adds no operation name
        assert ledger_for("inv-r-3").rebuilt_from == [1]  # but the turn changed the data (guard 2a reads both)

    async def test_a_rebuilt_version_is_new_data_the_user_confirms(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200
        context = await context_for(client, sid, "inv-r-4")
        assert read_session(context.state).data_confirmed  # type: ignore[union-attr]

        await prepare_data(TOP_20, context, from_version="original")

        view = read_session(context.state)
        assert view is not None and not view.data_confirmed and context.state[CONFIRMED] is not None

    async def test_undo_after_a_rebuild_steps_back_one_version_as_before(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-r-5")
        await prepare_data(TOP_10, context)
        top10 = context.state[DATASET_ID]
        await prepare_data(TOP_20, context, from_version="original")
        await write_back(runtime, sid, context)

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)

        assert undone.status_code == 200 and undone.json()["version"] == 2
        assert undone.json()["profile"]["rows"] == 10  # the top 10 the rebuild started after, not the original
        state = await _session_state(client, sid)
        assert state[DATASET_ID] == top10 and state[DATASET_TOP] == 3


class TestQueryFromAnEarlierVersion:
    async def test_the_pace_per_run_after_a_weekly_sum_reads_the_original(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, RUNS)
        context = await context_for(client, sid, "inv-q-1")
        weekly = await prepare_data(WEEKLY, context)
        assert weekly["status"] == "ok" and weekly["rows"] == 3
        before = dict(context.state)

        answer = await query_data(
            [{"op": "sort", "column": "Pace (min/km)"}],
            context,
            columns=["Date", "Pace (min/km)"],
            limit=1,
            from_version="original",
        )

        assert answer["status"] == "ok" and answer["rows"] == 8
        assert fenced(answer["table"], "user_data")["rows"] == [["2026-09-12", "4.9"]]
        assert fenced(answer["changes"], "tool_notes") == [
            "from your original table: sorted by Pace (min/km), ascending"
        ]
        assert context.state == before  # a question stores nothing, from any version

    async def test_without_operations_it_reads_the_version_as_it_is(self, client: httpx.AsyncClient) -> None:
        sid = await pasted_session(client, RUNS)
        context = await context_for(client, sid, "inv-q-2")
        await prepare_data(WEEKLY, context)

        answer = await query_data([], context, columns=["Pace (min/km)"], limit=3, from_version="1")

        assert answer["rows"] == 8 and fenced(answer["table"], "user_data")["columns"] == ["Pace (min/km)"]
        assert fenced(answer["changes"], "tool_notes") == ["from your original table, as it was: 8 rows, 4 columns"]

    async def test_no_from_version_reads_the_current_version(self, client: httpx.AsyncClient) -> None:
        """The existing rule wins: without `from_version` a question reads the data the user sees now."""
        sid = await pasted_session(client, RUNS)
        context = await context_for(client, sid, "inv-q-3")
        await prepare_data(WEEKLY, context)

        answer = await query_data([], context)

        assert answer["rows"] == 3 and "changes" not in answer
        assert "Pace (min/km)" not in fenced(answer["table"], "user_data")["columns"]


class TestRefusals:
    async def test_a_version_of_the_data_a_paste_replaced_is_refused(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-x-1")
        await prepare_data(TOP_10, context)
        await prepare_data([{"op": "keep_rows", "n": 3}], context)
        await write_back(runtime, sid, context)
        old = [*context.state[DATASET_HISTORY], context.state[DATASET_ID]]

        await paste(client, sid, RUNS)  # a new lineage: its versions start again at 1
        context = await context_for(client, sid, "inv-x-2")

        for number in ("2", "3"):
            assert await prepare_data(TOP_20, context, from_version=number) == {
                "status": "error",
                "code": "other_paste",
                "message": VERSION_MESSAGES["other_paste"],
            }
            refused = await query_data([], context, from_version=number)
            assert refused["code"] == "other_paste"
        assert all(get_services().datasets.get(dataset_id, sid) is None for dataset_id in old)
        assert context.state[DATASET_VERSION] == 1 and context.state[DATASET_TOP] == 1

    async def test_an_undone_version_is_gone_not_another_paste(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-x-3")
        await prepare_data(TOP_10, context)
        await prepare_data([{"op": "keep_rows", "n": 3}], context)
        await write_back(runtime, sid, context)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)).status_code == 200
        context = await context_for(client, sid, "inv-x-4")

        refused = await prepare_data([], context, from_version="3")

        assert refused["code"] == "version_not_kept"
        assert context.state[DATASET_VERSION] == 2  # nothing stored

    async def test_the_current_version_by_number_without_operations_changes_nothing(
        self, client: httpx.AsyncClient
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-x-5")
        await prepare_data(TOP_10, context)

        for version in ("current", "2"):
            refused = await prepare_data([], context, from_version=version)
            assert refused["status"] == "error" and refused["code"] == "invalid_operations"
        assert context.state[DATASET_VERSION] == 2

    @pytest.mark.parametrize("value", ["previous", "v2", "0", "-1"])
    async def test_a_from_version_outside_the_shape_is_refused_with_its_field(
        self, client: httpx.AsyncClient, value: str
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, f"inv-x-{value}")

        refused = await prepare_data(TOP_10, context, from_version=value)

        assert refused["code"] == "invalid_operations" and "from_version" in refused["errors"]
        assert ToolSafetyPlugin.check("prepare_data", {"operations": TOP_10, "from_version": value}, "anyplot") == (
            "invalid_arguments"
        )
        assert ToolSafetyPlugin.check("query_data", {"operations": [], "from_version": value}, "anyplot") == (
            "invalid_arguments"
        )


class TestToolSafety:
    @pytest.mark.parametrize("value", ["current", "original", "2", 2])
    def test_the_arguments_pass_with_every_form_of_from_version(self, value: object) -> None:
        assert ToolSafetyPlugin.check("prepare_data", {"operations": TOP_10, "from_version": value}, "anyplot") is None
        assert ToolSafetyPlugin.check("query_data", {"operations": [], "from_version": value}, "anyplot") is None

    def test_no_operation_passes_only_from_an_earlier_version(self) -> None:
        assert ToolSafetyPlugin.check("prepare_data", {"operations": [], "from_version": "original"}, "anyplot") is None
        assert ToolSafetyPlugin.check("prepare_data", {"operations": []}, "anyplot") == "invalid_arguments"

    async def test_a_plot_button_turn_refuses_a_rebuild_but_reads_an_earlier_version(self) -> None:
        """B3's plot-action guard holds: the click plots what it confirmed, so no rebuild there; a read stays."""
        for _ in plot_turn(True):
            rebuild = await before("prepare_data", {"operations": TOP_20, "from_version": "original"})
            assert rebuild == {"status": "error", "code": PLOT_ACTION_REFUSAL}
            assert await before("query_data", {"operations": [], "from_version": "original"}) is None


class TestSessionBlock:
    async def test_the_block_lists_the_versions_to_start_from_once_there_are_two(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        heading = VERSIONS_HEADING.split("{", 1)[0]
        context = await context_for(client, sid, "inv-b-1")
        assert heading not in await session_context(context)  # type: ignore[arg-type]

        await prepare_data(TOP_10, context)
        block = await session_context(context)  # type: ignore[arg-type]

        assert f"- {VERSIONS_HEADING.format(count=2)}" in block
        listed = re.search(r"<tool_notes>\n?(.*?)\n?</tool_notes>", block, re.DOTALL)
        assert listed is not None
        assert listed.group(1).splitlines() == [
            "1 (original): 24 rows, 3 columns",
            "2 (current): sorted by Points, descending; kept the first 10 of 24 rows, 14 dropped → 10 rows, 3 columns",
        ]

    async def test_a_scripted_turn_rebuilds_and_the_page_gets_the_where(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-b-2")
        await prepare_data(TOP_10, context)
        await write_back(runtime, sid, context)
        await runtime.write_state(await runtime.session(USER, sid), {"anyplot.summary_pending": None})
        script = default_script()
        script["root"] = [
            {"call": "prepare_data", "args": {"operations": TOP_20, "from_version": "original"}},
            {"text": "From your original table: kept the first 20 of 24 teams by points."},
        ]
        fake = swap_models("anthropic-vertex", script)

        events = await say(client, sid, {"text": "No, the first 20 after all."})

        done = events[-1][1]
        assert done["dataset"]["version"] == 3 and done["dataset"]["profile"]["rows"] == 20
        assert done["dataset"]["changes"][0] == "from your original table: sorted by Points, descending"
        first_block = fake.calls[0]["system"][-1]["text"]  # type: ignore[attr-defined]
        assert "2 (current): sorted by Points, descending; kept the first 10 of 24 rows" in first_block


# --- The versions themselves, on a bare store ----------------------------------------------------


def opened(store: DatasetStore, text: str = "a,b\n1,2\n3,4\n5,6\n") -> dict[str, Any]:
    state = initial_state(
        spec_id="scatter-basic", library="matplotlib", locale="en", snapshot=SNAPSHOT, normalised="x = 1", readiness={}
    )
    state.update(store_dataset(store, SID, parse_dataset(text), SNAPSHOT, notes_screened=True).state_delta())
    return state


def view_of(state: dict[str, Any]) -> SessionView:
    view = read_session(state)
    assert view is not None
    return view


def push(store: DatasetStore, state: dict[str, Any], rows: int) -> None:
    text = "a,b\n" + "".join(f"{i},{i}\n" for i in range(rows))
    version = push_version(store, SID, view_of(state), parse_dataset(text), SNAPSHOT, changes=[f"kept {rows} rows"])
    state.update(version.delta)


def test_the_original_outlives_the_history_cap_and_undo_never_reaches_it() -> None:
    store = DatasetStore()
    state = opened(store)
    original = state[DATASET_ID]
    for rows in range(2, 2 + MAX_DATASET_HISTORY + 2):  # versions 2 to 8: the original leaves the history at 7
        push(store, state, rows)

    assert original not in state[DATASET_HISTORY] and len(state[DATASET_HISTORY]) == MAX_DATASET_HISTORY
    assert store.get(original, SID) is not None and state[DATASET_ORIGINAL] == original
    kept = kept_versions(store, SID, view_of(state))
    assert [version.number for version in kept] == [1, 3, 4, 5, 6, 7, 8]
    assert len(store) == 7  # the current, five for undo and the original; version 2 left the store
    # Undo as before: five steps back, then nothing to undo, and the original stays for `from_version`.
    for _ in range(MAX_DATASET_HISTORY):
        restored = undo_version(store, SID, view_of(state), SNAPSHOT)
        assert restored is not None
        state.update(restored.delta)
    assert state[DATASET_VERSION] == 3
    assert undo_version(store, SID, view_of(state), SNAPSHOT) is None
    assert store.get(original, SID) is not None
    assert resolve_version(kept_versions(store, SID, view_of(state)), view_of(state), "original").stored.csv == (
        "a,b\n1,2\n3,4\n5,6\n"
    )


def test_a_new_paste_deletes_the_original_kept_past_the_history() -> None:
    store = DatasetStore()
    state = opened(store)
    for rows in range(2, 2 + MAX_DATASET_HISTORY + 2):
        push(store, state, rows)
    view = view_of(state)

    ingested = store_dataset(
        store, SID, parse_dataset("x,y\n1,1\n2,2\n"), SNAPSHOT, view.dataset_id, view.earlier_datasets
    )

    assert len(store) == 1 and store.get(ingested.dataset_id, SID) is not None


def test_resolve_names_the_refusal_by_the_highest_number_reached() -> None:
    store = DatasetStore()
    state = opened(store)
    push(store, state, 2)
    push(store, state, 3)
    state.update(undo_version(store, SID, view_of(state), SNAPSHOT).delta)  # type: ignore[union-attr]
    view = view_of(state)
    kept = kept_versions(store, SID, view)

    assert resolve_version(kept, view, "current").number == 2
    assert resolve_version(kept, view, 1).original
    with pytest.raises(VersionRefused) as undone:
        resolve_version(kept, view, 3)
    with pytest.raises(VersionRefused) as other:
        resolve_version(kept, view, 4)
    assert (undone.value.code, other.value.code) == ("version_not_kept", "other_paste")


def test_state_from_before_the_key_finds_the_original_in_the_history() -> None:
    store = DatasetStore()
    state = opened(store)
    original = state.pop(DATASET_ORIGINAL)
    state.pop(DATASET_TOP)
    push(store, state, 2)

    assert state[DATASET_ORIGINAL] == original  # the first push writes it
    del state[DATASET_ORIGINAL]
    assert kept_versions(store, SID, view_of(state))[0].stored.dataset_id == original


def test_the_lines_and_the_where() -> None:
    store = DatasetStore()
    state = opened(store)
    push(store, state, 2)
    kept = kept_versions(store, SID, view_of(state))
    long = KeptVersion(5, replace(kept[1].stored, changes=["x" * 400]), current=False, original=False)

    assert version_lines(kept) == ["1 (original): 3 rows, 2 columns", "2 (current): kept 2 rows → 2 rows, 2 columns"]
    assert len(version_lines([long])[0].split(" → ")[0]) == len("5: ") + MAX_VERSION_LINE_CHARS
    assert rebuilt_changes(kept[1], ["sorted by a, ascending"]) == ["sorted by a, ascending"]  # the current: as is
    assert rebuilt_changes(kept[0], ["sorted by a, ascending", "kept 2"]) == [
        "from your original table: sorted by a, ascending",
        "kept 2",
    ]
    assert rebuilt_changes(long, []) == ["from version 5, as it was: 2 rows, 2 columns"]
    assert len(rebuilt_changes(kept[0], ["y" * 300])[0]) == 300
