"""The run queue: the memory, rate and cost limiter of one instance, in front of whole pipeline runs.

Every `/v1/sessions/{sid}/messages` turn is one entry. An entry runs when both limits
allow it, in the order of its lane and then its arrival:

* **Concurrency.** At most `AGENT_RUN_CONCURRENCY` runs are in flight (default 1),
  because spikes S and S2 showed one 4 GiB instance serves one sandbox at a time safely.
* **Rate.** A run may start only while fewer than `AGENT_RUNS_PER_MINUTE` runs started
  in the last 60 seconds (default 1), a sliding window of start times.

The queue holds at most `capacity = AGENT_RUNS_PER_MINUTE * AGENT_QUEUE_MAX_WAIT_S / 60`
waiting entries (10 at the defaults): a new entry that would stand at a position past
it would wait longer than the maximum, so `submit` refuses it with `QueueFull`, which
the route answers as `503 capacity`. An entry that can start at once never waits and
is accepted even when `capacity` is 0. An entry that waited `AGENT_QUEUE_MAX_WAIT_S`
leaves with `QueueTimeout`, which the stream ends as `error{code:"capacity"}`; an
entry whose turn comes at that very moment starts instead.

The capacity is the owner's formula (2026-10-09) and assumes that runs end within the
60-second rate window. A run that takes longer holds the only slot past the window,
so every later start slips by the difference: at one run in flight, ten accepted
entries and 90-second runs, the last four wait the full maximum and leave with
`capacity`. Admission therefore promises a place, not a start.

**Lanes.** An entry carries a lane: `premium` entries go before every `normal` entry,
first come first served within a lane. Nothing sets `premium` yet; it is the lane for
users who later pay for their own tokens. It bypasses the normal lane only: the
concurrency and rate limits bind it too, and its position counts only the entries
ahead of it, so it can push normal entries past the maximum wait.

**Waiting.** `wait(ticket)` is an async generator that yields the entry's
`QueuePosition` at once, on every change of its position or of the queue length, and
again every `heartbeat_s` while nothing changes, so a quiet stream stays alive behind
proxies; it returns when the entry may run. Leaving it early (the consumer was
cancelled, for example when the client disconnected) withdraws a still-waiting
entry, so an abandoned entry never holds a place. A running entry holds its slot
until `release`: the route releases it when the run ends, and the run registry's
stale sweep releases one whose stream vanished.

The clock is injectable, and time-based changes (the rate window opening, an entry
expiring) are evaluated on every `pump`, so tests advance a fake clock and call
`pump()` instead of sleeping. One asyncio loop drives everything; nothing is locked.
No ADK import.
"""

import asyncio
import itertools
import math
import time
from collections import deque
from collections.abc import AsyncGenerator, Callable, Iterable
from dataclasses import dataclass, field
from typing import Literal, Self

from .settings import AgentSettings


Lane = Literal["premium", "normal"]
LANE_PRIORITY: dict[str, int] = {"premium": 0, "normal": 1}
"""Lower runs first; within a lane, the earlier arrival runs first."""
TicketState = Literal["waiting", "running", "done", "withdrawn", "expired"]
RATE_WINDOW_S = 60.0
HEARTBEAT_S = 15.0
"""Seconds after which a waiting entry's unchanged position is sent again."""
MIN_WAKE_S = 0.01


class QueueFull(Exception):
    """The entry would wait longer than the maximum; nothing was queued."""


class QueueTimeout(Exception):
    """The entry waited the maximum and left the queue without running."""


class QueueWithdrawn(Exception):
    """The entry left the queue before its turn: cancelled, purged or swept."""


@dataclass(frozen=True)
class QueuePosition:
    """Where a waiting entry stands: `position` 1 runs next; `waiting` counts every entry, this one included."""

    position: int
    waiting: int


@dataclass(eq=False)
class Ticket:
    """One queue entry: a run that waits, runs, or has left the queue."""

    user: str
    session_id: str
    lane: Lane
    seq: int
    enqueued_at: float
    state: TicketState = "waiting"
    started_at: float | None = None
    changed: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    @property
    def order(self) -> tuple[int, int]:
        return LANE_PRIORITY[self.lane], self.seq

    @property
    def waiting(self) -> bool:
        return self.state == "waiting"

    @property
    def running(self) -> bool:
        return self.state == "running"


