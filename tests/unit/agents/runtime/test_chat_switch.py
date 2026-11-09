"""The library switch asked for in the chat, and the fan-out that carries the tuned plot (2026-11-02).

`switch_plot` writes nothing: the turn's `done` carries `switch`, and the page carries it out with the
switch route and the carry run. The fan-out's dataset copy brings the plot memory and a carry along, so
every library of `.plot_all()` starts from its catalogue plot with the user's decisions.
"""

from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.memory import MEMORY, MEMORY_SEQ, memory_delta, plan, read_memory
from agents.anyplot.schemas import PlotResult, RememberItem
from agents.anyplot.services import CodeVersion, Services
from agents.anyplot.switch import CARRY, read_carry
from agents.main import Runtime, app, get_runtime

from .test_dataset_copy import USER as COPY_USER
from .test_dataset_copy import copy, open_session, paste
from .test_service_flow import HEADERS, USER, _session_state, parse_sse, permissive_queue
from .test_service_flow import open_session as open_confirmed


LINE = RememberItem(kind="reference_line", text="horizontal reference line at y = 7")
LABEL = RememberItem(kind="axis_label", target="x", text="x-axis label: 'Zeit (h)'", expected_text="Zeit (h)")


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


async def say(client: httpx.AsyncClient, sid: str, text: str) -> list[tuple[str, dict[str, Any]]]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": text})
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


def root_script(*calls: dict[str, Any]) -> dict[str, list[Any]]:
    return {"root": [*calls, {"text": "Okay."}]}


async def test_a_switch_asked_for_in_the_chat_goes_to_the_page(client: httpx.AsyncClient, swap_models) -> None:
    fake = swap_models("gemini", root_script({"call": "switch_plot", "args": {"library": "seaborn"}}))
    sid = await open_confirmed(client)

    events = await say(client, sid, "make it in seaborn")

    done = events[-1][1]
    assert events[-1][0] == "done" and done["switch"] == {"library": "seaborn", "plot": True}
    state = await _session_state(client, sid)
    assert state["anyplot.library"] == "matplotlib"  # the tool writes nothing; the page switches
    # The root learns which libraries it can switch to from the session block.
    system = str(fake.requests[0].config.system_instruction)
    assert "- Libraries to switch to (switch_plot): seaborn" in system


@pytest.mark.parametrize(
    ("args", "code"),
    [
        ({"library": "matplotlib"}, "same_library"),
        ({"library": "ggplot2"}, "library_unavailable"),  # not served here (`AGENT_LIBRARIES`)
        ({"library": "seaborn", "spec_id": "bar-basic"}, "plot_type_switch_unavailable"),
        ({"library": "Seaborn!"}, "invalid_arguments"),
    ],
)
async def test_a_switch_the_page_could_not_make_is_refused_and_never_sent(
    client: httpx.AsyncClient, swap_models, args: dict[str, Any], code: str
) -> None:
    from agents.anyplot.tools.session import switch_plot

    swap_models("gemini", root_script({"call": "switch_plot", "args": args}))
    sid = await open_confirmed(client)

    events = await say(client, sid, "make it in another library")

    assert "switch" not in events[-1][1]
    runtime = app.dependency_overrides[get_runtime]()
    session = await runtime.session(USER, sid)
    from types import SimpleNamespace

    context = SimpleNamespace(state=session.state, invocation_id="inv-switch", session=SimpleNamespace(id=sid))
    assert await switch_plot(tool_context=context, **args) == {"status": "error", "code": code}


@pytest.mark.parametrize(
    ("first", "second", "code"),
    [
        ({"call": "switch_plot", "args": {"library": "seaborn"}}, {"call": "plot_pipeline", "args": {}}, None),
        ({"call": "plot_pipeline", "args": {}}, {"call": "switch_plot", "args": {"library": "seaborn"}}, None),
    ],
)
async def test_a_turn_has_a_plot_run_or_a_switch_never_both(
    client: httpx.AsyncClient, swap_models, first: dict[str, Any], second: dict[str, Any], code: None
) -> None:
    """ToolSafety refuses the second of the two (Flash review, 2026-11-02): a run before the switch would be thrown
    away, and a switch after a run would plot the same change again in the other library."""
    from .fakes import SCATTER_PLAN, VERDICT_OK

    swap_models(
        "gemini",
        {
            "root": [first, second, {"text": "Okay."}],
            "adapter": [{"json": SCATTER_PLAN}],
            "reviewer": [{"json": VERDICT_OK}],
        },
    )
    sid = await open_confirmed(client)

    events = await say(client, sid, "make it in seaborn")

    plots = [data for name, data in events if name == "plot"]
    switch = events[-1][1].get("switch")
    if first["call"] == "switch_plot":
        assert plots == [] and switch == {"library": "seaborn", "plot": True}  # the run was refused
    else:
        assert len(plots) == 1 and switch is None  # the switch was refused


