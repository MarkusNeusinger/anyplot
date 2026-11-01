"""The run queue: the memory, rate and cost limiter of one instance, in front of the sandbox runs.

Only sandbox work enters it (owner decision of 2026-10-14): a chat turn starts at once,
and the turn takes an entry only when its root calls `plot_pipeline` or `run_data_code`
(`agents/main.py`, `TurnSlot`). The turn holds that entry until it ends, so a second
sandbox run in the same turn neither waits again nor books a second start. A plain
answer, a refusal, `prepare_data` or `generate_data` never touches the queue. An entry
carries a lane, and runs when its lane's limits allow it, in the order of its lane and
then its arrival.

**Lanes** (owner decision of 2026-11-01). Each lane has limits of its own:

* `normal`, every user who is not an admin, today and after the public launch:
  at most `AGENT_RUN_CONCURRENCY` runs in flight (default 1, because spikes S and S2
  showed one 4 GiB instance serves one sandbox at a time safely), a start only while
  fewer than `AGENT_RUNS_PER_MINUTE` runs started in the last 60 seconds (default 1,
  a sliding window of start times), and `AGENT_USER_MAX_RUNS` entries per user.
* `premium` shares the `normal` lane's limits and goes before every `normal` entry.
  Nothing sets it yet; it is the lane for users who later pay for their own tokens.
  The concurrency and rate limits bind it too, and its position counts only the
  entries ahead of it, so it can push normal entries past the maximum wait.
* `admin`, the admin's runs, the fan-out over every library (`.plot_all()`) above all:
  `AGENT_ADMIN_RUN_CONCURRENCY` runs in flight (default 5), no rate window unless
  `AGENT_ADMIN_RUNS_PER_MINUTE` sets one, and `AGENT_ADMIN_USER_MAX_RUNS` entries per
  admin (default 5).

The route picks the lane from the tier the BFF asserts for the caller (`X-Anyplot-Tier`,
`agents/main.py` `caller_tier`), never from anything the browser sets. The lanes never
wait for each other: an admin's runs take none of the `normal` lane's slot, rate window
or places, and the reverse. What they share is the one instance, so up to
`AGENT_RUN_CONCURRENCY + AGENT_ADMIN_RUN_CONCURRENCY` runs are in flight at once (6 at
the defaults). A run spends most of its time in model calls, which wait on the network,
but every render of every lane takes the instance's one render slot
(`render/serial.py`, `AGENT_RENDER_CONCURRENCY`), first come first served: a public
run's render can wait behind the renders of the admin's runs in flight (about 5 s
each), and the reverse.

**Capacity.** A lane holds at most `capacity = rate * AGENT_QUEUE_MAX_WAIT_S / 60`
waiting entries, where `rate` is its runs per minute (10 for the `normal` lane at the
defaults): a new entry that would stand at a position past it would wait longer than
the maximum, so `submit` refuses it with `QueueFull`, which the route answers as
`503 capacity`. A lane without a rate window counts its concurrency as its rate,
because under the formula's assumption below it starts at most that many runs a minute
(50 for the `admin` lane at the defaults, which its per-user cap keeps far lower: five
entries per admin). An entry that can start at once never waits and is accepted even
when `capacity` is 0. An entry that waited `AGENT_QUEUE_MAX_WAIT_S` leaves with
`QueueTimeout`, which the stream ends as `error{code:"capacity"}`; an entry whose turn
comes at that very moment starts instead.

The capacity is the owner's formula (2026-10-09) and assumes that runs end within the
60-second rate window. A run that takes longer holds the only slot past the window,
so every later start slips by the difference: at one run in flight, ten accepted
entries and 90-second runs, the last four wait the full maximum and leave with
`capacity`. Admission therefore promises a place, not a start. A run holds its slot
until its turn ends, the root's closing reply included.

**Per user.** A user may hold at most their lane's per-user cap of entries
(`AGENT_USER_MAX_RUNS`, default 3; `AGENT_ADMIN_USER_MAX_RUNS` for an admin), waiting
and running together, across all their sessions (owner decision of 2026-10-21: each
browser window is a session of its own, and a user's windows work in parallel, so the
cap bounds what one user puts into the shared queue). `submit` refuses one more with
`QueueUserLimit`, which the route ends as `error{code:"run_limit"}`, before it looks at
the lane's length: a user at the cap learns that from their own runs, not from
`capacity`. The cap is checked in `submit` because the queue already holds every entry
with its user; it changes neither the lane's capacity nor its order, and an entry the
cap refuses never took a place, a start or a position.

**Waiting.** `wait(ticket)` is an async generator that yields the entry's
`QueuePosition` at once, on every change of its position or of its lane's length, and
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


Lane = Literal["admin", "premium", "normal"]
LANE_PRIORITY: dict[str, int] = {"admin": 0, "premium": 0, "normal": 1}
"""Lower runs first among the entries under the same limits; within a lane, the earlier arrival runs first."""
Limits = Literal["admin", "public"]
LANE_LIMITS: dict[str, Limits] = {"admin": "admin", "premium": "public", "normal": "public"}
"""Whose limits bind a lane: the `admin` lane its own, `premium` and `normal` the public ones together."""
TicketState = Literal["waiting", "running", "done", "withdrawn", "expired"]
RATE_WINDOW_S = 60.0
HEARTBEAT_S = 15.0
"""Seconds after which a waiting entry's unchanged position is sent again."""
MIN_WAKE_S = 0.01


