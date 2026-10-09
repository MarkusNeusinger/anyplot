"""The run queue through `/v1`: two users, a full queue, the maximum wait, cancel and disconnect.

The runtime's queue runs at the production defaults (one run in flight, one start a
minute, a 600-second maximum wait) on a fake clock, so the tests advance time instead
of sleeping. A gated fake renderer holds a run in flight until the test opens the gate.
"""

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.render.contract import RenderJob, RenderResult
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.main import Runtime, app, get_runtime

from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK
from .test_run_queue import Clock
from .test_service_flow import HEADERS, USER, create_plot, headers_for, open_session


OTHER = "adm_fedcba9876543210"


@dataclass
class GatedBackend(FakeBackend):
    """Fixture renders that wait for `gate`; `entered` is set when a render begins."""

    entered: asyncio.Event = field(default_factory=asyncio.Event)
    gate: asyncio.Event = field(default_factory=asyncio.Event)

    async def render(self, job: RenderJob) -> RenderResult:
        self.entered.set()
        await self.gate.wait()
        return await super().render(job)


@pytest.fixture
def backend() -> GatedBackend:
    return GatedBackend()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def runtime(clock: Clock) -> Iterator[Runtime]:
    fresh = Runtime(queue=RunQueue(concurrency=1, per_minute=1, max_wait_s=600, clock=clock))
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://agents") as http:
        yield http


async def until(predicate: Callable[[], bool], what: str) -> None:
    """Poll the in-process tasks until `predicate` holds; fails after about two seconds."""
    for _ in range(200):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"timed out waiting for {what}")


def two_runs() -> dict[str, list[Any]]:
    return {
        "root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}] * 2,
        "adapter": [{"json": SCATTER_PLAN}, {"json": SCATTER_PLAN}],
        "reviewer": [{"json": VERDICT_OK}, {"json": VERDICT_OK}],
    }


def statuses(events: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    return [data for name, data in events if name == "status"]


async def test_the_second_user_waits_in_the_queue_then_runs(
    client: httpx.AsyncClient, runtime: Runtime, clock: Clock, backend: GatedBackend, swap_models
) -> None:
    swap_models("gemini", two_runs())
    first = await open_session(client)
    second = await open_session(client, user=OTHER)
    queue = runtime.run_queue()

    first_run = asyncio.create_task(create_plot(client, first))
    await asyncio.wait_for(backend.entered.wait(), 5)
    second_run = asyncio.create_task(create_plot(client, second, headers_for(OTHER)))
    await until(lambda: queue.waiting_count == 1, "the second run to queue")

    status = (await client.get("/v1/status", headers=HEADERS)).json()
    assert (status["waiting"], status["in_flight"]) == (1, 1)
    backend.gate.set()
    first_events = await asyncio.wait_for(first_run, 10)
    assert next(data for name, data in first_events if name == "plot")["status"] == "ok"
    assert not any(data["step"] == "queued" for data in statuses(first_events))

    # The first run is over, but only one run may start a minute: the second still waits.
    assert queue.waiting_count == 1 and queue.in_flight == 0
    clock.advance(60)
    queue.pump()
    second_events = await asyncio.wait_for(second_run, 10)

    assert second_events[0][0] == "ready"
    assert second_events[1] == ("status", {"step": "queued", "position": 1, "waiting": 1})
    steps = [data["step"] for data in statuses(second_events)]
    assert steps == ["queued", "adapting", "checking", "rendering", "reviewing"]
    assert next(data for name, data in second_events if name == "plot")["status"] == "ok"
    assert second_events[-1][0] == "done"
    assert runtime.active == {} and (queue.waiting_count, queue.in_flight) == (0, 0)


async def test_a_full_queue_answers_503_before_the_stream(client: httpx.AsyncClient, runtime: Runtime) -> None:
    sid = await open_session(client)
    queue = runtime.run_queue()
    queue.submit("adm_running", "s-running")
    for index in range(queue.capacity):
        queue.submit(f"adm_wait{index}", f"s-wait-{index}")

    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "create_plot"})

    assert (response.status_code, response.json()) == (503, {"detail": "capacity"})
    assert sid not in runtime.active and queue.waiting_count == 10