async def test_a_switch_without_a_session_is_refused() -> None:
    from types import SimpleNamespace

    from agents.anyplot.tools.session import switch_plot

    context = SimpleNamespace(state={}, invocation_id="inv-switch-0", session=SimpleNamespace(id="s0"))
    assert await switch_plot("seaborn", context) == {"status": "error", "code": "session_not_open"}


async def test_the_fanout_copy_brings_the_memory_and_a_carry(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    source = await open_session(client)
    await paste(client, source)
    held = plan([], [LINE, LABEL], seq=1, turn=2)
    await runtime.write_state(await runtime.session(COPY_USER, source), memory_delta(held.entries, 7))
    services.versions.add(
        source,
        CodeVersion(
            number=1,
            working="w",
            run_form="r",
            export="e",
            data_csv="a\n1\n",
            render_id="r1",
            result=PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
            library="matplotlib",
            spec_id="scatter-basic",
            theme="dark",
            theme_asked=True,
            requests=["add a line at 7"],
        ),
    )
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    assert response.json()["carry"] == {
        "decisions": 2,
        "newer": 2,
        "target_has_plot": False,
        "from_plot": True,
        "offer": True,
    }
    state = dict((await runtime.session(COPY_USER, target)).state)
    assert [entry.text for entry in read_memory(state)] == [LINE.text, LABEL.text] and state[MEMORY_SEQ] == 7
    carry = read_carry(state, ("scatter-basic", "seaborn"))
    assert carry is not None and (carry.theme, carry.expected_texts) == ("dark", ["Zeit (h)"])


async def test_the_fanout_copy_of_new_data_carries_only_the_asked_theme_of_the_earlier_plot(
    client: httpx.AsyncClient, runtime: Runtime, services: Services
) -> None:
    """Owner decisions of 2026-11-08 and 2026-11-09: the page's latest plot drew data v1, and the user pasted again
    before `.plot_all()`; the fan-out plots the new data with the memory and the theme the user asked for, never with
    the old plot's texts and requests."""
    source = await open_session(client)
    await paste(client, source)
    held = plan([], [LINE, LABEL], seq=1, turn=2)
    await runtime.write_state(await runtime.session(COPY_USER, source), memory_delta(held.entries, 7))
    services.versions.add(
        source,
        CodeVersion(
            number=1,
            working="w",
            run_form="r",
            export="e",
            data_csv="a\n1\n",
            render_id="r1",
            result=PlotResult(status="ok", attempts=1, artifacts=["plot.py"]),
            library="matplotlib",
            spec_id="scatter-basic",
            theme="dark",
            theme_asked=True,
            requests=["add a line at 7"],
            data_version=1,
        ),
    )
    await paste(client, source)  # data v2, confirmed
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.status_code == 200, response.text
    assert response.json()["carry"]["from_plot"] is True and response.json()["carry"]["decisions"] == 2
    carry = read_carry(dict((await runtime.session(COPY_USER, target)).state), ("scatter-basic", "seaborn"))
    # The asked theme carries (owner decision of 2026-11-09), the old plot's requests do not.
    assert carry is not None and (carry.theme, carry.requests) == ("dark", [])
    assert carry.expected_texts == ["Zeit (h)"]  # the memory still travels


async def test_a_copy_of_an_untuned_session_carries_nothing(client: httpx.AsyncClient, runtime: Runtime) -> None:
    source = await open_session(client)
    await paste(client, source)
    target = await open_session(client, library="seaborn", fanout=True)

    response = await copy(client, target, source)

    assert response.json()["carry"]["offer"] is False
    state = dict((await runtime.session(COPY_USER, target)).state)
    assert state[MEMORY] == [] and state.get(CARRY) is None
