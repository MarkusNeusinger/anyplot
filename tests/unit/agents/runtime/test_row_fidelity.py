"""The plot draws every row: the repeated-key warning on the binding answers and in the session block, the
server's line for rows without a value to draw in the shipped plot's "what changed" (`data/fidelity.py`), and the
server's data step that combines a repeated key before the run draws it (`repeated_keys.py`).

Owner decisions of 2026-11-08, after the persona round of 2026-11-06, where a line chart of 27 measurements over 9
lengths came out as 9 averaged points and nobody said so, and of 2026-11-09, after the plot code still averaged such
rows itself with the prompt asking it to draw every one. The sessions are opened through the real `/v1` routes;
every table is invented.
"""

import json
import re
from collections.abc import AsyncIterator, Iterator
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from agents.anyplot import pipeline
from agents.anyplot.agent import REPEATED_KEY_LINE, session_context
from agents.anyplot.data.fidelity import COMBINED_HEAD, LEFT_OUT_HEAD, function_is_open
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.plugins.ledger import RequestLedger
from agents.anyplot.plugins.tool_safety import fence_pipeline_notes
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.repeated_keys import choice_is_open, combine_repeated_key
from agents.anyplot.schemas import Binding, PipelineArgs
from agents.anyplot.services import Services
from agents.anyplot.session_state import CONFIRMED, DATASET_ID, PENDING_BASE, PENDING_REQUEST, confirmation_fingerprint
from agents.anyplot.tools.session import prepare_data, set_bindings
from agents.main import Runtime, app, get_runtime

from .conftest import CASES
from .fakes import ROOT_REPLY, SCATTER_PLAN, default_script
from .test_from_version import context_for, write_back
from .test_paste_conversions import SID, open_spec, paste, pasted
from .test_service_flow import HEADERS, USER, create_plot, permissive_queue, say


LENGTHS = "Length,Reading\n" + "".join(f"{10 + 5 * (i % 9)},{20 + (i * 7) % 13}.5\n" for i in range(27))
"""27 invented readings over 9 lengths, three per length."""
WARNING = (
    "x: column 'Length' holds 9 values in 27 rows; the plot draws one value per x, so rows with the same x need an "
    "aggregate first"
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


def fenced_lines(block: str, tag: str) -> list[list[str]]:
    return [match.splitlines() for match in re.findall(rf"<{tag}>\n(.*?)\n</{tag}>", block, re.DOTALL)]


class TestRepeatedKey:
    async def test_the_session_block_names_the_key_and_its_counts(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "line-styled")
        await paste(client, sid, LENGTHS)
        context = await context_for(client, sid, "inv-rk-1")

        block = await session_context(context)  # type: ignore[arg-type]

        line = REPEATED_KEY_LINE.format(fact="x has 9 values in 27 rows", per="x")
        lines = block.splitlines()
        assert lines[lines.index(line) + 1 : lines.index(line) + 4] == ["<user_data>", WARNING, "</user_data>"]
        assert "Length" not in line  # the column names stay inside the fence below it
        # A fact of the rows, not a column that misfits its role: no "Binding warnings" heading claims otherwise.
        assert not any(row.startswith("- Binding warnings:") for row in lines)

    async def test_the_bindings_route_and_set_bindings_answer_the_warning(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "line-styled")
        await paste(client, sid, LENGTHS)

        response = await client.put(
            f"/v1/sessions/{sid}/bindings",
            headers=HEADERS,
            json=[{"role": "x", "column": "Length"}, {"role": "y_1", "column": "Reading"}],
        )
        assert response.status_code == 200, response.text
        assert (response.json()["complete"], response.json()["warnings"]) == (True, [WARNING])

        context = await context_for(client, sid, "inv-rk-2")
        result = await set_bindings(
            [{"role": "x", "column": "Length"}, {"role": "y_1", "column": "Reading"}],
            context,  # type: ignore[arg-type]
        )
        assert result["status"] == "ok" and result["complete"] is True
        assert [WARNING] in [json.loads(lines[0]) for lines in fenced_lines(result["warnings"], "user_data")]

    async def test_unique_keys_add_no_line(self, client: httpx.AsyncClient) -> None:
        sid = await open_spec(client, "bar-basic")
        await paste(client, sid, "Fruit,Sold\nApples,12\nPears,7\nPlums,9\nCherries,15\n")
        context = await context_for(client, sid, "inv-rk-3")

        block = await session_context(context)  # type: ignore[arg-type]

        assert "- Repeated key:" not in block and "Binding warnings" not in block


class TestRowsWithoutAValue:
    async def test_the_shipped_plot_counts_the_rows_it_cannot_draw_first_and_stays_ok(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        """Two invented students without an exam score: the run's "what changed" says so with the count, first, and
        the status stays the render's (the server's notes never become residual ones)."""
        swap_models("gemini", default_script())
        header, *rows = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text().splitlines()
        for index in (3, 7):  # `Student,Study Hours,Exam Score`: the score of two rows left empty
            rows[index] = rows[index].rsplit(",", 1)[0] + ","
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, "\n".join([header, *rows]) + "\n")
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200, confirmed.text

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["residual_defects"] == []
        assert plot["changes"] == [f"{LEFT_OUT_HEAD}2 rows without y ('Exam Score')", *SCATTER_PLAN["changes"]]

    async def test_complete_rows_add_no_line(self, client: httpx.AsyncClient, swap_models) -> None:
        swap_models("gemini", default_script())
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, (CASES / "scatter-basic-matplotlib" / "data.csv").read_text())
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200, confirmed.text

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["changes"] == SCATTER_PLAN["changes"]


