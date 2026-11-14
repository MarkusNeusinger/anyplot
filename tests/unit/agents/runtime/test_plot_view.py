"""The view of the plot (`plot_view.py`): which rows of the table a plot run draws.

Owner decision of 2026-11-13: a selection and a top N belong with the plot and leave the table as pasted, cleaning
stays a step of the table, and the user's own word wins. The view is typed session state that `prepare_data` routes a
`keep_rows` into; a plot run draws the table through it and stores no data version for it.
"""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from pydantic import TypeAdapter

from agents.anyplot import pipeline, plot_view
from agents.anyplot.agent import VIEW_HEADING, session_context
from agents.anyplot.data.fidelity import COMBINED_IN_VIEW_HEAD
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import Operation, PrepareError
from agents.anyplot.dataset_versions import push_version
from agents.anyplot.plot_view import CLEARED_LINE, PLOT_VIEW, PlotView, ViewRefused, merged, route, table_only, view_of
from agents.anyplot.plugins.ledger import ToolCall, ledger_for
from agents.anyplot.plugins.tool_safety import TOOL_ALLOWED, call_outcome, changed_data
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import DATASET_ID, read_session
from agents.anyplot.tools.session import VIEW_BREAKS_BINDINGS, VIEW_CLEARED, prepare_data
from agents.main import Runtime, app, get_runtime
from agents.stream import turn_outcome

from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK, FakeAnthropic, default_script
from .test_from_version import TEAMS, context_for, fenced, pasted_session, points_of, write_back
from .test_paste_conversions import paste
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


def stored_now(sid: str, state: dict[str, Any]) -> Any:
    stored = get_services().datasets.get(state[DATASET_ID], sid)
    assert stored is not None
    return stored
