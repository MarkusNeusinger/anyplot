"""The view of the plot on the page: what the service tells the page about it, and the page's `.show_all()`.

A plot that drew a view of the plot (`plot_view.py`) shows fewer rows than the data card above it. The `plot` event
names the view that version drew (`view`: the counts and the view's parts), the turn's `done` names the view in force
after it, with or without a plot, and so do the answers of the routes that change the table without a turn. The
page's `.show_all()` is the action `show_all_rows`: the route clears the view in code and the run draws every row
again, from the latest plot.
"""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest
from google.adk.events.event import Event

from agents.anyplot import pipeline
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.plot_view import EVERY_ROW_LINE, MAX_PART_CHARS, MAX_SELECTIONS, PLOT_VIEW, PlotView, view_of
from agents.anyplot.plugins.ledger import RequestLedger
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.services import Services
from agents.anyplot.tools.session import prepare_data
from agents.main import ACTION_MESSAGES, NEW_DATA_ACTIONS, PLOT_ACTIONS, Runtime, app, get_runtime
from agents.stream import MAX_VIEW_PARTS, Translator, shown_view

from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK, FakeAnthropic, default_script
from .test_from_version import TEAMS, context_for, pasted_session, write_back
from .test_paste_conversions import paste
from .test_plot_new_data import change_data, plot_new_data
from .test_plot_view import CITIES, TOP_2, only, set_view, view_from
from .test_row_fidelity import HOURS, LINE_BINDINGS, QUESTION, SUMMED, bind_and_confirm, open_line_on_scatter_code
from .test_service_flow import HEADERS, SECOND_PLAN, USER, create_plot, parse_sse, permissive_queue, say
from .test_stream import parse


Events = list[tuple[str, dict[str, Any]]]
POINTS_40 = {"rows": 12, "of_rows": 24, "parts": ["Points ≥ 40"]}
"""The view "at least 40 points" on the 24 teams, as an event carries it."""


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


def one(events: Events, name: str) -> dict[str, Any]:
    return next(data for event, data in events if event == name)


def two_plots(second_reply: str = "Every row again.") -> dict[str, list[Any]]:
    """Two bare plot runs, one per turn: the first plot and the one a page action asks for."""
    return {
        "root": [
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
            {"call": "plot_pipeline", "args": {}},
            {"text": second_reply},
        ],
        "adapter": [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}],
        "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
    }


async def confirmed_teams(client: httpx.AsyncClient) -> str:
    sid = await pasted_session(client, TEAMS)
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
    return sid


async def show_all(client: httpx.AsyncClient, sid: str) -> httpx.Response:
    return await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "show_all_rows"})


class TestTheViewsWords:
    def test_a_view_reads_in_parts_one_per_selection_and_one_for_the_top_n(self) -> None:
        view = view_from(only("Land", "eq", "CH"), *TOP_2)

        assert view.parts(["Land"]) == ["Land = 'CH'", "top 2 by Umsatz"]
        assert view.words(["Land"]) == "Land = 'CH'; top 2 by Umsatz"
        assert PlotView().parts() == []

    def test_the_page_gets_the_counts_of_the_plots_line_and_the_parts(self) -> None:
        view = view_from(only("Land", "eq", "CH"), *TOP_2)
        seen = view_of(parse_dataset(CITIES), view)

        assert seen.shown(view) == {"rows": 2, "of_rows": 5, "parts": ["Land = 'CH'", "top 2 by Umsatz"]}
        # The same counts the plot's first line of "what changed" says.
        assert seen.note(view, 3, 200).startswith("The plot draws 2 of the 5 rows of data v3 (view: ")

    def test_a_part_with_long_values_gives_way_with_an_ellipsis(self) -> None:
        """The engine's words already shorten a long value and a long list; several of them in one selection can
        still outgrow a line of the card."""
        names = [f"Verwaltungsgemeinschaft Nummer {index:02d} im Kanton" for index in range(8)]
        table = parse_dataset("Stadt,Umsatz\n" + "".join(f"{name},{index}\n" for index, name in enumerate(names)))
        where = [
            {"column": "Stadt", "test": "eq", "values": names[:3]},
            {"column": "Stadt", "test": "ne", "value": names[7]},
        ]
        view = view_from({"op": "keep_rows", "where": where})
        assert len(view.parts(["Stadt"])[0]) > MAX_PART_CHARS

        shown = view_of(table, view).shown(view)

        assert (shown["rows"], shown["of_rows"]) == (3, 8)
        [part] = shown["parts"]
        assert len(part) == MAX_PART_CHARS and part.endswith("…") and part.startswith("Stadt is 'Verwaltungs")


