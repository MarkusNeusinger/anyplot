"""The view of the plot (`plot_view.py`): which rows of the table a plot run draws.

Owner decision of 2026-11-13: a selection and a top N belong with the plot and leave the table as pasted, cleaning
stays a step of the table, and the user's own word wins. The view is typed session state that `prepare_data` routes a
`keep_rows` into; a plot run draws the table through it and stores no data version for it.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from pydantic import TypeAdapter

from agents.anyplot import pipeline, plot_view
from agents.anyplot.agent import VIEW_BEFORE_LINE, VIEW_HEADING, session_context
from agents.anyplot.data.fidelity import COMBINED_IN_VIEW_HEAD
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, PrepareError
from agents.anyplot.data.store import DatasetStore, StoredDataset
from agents.anyplot.dataset_versions import push_version
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.plot_view import (
    CALENDAR_ORDER_LINE,
    CLEARED_LINE,
    IDLE_SELECTION_LINE,
    OLDEST_FIRST_LINE,
    PLOT_VIEW,
    PlotView,
    ViewRefused,
    drawn_in_order,
    merged,
    route,
    run_order,
    table_only,
    view_of,
)
from agents.anyplot.plugins.ledger import ToolCall, ledger_for
from agents.anyplot.plugins.tool_safety import TOOL_ALLOWED, call_outcome, changed_data
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.schemas import MAX_CHANGE_CHARS, Binding, DrawnRows
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import DATASET_ID, PLOT_VIEW_BEFORE, read_session
from agents.anyplot.tools.session import (
    NO_VIEW_TO_ASK,
    VIEW_APPLIED,
    VIEW_BREAKS_BINDINGS,
    VIEW_CLEARED,
    prepare_data,
    query_data,
)
from agents.main import Runtime, app, get_runtime
from agents.stream import turn_outcome

from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK, FakeAnthropic, default_script
from .test_from_version import TEAMS, context_for, fenced, pasted_session, points_of, write_back
from .test_paste_conversions import SID, paste
from .test_row_fidelity import (
    HOURS,
    LINE_BINDINGS,
    asked_then_chosen,
    bind_and_confirm,
    open_line_on_scatter_code,
    plot_with_choice,
    table_rows,
)
from .test_service_flow import HEADERS, SECOND_PLAN, USER, create_plot, permissive_queue, say


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


OPERATIONS = TypeAdapter(list[Operation])
CITIES = "Stadt,Land,Umsatz,Code\nBern,CH,1200,7\nKöln,DE,800,x1\nBasel,CH,800,9\nGenf,CH,800,3\nWien,AT,300,x2\n"
TOP_2 = [{"op": "sort", "column": "Umsatz", "descending": True}, {"op": "keep_rows", "n": 2}]


def only(column: str, test: str, value: object) -> dict[str, Any]:
    return {"op": "keep_rows", "where": [{"column": column, "test": test, "value": value}]}


def routed(*operations: dict[str, Any]) -> plot_view.Routed:
    return route(OPERATIONS.validate_python(list(operations)))


def view_from(*operations: dict[str, Any], held: PlotView | None = None) -> PlotView:
    return merged(held or PlotView(), routed(*operations))


class TestRoute:
    def test_the_end_of_a_call_is_the_views_and_what_stands_before_it_the_tables(self) -> None:
        rename = {"op": "rename", "column": "Umsatz", "name": "Revenue"}

        split = routed(
            rename, only("Land", "eq", "CH"), {"op": "sort", "column": "Revenue"}, {"op": "keep_rows", "n": 3}
        )

        assert [operation.op for operation in split.table] == ["rename"]
        assert [[condition.column for condition in where] for where in split.selections] == [["Land"]]
        assert split.top == plot_view.Top(column="Revenue", descending=False, n=3) and split.view

    def test_a_keep_rows_that_another_operation_builds_on_is_the_tables(self) -> None:
        """The selected rows summed per country need the other rows gone: the whole call changes the table."""
        total = {"op": "aggregate", "by": ["Land"], "column": "Umsatz", "how": "sum"}

        split = routed(only("Land", "ne", "AT"), total)

        assert [operation.op for operation in split.table] == ["keep_rows", "aggregate"] and not split.view

    @pytest.mark.parametrize(
        "operations",
        [
            [{"op": "keep_rows", "n": 3}],  # the first rows of no ranking: nothing a view could keep
            [{"op": "sort", "column": "Umsatz"}],  # a sort alone orders the table
            [{"op": "sort", "column": "Umsatz"}, {"op": "keep_rows", "n": 3, "target": "table"}],
            [{**only("Land", "eq", "CH"), "target": "table"}],
        ],
    )
    def test_what_no_view_can_hold_or_the_user_sends_to_the_table_is_the_tables(
        self, operations: list[dict[str, Any]]
    ) -> None:
        split = routed(*operations)

        assert len(split.table) == len(operations) and not split.view

    def test_reset_comes_first_or_not_at_all(self) -> None:
        assert routed({"op": "reset_view"}).reset and routed({"op": "reset_view"}).view
        assert routed({"op": "reset_view"}, *TOP_2).top is not None
        with pytest.raises(ViewRefused, match="first operation"):
            routed(only("Land", "eq", "CH"), {"op": "reset_view"})

    def test_a_call_from_an_earlier_version_is_the_tables_whatever_it_keeps(self) -> None:
        split = table_only(OPERATIONS.validate_python([{"op": "reset_view"}, *TOP_2]))

        assert [operation.op for operation in split.table] == ["sort", "keep_rows"]
        assert split.reset and split.top is None and not split.selections


class TestMerged:
    def test_a_new_top_n_takes_the_place_of_the_one_there(self) -> None:
        held = view_from(only("Land", "eq", "CH"), *TOP_2)

        view = view_from({"op": "sort", "column": "Umsatz"}, {"op": "keep_rows", "n": 4}, held=held)

        assert view.top == plot_view.Top(column="Umsatz", descending=False, n=4)
        assert len(view.selections) == 1  # the selection stays

    def test_a_selection_on_the_same_columns_replaces_and_another_one_narrows(self) -> None:
        held = view_from(only("Land", "eq", "CH"), *TOP_2)

        other_country = view_from(only("Land", "eq", "AT"), held=held)
        narrowed = view_from(only("Umsatz", "ge", 800), held=held)

        assert [where[0].value for where in other_country.selections] == ["AT"] and other_country.top == held.top
        assert [where[0].column for where in narrowed.selections] == ["Land", "Umsatz"]

    def test_reset_clears_before_the_rest_of_the_call_applies(self) -> None:
        held = view_from(only("Land", "eq", "CH"), *TOP_2)

        assert view_from({"op": "reset_view"}, held=held).empty
        again = view_from({"op": "reset_view"}, only("Umsatz", "ge", 800), held=held)
        assert [where[0].column for where in again.selections] == ["Umsatz"] and again.top is None

    def test_a_fourth_selection_is_refused_with_the_way_out(self) -> None:
        held = view_from(only("Land", "eq", "CH"), only("Umsatz", "ge", 1), only("Stadt", "ne", "x"))

        with pytest.raises(ViewRefused, match="reset_view"):
            view_from(only("Code", "ne", "y"), held=held)

    def test_a_stamp_tells_two_views_apart_and_is_none_for_every_row(self) -> None:
        assert PlotView().stamp() is None
        assert view_from(*TOP_2).stamp() != view_from(only("Land", "eq", "CH"), *TOP_2).stamp()
        assert view_from(*TOP_2).stamp() == view_from(*TOP_2).stamp()


class TestViewOf:
    def test_the_selections_apply_first_and_then_the_top_n(self) -> None:
        table = parse_dataset(CITIES)

        seen = view_of(table, view_from(only("Land", "eq", "CH"), *TOP_2))

        assert seen.parsed.csv.splitlines() == ["Stadt,Land,Umsatz,Code", "Bern,CH,1200,7", "Basel,CH,800,9"]
        assert (seen.rows, seen.of_rows) == (2, 5) and seen.summary(3) == "the plot draws 2 of 5 rows of data v3"
        assert seen.changes[0] == "kept 3 of 5 rows where Land = 'CH', 2 dropped"
        assert "the cut falls among 2 rows with Umsatz 800" in seen.changes[2]  # the tie of a top N is named here too

    def test_a_text_column_stays_text_also_when_the_rows_left_read_as_numbers(self) -> None:
        """`Code` is text for `x1` and `x2`; the Swiss rows hold 7, 9 and 3. A column that changed its kind would
        move the bindings the user confirmed."""
        table = parse_dataset(CITIES)

        seen = view_of(table, view_from(only("Land", "eq", "CH")))

        assert table.column_dtypes["Code"] == "text" and seen.parsed.column_dtypes == table.column_dtypes

    def test_a_view_that_fits_no_row_or_no_column_raises(self) -> None:
        table = parse_dataset(CITIES)

        with pytest.raises(PrepareError) as empty:
            view_of(table, view_from(only("Land", "eq", "FR")))
        with pytest.raises(PrepareError) as unknown:
            view_of(table, view_from(only("Ort", "eq", "Bern")))

        assert (empty.value.code, unknown.value.code) == ("empty_result", "unknown_column")

    def test_a_stored_view_with_a_day_bound_on_period_labels_is_cleared_when_read(self) -> None:
        """Quarter labels compare as text, so a day bound on them is refused: a view stored with one before draws
        every row again, with the line that says so, and reading the session goes on."""
        table = shown("Quartal,Menge\n2017-Q4,4\n2018-Q1,5\n2018-Q2,6\n")
        state = plot_view.view_delta(view_from(only("Quartal", "ge", "2018-01-01")))

        held = plot_view.current(state, table)

        assert table.column_dtypes["Quartal"] == "text"
        assert held.view.empty and held.viewed is None and held.cleared == CLEARED_LINE

    def test_the_note_of_a_run_keeps_its_counts_and_shortens_the_views_words(self) -> None:
        table = parse_dataset(CITIES)
        view = view_from(only("Land", "eq", "CH"), *TOP_2)
        seen = view_of(table, view)

        assert (
            seen.note(view, 3, 200) == "The plot draws 2 of the 5 rows of data v3 (view: Land = 'CH'; top 2 by Umsatz)"
        )
        short = seen.note(view, 3, 60)
        assert short.startswith("The plot draws 2 of the 5 rows of data v3 (view: ") and short.endswith("…)")
        assert len(short) == 60

    def test_the_adapter_and_the_reviewer_get_the_notes_counts_and_the_views_words(self) -> None:
        table = parse_dataset(CITIES)
        view = view_from(only("Land", "eq", "CH"), *TOP_2)

        drawn = view_of(table, view).drawn_rows(view)

        assert drawn == DrawnRows(rows=2, of_rows=5, view="Land = 'CH'; top 2 by Umsatz")

    def test_a_view_at_its_widest_gives_way_in_its_words_and_never_fails_the_request(self) -> None:
        """Three selections of twenty long values each: the words pass a change line's limit, the counts stand."""
        halls = [f"Lagerhalle {number:02d} am Westkai" for number in range(20)]
        table = parse_dataset(
            "Halle,Zone,Typ,Gewicht\n" + "".join(f"{hall},{hall},{hall},{n}\n" for n, hall in enumerate(halls))
        )
        selections = [
            {"op": "keep_rows", "where": [{"column": column, "test": "eq", "values": halls}]}
            for column in ("Halle", "Zone", "Typ")
        ]
        view = view_from(
            *selections, {"op": "sort", "column": "Gewicht", "descending": True}, {"op": "keep_rows", "n": 4}
        )

        drawn = view_of(table, view).drawn_rows(view)

        words = view.words(["Halle", "Zone", "Typ"])
        assert len(view.selections) == 3 and len(words) > MAX_CHANGE_CHARS
        assert (drawn.rows, drawn.of_rows, len(drawn.view)) == (4, 20, MAX_CHANGE_CHARS)
        assert drawn.view == words[: MAX_CHANGE_CHARS - 1] + "…"