HOURS = "Student,Study Hours,Exam Score\n" + "".join(f"S{i:02d},{2 + 2 * (i % 4)},{50 + 3 * i}\n" for i in range(12))
"""12 invented students over 4 study hours, three per hour; `Student` names each one and is bound to nothing."""
COMBINED = f"{COMBINED_HEAD}2: averaged 'Exam Score' over 12 rows into 4, one per 'Study Hours'"
SUMMED = f"{COMBINED_HEAD}2: summed 'Exam Score' over 12 rows into 4, one per 'Study Hours'"
LINE_BINDINGS = [{"role": "x", "column": "Study Hours"}, {"role": "y", "column": "Exam Score"}]
QUESTION = "The scores repeat per hour: sum or average them?"


def asked_then_chosen(how: str = "mean", **kwargs: Any) -> dict[str, list[Any]]:
    """The root's two turns on a key that repeats: the button's call is stopped for the user's choice and the root
    asks; the typed answer's call names the function and plots."""
    script = default_script(**kwargs)
    script["root"] = [
        {"call": "plot_pipeline", "args": {}},
        {"text": QUESTION},
        {"call": "plot_pipeline", "args": {"combine": how}},
        {"text": ROOT_REPLY},
    ]
    return script


async def plot_with_choice(client: httpx.AsyncClient, sid: str, answer: str = "average them") -> list[Any]:
    """The plot button, which makes no plot while the choice is open, then the turn of the typed answer."""
    asked = await create_plot(client, sid)
    assert [data["text"] for name, data in asked if name == "message"] == [QUESTION]
    assert not any(name == "plot" for name, _ in asked)  # a stop before the run shows the page no plot card
    return await say(client, sid, answer)


async def open_line_on_scatter_code(client: httpx.AsyncClient) -> str:
    """A `line-basic` session (x keys the marks) whose catalogue code is the scatter file `SCATTER_PLAN` adapts, so the
    scripted adapter ships a plot from whatever table the run gets."""
    snapshot = snapshot_from_repo("line-basic", "matplotlib").model_copy(
        update={"code": snapshot_from_repo("scatter-basic", "matplotlib").code}
    )
    body = {"user": USER, "spec_id": "line-basic", "library": "matplotlib", "locale": "en"}
    response = await client.post("/v1/sessions", headers=HEADERS, json={**body, "snapshot": snapshot.model_dump()})
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


async def bind_and_confirm(client: httpx.AsyncClient, sid: str, bindings: list[dict[str, str]]) -> None:
    bound = await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=bindings)
    assert bound.status_code == 200, bound.text
    confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
    assert confirmed.status_code == 200, confirmed.text


async def table_rows(client: httpx.AsyncClient, sid: str) -> list[str]:
    response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.text.strip().splitlines()[1:]