class TestTheEvents:
    def test_a_view_passes_as_two_counts_and_its_parts_as_plain_lines(self) -> None:
        assert shown_view(POINTS_40) == POINTS_40
        # A part names the user's columns and values: one sanitised line each, as in the plot's `changes`.
        dirty = {"rows": 1, "of_rows": 2, "parts": ["Name = '<b>x</b>'", "see https://evil.example/a", "", 7]}
        clean = shown_view(dirty)
        assert clean is not None and (clean["rows"], clean["of_rows"]) == (1, 2)
        assert all("<" not in part and "http" not in part for part in clean["parts"]) and len(clean["parts"]) <= 2
        # A view holds its selections and a top N at most: nothing past that count leaves the service.
        assert MAX_VIEW_PARTS == MAX_SELECTIONS + 1
        many = shown_view({"rows": 1, "of_rows": 2, "parts": [f"part {index}" for index in range(9)]})
        assert many is not None and many["parts"] == [f"part {index}" for index in range(MAX_VIEW_PARTS)]

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "Points ≥ 40",
            {"rows": 12, "parts": []},
            {"rows": "12", "of_rows": 24, "parts": []},
            {"rows": True, "of_rows": 24, "parts": []},
            {"rows": -1, "of_rows": 24, "parts": []},
            {"rows": 12, "of_rows": 24, "parts": "Points ≥ 40"},
        ],
    )
    def test_anything_else_is_no_view(self, value: object) -> None:
        assert shown_view(value) is None

    def test_a_plot_event_carries_the_view_only_with_a_stored_version(self) -> None:
        def plot(output: dict[str, Any], view: dict[str, Any] | None) -> dict[str, Any]:
            ledger = RequestLedger(request_id="req-1", shipped_view=view)
            translator = Translator(ledger, run_id="run-1", spec_id="scatter-basic")
            return parse(translator.translate(Event(author="plot_pipeline", output=output))[0])[1]

        shipped = {"status": "ok", "attempts": 1, "artifacts": [], "version": 2}
        assert plot(shipped, POINTS_40)["view"] == POINTS_40
        assert "view" not in plot(shipped, None)  # every row
        assert "view" not in plot({"status": "failed", "reason": "render", "attempts": 2}, POINTS_40)

    def test_done_says_null_for_every_row_and_nothing_without_data(self) -> None:
        translator = Translator(RequestLedger(request_id="req-1"), run_id="run-1", spec_id="scatter-basic")

        assert "view" not in parse(translator.done())[1]  # no data: nothing to say
        assert parse(translator.done(view=None))[1]["view"] is None
        assert parse(translator.done(view=POINTS_40))[1]["view"] == POINTS_40

    def test_the_actions_of_the_page_know_show_all_rows(self) -> None:
        assert "show_all_rows" in PLOT_ACTIONS and NEW_DATA_ACTIONS == {"plot_new_data", "show_all_rows"}
        assert ACTION_MESSAGES["show_all_rows"].startswith("[action] Create the plot from every row")