class RunQueue:
    """A two-lane FIFO of runs under a concurrency limit and a sliding-window rate limit."""

    def __init__(
        self,
        *,
        concurrency: int,
        per_minute: int,
        max_wait_s: float,
        clock: Callable[[], float] = time.monotonic,
        window_s: float = RATE_WINDOW_S,
    ) -> None:
        if concurrency < 1 or per_minute < 1 or max_wait_s <= 0 or window_s <= 0:
            raise ValueError("concurrency, rate, maximum wait and window must be positive")
        self.concurrency = concurrency
        self.per_minute = per_minute
        self.max_wait_s = max_wait_s
        self.window_s = window_s
        self._clock = clock
        self._waiting: list[Ticket] = []
        self._running: list[Ticket] = []
        self._starts: deque[float] = deque()
        self._seq = itertools.count(1)

    @classmethod
    def from_settings(cls, settings: AgentSettings, clock: Callable[[], float] = time.monotonic) -> Self:
        return cls(
            concurrency=settings.run_concurrency,
            per_minute=settings.runs_per_minute,
            max_wait_s=settings.queue_max_wait_s,
            clock=clock,
        )

    def now(self) -> float:
        """The queue's clock, which the run registry shares so its stale check measures the same time."""
        return self._clock()

    @property
    def capacity(self) -> int:
        """Waiting entries the maximum wait allows: the rate times the maximum wait, per window."""
        return math.floor(self.per_minute * self.max_wait_s / self.window_s)

    @property
    def waiting_count(self) -> int:
        return len(self._waiting)

    @property
    def in_flight(self) -> int:
        return len(self._running)

    def submit(self, user: str, session_id: str, lane: Lane = "normal") -> Ticket:
        """Queue a run, or start it at once; raises `QueueFull` when it would wait past the maximum."""
        now = self._clock()
        self._pump(now)
        ticket = Ticket(user=user, session_id=session_id, lane=lane, seq=next(self._seq), enqueued_at=now)
        position = 1 + sum(1 for other in self._waiting if other.order < ticket.order)
        if position > self.capacity and not (position == 1 and self._can_start(now)):
            raise QueueFull(f"position {position} is past the queue's capacity of {self.capacity}")
        self._waiting.append(ticket)
        self._waiting.sort(key=lambda entry: entry.order)
        self._wake(self._waiting)
        self._pump(now)
        return ticket

    def position(self, ticket: Ticket) -> QueuePosition | None:
        """The entry's place in the queue, or None once it left it."""
        if not ticket.waiting:
            return None
        return QueuePosition(position=self._waiting.index(ticket) + 1, waiting=len(self._waiting))

    def pump(self) -> None:
        """Start every entry the limits allow, then expire the waiting ones past the maximum wait."""
        self._pump(self._clock())

    def withdraw(self, ticket: Ticket) -> bool:
        """Take a waiting entry out of the queue (cancel, purge, a gone client); False if it was not waiting."""
        if not ticket.waiting:
            return False
        self._waiting.remove(ticket)
        ticket.state = "withdrawn"
        self._wake([ticket, *self._waiting])
        self.pump()
        return True

    def release(self, ticket: Ticket) -> None:
        """The run ended: free its slot, or withdraw it if it never started. Idempotent."""
        if ticket.waiting:
            self.withdraw(ticket)
            return
        if ticket.running:
            self._running.remove(ticket)
            ticket.state = "done"
            self._wake([ticket])
            self.pump()

    def next_change_at(self, now: float) -> float:
        """The next time a waiting entry's fate can change without any call: an expiry or the window opening."""
        if not self._waiting:
            return math.inf
        times = [entry.enqueued_at + self.max_wait_s for entry in self._waiting]
        self._trim(now)
        if len(self._running) < self.concurrency and len(self._starts) >= self.per_minute:
            times.append(self._starts[0] + self.window_s)
        return min(times)

    async def wait(self, ticket: Ticket, *, heartbeat_s: float = HEARTBEAT_S) -> AsyncGenerator[QueuePosition, None]:
        """Yield the entry's position while it waits (at once, on change, every heartbeat); return when it runs.

        Raises `QueueTimeout` when the entry waited the maximum, `QueueWithdrawn` when it
        was taken out of the queue. Leaving the generator early withdraws a waiting entry.
        """
        last: QueuePosition | None = None
        sent_at = -math.inf
        try:
            while True:
                ticket.changed.clear()  # cleared before the state is read, so no change is missed
                now = self._clock()
                self._pump(now)
                if ticket.running:
                    return
                if ticket.state == "expired":
                    raise QueueTimeout("the run waited the maximum time in the queue")
                current = self.position(ticket)
                if current is None:
                    raise QueueWithdrawn("the run left the queue before its turn")
                if current != last or now - sent_at >= heartbeat_s:
                    last, sent_at = current, now
                    yield current
                    continue
                wake_at = min(sent_at + heartbeat_s, self.next_change_at(now))
                try:
                    await asyncio.wait_for(ticket.changed.wait(), timeout=max(wake_at - now, MIN_WAKE_S))
                except TimeoutError:
                    pass
        finally:
            if ticket.waiting:
                self.withdraw(ticket)

    # --- internals -------------------------------------------------------------------------

    def _trim(self, now: float) -> None:
        while self._starts and now - self._starts[0] >= self.window_s:
            self._starts.popleft()

    def _can_start(self, now: float) -> bool:
        self._trim(now)
        return len(self._running) < self.concurrency and len(self._starts) < self.per_minute

    def _pump(self, now: float) -> None:
        # An entry past its maximum wait never starts, however late the pump that finds
        # it; one whose turn comes at the very moment its wait runs out starts rather
        # than leaving with `capacity`. So: expire the overdue, start, expire the due.
        expired = self._expire(lambda waited: waited > self.max_wait_s, now)
        started: list[Ticket] = []
        while self._waiting and self._can_start(now):
            entry = self._waiting.pop(0)
            entry.state, entry.started_at = "running", now
            self._running.append(entry)
            self._starts.append(now)
            started.append(entry)
        expired += self._expire(lambda waited: waited >= self.max_wait_s, now)
        if expired or started:
            self._wake([*expired, *started, *self._waiting])

    def _expire(self, past: Callable[[float], bool], now: float) -> list[Ticket]:
        expired = [entry for entry in self._waiting if past(now - entry.enqueued_at)]
        for entry in expired:
            self._waiting.remove(entry)
            entry.state = "expired"
        return expired

    @staticmethod
    def _wake(tickets: Iterable[Ticket]) -> None:
        for entry in tickets:
            entry.changed.set()