class TestPrepareData:
    async def test_a_selection_lands_in_the_view_and_leaves_the_table_its_version_and_the_confirmation(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
        context = await context_for(client, sid, "inv-v-1")
        table = context.state[DATASET_ID]

        answer = await prepare_data([only("Points", "ge", 40)], context)

        assert (answer["status"], answer["landed"], answer["version"]) == ("ok", "view", 1)
        assert (answer["rows"], answer["of_rows"]) == (12, 24) and answer["plot_outdated"] is False
        assert fenced(answer["view"], "tool_notes") == [
            "kept 12 of 24 rows where Points ≥ 40, 12 dropped",
            "the plot draws 12 of 24 rows of data v1",
        ]
        # Nothing of the data moved: the same table, every row, still confirmed.
        assert context.state[DATASET_ID] == table and len(points_of(sid, context.state)) == 24
        assert read_session(context.state).data_confirmed  # type: ignore[union-attr]
        assert context.state[PLOT_VIEW] == {"selections": [[{"column": "Points", "test": "ge", "value": "40"}]]}
        ledger = ledger_for("inv-v-1")
        assert ledger.view_ops == ["keep_rows"] and ledger.prep_ops == [] and ledger.dataset_changes == []

    async def test_a_top_n_builds_on_the_view_and_a_new_one_replaces_it(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-2")
        await prepare_data([only("Points", "ge", 40)], context)
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 3}]

        first = await prepare_data(top, context)
        second = await prepare_data([top[0], {"op": "keep_rows", "n": 5}], context)

        assert (first["rows"], second["rows"]) == (3, 5) and second["landed"] == "view"
        assert context.state[PLOT_VIEW]["top"] == {"column": "Points", "descending": True, "n": 5}
        assert len(context.state[PLOT_VIEW]["selections"]) == 1

    async def test_reset_view_shows_every_row_again(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-3")
        await prepare_data([only("Points", "ge", 40)], context)

        answer = await prepare_data([{"op": "reset_view"}], context)

        assert (answer["landed"], answer["rows"], answer["of_rows"]) == ("view", 24, 24)
        assert fenced(answer["view"], "tool_notes") == [VIEW_CLEARED, "the plot draws all 24 rows of data v1"]
        assert context.state[PLOT_VIEW] is None and ledger_for("inv-v-3").view_ops == ["keep_rows", "reset_view"]

    async def test_a_change_of_the_table_and_a_view_in_one_call_store_both(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-4")
        rename = {"op": "rename", "column": "Points", "name": "Punkte"}

        answer = await prepare_data([rename, only("Punkte", "ge", 40)], context)

        assert (answer["status"], answer["landed"], answer["version"], answer["rows"]) == (
            "ok",
            "table_and_view",
            2,
            24,
        )
        assert fenced(answer["changes"], "tool_notes") == ["renamed 'Points' to 'Punkte'"]
        assert fenced(answer["view"], "tool_notes")[-1] == "the plot draws 12 of 24 rows of data v2"
        ledger = ledger_for("inv-v-4")
        assert (ledger.prep_ops, ledger.view_ops) == (["rename"], ["keep_rows"])

    async def test_a_view_that_does_not_fit_refuses_the_whole_call(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The table's part is not stored either: a call lands whole or not at all."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-5")
        table = context.state[DATASET_ID]
        rename = {"op": "rename", "column": "Points", "name": "Punkte"}

        answer = await prepare_data([rename, only("Points", "ge", 40)], context)

        assert (answer["status"], answer["code"]) == ("error", "unknown_column")
        assert context.state[DATASET_ID] == table and context.state.get(PLOT_VIEW) is None

    async def test_the_users_word_sends_a_keep_rows_to_the_table(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-6")

        answer = await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)

        assert (answer["landed"], answer["version"], answer["rows"]) == ("table", 2, 12)
        assert context.state.get(PLOT_VIEW) is None and len(points_of(sid, context.state)) == 12

    async def test_a_table_change_that_the_view_no_longer_fits_clears_it_with_a_line(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-7")
        await prepare_data([only("Points", "ge", 40)], context)

        answer = await prepare_data([{"op": "drop_columns", "columns": ["Points"]}], context)

        assert (answer["status"], answer["landed"], answer["version"]) == ("ok", "table", 2)
        assert fenced(answer["view"], "tool_notes") == [CLEARED_LINE, "the plot draws all 24 rows of data v2"]
        assert context.state[PLOT_VIEW] is None

    async def test_a_view_that_leaves_a_bound_column_without_values_is_not_set(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, "x,y\n1,5\n2,\n3,\n4,8\n")
        context = await context_for(client, sid, "inv-v-8")
        view = read_session(context.state)
        assert view is not None and {binding.column for binding in view.bindings} == {"x", "y"}

        answer = await prepare_data([{"op": "keep_rows", "where": [{"column": "y", "test": "is_missing"}]}], context)

        assert (answer["status"], answer["code"]) == ("error", "invalid_operation")
        assert VIEW_BREAKS_BINDINGS in answer["message"] and context.state.get(PLOT_VIEW) is None

    async def test_the_session_block_lists_the_view_in_force(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-9")
        assert "View of the plot" not in await session_context(context)  # type: ignore[arg-type]
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 3}]
        await prepare_data([only("Points", "ge", 40), *top], context)

        block = await session_context(context)  # type: ignore[arg-type]

        assert f"- {VIEW_HEADING.format(rows=3, of_rows=24)}" in block
        assert "<tool_notes>\nPoints ≥ 40; top 3 by Points\n</tool_notes>" in block
        assert "- Dataset: 24 rows, 3 columns" in block  # the table, as before


class TestTheTurn:
    def test_a_view_alone_is_no_change_of_the_data(self) -> None:
        """So the plot of the new rows may run in the same turn, and the page's data card is not told of a change."""
        viewed = {"status": "ok", "landed": "view", "rows": 3, "of_rows": 24, "version": 1}
        both = {"status": "ok", "landed": "table_and_view", "rows": 24, "version": 2}

        assert call_outcome("prepare_data", viewed) == "viewed"
        assert call_outcome("prepare_data", both) == "changed"
        assert call_outcome("prepare_data", {"status": "ok", "rows": 24, "version": 2}) == "changed"

        ledger = ledger_for("inv-v-turn")
        ledger.tool_calls.append(ToolCall("prepare_data", TOOL_ALLOWED, "viewed"))
        assert not changed_data(ledger) and turn_outcome(ledger) == "kept"
        ledger.tool_calls.append(ToolCall("plot_pipeline", TOOL_ALLOWED, "shipped"))
        assert turn_outcome(ledger) == "plot"
        ledger.tool_calls.append(ToolCall("prepare_data", TOOL_ALLOWED, "changed"))
        assert changed_data(ledger) and turn_outcome(ledger) == "data"


async def set_view(runtime: Runtime, sid: str, *operations: dict[str, Any]) -> PlotView:
    """The view a `prepare_data` call with `operations` would store, written as ADK writes a tool's state."""
    view = view_from(*operations)
    await runtime.write_state(await runtime.session(USER, sid), plot_view.view_delta(view))
    return view


class TestThePlotRun:
    async def test_the_run_draws_the_views_rows_says_so_and_records_the_view(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        swap_models("gemini", default_script())
        sid = await pasted_session(client, TEAMS)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
        view = await set_view(runtime, sid, only("Points", "ge", 40))

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok"
        assert plot["changes"][0] == "The plot draws 12 of the 24 rows of data v1 (view: Points ≥ 40)"
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert drawn[0] == "Team,Points,Goals" and len(drawn) == 1 + 12
        assert all(int(row.split(",")[1]) >= 40 for row in drawn[1:])
        # The version holds the view and the rows it drew, so the downloaded code runs on the downloaded data.
        version = services.versions.latest_rendered(sid)
        assert version is not None and version.view == view.stamp()
        assert version.data_csv.strip().splitlines() == drawn and version.data_version == 1
        # The table is as it was: every row, no new version, still confirmed.
        assert len(await table_rows(client, sid)) == 24
        done = next(data for name, data in events if name == "done")
        assert done["data_confirmed"] is True and "dataset" not in done

    async def test_a_view_set_in_a_turn_is_drawn_in_that_turn(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        """A view changes no data, so nothing waits for the user's check: the root sets it and plots. The adapter
        hears that the rows changed, as it does for "plot the new data"."""
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 5}]
        script = {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": ROOT_REPLY},
                {"call": "prepare_data", "args": {"operations": top}},
                {"call": "plot_pipeline", "args": {"base": "previous"}},
                {"text": "The plot shows the top 5 now."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        }
        fake = swap_models("anthropic-vertex", script)
        sid = await pasted_session(client, TEAMS)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
        await create_plot(client, sid)
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 24

        events = await say(client, sid, "only the top 5 by points")

        plot = next(data for name, data in events if name == "plot")
        assert (plot["status"], plot["version"]) == ("ok", 2)
        assert plot["changes"][0] == "The plot draws 5 of the 24 rows of data v1 (view: top 5 by Points)"
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 5
        done = next(data for name, data in events if name == "done")
        assert (done["turn"], done["data_confirmed"]) == ("plot", True) and "dataset" not in done
        adapter_calls = [call for call in fake.calls if FakeAnthropic.kind(call) == "adapter"]
        assert pipeline.DATA_CHANGE_REQUEST in json.dumps(adapter_calls[-1], ensure_ascii=False, default=str)
        # The server's sentence is no request of the user's: the version's lineage stays empty of it.
        latest = services.versions.latest_rendered(sid)
        assert latest is not None and latest.requests == []

    async def test_a_view_that_no_longer_fits_is_cleared_and_the_run_draws_every_row(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", default_script())
        sid = await pasted_session(client, TEAMS)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
        await set_view(runtime, sid, only("Ghost", "ge", 40))

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["changes"][0] == CLEARED_LINE
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 24
        assert (await runtime.session(USER, sid)).state.get(PLOT_VIEW) is None


class TestRepeatedKeyUnderAView:
    """A key the rows repeat is combined before a plot of one value per key (owner decision of 2026-11-09). Under a
    view the rows in question are the view's."""

    async def test_a_key_that_repeats_only_outside_the_view_is_none_for_this_plot(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        """Three students per study hour, and the view keeps one of each hour: no question, no combine, four marks."""
        swap_models("gemini", default_script())
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        one_each = {"column": "Student", "test": "eq", "values": ["S00", "S01", "S02", "S03"]}
        await set_view(runtime, sid, {"op": "keep_rows", "where": [one_each]})

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and len(plot["changes"]) == 1 + len(SCATTER_PLAN["changes"])
        assert backend.jobs[-1].data_csv.strip().splitlines()[1:] == ["S00,2,50", "S01,4,53", "S02,6,56", "S03,8,59"]
        assert len(await table_rows(client, sid)) == 12

    async def test_a_key_that_repeats_within_the_view_is_asked_about_and_combined_for_the_plot_only(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        """A data version would be made of the whole table and add up rows the view leaves out, so under a view the
        rows are combined for the run alone: the table keeps all twelve, and the view stays adjustable."""
        swap_models("gemini", asked_then_chosen("sum"))
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        await set_view(runtime, sid, only("Exam Score", "ge", 59))

        events = await plot_with_choice(client, sid, "add them up")

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok"
        assert plot["changes"][:2] == [
            "The plot draws 9 of the 12 rows of data v1 (view: Exam Score ≥ 59)",
            f"{COMBINED_IN_VIEW_HEAD}: summed 'Exam Score' over 9 rows into 4, one per 'Study Hours'",
        ]
        # 59 + 71 + 83 for 8 hours, and two students each for the others.
        assert backend.jobs[-1].data_csv.strip().splitlines() == [
            "Study Hours,Exam Score",
            "2,136",
            "4,142",
            "6,148",
            "8,213",
        ]
        done = next(data for name, data in events if name == "done")
        assert "dataset" not in done and done["data_confirmed"] is True
        assert len(await table_rows(client, sid)) == 12

    async def test_the_answer_stays_with_the_view_so_a_later_change_of_the_plot_is_not_asked_again(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        """Without a view the answer becomes a data version and the key repeats no more. Under a view nothing is
        stored, so the view keeps the answer: a change of the plot runs, and draws the rows combined the same way."""
        script = asked_then_chosen("sum", plans=[SCATTER_PLAN, SECOND_PLAN])
        script["root"] += [
            {"call": "plot_pipeline", "args": {"change_request": "make the line thicker", "base": "previous"}},
            {"text": "Done."},
        ]
        script["reviewer"] = [{"json": VERDICT_OK}, {"json": VERDICT_OK}]
        swap_models("gemini", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        await set_view(runtime, sid, only("Exam Score", "ge", 59))
        await plot_with_choice(client, sid, "add them up")
        assert (await runtime.session(USER, sid)).state[PLOT_VIEW]["combine"] == "sum"

        events = await say(client, sid, "make the line thicker")

        plot = next(data for name, data in events if name == "plot")
        assert (plot["status"], plot["version"]) == ("ok", 2)
        assert plot["changes"][1].startswith(f"{COMBINED_IN_VIEW_HEAD}: summed 'Exam Score' over 9 rows into 4")
        assert backend.jobs[-1].data_csv.strip().splitlines()[1:] == ["2,136", "4,142", "6,148", "8,213"]
        # The same rows, combined the same way: the adapter is told of no change of the data.
        latest = services.versions.latest_rendered(sid)
        assert latest is not None and latest.view is not None and latest.view["combine"] == "sum"
        assert latest.requests == ["make the line thicker"]

    async def test_the_session_block_reads_the_rows_the_plot_draws(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        context = await context_for(client, sid, "inv-v-10")
        assert "- Repeated key:" in await session_context(context)  # type: ignore[arg-type]
        one_each = {"column": "Student", "test": "eq", "values": ["S00", "S01", "S02", "S03"]}

        await prepare_data([{"op": "keep_rows", "where": [one_each]}], context)

        assert "- Repeated key:" not in await session_context(context)  # type: ignore[arg-type]


class TestReviewedEdges:
    async def test_a_view_that_breaks_the_bindings_refuses_a_call_that_changes_the_table_too(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, "x,y,z\n1,5,a\n2,,b\n3,,c\n4,8,d\n")
        context = await context_for(client, sid, "inv-v-11")
        table = context.state[DATASET_ID]
        rename = {"op": "rename", "column": "z", "name": "w"}

        answer = await prepare_data(
            [rename, {"op": "keep_rows", "where": [{"column": "y", "test": "is_missing"}]}], context
        )

        assert (answer["status"], answer["code"]) == ("error", "invalid_operation")
        assert context.state[DATASET_ID] == table and context.state.get(PLOT_VIEW) is None

    async def test_a_table_change_that_empties_a_bound_column_in_the_view_clears_the_view(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, "x,y,z\n1,5,a\n2,6,b\n3,7,a\n4,8,b\n")
        context = await context_for(client, sid, "inv-v-12")
        await prepare_data([only("z", "eq", "a")], context)
        emptied = {"op": "blank", "columns": ["y"], "where": [{"column": "z", "test": "eq", "value": "a"}]}

        answer = await prepare_data([emptied], context)

        assert (answer["status"], answer["landed"], answer["version"]) == ("ok", "table", 2)
        assert fenced(answer["view"], "tool_notes")[0] == CLEARED_LINE and context.state[PLOT_VIEW] is None

    async def test_a_run_is_due_only_for_a_plot_of_this_confirmed_table(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        swap_models("gemini", default_script())
        sid = await pasted_session(client, TEAMS)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
        await create_plot(client, sid)
        context = await context_for(client, sid, "inv-v-13")

        on_the_plots_table = await prepare_data([only("Points", "ge", 40)], context)
        await prepare_data([{"op": "rename", "column": "Goals", "name": "Tore"}], context)
        on_a_new_version = await prepare_data([only("Points", "ge", 30)], context)

        assert on_the_plots_table["plot_outdated"] is True
        # The new version waits for the user's check: a plot run could not start, so none is called due.
        assert on_a_new_version["landed"] == "view" and on_a_new_version["plot_outdated"] is False


class TestTheDataTheViewBelongsTo:
    """The view was set on one table. A change of that table keeps it, new data takes it away: it would hide rows of
    a table the user never looked at through it."""

    async def test_a_new_paste_takes_the_view_away(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        await set_view(runtime, sid, only("Points", "ge", 40))
        assert (await runtime.session(USER, sid)).state[PLOT_VIEW] is not None

        await paste(client, sid, "Team,Points,Goals\nNeu A,50,3\nNeu B,20,1\n")  # the same columns, other data

        assert (await runtime.session(USER, sid)).state[PLOT_VIEW] is None

    async def test_the_summary_of_the_new_data_names_the_view_it_replaced_and_offers_it_again(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """Owner decision of 2026-11-14: on a new paste a view is checked anew. It is never carried over unseen, and
        never dropped unsaid: the summary turn names it, and it holds again only once the user says yes."""
        sid = await pasted_session(client, TEAMS)
        view = await set_view(runtime, sid, only("Points", "ge", 40))

        await paste(client, sid, "Team,Points,Goals\nNeu A,50,3\nNeu B,20,1\n")

        state = (await runtime.session(USER, sid)).state
        assert state[PLOT_VIEW] is None and state[PLOT_VIEW_BEFORE] == view.stamp()
        context = await context_for(client, sid, "inv-v-20")
        block = await session_context(context)  # type: ignore[arg-type]
        assert VIEW_BEFORE_LINE in block and "<tool_notes>\nPoints ≥ 40\n</tool_notes>" in block
        assert "- View of the plot: the plot draws" not in block  # named, not in force

        answer = await prepare_data([only("Points", "ge", 40)], context)

        assert (answer["landed"], answer["rows"]) == ("view", 1) and context.state[PLOT_VIEW_BEFORE] is None
        assert VIEW_BEFORE_LINE not in await session_context(context)  # type: ignore[arg-type]

    async def test_a_view_the_new_table_cannot_take_is_not_offered(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        await set_view(runtime, sid, only("Points", "ge", 40))

        await paste(client, sid, "Stadt,Umsatz\nBern,1200\nKöln,800\n")  # other columns: nothing to offer

        context = await context_for(client, sid, "inv-v-21")
        assert VIEW_BEFORE_LINE not in await session_context(context)  # type: ignore[arg-type]

    async def test_a_second_paste_before_the_summary_keeps_the_view_the_first_set_aside(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        view = await set_view(runtime, sid, only("Points", "ge", 40))
        await paste(client, sid, "Team,Points,Goals\nNeu A,50,3\nNeu B,20,1\n")

        await paste(client, sid, "Team,Points,Goals\nNeu C,60,4\nNeu D,10,0\n")

        assert (await runtime.session(USER, sid)).state[PLOT_VIEW_BEFORE] == view.stamp()

    async def test_a_computed_table_in_place_of_the_data_takes_it_away_and_a_change_keeps_it(
        self, client: httpx.AsyncClient, runtime: Runtime, services: Services
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-14")
        view = read_session(context.state)
        assert view is not None
        table = parse_dataset("p,q\n1,2\n3,4\n")

        replaced = push_version(services.datasets, sid, view, table, view.snapshot, rebind=True)
        changed = push_version(services.datasets, sid, view, parse_dataset(TEAMS), view.snapshot)

        assert replaced.delta[PLOT_VIEW] is None and PLOT_VIEW not in changed.delta

    async def test_an_undo_keeps_a_view_that_still_fits(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-15")
        await prepare_data([{"op": "rename", "column": "Goals", "name": "Tore"}], context)
        await prepare_data([only("Points", "ge", 40)], context)
        await write_back(runtime, sid, context)

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)

        assert undone.status_code == 200
        context = await context_for(client, sid, "inv-v-16")
        assert plot_view.current(context.state, stored_now(sid, context.state)).viewed is not None

    async def test_a_view_the_table_no_longer_fits_never_fails_a_later_call(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """After the undo the column the view names is gone. The view counts as none: the next call sets its own
        view, where the stale selection would have refused it for a column the user cannot see any more."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-v-17")
        await prepare_data([{"op": "rename", "column": "Points", "name": "Punkte"}], context)
        await prepare_data([only("Punkte", "ge", 40)], context)
        await write_back(runtime, sid, context)
        assert (await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)).status_code == 200
        context = await context_for(client, sid, "inv-v-18")
        assert context.state[PLOT_VIEW] is not None  # still stored, and no longer fitting

        answer = await prepare_data([only("Goals", "ge", 10)], context)

        assert (answer["status"], answer["landed"]) == ("ok", "view")
        assert context.state[PLOT_VIEW] == {"selections": [[{"column": "Goals", "test": "ge", "value": "10"}]]}

    async def test_a_view_that_leaves_a_bound_column_empty_is_none_for_every_reader(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """An undo can bring back a table on which the view still applies but leaves `y` without a value. The run
        would draw every row then, so the session block lists no view and the next call builds on none: the three
        agree on whether a view is in force."""
        sid = await pasted_session(client, "x,y,z\n1,,a\n2,6,b\n3,,a\n4,8,b\n")
        await set_view(runtime, sid, only("z", "eq", "a"))  # as an undo leaves it: stored, never checked on this table
        context = await context_for(client, sid, "inv-v-19")
        view = read_session(context.state)
        assert view is not None

        drawn = pipeline.drawn_through_view(context.state, view, stored_now(sid, context.state))
        block = await session_context(context)  # type: ignore[arg-type]
        answer = await prepare_data([only("x", "ge", 2)], context)

        assert drawn.cleared and drawn.stamp is None and drawn.notes == (CLEARED_LINE,)
        assert "View of the plot" not in block
        assert (answer["status"], answer["landed"], answer["rows"]) == ("ok", "view", 3)
        assert context.state[PLOT_VIEW] == {"selections": [[{"column": "x", "test": "ge", "value": "2"}]]}


def stored_now(sid: str, state: dict[str, Any]) -> Any:
    stored = get_services().datasets.get(state[DATASET_ID], sid)
    assert stored is not None
    return stored


SALES = (
    "Year,Month,Store,Amount\n2023,Nov,North,30\n2023,Nov,South,25\n2023,Dec,North,40\n"
    "2024,Jan,North,50\n2024,Jan,South,45\n2024,Feb,North,70\n2024,Feb,South,65\n"
)


class TestApplyView:
    """The view put in the table's place in one step: for "make that permanent", and before a change of the table
    that has to work on the rows the plot shows, where the change alone would read every row."""

    async def test_the_table_takes_the_views_rows_and_no_view_is_left(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-a-1")
        await prepare_data([only("Points", "ge", 40)], context)

        answer = await prepare_data([{"op": "apply_view"}], context)

        assert (answer["status"], answer["landed"], answer["version"], answer["rows"]) == ("ok", "table", 2, 12)
        assert fenced(answer["changes"], "tool_notes") == ["kept 12 of 24 rows where Points ≥ 40, 12 dropped"]
        assert fenced(answer["view"], "tool_notes") == [VIEW_APPLIED, "the plot draws all 12 rows of data v2"]
        assert context.state[PLOT_VIEW] is None and len(points_of(sid, context.state)) == 12
        # A data version like any other: the user checks it, and the turn changed the data.
        assert not read_session(context.state).data_confirmed  # type: ignore[union-attr]
        ledger = ledger_for("inv-a-1")
        assert ledger.prep_ops == ["apply_view"] and ledger.view_ops == ["keep_rows"]

    async def test_a_change_after_it_works_on_the_rows_the_plot_showed(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """ "Sum those per month" under "only 2024": the aggregate alone would add 2023 in, and the view, whose
        column the aggregate drops, would be cleared without a word of the rows it had stood for."""
        sid = await pasted_session(client, SALES)
        context = await context_for(client, sid, "inv-a-2")
        await prepare_data([only("Year", "eq", 2024)], context)
        per_month = {"op": "aggregate", "by": ["Month"], "column": "Amount", "how": "sum"}

        answer = await prepare_data([{"op": "apply_view"}, per_month], context)

        assert (answer["status"], answer["landed"], answer["rows"]) == ("ok", "table", 2)
        assert fenced(answer["changes"], "tool_notes")[0] == "kept 4 of 7 rows where Year = 2024, 3 dropped"
        table = stored_now(sid, context.state).csv.strip().splitlines()
        assert sorted(table[1:]) == ["Feb,135", "Jan,95"] and context.state[PLOT_VIEW] is None

    async def test_a_view_named_after_it_is_the_view_of_the_new_table(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-a-3")
        await prepare_data([only("Points", "ge", 40)], context)
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 3}]

        answer = await prepare_data([{"op": "apply_view"}, *top], context)

        assert (answer["landed"], answer["rows"]) == ("table_and_view", 12)
        held = context.state[PLOT_VIEW]
        assert held["top"] == {"column": "Points", "descending": True, "n": 3} and not held["selections"]
        assert fenced(answer["view"], "tool_notes")[0] == VIEW_APPLIED
        assert fenced(answer["view"], "tool_notes")[-1] == "the plot draws 3 of 12 rows of data v2"

    async def test_it_needs_a_view_comes_first_and_reads_the_current_table(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-a-4")
        table = context.state[DATASET_ID]

        without = await prepare_data([{"op": "apply_view"}], context)
        await prepare_data([only("Points", "ge", 40)], context)
        late = await prepare_data([{"op": "rename", "column": "Goals", "name": "Tore"}, {"op": "apply_view"}], context)
        both = await prepare_data([{"op": "reset_view"}, {"op": "apply_view"}], context)
        earlier = await prepare_data([{"op": "apply_view"}], context, from_version="original")

        assert [item["code"] for item in (without, late, both, earlier)] == ["invalid_operations"] * 4
        assert "there is no view of the plot to apply" in without["errors"]
        assert "leave from_version out" in earlier["errors"]
        assert context.state[DATASET_ID] == table and context.state[PLOT_VIEW] is not None


class TestASelectionThatHidesNoRow:
    """A change of the table that leaves only rows a selection keeps: the selection hides nothing any more and is
    cleared, whatever words the change used. The prep eval's `fr-appliquer-la-vue-au-tableau` kept the rows with a
    `keep_rows` of the table instead of `apply_view`, and the old selection stayed in force on the plot."""

    async def test_the_same_condition_on_the_table_clears_it(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-i-1")
        await prepare_data([only("Points", "ge", 40)], context)

        answer = await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)

        assert (answer["status"], answer["landed"], answer["version"], answer["rows"]) == ("ok", "table", 2, 12)
        assert context.state[PLOT_VIEW] is None
        assert fenced(answer["view"], "tool_notes") == [
            IDLE_SELECTION_LINE.format(words="Points ≥ 40"),
            "the plot draws all 12 rows of data v2",
        ]

    async def test_the_same_rows_in_other_words_clear_it(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        """Dropping the rows below 40 leaves exactly the rows `Points ≥ 40` showed: the rows decide, not the words."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-i-2")
        await prepare_data([only("Points", "ge", 40)], context)
        below = {"op": "drop_rows", "where": [{"column": "Points", "test": "lt", "value": "40"}]}

        answer = await prepare_data([below], context)

        assert (answer["status"], answer["rows"]) == ("ok", 12) and context.state[PLOT_VIEW] is None
        assert fenced(answer["view"], "tool_notes")[0] == IDLE_SELECTION_LINE.format(words="Points ≥ 40")

    async def test_a_selection_that_still_hides_rows_stays(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-i-3")
        await prepare_data([only("Points", "ge", 40)], context)
        held = context.state[PLOT_VIEW]
        below = {"op": "drop_rows", "where": [{"column": "Points", "test": "lt", "value": "20"}]}

        answer = await prepare_data([below], context)

        assert answer["status"] == "ok" and answer["rows"] > 12
        assert context.state[PLOT_VIEW] == held and "view" not in answer

    async def test_only_the_selection_goes_and_a_top_n_stays(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        """A top N orders the rows it draws even when it keeps them all, so it is no selection that hides nothing."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-i-4")
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 3}]
        await prepare_data([only("Points", "ge", 40), *top], context)

        answer = await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)

        assert context.state[PLOT_VIEW] == {"selections": [], "top": {"column": "Points", "descending": True, "n": 3}}
        lines = fenced(answer["view"], "tool_notes")
        assert lines[0] == IDLE_SELECTION_LINE.format(words="Points ≥ 40")
        assert lines[-1] == "the plot draws 3 of 12 rows of data v2" and answer["landed"] == "table"


POINTS_40 = {"selections": [[{"column": "Points", "test": "ge", "value": "40"}]]}
SHOWN_40 = {"rows": 12, "of_rows": 24, "parts": ["Points ≥ 40"]}


async def undo(client: httpx.AsyncClient, sid: str) -> dict[str, Any]:
    """The page's `.undo()`, its answer."""
    response = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)
    assert response.status_code == 200, response.text
    answer: dict[str, Any] = response.json()
    return answer


async def view_now(runtime: Runtime, sid: str) -> Any:
    return (await runtime.session(USER, sid)).state.get(PLOT_VIEW)


class TestTheUndoTakesBackTheView:
    """An undo takes back what the undone step did to the view of the plot too (`StoredDataset.view_change`): the view
    from before the step comes back while the view in force is still the one the step left. The undo's answer carries
    the view the page then draws."""

    async def test_a_selection_the_step_cleared_comes_back(self, client: httpx.AsyncClient, runtime: Runtime) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-u-1")
        await prepare_data([only("Points", "ge", 40)], context)
        await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)
        await write_back(runtime, sid, context)
        assert await view_now(runtime, sid) is None

        answer = await undo(client, sid)

        assert (answer["version"], answer["view"]) == (1, SHOWN_40)
        assert await view_now(runtime, sid) == POINTS_40

    async def test_the_view_an_apply_view_moved_into_the_table_comes_back(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-u-2")
        await prepare_data([only("Points", "ge", 40)], context)
        await prepare_data([{"op": "apply_view"}], context)
        await write_back(runtime, sid, context)

        answer = await undo(client, sid)

        assert (answer["version"], answer["view"]) == (1, SHOWN_40)
        assert await view_now(runtime, sid) == POINTS_40

    async def test_a_view_the_user_changed_after_the_step_stays(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The later view is the user's later word: the undo leaves it, and the answer draws it on the old table."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-u-3")
        await prepare_data([only("Points", "ge", 40)], context)
        await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)
        await prepare_data([only("Goals", "ge", 10)], context)
        await write_back(runtime, sid, context)
        later = await view_now(runtime, sid)

        answer = await undo(client, sid)

        assert later == {"selections": [[{"column": "Goals", "test": "ge", "value": "10"}]]}
        assert await view_now(runtime, sid) == later
        assert answer["view"] == {"rows": 17, "of_rows": 24, "parts": ["Goals ≥ 10"]}

    async def test_two_undos_take_back_two_steps_each_with_its_own_view(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The second step changed no view: its undo leaves the view as it is, the first one's brings it back."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-u-4")
        await prepare_data([only("Points", "ge", 40)], context)
        await prepare_data([{**only("Points", "ge", 40), "target": "table"}], context)
        await prepare_data([{"op": "rename", "column": "Goals", "name": "Tore"}], context)
        await write_back(runtime, sid, context)

        first = await undo(client, sid)
        first_view = await view_now(runtime, sid)
        second = await undo(client, sid)

        assert (first["version"], first["view"], first_view) == (2, None, None)
        assert (second["version"], second["view"]) == (1, SHOWN_40)
        assert await view_now(runtime, sid) == POINTS_40

    async def test_a_view_set_with_a_change_of_the_table_goes_with_its_undo(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """The side effect of the same rule: a call that renamed a column and set a view on it is undone whole, so the
        view from before it (none) is in force again, not one that names a column the old table does not have."""
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-u-5")
        await prepare_data([{"op": "rename", "column": "Points", "name": "Punkte"}, only("Punkte", "ge", 40)], context)
        await write_back(runtime, sid, context)
        assert await view_now(runtime, sid) == {"selections": [[{"column": "Punkte", "test": "ge", "value": "40"}]]}

        answer = await undo(client, sid)

        assert (answer["version"], answer["view"]) == (1, None)
        assert await view_now(runtime, sid) is None


class TestQuestionsUnderAView:
    """A question reads the whole table unless it asks for the rows the plot draws, and the answer says which: a
    total over 24 rows is no total of the 12 the user is looking at."""

    async def test_an_answer_says_that_it_read_every_row_and_how_to_ask_of_the_view(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-q-1")
        assert "view" not in await query_data([], context)  # no view, nothing to say
        await prepare_data([only("Points", "ge", 40)], context)

        answer = await query_data([{"op": "sort", "column": "Points", "descending": True}], context, limit=1)

        assert answer["status"] == "ok" and answer["rows"] == 24
        note = re.search(r"<tool_notes>\n?(.*?)\n?</tool_notes>", answer["view"], re.DOTALL)
        assert note is not None and note.group(1) == (
            "this answer reads every row of the table; the plot draws 12 of the table's 24 rows (view: Points ≥ 40). "
            "To ask about the rows the plot draws, start the operations with apply_view"
        )

    async def test_apply_view_asks_the_question_of_the_rows_the_plot_draws_and_stores_nothing(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-q-2")
        await prepare_data([only("Points", "ge", 40)], context)
        table, view = context.state[DATASET_ID], dict(context.state[PLOT_VIEW])
        lowest = {"op": "sort", "column": "Points", "descending": False}

        answer = await query_data([{"op": "apply_view"}, lowest], context, limit=1)

        assert answer["status"] == "ok" and answer["rows"] == 12
        shown = fenced(answer["table"], "user_data")
        assert int(shown["rows"][0][shown["columns"].index("Points")]) >= 40  # the lowest of the rows shown
        assert "this answer reads the rows the plot draws, 12 of the table's 24 rows" in answer["view"]
        assert fenced(answer["changes"], "tool_notes")[0] == "kept 12 of 24 rows where Points ≥ 40, 12 dropped"
        assert context.state[DATASET_ID] == table and context.state[PLOT_VIEW] == view

    async def test_apply_view_without_a_view_is_refused_with_the_way_on(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-q-3")

        answer = await query_data([{"op": "apply_view"}], context)

        assert (answer["status"], answer["code"]) == ("error", "invalid_operations")
        assert NO_VIEW_TO_ASK in answer["errors"]

    async def test_a_cut_among_equal_values_is_named_in_an_answer_too(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        """ "Which 2 are largest" over three equal values: the answer returns two rows, and its lines name the one
        left out, in a question's words: nothing is dropped."""
        sid = await pasted_session(client, "Stadt,Umsatz\nBern,1200\nKöln,800\nBasel,800\nGenf,800\nWien,300\n")
        context = await context_for(client, sid, "inv-q-4")
        largest = {"op": "sort", "column": "Umsatz", "descending": True}

        cut = await query_data([largest], context, limit=2)
        clean = await query_data([largest], context, limit=4)

        assert fenced(cut["changes"], "tool_notes") == [
            "sorted by Umsatz, descending",
            "the first 2 of 5 rows are returned; the cut falls among 3 rows with Umsatz 800: "
            "1 returned (Stadt 'Köln') and 2 left out (Stadt 'Basel' and 'Genf')",
        ]
        assert fenced(clean["changes"], "tool_notes") == ["sorted by Umsatz, descending"]


VISITS = "Date,Visitors,Sales\n2026-11-08,412,90\n2026-11-07,398,70\n2026-11-06,455,80\n2026-11-05,430,60\n"
"""Four days, newest first, as an export lists them. The sales fall with the visitors' dates in no order."""
VISIT_BINDINGS = [{"role": "x", "column": "Date"}, {"role": "y", "column": "Visitors"}]
DRAWN_BY_DATE = OLDEST_FIRST_LINE.format(column="Date")


def bound(*pairs: tuple[str, str]) -> list[Binding]:
    return [Binding(role=role, column=column) for role, column in pairs]


def shown(text: str) -> StoredDataset:
    store = DatasetStore()
    stored = store.get(store.put(SID, parse_dataset(text)), SID)
    assert stored is not None
    return stored


def dates_of(stored: StoredDataset, column: str = "Date") -> list[str]:
    rows = stored.csv.strip().splitlines()
    place = rows[0].split(",").index(column)
    return [row.split(",")[place] for row in rows[1:]]


def ordered_by(table: StoredDataset, *pairs: tuple[str, str]) -> str | None:
    """The column a run with these bindings orders the rows of `table` by, or None."""
    order = run_order(bound(*pairs), table, PlotView())
    return order.column if order is not None else None


class TestTheDateOrderOfARun:
    """Owner decision of 2026-11-13: an order is the plot's. A run draws a bound date column that runs newest first
    oldest first by itself, for the run alone, and the table keeps the rows as the user pasted them."""

    def test_a_bound_date_column_that_runs_newest_first_orders_the_rows_of_the_run(self) -> None:
        table = shown(VISITS)

        drawn, line = drawn_in_order(table, bound(("x", "Date"), ("y", "Visitors")), PlotView())

        assert line == "The plot draws the rows oldest first by 'Date'; the table runs newest first and stays as it is"
        assert dates_of(drawn) == ["2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08"]
        assert drawn.csv.strip().splitlines()[1] == "2026-11-05,430,60"  # whole rows move, no cell changes
        # The same data version, seen in the plot's order: nothing is stored and the table is as it was.
        assert (drawn.dataset_id, drawn.number) == (table.dataset_id, table.number)
        assert dates_of(table)[0] == "2026-11-08"
        assert next(column.order for column in drawn.profile.columns if column.name == "Date") == "ascending"

    @pytest.mark.parametrize(
        ("text", "bindings"),
        [
            (VISITS, [("x", "Visitors"), ("y", "Sales")]),  # the date column is bound to nothing
            ("Date,Visitors\n2026-11-05,430\n2026-11-06,455\n2026-11-07,398\n", [("x", "Date"), ("y", "Visitors")]),
            ("Date,Visitors\n2026-11-07,398\n2026-11-05,430\n2026-11-06,455\n", [("x", "Date"), ("y", "Visitors")]),
            ("Rank,Visitors\n3,398\n2,430\n1,455\n", [("x", "Rank"), ("y", "Visitors")]),  # numbers that fall
        ],
    )
    def test_rows_no_bound_date_column_runs_newest_first_through_are_drawn_as_they_stand(
        self, text: str, bindings: list[tuple[str, str]]
    ) -> None:
        table = shown(text)

        drawn, line = drawn_in_order(table, bound(*bindings), PlotView())

        assert line is None and drawn is table

    def test_rows_without_a_date_come_last_and_equal_dates_keep_their_order(self) -> None:
        table = shown("Date,Shift\n2026-11-07,late\n2026-11-07,early\n,unknown\n2026-11-05,late\n")

        drawn, line = drawn_in_order(table, bound(("x", "Date"), ("y", "Shift")), PlotView())

        assert line is not None
        assert drawn.csv.strip().splitlines()[1:] == [
            "2026-11-05,late",
            "2026-11-07,late",
            "2026-11-07,early",
            ",unknown",
        ]

    def test_a_top_n_by_another_column_keeps_the_order_the_user_asked_for(self) -> None:
        """The three best days by sales happen to fall with the dates: their order is the ranking's, not time's. A top
        N by the date itself ("the latest 3") leaves the newest rows newest first, and those are drawn in date order."""
        bindings = bound(("x", "Date"), ("y", "Sales"))
        by_sales = view_from({"op": "sort", "column": "Sales", "descending": True}, {"op": "keep_rows", "n": 3})
        latest = view_from({"op": "sort", "column": "Date", "descending": True}, {"op": "keep_rows", "n": 3})
        table = shown("Date,Sales\n2026-11-08,90\n2026-11-07,80\n2026-11-06,70\n2026-11-05,60\n")
        ranked = plot_view.viewed_dataset(table, view_of(table.as_parsed(), by_sales))
        newest = plot_view.viewed_dataset(table, view_of(table.as_parsed(), latest))

        assert run_order(bindings, ranked, by_sales) is None
        assert drawn_in_order(ranked, bindings, by_sales) == (ranked, None)
        drawn, line = drawn_in_order(newest, bindings, latest)
        assert line is not None and dates_of(drawn) == ["2026-11-06", "2026-11-07", "2026-11-08"]

    def test_rows_that_would_read_back_differently_are_drawn_as_they_stand(self, monkeypatch) -> None:
        """An order moves rows and nothing else. Should the ordered table read back with another kind of column, the
        bindings the user confirmed would no longer be the ones drawn, so the run keeps the rows as they are."""
        table = shown(VISITS)
        as_text = parse_dataset(VISITS, text_columns=["Visitors"])
        monkeypatch.setattr(plot_view, "_seen", lambda *_: plot_view.Viewed(as_text, [], as_text.profile.rows))

        assert drawn_in_order(table, bound(("x", "Date"), ("y", "Visitors")), PlotView()) == (table, None)

        def refuses(*_: object) -> plot_view.Viewed:
            raise PrepareError("invalid_operation", "the rows could not be ordered")

        monkeypatch.setattr(plot_view, "_seen", refuses)  # an order the engine cannot make never fails the run
        assert drawn_in_order(table, bound(("x", "Date"), ("y", "Visitors")), PlotView()) == (table, None)

    def test_the_first_bound_one_decides_when_two_date_columns_run_newest_first(self) -> None:
        table = shown("Start,End,Task\n2026-11-08,2026-11-09,c\n2026-11-05,2026-11-08,b\n2026-11-01,2026-11-07,a\n")

        assert ordered_by(table, ("end", "End"), ("start", "Start")) == "End"
        assert ordered_by(table, ("start", "Start"), ("end", "End")) == "Start"

    async def test_a_run_draws_the_rows_oldest_first_says_so_once_and_leaves_the_table_as_pasted(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        script = default_script()
        script["root"] = [
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
            {"call": "plot_pipeline", "args": {"base": "previous", "change_request": "a thicker line"}},
            {"text": "The line is thicker now."},
        ]
        script["adapter"] = [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}]
        script["reviewer"] = [{"json": VERDICT_OK}, {"json": VERDICT_OK}]
        swap_models("anthropic-vertex", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, VISITS)
        await bind_and_confirm(client, sid, VISIT_BINDINGS)

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["changes"][0] == DRAWN_BY_DATE
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert [row.split(",")[0] for row in drawn[1:]] == ["2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08"]
        # The version holds the rows it drew, so the downloaded code runs on the downloaded data; no view is recorded.
        version = services.versions.latest_rendered(sid)
        assert version is not None and version.data_csv.strip().splitlines() == drawn
        assert (version.view, version.data_version) == (None, 1)
        # The table is as pasted: newest first, no new version, still confirmed.
        assert [row.split(",")[0] for row in await table_rows(client, sid)][0] == "2026-11-08"
        done = next(data for name, data in events if name == "done")
        assert done["data_confirmed"] is True and "dataset" not in done

        # A change of that plot draws the same rows in the same order, and does not say it again.
        changed = await say(client, sid, "make the line thicker")

        again = next(data for name, data in changed if name == "plot")
        assert (again["status"], again["version"]) == ("ok", 2)
        assert DRAWN_BY_DATE not in again["changes"]
        assert backend.jobs[-1].data_csv.strip().splitlines() == drawn

    async def test_a_date_column_bound_after_the_first_plot_is_ordered_and_said_on_the_change(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        """The first plot drew two number columns in the pasted order. Binding the date changes neither the data
        version nor the view, so only the table the earlier version drew tells that this order is new to the user."""
        script = default_script()
        script["root"] = [
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
            {"call": "plot_pipeline", "args": {"base": "previous", "change_request": "the visitors over time"}},
            {"text": "The plot shows the visitors per day now."},
        ]
        script["adapter"] = [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}]
        script["reviewer"] = [{"json": VERDICT_OK}, {"json": VERDICT_OK}]
        swap_models("anthropic-vertex", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, VISITS)
        await bind_and_confirm(client, sid, [{"role": "x", "column": "Sales"}, {"role": "y", "column": "Visitors"}])
        first = next(data for name, data in await create_plot(client, sid) if name == "plot")
        assert first["status"] == "ok" and DRAWN_BY_DATE not in first["changes"]
        assert backend.jobs[-1].data_csv.strip().splitlines()[1].startswith("2026-11-08")

        await bind_and_confirm(client, sid, VISIT_BINDINGS)
        events = await say(client, sid, "show the visitors over time")

        plot = next(data for name, data in events if name == "plot")
        assert (plot["status"], plot["version"]) == ("ok", 2) and plot["changes"][0] == DRAWN_BY_DATE
        assert backend.jobs[-1].data_csv.strip().splitlines()[1].startswith("2026-11-05")

    async def test_under_a_view_the_rows_it_shows_are_ordered_and_both_lines_are_said(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", default_script())
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, VISITS)
        await bind_and_confirm(client, sid, VISIT_BINDINGS)
        await set_view(runtime, sid, only("Visitors", "ge", 400))

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok"
        assert plot["changes"][:2] == [
            "The plot draws 3 of the 4 rows of data v1 (view: Visitors ≥ 400)",
            DRAWN_BY_DATE,
        ]
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert [row.split(",")[0] for row in drawn[1:]] == ["2026-11-05", "2026-11-06", "2026-11-08"]


ALPHABETICAL = "Monat,Besucher\nApr,2105\nFeb,1395\nJan,1210\nJun,2930\nMai,2475\nMär,1840\n"
"""Six months as a spreadsheet sorts their names: by the alphabet."""
MONTH_BINDINGS = [{"role": "category", "column": "Monat"}, {"role": "value", "column": "Besucher"}]
DRAWN_BY_MONTH = CALENDAR_ORDER_LINE.format(column="Monat")


async def open_bars_on_scatter_code(client: httpx.AsyncClient) -> str:
    """A `bar-basic` session (its category takes text) whose catalogue code is the scatter file `SCATTER_PLAN` adapts,
    so the scripted adapter ships a plot from whatever table the run gets."""
    snapshot = snapshot_from_repo("bar-basic", "matplotlib").model_copy(
        update={"code": snapshot_from_repo("scatter-basic", "matplotlib").code}
    )
    body = {"user": USER, "spec_id": "bar-basic", "library": "matplotlib", "locale": "en"}
    response = await client.post("/v1/sessions", headers=HEADERS, json={**body, "snapshot": snapshot.model_dump()})
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


def months_table(*months: str) -> str:
    """A table of month names in this order, each with its place in the paste as its value."""
    return "Monat,Wert\n" + "".join(f"{month},{place}\n" for place, month in enumerate(months, 1))


class TestTheMonthOrderOfARun:
    """Owner decision of 2026-11-15: a column of month names that is out of calendar order is the plot's to order, as
    newest-first dates are. A run draws it in calendar order by itself, and the table keeps the rows as pasted."""

    def test_bound_month_names_out_of_calendar_order_order_the_rows_of_the_run(self) -> None:
        table = shown(ALPHABETICAL)

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Besucher")), PlotView())

        assert line == (
            "The plot draws the rows in calendar order by 'Monat'; "
            "the table lists its months in another order and stays as it is"
        )
        assert drawn.csv.strip().splitlines()[1:] == [
            "Jan,1210",
            "Feb,1395",
            "Mär,1840",
            "Apr,2105",
            "Mai,2475",
            "Jun,2930",
        ]
        # The same data version, seen in the plot's order: nothing is stored and the table is as it was.
        assert (drawn.dataset_id, drawn.number) == (table.dataset_id, table.number)
        assert dates_of(table, "Monat")[0] == "Apr"
        assert dict(drawn.column_dtypes) == dict(table.column_dtypes)

    @pytest.mark.parametrize(
        "months",
        [
            ("Jan", "Feb", "Mär", "Apr"),  # from January on
            ("Jan", "Feb", "Nov", "Dez"),  # from January on, with a gap
            ("Jul", "Aug", "Sep", "Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun"),  # a fiscal year
            ("Nov", "Dez", "Jan", "Feb"),  # a winter, over the turn of the year
            ("Okt", "Nov", "Dez", "Jan", "Feb", "Okt", "Nov", "Dez", "Jan", "Feb"),  # two of them, one after the other
            ("Jan", "Jan", "Feb", "Feb", "Mär", "Mär"),  # two series, month by month
            ("Jan", "Feb", "Mär", "Jan", "Feb", "Mär"),  # two series, one after the other
        ],
    )
    def test_months_that_run_along_the_calendar_are_drawn_as_they_stand(self, months: tuple[str, ...]) -> None:
        table = shown(months_table(*months))

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Wert")), PlotView())

        assert line is None and drawn is table

    def test_months_that_run_backward_over_the_turn_of_the_year_are_turned_round(self) -> None:
        """The newest first, as an export lists the last six months. An order from January would put January to March
        before October to December and tear the run apart, so the rows are drawn in the reverse of the paste."""
        table = shown(months_table("Mär", "Feb", "Jan", "Dez", "Nov", "Okt"))

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Wert")), PlotView())

        assert line == DRAWN_BY_MONTH
        assert drawn.csv.strip().splitlines() == ["Monat,Wert", "Okt,6", "Nov,5", "Dez,4", "Jan,3", "Feb,2", "Mär,1"]
        assert dict(drawn.column_dtypes) == dict(table.column_dtypes)  # the number that turned the rows is gone

    def test_a_year_that_runs_backward_is_drawn_from_january_on(self) -> None:
        months = ("Dez", "Nov", "Okt", "Sep", "Aug", "Jul", "Jun", "Mai", "Apr", "Mär", "Feb", "Jan")
        table = shown(months_table(*months))

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Wert")), PlotView())

        assert line == DRAWN_BY_MONTH and dates_of(drawn, "Monat") == list(reversed(months))

    def test_series_that_each_run_backward_are_ordered_by_month_and_keep_their_order_within_it(self) -> None:
        """Month names without a year cannot tell one pass from the next, so months that come back are ordered from
        January, by the engine's stable sort: the series keep the order of the paste within each month."""
        table = shown("Monat,Filiale,Wert\nMär,Bern,3\nFeb,Bern,2\nJan,Bern,1\nMär,Chur,6\nFeb,Chur,5\nJan,Chur,4\n")

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Wert"), ("color", "Filiale")), PlotView())

        assert line == DRAWN_BY_MONTH
        assert drawn.csv.strip().splitlines()[1:] == [
            "Jan,Bern,1",
            "Jan,Chur,4",
            "Feb,Bern,2",
            "Feb,Chur,5",
            "Mär,Bern,3",
            "Mär,Chur,6",
        ]

    def test_month_names_no_role_is_bound_to_are_no_reason_to_order_the_rows(self) -> None:
        table = shown("Monat,Besucher,Umsatz\nApr,2105,9\nFeb,1395,7\nJan,1210,8\n")

        assert drawn_in_order(table, bound(("x", "Besucher"), ("y", "Umsatz")), PlotView()) == (table, None)

    def test_a_top_n_by_another_column_keeps_the_order_the_user_asked_for(self) -> None:
        """The three best months are a ranking. A top N by the month column itself is drawn in calendar order."""
        bindings = bound(("x", "Monat"), ("y", "Besucher"))
        best = view_from({"op": "sort", "column": "Besucher", "descending": True}, {"op": "keep_rows", "n": 3})
        last = view_from({"op": "sort", "column": "Monat", "descending": True}, {"op": "keep_rows", "n": 3})
        table = shown(ALPHABETICAL)
        ranked = plot_view.viewed_dataset(table, view_of(table.as_parsed(), best))
        latest = plot_view.viewed_dataset(table, view_of(table.as_parsed(), last))

        assert dates_of(ranked, "Monat") == ["Jun", "Mai", "Apr"]
        assert drawn_in_order(ranked, bindings, best) == (ranked, None)
        drawn, line = drawn_in_order(latest, bindings, last)
        assert line == DRAWN_BY_MONTH and dates_of(drawn, "Monat") == ["Apr", "Mai", "Jun"]

    def test_a_bound_date_column_is_the_time_axis_and_month_names_beside_it_never_order_the_rows(self) -> None:
        """Four months of two years, each with its date and its month name: ordering the rows by the names would put
        March 2026 before November 2025 and take the dates out of their order. The date column decides alone,
        whichever role comes first: newest first it orders the rows, oldest first or in no order they stand."""
        rows = ["2025-01-01,Jan,1", "2025-11-01,Nov,2", "2026-03-01,Mär,3", "2026-06-01,Jun,4"]
        head = "Datum,Monat,Wert\n"
        oldest_first = shown(head + "\n".join(rows) + "\n")
        newest_first = shown(head + "\n".join(reversed(rows)) + "\n")
        no_order = shown(head + "\n".join([rows[2], rows[0], rows[3], rows[1]]) + "\n")

        assert ordered_by(oldest_first, ("x", "Datum"), ("y", "Wert")) is None
        assert ordered_by(oldest_first, ("x", "Wert"), ("y", "Monat")) == "Monat"  # out of order when it stands alone
        assert ordered_by(oldest_first, ("label", "Monat"), ("x", "Datum"), ("y", "Wert")) is None
        assert ordered_by(newest_first, ("label", "Monat"), ("x", "Datum"), ("y", "Wert")) == "Datum"
        assert ordered_by(no_order, ("label", "Monat"), ("x", "Datum"), ("y", "Wert")) is None

    def test_the_first_bound_month_column_that_is_out_of_order_decides(self) -> None:
        table = shown("Von,Bis,Wert\nJan,Mär,1\nFeb,Jan,2\nMär,Feb,3\n")

        assert ordered_by(table, ("start", "Von"), ("end", "Bis")) == "Bis"  # the first one stands as it is
        assert ordered_by(table, ("start", "Von"), ("y", "Wert")) is None

    def test_a_number_column_of_that_name_in_the_table_is_never_the_one_that_turns_the_rows(self) -> None:
        """Turning a run round numbers the rows in a column of its own and drops it again: a column of the user's
        with the name it would take stays in the table."""
        table = shown("Monat,Monat (row),Wert\nMär,7,1\nFeb,8,2\nJan,9,3\nDez,10,4\n")

        drawn, line = drawn_in_order(table, bound(("x", "Monat"), ("y", "Wert")), PlotView())

        assert line == DRAWN_BY_MONTH
        assert drawn.csv.strip().splitlines() == ["Monat,Monat (row),Wert", "Dez,10,4", "Jan,9,3", "Feb,8,2", "Mär,7,1"]

    async def test_a_run_draws_the_months_in_calendar_order_says_so_once_and_leaves_the_table_as_pasted(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        script = default_script()
        script["root"] = [
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
            {"call": "plot_pipeline", "args": {"base": "previous", "change_request": "a thicker line"}},
            {"text": "The line is thicker now."},
        ]
        script["adapter"] = [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}]
        script["reviewer"] = [{"json": VERDICT_OK}, {"json": VERDICT_OK}]
        swap_models("anthropic-vertex", script)
        sid = await open_bars_on_scatter_code(client)
        await paste(client, sid, ALPHABETICAL)
        await bind_and_confirm(client, sid, MONTH_BINDINGS)

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["changes"][0] == DRAWN_BY_MONTH
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert [row.split(",")[0] for row in drawn[1:]] == ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun"]
        version = services.versions.latest_rendered(sid)
        assert version is not None and version.data_csv.strip().splitlines() == drawn
        assert (version.view, version.data_version) == (None, 1)
        # The table is as pasted: by the alphabet, no new version, still confirmed.
        assert [row.split(",")[0] for row in await table_rows(client, sid)][0] == "Apr"
        done = next(data for name, data in events if name == "done")
        assert done["data_confirmed"] is True and "dataset" not in done

        # A change of that plot draws the same rows in the same order, and does not say it again.
        changed = await say(client, sid, "make the line thicker")

        again = next(data for name, data in changed if name == "plot")
        assert (again["status"], again["version"]) == ("ok", 2)
        assert DRAWN_BY_MONTH not in again["changes"]
        assert backend.jobs[-1].data_csv.strip().splitlines() == drawn