class TestWhatAPlotAndATurnSay:
    async def test_a_plot_through_a_view_names_it_and_the_turn_names_the_view_in_force(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        swap_models("gemini", default_script())
        sid = await confirmed_teams(client)
        await set_view(runtime, sid, only("Points", "ge", 40))

        events = await create_plot(client, sid)

        plot = one(events, "plot")
        assert plot["view"] == POINTS_40
        assert plot["changes"][0] == "The plot draws 12 of the 24 rows of data v1 (view: Points ≥ 40)"
        assert one(events, "done")["view"] == POINTS_40

    async def test_a_plot_of_every_row_carries_no_view_and_the_turn_says_so(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        swap_models("gemini", default_script())
        sid = await confirmed_teams(client)

        events = await create_plot(client, sid)

        assert "view" not in one(events, "plot")
        assert one(events, "done")["view"] is None

    async def test_a_view_set_without_a_plot_reaches_the_page_at_the_turns_end(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        """The root may set a view and leave the plot for the next turn: the data card still says what the next plot
        draws, which only the turn's `done` can tell it."""
        top = [{"op": "sort", "column": "Points", "descending": True}, {"op": "keep_rows", "n": 5}]
        script = {
            "root": [{"call": "prepare_data", "args": {"operations": top}}, {"text": "Set: the top 5 by points."}],
            "adapter": [],
            "reviewer": [],
        }
        swap_models("anthropic-vertex", script)
        sid = await confirmed_teams(client)

        events = await say(client, sid, "only the top 5 by points, plot it later")

        done = one(events, "done")
        assert done["view"] == {"rows": 5, "of_rows": 24, "parts": ["top 5 by Points"]}
        assert done["turn"] == "kept" and "dataset" not in done and done["data_confirmed"] is True
        assert not any(name == "plot" for name, _ in events)


class TestShowAll:
    async def test_it_clears_the_view_and_draws_every_row_from_the_latest_plot(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        fake = swap_models("anthropic-vertex", two_plots())
        sid = await confirmed_teams(client)
        await set_view(runtime, sid, only("Points", "ge", 40))
        first = one(await create_plot(client, sid), "plot")
        assert first["view"] == POINTS_40 and len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 12

        response = await show_all(client, sid)

        assert response.status_code == 200, response.text
        events = parse_sse(response.text)
        plot = one(events, "plot")
        assert (plot["status"], plot["version"], plot["new_data"]) == ("ok", 2, "previous")
        assert "view" not in plot
        assert plot["changes"][0] == EVERY_ROW_LINE.format(number=1, rows=24)
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 24
        done = one(events, "done")
        assert done["view"] is None and done["data_confirmed"] is True and "dataset" not in done
        # The view is gone from the session, the table is the one the user confirmed, and the version says so.
        assert (await runtime.session(USER, sid)).state.get(PLOT_VIEW) is None
        latest = services.versions.latest_rendered(sid)
        assert latest is not None and latest.view is None and latest.data_version == 1
        # The run changed the latest plot with the server's sentence that the rows changed, no request of the user's.
        adapter_calls = [call for call in fake.calls if FakeAnthropic.kind(call) == "adapter"]
        assert pipeline.DATA_CHANGE_REQUEST in json.dumps(adapter_calls[-1], ensure_ascii=False, default=str)
        assert latest.requests == []
        # The root read the page's own line, never words of the user.
        root_calls = [call for call in fake.calls if FakeAnthropic.kind(call) == "root"]
        assert ACTION_MESSAGES["show_all_rows"] in json.dumps(root_calls[-1], ensure_ascii=False, default=str)

    async def test_it_is_refused_when_no_view_is_set_and_the_latest_plot_drew_every_row(
        self, client: httpx.AsyncClient, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", default_script())
        sid = await confirmed_teams(client)
        await create_plot(client, sid)
        jobs = len(backend.jobs)

        response = await show_all(client, sid)

        assert (response.status_code, response.json()) == (422, {"detail": "no_view"})
        assert len(backend.jobs) == jobs  # nothing ran

    async def test_a_session_without_a_plot_or_a_view_refuses_it_too(self, client: httpx.AsyncClient) -> None:
        sid = await confirmed_teams(client)

        response = await show_all(client, sid)

        assert (response.status_code, response.json()) == (422, {"detail": "no_view"})

    async def test_a_page_behind_the_session_still_gets_its_redraw(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        """The chat cleared the view without a plot (`reset_view`), and the card of the latest plot still shows the
        view it drew: its `.show_all()` redraws that plot from every row."""
        swap_models("anthropic-vertex", two_plots())
        sid = await confirmed_teams(client)
        await set_view(runtime, sid, only("Points", "ge", 40))
        await create_plot(client, sid)
        await runtime.write_state(await runtime.session(USER, sid), {PLOT_VIEW: None})

        response = await show_all(client, sid)

        assert response.status_code == 200, response.text
        plot = one(parse_sse(response.text), "plot")
        assert (plot["status"], plot["version"]) == ("ok", 2) and "view" not in plot
        assert plot["changes"][0] == EVERY_ROW_LINE.format(number=1, rows=24)
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 24


class TestTheLineForEveryRow:
    """`EVERY_ROW_LINE`: a run whose base version drew a view, with none set any more, names the rows it draws."""

    async def test_it_names_the_version_the_run_draws_when_the_table_changed_too(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        """The view was set on data v1 and is gone, and the table lost a row since: the line counts data v2's rows,
        and says nothing of drawing them again."""
        swap_models("anthropic-vertex", two_plots())
        sid = await confirmed_teams(client)
        await set_view(runtime, sid, only("Points", "ge", 40))
        await create_plot(client, sid)
        await runtime.write_state(await runtime.session(USER, sid), {PLOT_VIEW: None})
        await change_data(runtime, services, sid)

        plot = await plot_new_data(client, sid)

        assert (plot["status"], plot["version"], plot["new_data"]) == ("ok", 2, "previous")
        assert plot["changes"][0] == EVERY_ROW_LINE.format(number=2, rows=23)
        assert plot["changes"][0] == "The view of the plot is cleared: the plot draws every row of data v2, 23 in all"
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 23

    async def test_a_key_combined_into_a_new_version_is_said_instead(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        """Without the view the plot's key repeats, and the run combines it into a new data version: the plot draws
        that version's four rows, so a line that counted the table's twelve would contradict the one after it."""
        script = {
            "root": [
                {"call": "plot_pipeline", "args": {}},
                {"text": ROOT_REPLY},
                {"call": "plot_pipeline", "args": {}},
                {"text": QUESTION},
                {"call": "plot_pipeline", "args": {"combine": "sum", "base": "previous"}},
                {"text": "Summed per hour."},
            ],
            "adapter": [{"json": SCATTER_PLAN}, {"json": SECOND_PLAN}],
            "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
        }
        swap_models("anthropic-vertex", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        # One student per study hour: no key repeats among the rows the view shows.
        one_each = {"column": "Student", "test": "eq", "values": ["S00", "S01", "S02", "S03"]}
        await set_view(runtime, sid, {"op": "keep_rows", "where": [one_each]})
        first = one(await create_plot(client, sid), "plot")
        # The engine's words name three values of a longer list and count the rest.
        assert first["view"] == {"rows": 4, "of_rows": 12, "parts": ["Student is 'S00', 'S01', 'S02' or 1 more"]}

        # Every row again: three students share each hour, so the run stops and the root asks.
        asked = parse_sse((await show_all(client, sid)).text)
        assert [data["text"] for name, data in asked if name == "message"] == [QUESTION]
        assert not any(name == "plot" for name, _ in asked) and one(asked, "done")["view"] is None

        events = await say(client, sid, "add them up")

        plot = one(events, "plot")
        assert (plot["status"], plot["version"]) == ("ok", 2)
        assert plot["changes"][0] == SUMMED
        assert not any(line.startswith("The view of the plot is cleared") for line in plot["changes"])
        # Three students per hour: 50 + 62 + 74 for two hours, and so on.
        assert backend.jobs[-1].data_csv.strip().splitlines()[1:] == ["2,186", "4,195", "6,204", "8,213"]


class TestTheDataRoutes:
    async def test_an_undo_says_whether_the_view_still_holds_on_the_restored_table(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-page-1")
        await prepare_data([{"op": "drop_rows", "where": [{"column": "Points", "test": "lt", "value": 20}]}], context)
        await prepare_data([only("Points", "ge", 40)], context)
        await write_back(runtime, sid, context)

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)

        assert undone.status_code == 200, undone.text
        body = undone.json()
        # The rows the drop took are back: the view shows the same 12 rows, of 24 again.
        assert body["version"] == 1 and body["view"] == POINTS_40

    async def test_an_undo_to_a_table_the_view_does_not_fit_says_every_row(
        self, client: httpx.AsyncClient, runtime: Runtime
    ) -> None:
        sid = await pasted_session(client, TEAMS)
        context = await context_for(client, sid, "inv-page-2")
        await prepare_data([{"op": "rename", "column": "Points", "name": "Punkte"}], context)
        await prepare_data([only("Punkte", "ge", 40)], context)
        await write_back(runtime, sid, context)

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)

        assert undone.status_code == 200, undone.text
        assert undone.json()["view"] is None  # `Punkte` is `Points` again: the next plot draws every row
