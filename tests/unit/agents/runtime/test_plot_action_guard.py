"""A plot button's turn plots what the click confirmed, and a column the user wants plotted is bound in the data turn.

Persona tests of 2026-11-06: twice the user pressed the plot button right after a data change and got "not
confirmed yet" instead of a plot. The root had called `set_bindings` in the `create_plot` turn to add the new
derived column, and the click's confirmation is a fingerprint of the data and the bindings, so the run stopped on
`data_unconfirmed`. ToolSafety now lets a plot button's turn only read and plot (`RequestLedger.plot_action`,
`PLOT_ACTION_TOOLS`), and root.md has the data turn bind the column. A third misfire answered the note sent with a
re-paste with the rule for a table typed into the message; the session block's line now says where the table is.
"""

from collections.abc import AsyncIterator, Iterator
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import PASTED_LINE
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.pipeline import load_inputs
from agents.anyplot.plugins.ledger import CURRENT_LEDGER, RequestLedger
from agents.anyplot.plugins.tool_safety import CAP_MESSAGE, PLOT_ACTION_REFUSAL, PLOT_ACTION_TOOLS, ToolSafetyPlugin
from agents.anyplot.policy import root_instruction
from agents.anyplot.services import Services, get_services
from agents.anyplot.session_state import BINDINGS, confirm_delta, read_session
from agents.anyplot.tools.session import ROOT_TOOL_NAMES, prepare_data, set_bindings
from agents.main import ACTION_MESSAGES, PLOT_ACTIONS, Runtime, app, get_runtime

