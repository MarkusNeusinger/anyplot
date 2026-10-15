"""Questions about the data never change it (`query_data`), and a step-2 note survives a binding change.

Live test round 2 of 2026-10-15: asked "Welches Land hatte 2023 den höchsten Pro-Kopf-Ausstoss?",
the root filtered the user's dataset to the rows of 2023 with `prepare_data`, then asked the user
to `.undo()` it; and a step-2 note ("only co2_per_capita, title ...") changed the bindings, which
dropped the confirmation, so the plot stopped on `data_unconfirmed` and the title was lost. The
tools are called as ADK would call them (a context with the session state) on sessions opened
through the real `/v1` routes; the flow test drives the whole turn with scripted models.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.query import MAX_QUERY_COLUMNS, MAX_QUERY_ROWS, run_query
from agents.anyplot.data.roles import DataRole
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.pipeline import (
    EXPECTED_HEADING,
    keep_pending_request,
    kept_texts,
    merged_request,
    settle_pending_request,
    take_pending_request,
)
from agents.anyplot.plugins.tool_safety import ToolSafetyPlugin, result_limit, result_size
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome
from agents.anyplot.schemas import MAX_CHANGE_REQUEST_CHARS, Binding, PipelineArgs
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import (
    BINDINGS,
    CONFIRMED,
    DATASET_ID,
    DATASET_VERSION,
    PENDING_BINDINGS,
    PENDING_EXPECTED_TEXTS,
    PENDING_REQUEST,
    narrows,
    read_session,
)
from agents.anyplot.settings import get_settings
from agents.anyplot.tools.session import query_data, query_result, set_bindings
from agents.main import Runtime, app, get_runtime

from .fakes import SCATTER_PLAN, VERDICT_OK, ScriptedLlm
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    create_plot,
    open_session,
    parse_sse,
    permissive_queue,
    snapshot_body,
)


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


# The OWID table of the live test, three of its five countries and three of its years.
OWID = (
    "country,year,co2_per_capita,share_global_co2\n"
    "Austria,2021,6.9,0.21\nAustria,2022,6.5,0.2\nAustria,2023,6.233,0.19\n"
    "Germany,2021,8.1,1.8\nGermany,2022,7.9,1.75\nGermany,2023,7.023,1.6\n"
    "Switzerland,2021,4.1,0.1\nSwitzerland,2022,3.9,0.1\nSwitzerland,2023,3.7,0.09\n"
)
YEAR_2023 = {"column": "year", "test": "ne", "value": 2023}


async def open_line_multi(client: httpx.AsyncClient, data: str = OWID) -> tuple[str, list[Binding]]:
    """A confirmed line-multi session on `data`; returns the session id and the default bindings."""
    response = await client.post(
        "/v1/sessions",
        headers=HEADERS,
        json={
            "user": USER,
            "spec_id": "line-multi",
            "library": "matplotlib",
            "locale": "de",
            "snapshot": snapshot_from_repo("line-multi", "matplotlib").model_dump(),
        },
    )
    assert response.status_code == 200, response.text
    sid: str = response.json()["session_id"]
    stored = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": data})
    assert stored.status_code == 200, stored.text
    bindings = [Binding.model_validate(item) for item in stored.json()["bindings"]]
    confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
    assert confirmed.status_code == 200, confirmed.text
    return sid, bindings


async def context_for(client: httpx.AsyncClient, sid: str, invocation: str) -> SimpleNamespace:
    context = SimpleNamespace(state=await _session_state(client, sid), session=SimpleNamespace(id=sid))
    context.invocation_id = invocation
    return context


def table_of(result: dict[str, Any]) -> dict[str, Any]:
    """The `<user_data>` table of a `query_data` result."""
    match = re.search(r"<user_data>\n?(.*?)\n?</user_data>", result["table"], re.DOTALL)
    assert match is not None, result
    table: dict[str, Any] = json.loads(match.group(1))
    return table


class TestQueryData:
    """Fixtures for the three kinds of question the live test asked: a maximum in a year, a share, a trend."""

    async def test_the_largest_value_in_a_year_leaves_the_data_as_it_was(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-q-1")
        before = dict(context.state)

        result = await query_data(
            [{"op": "drop_rows", "where": [YEAR_2023]}, {"op": "sort", "column": "co2_per_capita", "descending": True}],
            context,
            columns=["country", "co2_per_capita"],
            limit=1,
        )

        assert result["status"] == "ok", result
        assert table_of(result) == {"columns": ["country", "co2_per_capita"], "rows": [["Germany", "7.023"]]}
        assert (result["rows"], result["truncated"]) == (3, True)
        # Nothing stored: the same dataset, version and confirmation, and no state written.
        assert context.state == before
        view = read_session(context.state)
        assert view is not None and view.data_confirmed and view.dataset_version == 1
        assert get_services().datasets.get(context.state[DATASET_ID], sid).profile.rows == 9  # type: ignore[union-attr]

    async def test_a_share_per_year(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-q-2")

        result = await query_data(
            [
                {
                    "op": "derive",
                    "name": "share_pct",
                    "how": "share",
                    "columns": ["co2_per_capita"],
                    "within": ["year"],
                    "percent": True,
                },
                {"op": "drop_rows", "where": [YEAR_2023]},
                {"op": "sort", "column": "share_pct", "descending": True},
            ],
            context,
            columns=["country", "share_pct"],
        )

        rows = table_of(result)["rows"]
        assert [row[0] for row in rows] == ["Germany", "Austria", "Switzerland"]
        assert sum(float(row[1]) for row in rows) == pytest.approx(100.0)
        assert "share_pct" in result["changes"]  # the steps applied to the copy, fenced as tool notes
        assert context.state[DATASET_VERSION] == 1

    async def test_a_trend_as_an_index(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-q-3")

        result = await query_data(
            [
                {
                    "op": "derive",
                    "name": "index",
                    "how": "index",
                    "columns": ["co2_per_capita"],
                    "within": ["country"],
                    "order": "year",
                },
                {"op": "drop_rows", "where": [YEAR_2023]},
                {"op": "sort", "column": "index", "descending": False},
            ],
            context,
            columns=["country", "index"],
            limit=3,
        )

        rows = table_of(result)["rows"]
        assert rows[0][0] == "Germany" and float(rows[0][1]) == pytest.approx(7.023 / 8.1 * 100)
        assert all(float(row[1]) < 100 for row in rows)  # every country fell from 2021 to 2023

    async def test_without_operations_it_reads_the_first_rows(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)

        result = await query_data([], await context_for(client, sid, "inv-q-4"))

        table = table_of(result)
        assert table["columns"] == ["country", "year", "co2_per_capita", "share_global_co2"]
        assert len(table["rows"]) == 9 and result["truncated"] is False

    async def test_errors_name_the_column_and_change_nothing(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-q-5")
        before = dict(context.state)

        unknown = await query_data([{"op": "sort", "column": "Jahr"}], context)
        empty = await query_data(
            [{"op": "drop_rows", "where": [{"column": "year", "test": "gt", "value": 0}]}], context
        )
        invalid = await query_data([{"op": "sort"}], context)

        assert (unknown["status"], unknown["code"]) == ("error", "unknown_column")
        assert (empty["status"], empty["code"]) == ("error", "empty_result")
        assert (invalid["status"], invalid["code"]) == ("error", "invalid_operations")
        assert context.state == before

    @pytest.mark.parametrize("cell", ["a" * 40, "é" * 40, "\N{CJK UNIFIED IDEOGRAPH-4E00}" * 40])
    def test_the_result_stays_within_its_cap_at_its_largest(self, cell: str) -> None:
        names = [f"{'c' * 60}{i:02d}" for i in range(MAX_QUERY_COLUMNS + 2)]
        rows = "\n".join(",".join(cell for _ in names) for _ in range(MAX_QUERY_ROWS + 5))
        parsed = parse_dataset(",".join(names) + "\n" + rows + "\n")
        answer = run_query(parsed, [], limit=MAX_QUERY_ROWS)

        result = query_result(answer)

        assert len(answer.columns) == MAX_QUERY_COLUMNS and len(answer.rows) == MAX_QUERY_ROWS
        assert result_size(result) <= result_limit("query_data")
        assert result["truncated"] is True and result["rows"] == MAX_QUERY_ROWS + 5
        assert table_of(result)["rows"]  # cut by rows, never to nothing
        if cell.isascii():
            assert len(table_of(result)["rows"]) == MAX_QUERY_ROWS  # plain text fits whole

    @pytest.mark.parametrize(
        ("arguments", "verdict"),
        [
            ({"operations": []}, None),
            ({"operations": [{"op": "sort", "column": "year"}], "columns": ["year"], "limit": 25}, None),
            ({"operations": [], "columns": None, "limit": 5}, None),
            ({"operations": [], "limit": 26}, "invalid_arguments"),
            ({"operations": [], "columns": [f"c{i}" for i in range(9)]}, "invalid_arguments"),
            ({"operations": [{"op": "sort", "column": "year"}] * 6}, "invalid_arguments"),
            ({"operations": [], "expression": "df.max()"}, "invalid_arguments"),
            # A condition value is data, compared with the cells: a web address in it passes.
            (
                {
                    "operations": [
                        {"op": "drop_rows", "where": [{"column": "url", "test": "eq", "value": "https://a.b"}]}
                    ]
                },
                None,
            ),
        ],
    )
    def test_tool_safety_bounds_the_arguments(self, arguments: dict[str, Any], verdict: str | None) -> None:
        assert ToolSafetyPlugin.check("query_data", arguments, "anyplot") == verdict


def roles() -> list[DataRole]:
    return snapshot_from_repo("line-multi", "matplotlib").roles()


def bind(*pairs: tuple[str, str]) -> list[Binding]:
    return [Binding(role=role, column=column) for role, column in pairs]


class TestNarrowedBindings:
    """Bindings that only leave out roles the user confirmed keep the confirmation (`AGENT_NARROWED_BINDINGS`)."""

    CONFIRMED = bind(("x", "year"), ("y1", "co2_per_capita"), ("y2", "share_global_co2"), ("series", "country"))

    @pytest.mark.parametrize(
        ("bindings", "expected"),
        [
            (bind(("x", "year"), ("y1", "co2_per_capita"), ("series", "country")), True),  # drops the 2nd line
            (bind(("x", "year"), ("y1", "share_global_co2"), ("series", "country")), False),  # y1 plots another column
            (bind(("x", "year"), ("y1", "co2_per_capita"), ("y2", "share_global_co2")), False),  # series dropped
            (bind(("x", "year"), ("y1", "co2_per_capita")), False),  # series and a line dropped
            (bind(("y1", "co2_per_capita"), ("y2", "share_global_co2"), ("series", "country")), False),  # x dropped
            (CONFIRMED, False),  # nothing left out
            (bind(("x", "year"), ("y1", "share_global_co2"), ("y2", "co2_per_capita"), ("series", "country")), False),
            (bind(("x", "co2_per_capita"), ("y1", "year")), False),  # a column in another role
            (bind(("x", "year"), ("y1", "co2_per_capita"), ("series", "share_global_co2")), False),
        ],
    )
    def test_narrows(self, bindings: list[Binding], expected: bool) -> None:
        assert narrows(self.CONFIRMED, bindings, roles()) is expected

    async def test_a_note_that_drops_a_series_keeps_the_confirmation(self, client: httpx.AsyncClient) -> None:
        sid, defaults = await open_line_multi(client)
        assert {(b.role, b.column) for b in defaults} == {(b.role, b.column) for b in self.CONFIRMED}
        context = await context_for(client, sid, "inv-b-1")

        result = await set_bindings(
            [
                {"role": "x", "column": "year"},
                {"role": "y1", "column": "co2_per_capita"},
                {"role": "series", "column": "country"},
            ],
            context,
        )

        assert result["status"] == "ok" and result["data_confirmed"] is True, result
        view = read_session(context.state)
        assert view is not None and view.data_confirmed and len(view.bindings) == 3

    async def test_a_swap_drops_the_confirmation(self, client: httpx.AsyncClient) -> None:
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-b-2")

        result = await set_bindings(
            [
                {"role": "x", "column": "year"},
                {"role": "y1", "column": "share_global_co2"},
                {"role": "y2", "column": "co2_per_capita"},
                {"role": "series", "column": "country"},
            ],
            context,
        )

        assert result["status"] == "ok" and result["data_confirmed"] is False

    async def test_reset_asks_again_for_a_narrowing_too(
        self, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_NARROWED_BINDINGS", "reset")
        get_settings.cache_clear()
        sid, _ = await open_line_multi(client)
        context = await context_for(client, sid, "inv-b-3")

        result = await set_bindings(
            [
                {"role": "x", "column": "year"},
                {"role": "y1", "column": "co2_per_capita"},
                {"role": "series", "column": "country"},
            ],
            context,
        )

        assert result["data_confirmed"] is False
        assert context.state[CONFIRMED] != ""  # the old fingerprint stays, it just no longer matches
        get_settings.cache_clear()


class TestPendingRequest:
    """A first plot's note that stopped on `not_ready` is kept for the next run."""

    @pytest.mark.parametrize(
        ("reason", "args", "kept"),
        [
            ("data_unconfirmed", PipelineArgs(change_request="Title: CO2 per capita"), "Title: CO2 per capita"),
            ("incomplete_bindings", PipelineArgs(change_request="log y"), "log y"),
            ("no_dataset", PipelineArgs(change_request="log y"), None),
            ("data_unconfirmed", PipelineArgs(), None),
            ("data_unconfirmed", PipelineArgs(change_request="bigger", base="previous"), None),
        ],
    )
    def test_keep(self, reason: Any, args: PipelineArgs, kept: str | None) -> None:
        state: dict[str, Any] = {}
        keep_pending_request(state, args, reason)
        assert state.get(PENDING_REQUEST) == kept

    def test_a_second_blocked_request_joins_the_first(self) -> None:
        state: dict[str, Any] = {}
        keep_pending_request(state, PipelineArgs(change_request="Title: CO2 per capita"), "data_unconfirmed")
        keep_pending_request(state, PipelineArgs(change_request="log y"), "data_unconfirmed")
        keep_pending_request(state, PipelineArgs(change_request="log y"), "data_unconfirmed")  # a repeat adds nothing

        assert state[PENDING_REQUEST] == "Title: CO2 per capita\nlog y"
        assert take_pending_request(state, PipelineArgs()).change_request == "Title: CO2 per capita\nlog y"

    async def test_a_fresh_paste_drops_the_kept_request(self, client: httpx.AsyncClient) -> None:
        sid = await open_session(client)
        runtime = app.dependency_overrides[get_runtime]()
        session = await runtime.session(USER, sid)
        await runtime.write_state(session, {PENDING_REQUEST: "Title: Swiss emissions"})
        assert (await _session_state(client, sid))[PENDING_REQUEST] == "Title: Swiss emissions"

        stored = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": OWID})

        assert stored.status_code == 200, stored.text
        assert (await _session_state(client, sid)).get(PENDING_REQUEST) is None

    @pytest.mark.parametrize(
        ("args", "expected"),
        [
            (PipelineArgs(), "Title: A"),
            (PipelineArgs(change_request="log y"), "Title: A\nlog y"),
            (PipelineArgs(change_request="Title: A"), "Title: A"),
            (PipelineArgs(change_request="x" * 595), "x" * 595),  # too little room left: the run's own stands alone
            (PipelineArgs(change_request="bigger", base="previous"), "bigger"),
        ],
    )
    def test_take(self, args: PipelineArgs, expected: str) -> None:
        state: dict[str, Any] = {PENDING_REQUEST: "Title: A"}
        assert take_pending_request(state, args).change_request == expected
        assert state[PENDING_REQUEST] == "Title: A"  # kept until a run ships

    def test_a_long_kept_note_is_cut_not_dropped(self) -> None:
        pending = "Title: " + "t" * 400
        merged = merged_request(pending, "y" * 300)

        assert len(merged) <= MAX_CHANGE_REQUEST_CHARS
        assert merged.startswith("Title: ttt") and merged.endswith("…\n" + "y" * 300)

    @pytest.mark.parametrize(
        ("shipped", "args", "kept"),
        [
            (True, PipelineArgs(change_request="Title: A\nlog y"), None),
            (False, PipelineArgs(change_request="Title: A\nlog y"), "Title: A\nlog y"),  # a failed run loses nothing
            (False, PipelineArgs(change_request="bigger", base="previous"), "Title: A"),
            (True, PipelineArgs(change_request="bigger", base="previous"), "Title: A"),  # took nothing, clears nothing
            (False, PipelineArgs(), "Title: A"),
        ],
    )
    def test_settle(self, shipped: bool, args: PipelineArgs, kept: str | None) -> None:
        state: dict[str, Any] = {PENDING_REQUEST: "Title: A"}
        settle_pending_request(state, args, shipped)
        assert state[PENDING_REQUEST] == kept

    def test_settle_after_a_change_cleans_corrupt_stored_texts(self) -> None:
        state: dict[str, Any] = {PENDING_REQUEST: "Title: A", PENDING_EXPECTED_TEXTS: ["A", "   ", "a\x07b", 7]}
        settle_pending_request(state, PipelineArgs(change_request="bigger", base="previous"), shipped=True)
        assert state == {PENDING_REQUEST: "Title: A", PENDING_EXPECTED_TEXTS: ["A"]}

    @pytest.mark.parametrize(
        "change",
        [
            ("put", "bindings", [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]),
            ("post", "library", {"library": "seaborn", "snapshot": snapshot_body(library="seaborn")}),
            ("post", "dataset", {"text": OWID}),
        ],
    )
    async def test_a_binding_change_new_data_or_a_library_switch_drops_the_note(
        self, client: httpx.AsyncClient, change: tuple[str, str, Any]
    ) -> None:
        sid = await open_session(client)
        runtime = app.dependency_overrides[get_runtime]()
        kept = {PENDING_REQUEST: "Title: A", PENDING_EXPECTED_TEXTS: ["A"]}
        await runtime.write_state(await runtime.session(USER, sid), kept)
        method, path, body = change

        response = await client.request(method.upper(), f"/v1/sessions/{sid}/{path}", headers=HEADERS, json=body)

        assert response.status_code == 200, response.text
        state = await _session_state(client, sid)
        assert state.get(PENDING_REQUEST) is None and state.get(PENDING_EXPECTED_TEXTS) is None

    def test_every_state_write_of_new_bindings_or_data_drops_the_note(self) -> None:
        from agents.anyplot.dataset_versions import _delta
        from agents.anyplot.session_state import apply_bindings, initial_state

        _, delta = apply_bindings([], roles(), parse_dataset(OWID).profile)
        snapshot = snapshot_from_repo("line-multi", "matplotlib")
        state = initial_state(
            spec_id="line-multi", library="seaborn", locale="de", snapshot=snapshot, normalised="", readiness={}
        )
        for written in (_delta("d", [], [], 2), delta, state):
            assert written[PENDING_REQUEST] is None and written[PENDING_EXPECTED_TEXTS] is None

    def test_the_texts_travel_with_the_note(self) -> None:
        state: dict[str, Any] = {BINDINGS: []}
        args = PipelineArgs(change_request="Title: CO2 pro Kopf", expected_texts=["CO2 pro Kopf"])
        keep_pending_request(state, args, "data_unconfirmed")

        assert state[PENDING_EXPECTED_TEXTS] == ["CO2 pro Kopf"]
        taken = take_pending_request(state, PipelineArgs())  # a bare `.create_plot()` fills in the kept texts
        assert (taken.change_request, taken.expected_texts) == ("Title: CO2 pro Kopf", ["CO2 pro Kopf"])
        settle_pending_request(state, taken, shipped=False)  # a failed run keeps both
        assert state[PENDING_EXPECTED_TEXTS] == ["CO2 pro Kopf"]
        settle_pending_request(state, taken, shipped=True)
        assert state[PENDING_REQUEST] is None and state[PENDING_EXPECTED_TEXTS] is None

    @pytest.mark.parametrize(
        ("own", "expected"),
        [
            (PipelineArgs(change_request="call it Study time", expected_texts=["Study time"]), ["Study time"]),
            (PipelineArgs(change_request="log y"), []),  # the user's latest word brings no text: none is checked
            (PipelineArgs(expected_texts=["12 %"]), ["12 %"]),
            (PipelineArgs(), ["Lernzeit"]),
        ],
    )
    def test_a_run_with_its_own_word_replaces_the_kept_texts(self, own: PipelineArgs, expected: list[str]) -> None:
        # Review of 2026-10-15: the root never sees the kept texts, so a withdrawn one must not be checked.
        state: dict[str, Any] = {PENDING_REQUEST: "Title: Lernzeit", PENDING_EXPECTED_TEXTS: ["Lernzeit"]}
        assert take_pending_request(state, own).expected_texts == expected

    def test_the_latest_blocked_turn_decides_the_texts(self) -> None:
        state: dict[str, Any] = {BINDINGS: []}
        for turn in range(1, 4):
            texts = [f"t{turn}.{index}" for index in range(4)]
            keep_pending_request(
                state, PipelineArgs(change_request=f"note {turn}", expected_texts=texts), "data_unconfirmed"
            )

        assert state[PENDING_EXPECTED_TEXTS] == ["t3.0", "t3.1", "t3.2", "t3.3"]  # never the oldest
        assert state[PENDING_REQUEST] == "note 1\nnote 2\nnote 3"

    def test_texts_alone_are_kept_and_reach_a_bare_first_plot(self) -> None:
        state: dict[str, Any] = {BINDINGS: []}
        keep_pending_request(state, PipelineArgs(expected_texts=["12 %"]), "incomplete_bindings")

        assert state[PENDING_EXPECTED_TEXTS] == ["12 %"] and state[PENDING_REQUEST] is None
        taken = take_pending_request(state, PipelineArgs())
        assert (taken.change_request, taken.expected_texts) == ("", ["12 %"])
        assert take_pending_request(state, PipelineArgs(base="previous")).expected_texts == []

    @pytest.mark.parametrize(
        ("stored", "expected"),
        [
            (["a", "b", "a"], ["a", "b"]),
            (["ok", 7, "", "   ", "x" * 121, "a\x07b", None], ["ok"]),  # read through the PipelineArgs validator
            (["1", "2", "3", "4", "5", "6"], ["1", "2", "3", "4", "5"]),
            ("not a list", []),
            (None, []),
        ],
    )
    def test_kept_texts(self, stored: object, expected: list[str]) -> None:
        assert kept_texts(stored) == expected

    def test_a_whitespace_or_control_text_is_refused_from_the_root_too(self) -> None:
        for bad in ("   ", "a\x07b"):
            with pytest.raises(ValueError):
                PipelineArgs(expected_texts=[bad])

    def test_filling_the_roles_open_when_the_note_was_kept_keeps_it(self) -> None:
        from agents.anyplot.session_state import apply_bindings

        held = [{"role": "x", "column": "year"}]
        profile = parse_dataset(OWID).profile
        filled = bind(("x", "year"), ("y1", "co2_per_capita"))
        changed = bind(("x", "co2_per_capita"), ("y1", "year"))

        assert PENDING_REQUEST not in apply_bindings(filled, roles(), profile, held)[1]
        assert apply_bindings(changed, roles(), profile, held)[1][PENDING_REQUEST] is None
        assert apply_bindings(filled, roles(), profile, None)[1][PENDING_REQUEST] is None

    async def test_a_note_held_on_incomplete_bindings_survives_the_binding_that_completes_them(
        self, client: httpx.AsyncClient
    ) -> None:
        sid, _ = await open_line_multi(client)
        runtime = app.dependency_overrides[get_runtime]()
        partial = [{"role": "x", "column": "year"}]
        await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=partial)
        state: dict[str, Any] = dict(await _session_state(client, sid))
        keep_pending_request(
            state, PipelineArgs(change_request="Title: A", expected_texts=["A"]), "incomplete_bindings"
        )
        kept = {key: state[key] for key in (PENDING_REQUEST, PENDING_EXPECTED_TEXTS, PENDING_BINDINGS)}
        await runtime.write_state(await runtime.session(USER, sid), kept)

        filled = [*partial, {"role": "y1", "column": "co2_per_capita"}]
        response = await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=filled)

        assert response.status_code == 200, response.text
        after = await _session_state(client, sid)
        assert (after[PENDING_REQUEST], after[PENDING_EXPECTED_TEXTS]) == ("Title: A", ["A"])
        changed = [{"role": "x", "column": "co2_per_capita"}, {"role": "y1", "column": "year"}]
        await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=changed)
        assert (await _session_state(client, sid))[PENDING_REQUEST] is None

    async def test_a_replaced_text_is_not_checked(
        self, client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch, backend: FakeBackend
    ) -> None:
        """`AGENT_EXPECT_CHECK=repair`: the render draws the new title only, so a check of the kept one would miss."""
        monkeypatch.setenv("AGENT_EXPECT_CHECK", "repair")
        get_settings.cache_clear()
        probe = {"texts": [], "labels": [{"kind": "title", "text": "Study time"}]}
        backend.script = lambda job, theme: FakeOutcome(probe=probe)
        swap_axes = {
            "call": "set_bindings",
            "args": {"bindings": [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]},
        }
        script = {
            "root": [
                swap_axes,
                {
                    "call": "plot_pipeline",
                    "args": {"change_request": "Title: Lernzeit", "expected_texts": ["Lernzeit"]},
                },
                {"text": "Please confirm the new bindings."},
                # After the confirmation the user replaces the title in words.
                {
                    "call": "plot_pipeline",
                    "args": {"change_request": "Title: Study time", "expected_texts": ["Study time"]},
                },
                {"text": "Here is your plot."},
            ],
            "adapter": [{"json": SCATTER_PLAN}] * 3,
            "reviewer": [{"json": VERDICT_OK}] * 3,
        }
        swap_models("gemini", script)
        sid = await open_session(client)
        await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "swap axes, title Lernzeit"})
        await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)

        response = await client.post(
            f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "call it 'Study time'"}
        )

        plot = next(data for name, data in parse_sse(response.text) if name == "plot")
        assert plot["status"] in ("ok", "needs_attention"), plot
        shows = get_services().versions.all(sid)[-1].result.shows  # the plot event leaves `shows` to the root
        assert shows is not None and shows.texts is not None  # the texts were measured
        assert shows.requested_not_found == []  # the withdrawn "Lernzeit" was never checked
        assert plot["attempts"] == 1  # so no repair round ran for it
        assert (await _session_state(client, sid))[PENDING_EXPECTED_TEXTS] is None
        get_settings.cache_clear()

    async def test_a_kept_text_reaches_the_next_create_plot(
        self, client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch, backend: FakeBackend
    ) -> None:
        """`AGENT_EXPECT_CHECK=repair`: the render never draws the kept title, so the kept text shows as checked."""
        monkeypatch.setenv("AGENT_EXPECT_CHECK", "repair")
        get_settings.cache_clear()
        probe = {"texts": [], "labels": [{"kind": "title", "text": "Exam Score by Study Hours"}]}
        backend.script = lambda job, theme: FakeOutcome(probe=probe)
        script = {
            "root": [
                {
                    "call": "set_bindings",
                    "args": {
                        "bindings": [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
                    },
                },
                {
                    "call": "plot_pipeline",
                    "args": {"change_request": "Title: Lernzeit", "expected_texts": ["Lernzeit"]},
                },
                {"text": "Please confirm the new bindings."},
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here is your plot."},
            ],
            "adapter": [{"json": SCATTER_PLAN}] * 3,
            "reviewer": [{"json": VERDICT_OK}] * 3,
        }
        fake = swap_models("gemini", script)
        sid = await open_session(client)

        await client.post(
            f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "swap the axes, title Lernzeit"}
        )
        kept = await _session_state(client, sid)
        assert (kept[PENDING_REQUEST], kept[PENDING_EXPECTED_TEXTS]) == ("Title: Lernzeit", ["Lernzeit"])
        await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        # The confirmation is no binding change: the note and its texts survive it.
        assert (await _session_state(client, sid))[PENDING_EXPECTED_TEXTS] == ["Lernzeit"]
        events = await create_plot(client, sid)

        assert next(data for name, data in events if name == "plot")["status"] in ("ok", "needs_attention")
        assert isinstance(fake, ScriptedLlm)
        adapter = [r for r in fake.requests if (r.config.labels or {})["agent_kind"] == "adapter"]
        text = "".join(part.text or "" for part in adapter[0].contents[-1].parts or [])
        assert EXPECTED_HEADING in text and "Lernzeit" in text
        shows = get_services().versions.all(sid)[-1].result.shows
        assert shows is not None and shows.requested_not_found == ["Lernzeit"]  # the kept text was checked
        assert (await _session_state(client, sid))[PENDING_EXPECTED_TEXTS] is None
        get_settings.cache_clear()

    async def test_a_note_survives_a_binding_change_that_asks_for_confirmation(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        note = "Title: Exam score by study hours"
        script = {
            "root": [
                # The note's turn: the root swaps the axes, which asks for `.confirm()` again, then plots.
                {
                    "call": "set_bindings",
                    "args": {
                        "bindings": [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]
                    },
                },
                {"call": "plot_pipeline", "args": {"change_request": note}},
                {"text": "Please confirm the new bindings; your title is kept."},
                # The bare `.create_plot()` after the confirmation.
                {"call": "plot_pipeline", "args": {}},
                {"text": "Here is your plot."},
            ],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        }
        fake = swap_models("gemini", script)
        sid = await open_session(client)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "swap the axes"})
        plot = next(data for name, data in parse_sse(response.text) if name == "plot")
        assert (plot["status"], plot["reason"]) == ("not_ready", "data_unconfirmed")
        assert (await _session_state(client, sid))[PENDING_REQUEST] == note

        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200
        events = await create_plot(client, sid)

        assert next(data for name, data in events if name == "plot")["status"] == "ok"
        assert isinstance(fake, ScriptedLlm)
        adapter = [r for r in fake.requests if (r.config.labels or {})["agent_kind"] == "adapter"]
        text = "".join(part.text or "" for part in adapter[0].contents[-1].parts or [])
        assert note in text
        assert (await _session_state(client, sid))[PENDING_REQUEST] is None
