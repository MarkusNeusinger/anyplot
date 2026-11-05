"""A turn read again through `/v1`: the numbered stream, `GET .../turn` after a cut, the pings, and what it refuses.

The browser can lose a turn's stream between itself and the edge proxy while the origin runs the turn to its end
and stores its plot. The page then reads the rest of the turn with `Last-Event-ID` (`agents/turn_log.py`). The
log only records: a client that goes still cancels the run, as before.
"""

import asyncio
import json
from collections.abc import AsyncGenerator, AsyncIterator, Iterator
from typing import Any, cast

import httpx
import pytest

from agents.anyplot.services import Services
from agents.main import MessageBody, Runtime, app, get_runtime, get_turn, post_message
from agents.turn_log import PING

from .fakes import default_script
from .test_run_queue_flow import GatedBackend
from .test_service_flow import HEADERS, USER, headers_for, open_session, permissive_queue


Event = tuple[str | None, str, dict[str, Any]]
"""One SSE event of an answer: its id (None for none), its type and its data."""


@pytest.fixture
def backend() -> GatedBackend:
    return GatedBackend()


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://agents") as http:
        yield http


def events_of(text: str) -> list[Event]:
    """The events of an SSE answer in order; comment blocks (`: ping`) are left out."""
    events: list[Event] = []
    for block in text.split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if not line.startswith(":") and ": " in line)
        if fields:
            events.append((fields.get("id"), fields["event"], json.loads(fields["data"])))
    return events


async def plot_turn(client: httpx.AsyncClient, sid: str) -> str:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "create_plot"})
    assert response.status_code == 200, response.text
    return response.text


async def read_turn(client: httpx.AsyncClient, sid: str, last_event_id: str | None, user: str = USER) -> httpx.Response:
    headers = HEADERS if user == USER else headers_for(user)
    if last_event_id is not None:
        headers = {**headers, "Last-Event-ID": last_event_id}
    return await client.get(f"/v1/sessions/{sid}/turn", headers=headers)


async def body_of(response: Any) -> str:
    """The whole body of a route's `StreamingResponse`, called directly."""
    return "".join([chunk async for chunk in cast(AsyncIterator[str], response.body_iterator)])


async def test_every_event_is_numbered_and_the_turn_reads_again_after_any_of_them(
    client: httpx.AsyncClient, backend: GatedBackend, swap_models
) -> None:
    backend.gate.set()
    swap_models("gemini", default_script())
    sid = await open_session(client)

    turn = events_of(await plot_turn(client, sid))

    run_id = turn[0][2]["run_id"]
    assert [event_id for event_id, _, _ in turn] == [f"{run_id}.{n}" for n in range(1, len(turn) + 1)]
    assert turn[-1][1] == "done" and any(name == "plot" for _, name, _ in turn)
    for seen in (1, len(turn) - 2, len(turn)):
        response = await read_turn(client, sid, f"{run_id}.{seen}")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/event-stream")
        assert events_of(response.text) == turn[seen:]  # exactly what the turn's stream sent after `seen`


async def test_a_read_follows_a_running_turn_to_its_end(
    client: httpx.AsyncClient, runtime: Runtime, backend: GatedBackend, swap_models
) -> None:
    """The cut of the live case: the origin's turn goes on, and the page reads the rest of it while it runs."""
    swap_models("gemini", default_script())
    sid = await open_session(client)
    turn = asyncio.create_task(plot_turn(client, sid))
    await asyncio.wait_for(backend.entered.wait(), 10)  # the pipeline renders: the turn is half way
    log = runtime.turns[sid]
    seen = len(log.events)

    response = await get_turn(sid, USER, runtime, f"{log.run_id}.{seen}")
    reader = asyncio.create_task(body_of(response))
    await asyncio.sleep(0.05)
    assert not reader.done()  # nothing after `seen` yet: the read waits for the turn
    backend.gate.set()
    whole, rest = await asyncio.wait_for(asyncio.gather(turn, reader), 10)

    assert events_of(rest) == events_of(whole)[seen:]
    assert events_of(rest)[-1][1] == "done" and any(name == "plot" for _, name, _ in events_of(rest))


async def test_a_quiet_step_sends_a_ping_on_the_turns_stream(
    client: httpx.AsyncClient, backend: GatedBackend, swap_models, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A model call or a render may send nothing for minutes: the stream writes an unnumbered comment meanwhile."""
    monkeypatch.setattr("agents.main.HEARTBEAT_S", 0.01)
    swap_models("gemini", default_script())
    sid = await open_session(client)
    turn = asyncio.create_task(plot_turn(client, sid))
    await asyncio.wait_for(backend.entered.wait(), 10)
    await asyncio.sleep(0.1)
    backend.gate.set()
    text = await asyncio.wait_for(turn, 10)

    assert f"\n\n{PING}" in text
    events = events_of(text)
    assert events[-1][1] == "done" and all(event_id for event_id, _, _ in events)


async def test_a_client_gone_mid_turn_still_cancels_the_run_and_ends_its_log(
    client: httpx.AsyncClient, runtime: Runtime, backend: GatedBackend, swap_models
) -> None:
    """The log never holds a run: closing the turn's stream releases it at once, and a read of it ends."""
    swap_models("gemini", default_script())
    sid = await open_session(client)
    response = await post_message(sid, MessageBody(action="create_plot"), USER, "admin", runtime, "req-gone")
    stream = cast(AsyncGenerator[str, None], response.body_iterator)
    async for chunk in stream:
        if '"step":"rendering"' in chunk:
            break
    await stream.aclose()

    log = runtime.turns[sid]
    assert log.ended and sid not in runtime.active
    assert all(name != "done" for _, name, _ in events_of("".join(log.events)))
    read = await read_turn(client, sid, f"{log.run_id}.1")
    assert read.status_code == 200
    assert events_of(read.text) == events_of("".join(log.events))[1:]  # what it sent, then the end


async def test_a_read_names_the_sessions_latest_turn_or_is_refused(
    client: httpx.AsyncClient, runtime: Runtime, backend: GatedBackend, swap_models
) -> None:
    backend.gate.set()
    swap_models("gemini", {**default_script(), "root": [{"text": "first"}, {"text": "second"}]})
    sid = await open_session(client)
    assert (await read_turn(client, sid, "0123456789abcdef.1")).json() == {"detail": "not_found"}  # no turn yet

    first = events_of(await plot_turn(client, sid))
    first_run = first[0][2]["run_id"]
    assert (await read_turn(client, sid, f"{first_run}.{len(first) + 1}")).json() == {"detail": "not_found"}
    assert (await read_turn(client, sid, f"{'f' * 16}.1")).json() == {"detail": "not_found"}
    second = events_of(await plot_turn(client, sid))
    assert (await read_turn(client, sid, f"{first_run}.1")).json() == {"detail": "not_found"}  # a newer turn
    assert (await read_turn(client, sid, f"{second[0][2]['run_id']}.1")).status_code == 200

    for malformed in (None, "r1.1", f"{first_run}", f"{first_run.upper()}.1"):
        assert (await read_turn(client, sid, malformed)).status_code == 422
    other = await read_turn(client, sid, f"{first_run}.1", user="adm_fedcba9876543210")
    assert (other.status_code, other.json()) == (404, {"detail": "session_expired"})

    await client.delete(f"/v1/sessions/{sid}", headers=HEADERS)
    assert sid not in runtime.turns