from .conftest import CASES
from .fakes import SCATTER_PLAN, VERDICT_OK
from .test_service_flow import (
    HEADERS,
    USER,
    _session_state,
    create_plot,
    open_session,
    parse_sse,
    permissive_queue,
    request_text,
    requests_of,
    tool_responses,
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


WRITES: dict[str, dict[str, Any]] = {
    "set_bindings": {"bindings": [{"role": "x", "column": "Study Hours"}, {"role": "y", "column": "Exam Score"}]},
    "prepare_data": {"operations": [{"op": "rename", "column": "Exam Score", "name": "Score"}]},
    "generate_data": {
        "variables": [{"name": "x", "start": "0", "stop": "1"}],
        "series": [{"name": "y", "expression": "x**2"}],
    },
    "run_data_code": {"code": "import pandas as pd\ndf = pd.DataFrame({'x': [1, 2]})", "source_language": "python"},
    "set_language": {"language": "de", "applies_to": "plot"},
    "keep_plot_request": {"change_request": "Title 'Scores'"},
    "forget": {"entry_id": "m1"},
    "switch_plot": {"library": "seaborn"},
}
"""A valid call of every root tool that stores a change, so a refusal is the guard's and never the arguments'."""
READS: dict[str, dict[str, Any]] = {
    "get_dataset_profile": {},
    "get_spec_brief": {},
    "get_current_code": {"version": 0},
    "query_data": {"operations": []},
    "plot_pipeline": {},
}


def plot_turn(plot_action: bool) -> Iterator[RequestLedger]:
    ledger = RequestLedger(request_id="req-1", user_id="adm_1", session_id="s1", kind="action", plot_action=plot_action)
    token = CURRENT_LEDGER.set(ledger)
    yield ledger
    CURRENT_LEDGER.reset(token)


@pytest.fixture
def action_ledger() -> Iterator[RequestLedger]:
    yield from plot_turn(True)


@pytest.fixture
def text_ledger() -> Iterator[RequestLedger]:
    yield from plot_turn(False)


async def before(name: str, args: dict[str, Any], agent: str = "anyplot") -> dict[str, Any] | None:
    return await ToolSafetyPlugin().before_tool_callback(
        tool=SimpleNamespace(name=name),  # type: ignore[arg-type]
        tool_args=args,
        tool_context=SimpleNamespace(invocation_id="inv-1", agent_name=agent),  # type: ignore[arg-type]
    )


class TestTheGuard:
    def test_every_root_tool_is_either_a_read_or_a_write(self) -> None:
        """A tool added later must take a side here: unlisted, a plot button's turn refuses it."""
        assert set(READS) == PLOT_ACTION_TOOLS
        assert set(READS) | set(WRITES) == ROOT_TOOL_NAMES

    @pytest.mark.parametrize("name", sorted(WRITES))
    async def test_a_plot_action_refuses_every_tool_that_stores_a_change(
        self, name: str, action_ledger: RequestLedger
    ) -> None:
        assert ToolSafetyPlugin.check(name, WRITES[name], "anyplot") is None  # a valid call in any other turn
        assert await before(name, WRITES[name]) == {"status": "error", "code": PLOT_ACTION_REFUSAL}
        assert action_ledger.tools == []  # a refused call is no tool the turn used

    @pytest.mark.parametrize("name", sorted(WRITES))
    async def test_a_text_turn_keeps_every_tool(self, name: str, text_ledger: RequestLedger) -> None:
        assert await before(name, WRITES[name]) is None

    async def test_a_plot_action_reads_and_plots_once(self, action_ledger: RequestLedger) -> None:
        for name, args in READS.items():
            assert await before(name, args) is None, name
        assert await before("plot_pipeline", {}) == {
            "status": "error",
            "code": "one_pipeline_per_turn",
            "message": CAP_MESSAGE.format(tool="plot_pipeline", calls=1),
        }

    async def test_the_guard_comes_before_the_arguments_and_after_the_allowlist(
        self, action_ledger: RequestLedger
    ) -> None:
        """A fixed call would be refused all the same, so the refusal names the guard, without validation lines."""
        broken = {"operations": [{"op": "rename", "column": "Exam Score"}]}
        assert await before("prepare_data", broken) == {"status": "error", "code": PLOT_ACTION_REFUSAL}
        assert await before("set_bindings", {"bindings": "x"}) == {"status": "error", "code": PLOT_ACTION_REFUSAL}
        assert await before("google_search", {}) == {"status": "error", "code": "tool_not_allowed"}
        assert await before("set_bindings", {}, agent="adapter_matplotlib") == {
            "status": "error",
            "code": "tool_not_allowed",
        }

    def test_the_plot_buttons_are_the_create_and_the_carry(self) -> None:
        assert PLOT_ACTIONS == {"create_plot", "carry_plot"} and PLOT_ACTIONS < set(ACTION_MESSAGES)

    def test_the_prompt_names_the_code_and_every_refused_tool(self) -> None:
        policy = root_instruction()
        assert f"`{PLOT_ACTION_REFUSAL}`" in policy
        rule = next(line for line in policy.splitlines() if PLOT_ACTION_REFUSAL in line)
        for name in WRITES:
            assert f"`{name}`" in rule, name

    def test_the_prompt_binds_only_a_role_the_turns_own_change_left_open(self) -> None:
        """Prep eval of 2026-11-07: with the binding rule unscoped, the root filled a role that was open before the turn
        with a `row_number` on a plain "drop the Total row" (7 of 8 case runs from #12593 on, 0 of 9 before it)."""
        policy = root_instruction()
        rule = next(line for line in policy.splitlines() if "you can bind yourself" in line)
        later = next(line for line in policy.splitlines() if "In a later turn a line matters only" in line)

        assert "A required role that lost its bound column in this turn's data change" in rule
        assert "A required role that was already open before the turn is not yours to fill" in rule
        assert '"Conversions for open roles"' in rule
        assert "never add a line's conversion or a `row_number` to the operations of another change" in later
        assert "also when an `aggregate` of this turn rebuilds the table" in later


DERIVE = {"op": "derive", "name": "Score per Hour", "how": "ratio", "columns": ["Exam Score", "Study Hours"]}
REBOUND = [{"role": "x", "column": "Study Hours"}, {"role": "y", "column": "Score per Hour"}]
ORIGINAL = [{"role": "x", "column": "Study Hours"}, {"role": "y", "column": "Exam Score"}]


async def test_a_click_after_a_derived_column_data_turn_plots(client: httpx.AsyncClient, swap_models) -> None:
    """The football case: a new column to plot in place of the old one. The data turn makes and binds it; the click
    confirms what the panel shows, and the root's attempt to bind again in the click's turn is refused, not fatal."""
    script = {
        "root": [
            # The data turn: make the column, read the bindings in force, bind it in place of the one it replaces.
            {"call": "prepare_data", "args": {"operations": [DERIVE]}},
            {"call": "get_dataset_profile", "args": {}},
            {"call": "set_bindings", "args": {"bindings": REBOUND}},
            {"text": "I added Score per Hour (Exam Score / Study Hours) and bound it to y."},
            # The click's turn: a change the root tries is refused, the plot runs on what was confirmed.
            {"call": "set_bindings", "args": {"bindings": ORIGINAL}},
            {"call": "plot_pipeline", "args": {}},
            {"text": "Your plot is ready: Score per Hour against Study Hours."},
        ],
        "adapter": [{"json": SCATTER_PLAN}],
        "reviewer": [{"json": VERDICT_OK}],
    }
    fake = swap_models("gemini", script)
    sid = await open_session(client)  # confirmed by the helper

    data_turn = await client.post(
        f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "add score per hour and plot that instead"}
    )
    done = parse_sse(data_turn.text)[-1][1]
    assert done["bindings"] == REBOUND and done["data_confirmed"] is False
    assert done["dataset"]["version"] == 2

    # The click: `.create_plot()` ("plot the new data") confirms the data and the bindings as shown, then plots.
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
    events = await create_plot(client, sid)

    plot = next(data for name, data in events if name == "plot")
    assert plot["status"] == "ok", plot
    done = next(data for name, data in events if name == "done")
    assert done["data_confirmed"] is True and done["bindings"] == REBOUND
    assert tool_responses(fake, "set_bindings")[-1] == {"status": "error", "code": PLOT_ACTION_REFUSAL}
    state = await _session_state(client, sid)
    assert state[BINDINGS] == REBOUND