async def test_a_user_with_a_queued_run_gets_409_and_cancel_leaves_the_queue(
    client: httpx.AsyncClient, runtime: Runtime, swap_models
) -> None:
    swap_models("gemini", two_runs())
    first = await open_session(client)
    second = await open_session(client)
    queue = runtime.run_queue()
    queue.submit("adm_running", "s-running")  # another user's run holds the only slot

    queued = asyncio.create_task(create_plot(client, first))
    await until(lambda: queue.waiting_count == 1, "the run to queue")

    same_session = await client.post(f"/v1/sessions/{first}/messages", headers=HEADERS, json={"text": "hi"})
    other_session = await client.post(
        f"/v1/sessions/{second}/messages", headers=HEADERS, json={"action": "create_plot"}
    )
    toggle = await client.post(f"/v1/sessions/{first}/versions/1/render", headers=HEADERS, json={"theme": "dark"})
    assert (same_session.status_code, same_session.json()) == (409, {"detail": "run_active"})
    assert (other_session.status_code, other_session.json()) == (409, {"detail": "run_active"})
    assert (toggle.status_code, toggle.json()) == (409, {"detail": "run_active"})

    cancel = await client.post(f"/v1/sessions/{first}/cancel", headers=HEADERS)
    events = await asyncio.wait_for(queued, 5)

    assert cancel.status_code == 204
    assert [name for name, _ in events] == ["ready", "status", "done"]
    assert events[1][1] == {"step": "queued", "position": 1, "waiting": 1}
    assert queue.waiting_count == 0 and first not in runtime.active


async def test_a_run_that_waited_the_maximum_ends_with_capacity(
    client: httpx.AsyncClient, runtime: Runtime, clock: Clock, swap_models
) -> None:
    fake = swap_models("gemini", two_runs())
    sid = await open_session(client)
    queue = runtime.run_queue()
    queue.submit("adm_running", "s-running")
    waiting = asyncio.create_task(create_plot(client, sid))
    await until(lambda: queue.waiting_count == 1, "the run to queue")

    clock.advance(600)
    queue.pump()
    events = await asyncio.wait_for(waiting, 5)

    assert [name for name, _ in events] == ["ready", "status", "error", "done"]
    assert events[2][1] == {"code": "capacity", "ref": "req-1"}
    assert events[3][1] == {"llm_calls": 0, "tokens": 0}
    assert fake.requests == [] and sid not in runtime.active


async def test_a_client_gone_while_queued_leaves_the_queue(client: httpx.AsyncClient, runtime: Runtime) -> None:
    sid = await open_session(client)
    queue = runtime.run_queue()
    queue.submit("adm_running", "s-running")
    waiting = asyncio.create_task(create_plot(client, sid))
    await until(lambda: queue.waiting_count == 1, "the run to queue")

    waiting.cancel()
    await until(lambda: queue.waiting_count == 0, "the entry to leave the queue")

    assert sid not in runtime.active
    with pytest.raises(asyncio.CancelledError):
        await waiting


async def test_queued_time_does_not_count_toward_the_deadline(
    client: httpx.AsyncClient, runtime: Runtime, clock: Clock, backend: GatedBackend, swap_models
) -> None:
    """An entry that waited far longer than the request deadline still runs to a plot."""
    backend.gate.set()
    swap_models("gemini", two_runs())
    sid = await open_session(client)
    queue = runtime.run_queue()
    blocker = queue.submit("adm_running", "s-running")
    waiting = asyncio.create_task(create_plot(client, sid))
    await until(lambda: queue.waiting_count == 1, "the run to queue")

    clock.advance(500)  # past the 180-second request deadline, inside the 600-second wait
    queue.release(blocker)
    events = await asyncio.wait_for(waiting, 10)

    assert next(data for name, data in events if name == "plot")["status"] == "ok"
    assert "error" not in [name for name, _ in events]


async def test_a_queued_entry_is_stale_only_after_the_maximum_wait(runtime: Runtime, clock: Clock) -> None:
    from agents.anyplot.settings import get_settings
    from agents.main import STALE_RUN_MARGIN_S, ActiveRun

    queue = runtime.run_queue()
    queue.submit("adm_running", "s-running")
    ticket = queue.submit(USER, "s1")
    runtime.active["s1"] = ActiveRun(abort=asyncio.Event(), user=USER, started=runtime.now(), ticket=ticket)

    clock.advance(400)  # longer than the request deadline plus its margin
    runtime.drop_stale(get_settings())
    assert "s1" in runtime.active
    clock.advance(200 + STALE_RUN_MARGIN_S + 1)
    runtime.drop_stale(get_settings())
    assert "s1" not in runtime.active and queue.waiting_count == 0