class QueueFull(Exception):
    """The entry would wait longer than the maximum; nothing was queued."""


class QueueUserLimit(Exception):
    """The user already holds the most entries a user may hold, waiting or running; nothing was queued."""


class QueueTimeout(Exception):
    """The entry waited the maximum and left the queue without running."""


class QueueWithdrawn(Exception):
    """The entry left the queue before its turn: cancelled, purged or swept."""


@dataclass(frozen=True)
class QueuePosition:
    """Where a waiting entry stands among the entries under its lane's limits: `position` 1 runs next; `waiting`
    counts every one of them, this one included."""

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


@dataclass(frozen=True)
class LaneLimits:
    """The limits of one lane: runs in flight, starts per rate window (None: no window), entries per user (None: no
    cap)."""

    concurrency: int
    per_minute: int | None = None
    per_user: int | None = None

    def __post_init__(self) -> None:
        if self.concurrency < 1 or (self.per_minute is not None and self.per_minute < 1):
            raise ValueError("concurrency and rate must be positive")
        if self.per_user is not None and self.per_user < 1:
            raise ValueError("the per-user cap must be positive")


@dataclass(eq=False)
class _Pool:
    """The entries under one set of limits: waiting in order, running, and the start times in the rate window."""

    limits: LaneLimits
    waiting: list[Ticket] = field(default_factory=list)
    running: list[Ticket] = field(default_factory=list)
    starts: deque[float] = field(default_factory=deque)