async def test_an_extra_series_bound_in_the_data_turn_passes_the_gate_after_the_click(
    client: httpx.AsyncClient,
) -> None:
    """The ratio case: a derived column added as one more member of a number family (`y3`) in the data turn. Adding
    a series is no narrowing, so in the click's turn it voided the confirmation; in the data turn it is confirmed."""
    response = await client.post(
        "/v1/sessions",
        headers=HEADERS,
        json={
            "user": USER,
            "spec_id": "line-multi",
            "library": "matplotlib",
            "locale": "en",
            "snapshot": snapshot_from_repo("line-multi", "matplotlib").model_dump(),
        },
    )
    sid = response.json()["session_id"]
    table = "year,sales,costs\n2021,10,4\n2022,12,5\n2023,15,5\n2024,14,7\n"
    stored = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": table})
    assert stored.json()["bindings"] == [
        {"role": "x", "column": "year"},
        {"role": "y1", "column": "sales"},
        {"role": "y2", "column": "costs"},
    ]
    context = SimpleNamespace(state=await _session_state(client, sid), session=SimpleNamespace(id=sid))
    context.invocation_id = "inv-ratio"
    ratio = {"op": "derive", "name": "margin", "how": "ratio", "columns": ["costs", "sales"]}

    made = await prepare_data([ratio], context)  # type: ignore[arg-type]
    assert made["status"] == "ok", made
    bound = await set_bindings(
        [*stored.json()["bindings"], {"role": "y3", "column": "margin"}],
        context,  # type: ignore[arg-type]
    )
    assert bound["status"] == "ok" and bound["complete"] is True and bound["data_confirmed"] is False

    view = read_session(context.state)
    assert view is not None
    context.state.update(confirm_delta(view))  # the click confirms the data and the bindings as the panel shows them
    run = SimpleNamespace(state=context.state, session=SimpleNamespace(id=sid))
    after, dataset, reason = load_inputs(run, get_services())  # type: ignore[arg-type]
    assert reason is None and dataset is not None
    assert after is not None and ("y3", "margin") in {(binding.role, binding.column) for binding in after.bindings}


