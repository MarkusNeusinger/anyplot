"""Tests for agents/anyplot/render/serial.py: serial renders by construction, runs before toggles."""

import asyncio
from dataclasses import dataclass, field

import pytest

from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.render.contract import RenderJob, RenderResult, Theme
from agents.anyplot.render.serial import RenderBusy, RenderSlots, SerialRenderer
from agents.anyplot.services import Services


def job(job_id: str, *themes: Theme) -> RenderJob:
    return RenderJob(
        job_id=job_id,
        language="python",
        library="matplotlib",
        source="x = 1",
        data_csv="a\n1\n",
        themes=themes or ("light",),
    )


@dataclass
class HeldBackend(FakeBackend):
    """Fixture renders that each wait for `release`; records the order and the most renders at once."""

    release: asyncio.Event = field(default_factory=asyncio.Event)
    order: list[str] = field(default_factory=list)
    running: int = 0
    most: int = 0

    async def render(self, job: RenderJob) -> RenderResult:
        self.running += 1
        self.most = max(self.most, self.running)
        self.order.append(f"{job.job_id}-{'+'.join(job.themes)}")
        try:
            await self.release.wait()
            return await super().render(job)
        finally:
            self.running -= 1


async def settle() -> None:
    for _ in range(20):
        await asyncio.sleep(0)


async def test_concurrent_renders_run_one_at_a_time() -> None:
    backend = HeldBackend()
    serial = SerialRenderer(backend, concurrency=1)

    tasks = [asyncio.create_task(serial.render(job(f"j{index}"))) for index in range(4)]
    await settle()
    assert backend.running == 1 and serial.slots.waiting == 3
    backend.release.set()
    results = await asyncio.gather(*tasks)

    assert backend.most == 1 and [result.job_id for result in results] == ["j0", "j1", "j2", "j3"]
    assert serial.slots.busy == 0


async def test_a_two_theme_job_renders_one_theme_per_slot() -> None:
    backend = HeldBackend()
    backend.release.set()
    serial = SerialRenderer(backend, concurrency=1)

    result = await serial.render(job("both", "light", "dark"))

    assert backend.order == ["both-light", "both-dark"] and backend.most == 1
    assert set(result.outputs) == {"light", "dark"} and result.job_id == "both"


async def test_a_concurrency_of_two_runs_two() -> None:
    backend = HeldBackend()
    serial = SerialRenderer(backend, concurrency=2)

    tasks = [asyncio.create_task(serial.render(job(f"j{index}"))) for index in range(3)]
    await settle()
    assert backend.running == 2
    backend.release.set()
    await asyncio.gather(*tasks)

    assert backend.most == 2


async def test_a_waiting_run_render_goes_before_earlier_toggles() -> None:
    backend = HeldBackend()
    serial = SerialRenderer(backend, concurrency=1)

    first = asyncio.create_task(serial.render(job("busy")))
    await settle()
    toggles = [asyncio.create_task(serial.render(job(f"t{index}"), lane="toggle")) for index in range(3)]
    await settle()
    run = asyncio.create_task(serial.render(job("run")))
    await settle()
    backend.release.set()
    await asyncio.gather(first, run, *toggles)

    assert backend.order == ["busy-light", "run-light", "t0-light", "t1-light", "t2-light"]


async def test_a_bounded_wait_raises_render_busy_and_renders_nothing() -> None:
    backend = HeldBackend()
    serial = SerialRenderer(backend, concurrency=1)
    first = asyncio.create_task(serial.render(job("busy")))
    await settle()

    with pytest.raises(RenderBusy):
        await serial.render(job("toggle"), lane="toggle", wait_s=0.05)

    assert backend.order == ["busy-light"] and serial.slots.waiting == 0
    backend.release.set()
    await first
    assert serial.slots.busy == 0
    await serial.render(job("after"), lane="toggle", wait_s=0.05)  # the slot was not leaked


async def test_a_cancelled_waiter_leaves_the_line() -> None:
    backend = HeldBackend()
    serial = SerialRenderer(backend, concurrency=1)
    first = asyncio.create_task(serial.render(job("busy")))
    await settle()
    gone = asyncio.create_task(serial.render(job("gone")))
    later = asyncio.create_task(serial.render(job("later")))
    await settle()

    gone.cancel()
    await settle()
    backend.release.set()
    await asyncio.gather(first, later)

    assert gone.cancelled() and backend.order == ["busy-light", "later-light"]
    assert serial.slots.busy == 0


async def test_a_slot_handed_to_a_waiter_cancelled_at_that_moment_is_passed_on() -> None:
    slots = RenderSlots(1)
    await slots.acquire("run")
    waiter = asyncio.create_task(slots.acquire("run"))
    nxt = asyncio.create_task(slots.acquire("toggle"))
    await settle()

    slots.release()  # hands the slot to `waiter` ...
    waiter.cancel()  # ... which is cancelled before it resumes
    await settle()

    assert waiter.cancelled() and nxt.done() and slots.busy == 1
    slots.release()
    assert slots.busy == 0


def test_render_slots_need_a_positive_limit() -> None:
    with pytest.raises(ValueError):
        RenderSlots(0)


def test_services_put_every_backend_behind_the_render_slots() -> None:
    fake = FakeBackend()
    services = Services(backend_factory=lambda: fake)

    backend = services.backend

    assert isinstance(backend, SerialRenderer) and backend.backend is fake
    assert backend.slots.limit == 1 and backend.name == "fake"
    assert services.backend is backend
