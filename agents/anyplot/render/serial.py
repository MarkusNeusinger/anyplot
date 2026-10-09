"""Serial renders by construction: the one render semaphore of the instance, in front of every backend.

Spikes S and S2 showed that one 4 GiB instance serves one sandbox at a time safely,
so renders must stay serial whichever backend runs them and whichever route asks.
`SerialRenderer` wraps the backend `make_backend` built (`Services.backend` applies
it), so no backend has to remember a semaphore of its own:

* **One theme per slot.** A job is rendered theme by theme, each under one of
  `AGENT_RENDER_CONCURRENCY` slots (default 1), so even a two-theme job never runs
  two sandboxes at once.
* **Runs first.** A slot that comes free goes to a waiting pipeline render (`run`
  lane) before a waiting theme toggle (`toggle` lane), first come first served
  within a lane. A run therefore waits for at most the render in progress, never
  for a line of toggles that arrived before it.
* **Bounded waits.** A caller may pass `wait_s`: when no slot came free in time,
  `render` raises `RenderBusy` and nothing ran. The theme toggle uses it, so a
  synchronous route never hangs behind a busy instance.

The render's own `job.timeout_s` starts when the backend runs it, after the wait.
No ADK import.
"""

import asyncio
from collections import deque
from dataclasses import replace
from typing import Literal

from .contract import RenderBackend, RenderJob, RenderResult


RenderLane = Literal["run", "toggle"]
LANE_ORDER: tuple[RenderLane, ...] = ("run", "toggle")
"""The order in which waiting lanes get a freed slot."""


class RenderBusy(Exception):
    """No render slot came free within the caller's wait; nothing was rendered."""


class RenderSlots:
    """`limit` render slots with two waiting lanes; a freed slot goes to the `run` lane first."""

    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("the render concurrency must be positive")
        self.limit = limit
        self.busy = 0
        self._waiters: dict[RenderLane, deque[asyncio.Future[None]]] = {lane: deque() for lane in LANE_ORDER}

    @property
    def waiting(self) -> int:
        return sum(1 for lane in LANE_ORDER for future in self._waiters[lane] if not future.done())

    async def acquire(self, lane: RenderLane, wait_s: float | None = None) -> None:
        """Take a slot; raises `TimeoutError` when none came free within `wait_s` seconds (None waits)."""
        if self.busy < self.limit:  # a free slot means nobody waits: release hands slots over
            self.busy += 1
            return
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._waiters[lane].append(future)
        try:
            async with asyncio.timeout(wait_s):
                await future
        except BaseException:
            if future.done() and not future.cancelled():
                self.release()  # the slot was handed over just as the caller gave up: pass it on
            else:
                future.cancel()
                if future in self._waiters[lane]:
                    self._waiters[lane].remove(future)
            raise

    def release(self) -> None:
        """Hand the slot to the next waiter (runs first), or free it."""
        for lane in LANE_ORDER:
            waiters = self._waiters[lane]
            while waiters:
                future = waiters.popleft()
                if not future.done():
                    future.set_result(None)
                    return
        self.busy -= 1


class SerialRenderer:
    """Any `RenderBackend`, rendering one theme per slot under `RenderSlots`."""

    def __init__(self, backend: RenderBackend, *, concurrency: int) -> None:
        self.backend = backend
        self.name = backend.name
        self.slots = RenderSlots(concurrency)

    async def render(self, job: RenderJob, *, lane: RenderLane = "run", wait_s: float | None = None) -> RenderResult:
        """Render every theme of `job`, one slot at a time; raises `RenderBusy` when a slot wait ran out."""
        result = RenderResult(job_id=job.job_id)
        for theme in job.themes:
            part = job if len(job.themes) == 1 else replace(job, themes=(theme,))
            try:
                await self.slots.acquire(lane, wait_s)
            except TimeoutError:
                raise RenderBusy(f"no render slot came free within {wait_s} s") from None
            try:
                rendered = await self.backend.render(part)
            finally:
                self.slots.release()
            result.outputs.update(rendered.outputs)
        return result