class RunQueue:
    """A FIFO of runs per lane, each lane under its own concurrency limit, sliding-window rate limit and per-user cap.

    The keyword limits are the public ones, which bind the `normal` and `premium` lanes; `admin` gives the `admin`
    lane its own. Without `admin` the queue has no admin lane, and an admin entry is refused with `ValueError`.
    """

    def __init__(
        self,
        *,
        concurrency: int,
        per_minute: int,
        max_wait_s: float,
        clock: Callable[[], float] = time.monotonic,
        window_s: float = RATE_WINDOW_S,
        per_user: int | None = None,
        admin: LaneLimits | None = None,
    ) -> None:
        if max_wait_s <= 0 or window_s <= 0:
            raise ValueError("maximum wait and window must be positive")
        self.max_wait_s = max_wait_s
        self.window_s = window_s
        self._pools: dict[Limits, _Pool] = {"public": _Pool(LaneLimits(concurrency, per_minute, per_user))}
        if admin is not None:
            self._pools["admin"] = _Pool(admin)
        self._clock = clock
        self._seq = itertools.count(1)

    @classmethod
    def from_settings(cls, settings: AgentSettings, clock: Callable[[], float] = time.monotonic) -> Self:
        return cls(
            concurrency=settings.run_concurrency,
            per_minute=settings.runs_per_minute,
            max_wait_s=settings.queue_max_wait_s,
            clock=clock,
            per_user=settings.user_max_runs,
            admin=LaneLimits(
                concurrency=settings.admin_run_concurrency,
                per_minute=settings.admin_runs_per_minute,
                per_user=settings.admin_user_max_runs,
            ),
        )

    def now(self) -> float:
        """The queue's clock, which the run registry shares so its stale check measures the same time."""
        return self._clock()

    def limits(self, lane: Lane) -> LaneLimits:
        """The limits that bind `lane`; `ValueError` for the admin lane of a queue without one."""
        return self._pool(lane).limits

    @property
    def concurrency(self) -> int:
        """Runs in flight the public lanes allow (`AGENT_RUN_CONCURRENCY`)."""
        return self._pools["public"].limits.concurrency

    @property
    def per_minute(self) -> int | None:
        """Starts per window the public lanes allow (`AGENT_RUNS_PER_MINUTE`)."""
        return self._pools["public"].limits.per_minute

    @property
    def per_user(self) -> int | None:
        """Entries one user may hold in the public lanes, waiting and running (`AGENT_USER_MAX_RUNS`); None sets no
        cap."""
        return self._pools["public"].limits.per_user

    @property
    def capacity(self) -> int:
        """Waiting entries the maximum wait allows in the public lanes (`lane_capacity`)."""
        return self.lane_capacity("normal")

    def lane_capacity(self, lane: Lane) -> int:
        """Waiting entries the maximum wait allows under `lane`'s limits: the rate times the maximum wait, per window.

        A lane without a rate window counts its concurrency as its rate: under the formula's assumption that a run
        ends within the window, it starts at most that many runs per window.
        """
        limits = self.limits(lane)
        rate = limits.per_minute if limits.per_minute is not None else limits.concurrency
        return math.floor(rate * self.max_wait_s / self.window_s)

    @property
    def waiting_count(self) -> int:
        """Waiting entries in every lane."""
        return sum(len(pool.waiting) for pool in self._pools.values())

    @property
    def in_flight(self) -> int:
        """Runs in flight in every lane."""
        return sum(len(pool.running) for pool in self._pools.values())

    def user_entries(self, user: str, lane: Lane = "normal") -> int:
        """The user's entries under `lane`'s limits, waiting and running, in every session."""
        pool = self._pool(lane)
        return sum(1 for entry in (*pool.waiting, *pool.running) if entry.user == user)

    def submit(self, user: str, session_id: str, lane: Lane = "normal") -> Ticket:
        """Queue a run in `lane`, or start it at once.

        Raises `QueueUserLimit` when the user already holds the lane's per-user cap of entries (checked first), and
        `QueueFull` when the run would wait past the maximum.
        """
        pool = self._pool(lane)
        now = self._clock()
        self._pump(now)  # an entry that expired just now no longer counts against its user
        per_user = pool.limits.per_user
        if per_user is not None and self.user_entries(user, lane) >= per_user:
            raise QueueUserLimit(f"the user already holds {per_user} entries")
        ticket = Ticket(user=user, session_id=session_id, lane=lane, seq=next(self._seq), enqueued_at=now)
        position = 1 + sum(1 for other in pool.waiting if other.order < ticket.order)
        capacity = self.lane_capacity(lane)
        if position > capacity and not (position == 1 and self._can_start(pool, now)):
            raise QueueFull(f"position {position} is past the lane's capacity of {capacity}")
        pool.waiting.append(ticket)
        pool.waiting.sort(key=lambda entry: entry.order)
        self._wake(pool.waiting)
        self._pump(now)
        return ticket

    def position(self, ticket: Ticket) -> QueuePosition | None:
        """The entry's place among the entries under its lane's limits, or None once it left the queue."""
        if not ticket.waiting:
            return None
        waiting = self._pool(ticket.lane).waiting
        return QueuePosition(position=waiting.index(ticket) + 1, waiting=len(waiting))

    def pump(self) -> None:
        """Start every entry the limits allow, then expire the waiting ones past the maximum wait."""
        self._pump(self._clock())

    def withdraw(self, ticket: Ticket) -> bool:
        """Take a waiting entry out of the queue (cancel, purge, a gone client); False if it was not waiting."""
        if not ticket.waiting:
            return False
        pool = self._pool(ticket.lane)
        pool.waiting.remove(ticket)
        ticket.state = "withdrawn"
        self._wake([ticket, *pool.waiting])
        self.pump()
        return True

    def release(self, ticket: Ticket) -> None:
        """The run ended: free its slot, or withdraw it if it never started. Idempotent."""
        if ticket.waiting:
            self.withdraw(ticket)
            return
        if ticket.running:
            self._pool(ticket.lane).running.remove(ticket)
            ticket.state = "done"
            self._wake([ticket])
            self.pump()

    def next_change_at(self, now: float) -> float:
        """The next time a waiting entry's fate can change without any call: an expiry or a window opening."""
        times = [math.inf]
        for pool in self._pools.values():
            if not pool.waiting:
                continue
            times += [entry.enqueued_at + self.max_wait_s for entry in pool.waiting]
            self._trim(pool, now)
            limits = pool.limits
            if (
                len(pool.running) < limits.concurrency
                and limits.per_minute is not None
                and len(pool.starts) >= limits.per_minute
            ):
                times.append(pool.starts[0] + self.window_s)
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

    def _pool(self, lane: Lane) -> _Pool:
        pool = self._pools.get(LANE_LIMITS[lane])
        if pool is None:
            raise ValueError(f"this queue has no {lane} lane")
        return pool

    def _trim(self, pool: _Pool, now: float) -> None:
        while pool.starts and now - pool.starts[0] >= self.window_s:
            pool.starts.popleft()

    def _can_start(self, pool: _Pool, now: float) -> bool:
        self._trim(pool, now)
        limits = pool.limits
        rate_ok = limits.per_minute is None or len(pool.starts) < limits.per_minute
        return len(pool.running) < limits.concurrency and rate_ok

    def _pump(self, now: float) -> None:
        # An entry past its maximum wait never starts, however late the pump that finds
        # it; one whose turn comes at the very moment its wait runs out starts rather
        # than leaving with `capacity`. So: expire the overdue, start, expire the due.
        # Each lane's limits are evaluated on their own: one lane never waits for another.
        for pool in self._pools.values():
            expired = self._expire(pool, lambda waited: waited > self.max_wait_s, now)
            started: list[Ticket] = []
            while pool.waiting and self._can_start(pool, now):
                entry = pool.waiting.pop(0)
                entry.state, entry.started_at = "running", now
                pool.running.append(entry)
                pool.starts.append(now)
                started.append(entry)
            expired += self._expire(pool, lambda waited: waited >= self.max_wait_s, now)
            if expired or started:
                self._wake([*expired, *started, *pool.waiting])

    @staticmethod
    def _expire(pool: _Pool, past: Callable[[float], bool], now: float) -> list[Ticket]:
        expired = [entry for entry in pool.waiting if past(now - entry.enqueued_at)]
        for entry in expired:
            pool.waiting.remove(entry)
            entry.state = "expired"
        return expired

    @staticmethod
    def _wake(tickets: Iterable[Ticket]) -> None:
        for entry in tickets:
            entry.changed.set()