class TestCombinedKey:
    """Owner decision of 2026-11-09: a repeated key that reaches the plot run is combined by the server first, as a
    data step with a number, a change line and an undo, and the plot draws every row of that version."""

    async def test_the_run_combines_the_key_announces_it_and_draws_the_new_version(
        self, client: httpx.AsyncClient, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", asked_then_chosen("mean"))
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        events = await plot_with_choice(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["residual_defects"] == []
        assert plot["changes"] == [COMBINED, *SCATTER_PLAN["changes"]]
        # The plot drew the four combined rows, one per hour: the mean of each hour's three scores.
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert drawn[0] == "Study Hours,Exam Score" and len(drawn) == 1 + 4
        assert drawn[1:] == ["2,62", "4,65", "6,68", "8,71"]
        # The step is a data version of its own: numbered, on the card with its change line, still confirmed.
        done = next(data for name, data in events if name == "done")
        assert done["dataset"]["version"] == 2 and done["data_confirmed"] is True
        assert done["dataset"]["changes"] == ["averaged Exam Score by Study Hours: 4 rows, 1 other column dropped"]
        assert await table_rows(client, sid) == drawn[1:]

    async def test_a_run_that_ships_nothing_announces_the_step_and_keeps_the_kept_note(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """The data changed all the same, so the failed result names the step; the new version drops a kept note,
        and the run, which took it before the step, writes it back for the next one."""
        unusable = {"edits": [{"find": "not in the code", "replace": "df = load_user_data()"}], "changes": ["x"]}
        swap_models("gemini", asked_then_chosen("mean", plans=[unusable] * 6))
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        await runtime.write_state(await runtime.session(USER, sid), {PENDING_REQUEST: "make the line thicker"})

        events = await plot_with_choice(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "failed" and plot["changes"] == [COMBINED]
        assert next(data for name, data in events if name == "done")["dataset"]["version"] == 2
        assert (await runtime.session(USER, sid)).state[PENDING_REQUEST] == "make the line thicker"

    async def test_the_button_alone_makes_no_plot_and_no_data_version_while_the_choice_is_open(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend, services: Services
    ) -> None:
        """A line of scores per hour may want the sum or the mean, and the plot type cannot tell: the call is stopped
        before the run, the root asks, and nothing is combined, rendered or stored until the user says which. The
        button names no function, so a choice the root passes with it is dropped as the root's own."""
        script = asked_then_chosen("mean")
        script["root"][0] = {"call": "plot_pipeline", "args": {"combine": "mean"}}
        fake = swap_models("gemini", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        events = await create_plot(client, sid)

        assert [data["text"] for name, data in events if name == "message"] == [QUESTION]
        assert not any(name == "plot" for name, _ in events) and backend.jobs == []
        assert "dataset" not in next(data for name, data in events if name == "done")
        assert await table_rows(client, sid) == HOURS.strip().splitlines()[1:]
        answer = next(
            part.function_response.response
            for content in fake.requests[-1].contents
            for part in content.parts or []
            if part.function_response is not None and part.function_response.name == "plot_pipeline"
        )
        assert (answer["status"], answer["code"], answer["reason"]) == ("error", "combine_choice", "combine_choice")
        assert "whether to sum or to average them" in answer["message"]
        assert services.usage.user_runs(USER) == 0  # a call stopped before the run uses up none of the day's runs

    async def test_the_root_cannot_answer_its_own_question_in_the_same_turn(
        self, client: httpx.AsyncClient, swap_models, backend: FakeBackend
    ) -> None:
        """A call stopped for the choice is not retried with one: the turn that was told to ask makes no plot,
        whatever function its second call names. The answer comes with the user's next message."""
        script = default_script()
        script["root"] = [
            {"call": "plot_pipeline", "args": {}},
            {"call": "plot_pipeline", "args": {"combine": "mean"}},
            {"text": QUESTION},
        ]
        fake = swap_models("gemini", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        events = await say(client, sid, "plot it")

        assert not any(name == "plot" for name, _ in events) and backend.jobs == []
        codes = [
            part.function_response.response["code"]
            for content in fake.requests[-1].contents
            for part in content.parts or []
            if part.function_response is not None and part.function_response.name == "plot_pipeline"
        ]
        assert codes == ["combine_choice", "combine_choice"]
        assert await table_rows(client, sid) == HOURS.strip().splitlines()[1:]

    async def test_the_users_sum_is_the_function_of_the_step(
        self, client: httpx.AsyncClient, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", asked_then_chosen("sum"))
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        events = await plot_with_choice(client, sid, "sum them")

        plot = next(data for name, data in events if name == "plot")
        assert plot["status"] == "ok" and plot["changes"] == [SUMMED, *SCATTER_PLAN["changes"]]
        drawn = backend.jobs[-1].data_csv.strip().splitlines()
        assert drawn[1:] == ["2,186", "4,195", "6,204", "8,213"]  # three scores per hour, added up
        done = next(data for name, data in events if name == "done")
        assert done["dataset"]["changes"] == ["summed Exam Score by Study Hours: 4 rows, 1 other column dropped"]

    async def test_a_request_sent_with_the_stopped_call_is_kept_for_the_plot(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models
    ) -> None:
        """A typed wish whose plot waits for the choice is kept like one that waits for the user's check."""
        script = asked_then_chosen("sum")
        script["root"][0] = {"call": "plot_pipeline", "args": {"change_request": "log scale on y"}}
        fake = swap_models("gemini", script)
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        await say(client, sid, "plot it with a log scale on y")

        assert (await runtime.session(USER, sid)).state[PENDING_REQUEST] == "log scale on y"
        answer = next(
            part.function_response.response
            for content in fake.requests[-1].contents
            for part in content.parts or []
            if part.function_response is not None and part.function_response.name == "plot_pipeline"
        )
        assert answer["request_kept"] is True

        events = await say(client, sid, "sum them")

        assert next(data for name, data in events if name == "plot")["status"] == "ok"
        assert (await runtime.session(USER, sid)).state.get(PENDING_REQUEST) is None  # the plot took the wish

    async def test_undo_brings_the_raw_rows_back(self, client: httpx.AsyncClient, swap_models) -> None:
        swap_models("gemini", asked_then_chosen("mean"))
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        await plot_with_choice(client, sid)

        undone = await client.post(f"/v1/sessions/{sid}/dataset/undo", headers=HEADERS)

        assert undone.status_code == 200, undone.text
        assert undone.json()["version"] == 1
        assert await table_rows(client, sid) == HOURS.strip().splitlines()[1:]

    async def test_a_scatter_with_repeats_is_drawn_as_it_is(
        self, client: httpx.AsyncClient, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", default_script())
        sid = await open_spec(client, "scatter-basic")
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["changes"] == SCATTER_PLAN["changes"]
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 12
        assert "dataset" not in next(data for name, data in events if name == "done")

    async def test_an_aggregate_the_user_made_first_is_not_made_again(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, backend: FakeBackend
    ) -> None:
        swap_models("gemini", default_script())
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        context = await context_for(client, sid, "inv-ck-1")
        operation = {"op": "aggregate", "by": ["Study Hours"], "column": "Exam Score", "how": "mean"}
        made = await prepare_data([operation], context)  # type: ignore[arg-type]
        assert made["status"] == "ok" and made["version"] == 2
        await write_back(runtime, sid, context)
        confirmed = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirmed.status_code == 200, confirmed.text

        events = await create_plot(client, sid)

        plot = next(data for name, data in events if name == "plot")
        assert plot["changes"] == SCATTER_PLAN["changes"]
        assert len(backend.jobs[-1].data_csv.strip().splitlines()) == 1 + 4
        assert "dataset" not in next(data for name, data in events if name == "done")

    async def test_a_second_run_on_the_combined_version_combines_nothing(
        self, client: httpx.AsyncClient, swap_models
    ) -> None:
        script = asked_then_chosen("mean")
        swap_models("gemini", {**script, "root": [*script["root"], *default_script()["root"]]})
        sid = await open_line_on_scatter_code(client)
        await paste(client, sid, HOURS)
        await bind_and_confirm(client, sid, LINE_BINDINGS)
        await plot_with_choice(client, sid)

        again = await create_plot(client, sid)  # no key repeats any more: the button plots, and nothing is asked

        plot = next(data for name, data in again if name == "plot")
        assert not any(change.startswith(COMBINED_HEAD) for change in plot["changes"])
        assert "dataset" not in next(data for name, data in again if name == "done")
        assert len(await table_rows(client, sid)) == 4


class TestCombineRepeatedKey:
    """`combine_repeated_key` on its own: the store and the session view, no run."""

    @staticmethod
    def confirmed(spec: str, bindings: list[dict[str, str]], text: str = HOURS) -> tuple[Any, Any]:
        store, view = pasted(text, spec)
        bound = [Binding(**item) for item in bindings]
        return store, replace(view, bindings=bound, confirmed=confirmation_fingerprint(view.dataset_id, bound))

    def test_the_aggregate_is_the_next_version_and_the_confirmation_moves_to_it(self) -> None:
        store, view = self.confirmed("line-basic", LINE_BINDINGS)

        combined = combine_repeated_key(store, SID, view, store.get(view.dataset_id, SID))

        assert combined is not None and combined.line == COMBINED
        assert (combined.version.version, combined.version.stored.profile.rows) == (2, 4)
        assert combined.version.bindings == view.bindings
        delta = combined.delta()
        assert delta[DATASET_ID] == combined.version.dataset_id
        assert delta[CONFIRMED] == confirmation_fingerprint(combined.version.dataset_id, combined.version.bindings)

    def test_unconfirmed_data_and_a_box_plot_combine_nothing(self) -> None:
        store, view = pasted(HOURS, "line-basic")
        bound = [Binding(**item) for item in LINE_BINDINGS]
        unconfirmed = replace(view, bindings=bound)
        assert combine_repeated_key(store, SID, unconfirmed, store.get(view.dataset_id, SID)) is None

        weights = "Line,Weight\n" + "".join(f"{'ABC'[i % 3]},{500 + i}\n" for i in range(12))
        bindings = [{"role": "category", "column": "Line"}, {"role": "value", "column": "Weight"}]
        store, box = self.confirmed("box-basic", bindings, weights)
        assert box.data_confirmed  # the repeats are the box's: confirmed data, complete bindings, nothing combined
        assert combine_repeated_key(store, SID, box, store.get(box.dataset_id, SID)) is None
        assert not choice_is_open(box, store.get(box.dataset_id, SID))  # nothing to combine, nothing to ask

    def test_the_users_function_replaces_the_plot_types(self) -> None:
        store, view = self.confirmed("line-basic", LINE_BINDINGS)

        summed = combine_repeated_key(store, SID, view, store.get(view.dataset_id, SID), "sum")

        assert summed is not None and (summed.aggregate.how, summed.line) == ("sum", SUMMED)

    def test_the_choice_is_open_where_the_plot_type_does_not_say_that_rows_add_up(self) -> None:
        """A line or a plain bar draws a measurement per key, an amount or a rate: the user says which. The slices of
        a pie add up by what a pie is, so nothing is asked there. Unconfirmed data is never combined, so never asked
        about either."""
        store, line = self.confirmed("line-basic", LINE_BINDINGS)
        assert function_is_open("line-basic") and function_is_open("bar-basic")
        assert choice_is_open(line, store.get(line.dataset_id, SID))
        assert not choice_is_open(replace(line, confirmed=None), store.get(line.dataset_id, SID))

        shares = "Party,Votes\n" + "".join(f"{'ABC'[i % 3]},{100 + i}\n" for i in range(9))
        bindings = [{"role": "category", "column": "Party"}, {"role": "value", "column": "Votes"}]
        store, pie = self.confirmed("pie-basic", bindings, shares)
        assert not function_is_open("pie-basic")
        assert not choice_is_open(pie, store.get(pie.dataset_id, SID))
        # The slices add up whatever a call names: a function passed for a pie is not taken.
        combined = combine_repeated_key(store, SID, pie, store.get(pie.dataset_id, SID), "mean")
        assert combined is not None and combined.aggregate.how == "sum"

    def test_the_answer_goes_on_the_plot_its_stopped_call_meant(self) -> None:
        """The stopped call was a change of the plot the library has, kept as that: the call that brings the user's
        function continues it on that plot, where a catalogue base would lose every edit the plot carries. A first
        plot's kept note, and a call without a function, keep the base they name."""
        answer = PipelineArgs(combine="sum")
        kept_change = {PENDING_REQUEST: "thicker line", PENDING_BASE: "previous"}
        first_plot_note = {PENDING_REQUEST: "thicker line"}

        assert pipeline.continue_stopped_change(kept_change, answer).base == "previous"
        assert pipeline.continue_stopped_change(first_plot_note, answer).base == "catalogue"
        assert pipeline.continue_stopped_change(kept_change, PipelineArgs()).base == "catalogue"
        assert pipeline.continue_stopped_change({}, answer) == answer


def test_a_run_re_run_on_resume_announces_the_step_of_its_first_run() -> None:
    """ADK re-runs the pipeline node on resume (`rerun_on_resume`): the key is combined already, so the step is found
    in the invocation's ledger, announced again, and never made a second time."""
    store, view = pasted(HOURS, "line-basic")
    dataset = store.get(view.dataset_id, SID)
    ledger = RequestLedger()
    ledger.data_step = (view.dataset_id, COMBINED)
    services = SimpleNamespace(datasets=store)
    ctx = SimpleNamespace(state={}, session=SimpleNamespace(id=SID))

    drawn = pipeline._combine_repeated_key(ctx, services, view, dataset, ledger)  # type: ignore[arg-type]

    assert drawn == (view, dataset, COMBINED) and ctx.state == {}


class TestTheRootReadsTheStep:
    def test_a_combined_run_changed_the_data_shipped_or_not(self) -> None:
        shipped = {"status": "ok", "attempts": 1, "changes": [COMBINED], "combined": True}
        failed = {"status": "failed", "reason": "render", "attempts": 2, "changes": [COMBINED], "combined": True}
        plain = {"status": "ok", "attempts": 1, "changes": []}

        assert fence_pipeline_notes(shipped)["data_changed"] is True
        assert fence_pipeline_notes(failed)["data_changed"] is True
        assert fence_pipeline_notes(plain)["data_changed"] is False
        assert "combined" not in fence_pipeline_notes(shipped) and "data_changed" not in fence_pipeline_notes(
            {"status": "failed", "reason": "render", "attempts": 2}
        )