async def test_data_changed_and_never_confirmed_still_asks_for_the_confirmation(
    client: httpx.AsyncClient, swap_models
) -> None:
    """The guard confirms nothing: a plot action on data the user changed and never confirmed stops as before."""
    script = {
        "root": [
            {"call": "prepare_data", "args": {"operations": [DERIVE]}},
            {"text": "I added Score per Hour."},
            {"call": "plot_pipeline", "args": {}},
            {"text": "The new data is not confirmed yet."},
        ]
    }
    swap_models("gemini", script)
    sid = await open_session(client)

    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "add score per hour"})
    events = await create_plot(client, sid)  # a stale page: no confirmation before the action

    plot = next(data for name, data in events if name == "plot")
    assert (plot["status"], plot["reason"]) == ("not_ready", "data_unconfirmed")


@pytest.mark.parametrize("action", ["create_plot", "carry_plot"])
async def test_both_plot_buttons_refuse_a_change_and_still_plot(
    client: httpx.AsyncClient, swap_models, action: str
) -> None:
    script = {
        "root": [
            {"call": "prepare_data", "args": {"operations": [DERIVE]}},
            {"call": "plot_pipeline", "args": {}},
            {"text": "Your plot is ready."},
        ],
        "adapter": [{"json": SCATTER_PLAN}],
        "reviewer": [{"json": VERDICT_OK}],
    }
    fake = swap_models("gemini", script)
    sid = await open_session(client)
    before_turn = read_session(await _session_state(client, sid))

    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": action})
    events = parse_sse(response.text)

    assert next(data for name, data in events if name == "plot")["status"] == "ok"
    refused = tool_responses(fake, "prepare_data")  # every root request after the call carries its answer
    assert refused and all(answer == {"status": "error", "code": PLOT_ACTION_REFUSAL} for answer in refused)
    after = read_session(await _session_state(client, sid))
    assert before_turn is not None and after is not None
    assert (after.dataset_id, after.dataset_version) == (before_turn.dataset_id, before_turn.dataset_version)
    assert "dataset" not in next(data for name, data in events if name == "done")


async def test_the_summary_action_keeps_its_data_tools(client: httpx.AsyncClient, swap_models) -> None:
    """Only the plot buttons are guarded: the summary action may still act on the notes with `prepare_data`."""
    script = {"root": [{"call": "prepare_data", "args": {"operations": [DERIVE]}}, {"text": "24 rows."}]}
    fake = swap_models("gemini", script)
    sid = await open_session(client)

    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "summarize_data"})

    assert tool_responses(fake, "prepare_data")[0]["status"] == "ok"
    assert parse_sse(response.text)[-1][1]["dataset"]["version"] == 2


async def test_the_note_sent_with_a_re_paste_reads_as_its_attachment(client: httpx.AsyncClient, swap_models) -> None:
    """The session block says the table came in as the attachment, so the rule for typed tables is not this turn's."""
    fake = swap_models("gemini", {"root": [{"text": "24 rows again; x is Study Hours, y is Exam Score."}]})
    sid = await open_session(client)  # data pasted and summarized
    data = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text()
    repasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": data})
    assert repasted.status_code == 200, repasted.text

    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "here is the table again"})

    block = request_text(requests_of(fake, "root")[0])
    assert PASTED_LINE in block
    assert "attachment" in PASTED_LINE and "never data you would have to read from the message" in PASTED_LINE
    policy = root_instruction()
    assert "never say then that you cannot read data from a message" in policy


async def test_a_typed_table_without_an_attachment_keeps_the_message_rule(
    client: httpx.AsyncClient, swap_models
) -> None:
    """A table typed into the box is a message: no line says a table came in, and the policy's rule stands."""
    fake = swap_models("gemini", {"root": [{"text": "I cannot read data from a message; paste the table."}]})
    sid = await open_session(client)  # summarized: the next message is no note sent with a paste

    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "name,city\nAnna,Wien"})

    block = request_text(requests_of(fake, "root")[0])
    assert PASTED_LINE not in block and "- Data: pasted just now" not in block
    assert "You cannot read data from a message: say so in one sentence" in root_instruction()
