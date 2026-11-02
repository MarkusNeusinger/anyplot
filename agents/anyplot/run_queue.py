"""The run queue: the memory, rate and cost limiter of one instance, in front of the sandbox runs.

Only sandbox work enters it (owner decision of 2026-10-14): a chat turn starts at once,
and the turn takes an entry only when its root calls `plot_pipeline` or `run_data_code`
(`agents/main.py`, `TurnSlot`). The turn holds that entry until it ends, so a second
sandbox run in the same turn neither waits again nor books a second start. A plain
answer, a refusal, `prepare_data` or `generate_data` never touches the queue. An entry
runs when both limits allow it, in the order of its lane and then its arrival:

* **Concurrency.** At most `AGENT_RUN_CONCURRENCY` runs are in flight in the whole
  instance, every lane together (default 5 since 2026-11-01, 1 before). A run spends most
  of its time in model calls, which wait on the network; its renders go to the renderer
  service through the instance's one render slot (`render/serial.py`).
* **Rate.** A run may start only while fewer than `AGENT_RUNS_PER_MINUTE` runs started in
  the last 60 seconds (a sliding window of start times), and since 2026-11-01 at least
  `60 / AGENT_RUNS_PER_MINUTE` seconds after the previous start (`start_gap_s`): at the
  default of 6, one start every 10 seconds (owner decision of 2026-11-01, "1 start every
  10 s"). The window alone would let a fan-out start five runs at once, whose renders then
  meet in the one render slot (24 s of waiting at the 95th percentile in the measurement
  of 2026-11-01); the gap spreads them.

The queue holds at most `capacity = AGENT_RUNS_PER_MINUTE * AGENT_QUEUE_MAX_WAIT_S / 60`
waiting entries (60 at the defaults): a new entry that would stand at a position past
it would wait longer than the maximum, so `submit` refuses it with `QueueFull`, which
the route answers as `503 capacity`. An entry that can start at once never waits and
is accepted even when `capacity` is 0. An entry that waited `AGENT_QUEUE_MAX_WAIT_S`
leaves with `QueueTimeout`, which the stream ends as `error{code:"capacity"}`; an
entry whose turn comes at that very moment starts instead. Every waiting entry holds an
open stream, so the instance's Cloud Run concurrency (`agents/cloudbuild.yaml`) covers
the capacity, the runs in flight and the other routes.

The capacity is the owner's formula (2026-10-09) and assumes that runs end within the
time their starts take: at one run in flight and one start a minute, ten accepted
entries and 90-second runs, the last four wait the full maximum and leave with
`capacity`. Admission therefore promises a place, not a start. A run holds its slot
until its turn ends, the root's closing reply included.

**Lanes** (owner decision of 2026-11-01). An entry carries a lane. Every lane shares the
concurrency, the rate and the capacity above; the lanes differ in their per-user cap and
their order:

* `normal`, every user who is not an admin, today and after the public launch:
  `AGENT_USER_MAX_RUNS` entries per user (default 2 since 2026-11-01, 3 before).
* `admin`, the admin's runs, the fan-out over every library (`.plot_all()`) above all:
  `AGENT_ADMIN_USER_MAX_RUNS` entries per admin (default 5), in the order of arrival
  with the `normal` entries. The admin's other exemptions (no per-user day caps, no
  message minute) live in the usage book (`plugins/ledger.py`).
* `premium` goes before every `normal` and `admin` entry, under the `normal` lane's
  per-user cap. Nothing sets it yet; it is the lane for users who later pay for their own
  tokens. The concurrency and rate limits bind it too, and its position counts only the
  entries ahead of it, so it can push other entries past the maximum wait.

The route picks the lane from the tier the BFF asserts for the caller (`X-Anyplot-Tier`,
`agents/main.py` `caller_tier`), never from anything the browser sets.

**Per user.** A user may hold at most their lane's per-user cap of entries, waiting and
running together, across all their sessions (owner decision of 2026-10-21: each browser
window is a session of its own, and a user's windows work in parallel, so the cap
bounds what one user puts into the shared queue). `submit` refuses one more with
`QueueUserLimit`, which the route ends as `error{code:"run_limit"}`, before it looks at
the queue's length: a user at the cap learns that from their own runs, not from
`capacity`. The cap is checked in `submit` because the queue already holds every entry
with its user; it changes neither the queue's capacity nor its order, and an entry the
cap refuses never took a place, a start or a position.

**Waiting.** `wait(ticket)` is an async generator that yields the entry's
`QueuePosition` at once, on every change of its position or of the queue length, and
again every `heartbeat_s` while nothing changes, so a quiet stream stays alive behind
proxies; it returns when the entry may run. Leaving it early (the consumer was
cancelled, for example when the client disconnected) withdraws a still-waiting
entry, so an abandoned entry never holds a place. A running entry holds its slot
until `release`: the route releases it when the run ends, and the run registry's
stale sweep releases one whose stream vanished.

The clock is injectable, and time-based changes (the rate window opening, the start gap
passing, an entry expiring) are evaluated on every `pump`, so tests advance a fake clock
and call `pump()` instead of sleeping. One asyncio loop drives everything; nothing is
locked. No ADK import.
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
LANE_PRIORITY: dict[str, int] = {"premium": 0, "normal": 1, "admin": 1}
"""Lower runs first; within the same priority, the earlier arrival runs first."""
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
    """Where a waiting entry stands: `position` 1 runs next; `waiting` counts every entry, this one included."""

    position: int
    waiting: int


@dataclass(eq=False)
class Ticket:
    """One queue entry: a run that waits, runs, or has left the queue.

    `submitted_position` is where the entry stood when it was submitted, 0 when it started at once: the usage
    telemetry's `queue_position` (`pipeline_run`), never a user id or anything that names one.
    """

    user: str
    session_id: str
    lane: Lane
    seq: int
    enqueued_at: float
    state: TicketState = "waiting"
    started_at: float | None = None
    submitted_position: int = 0
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

    @property
    def waited_s(self) -> float | None:
        """Seconds from submit to start, 0 for an entry that started at once; None before it started."""
        return None if self.started_at is None else self.started_at - self.enqueued_at


class RunQueue:
    """A FIFO of runs under a concurrency limit, a sliding-window rate limit, a minimum gap between starts, and a
    per-user cap per lane."""

    def __init__(
        self,
        *,
        concurrency: int,
        per_minute: int,
        max_wait_s: float,
        clock: Callable[[], float] = time.monotonic,
        window_s: float = RATE_WINDOW_S,
        per_user: int | None = None,
        admin_per_user: int | None = None,
        start_gap_s: float = 0.0,
    ) -> None:
        if concurrency < 1 or per_minute < 1 or max_wait_s <= 0 or window_s <= 0:
            raise ValueError("concurrency, rate, maximum wait and window must be positive")
        if any(cap is not None and cap < 1 for cap in (per_user, admin_per_user)):
            raise ValueError("the per-user cap must be positive")
        if start_gap_s < 0:
            raise ValueError("the start gap must not be negative")
        self.concurrency = concurrency
        self.per_minute = per_minute
        self.max_wait_s = max_wait_s
        self.window_s = window_s
        self.per_user = per_user
        """Entries one user may hold in the `normal` and `premium` lanes, waiting and running (`AGENT_USER_MAX_RUNS`);
        None sets no cap."""
        self.admin_per_user = admin_per_user
        """Entries one admin may hold in the `admin` lane (`AGENT_ADMIN_USER_MAX_RUNS`); None sets no cap."""
        self.start_gap_s = start_gap_s
        """The least seconds between two starts, every lane together (`60 / AGENT_RUNS_PER_MINUTE` from the
        settings); 0 leaves only the window."""
        self._clock = clock
        self._waiting: list[Ticket] = []
        self._running: list[Ticket] = []
        self._starts: deque[float] = deque()
        self._last_start = -math.inf
        self._seq = itertools.count(1)

    @classmethod
    def from_settings(cls, settings: AgentSettings, clock: Callable[[], float] = time.monotonic) -> Self:
        return cls(
            concurrency=settings.run_concurrency,
            per_minute=settings.runs_per_minute,
            max_wait_s=settings.queue_max_wait_s,
            clock=clock,
            per_user=settings.user_max_runs,
            admin_per_user=settings.admin_user_max_runs,
            start_gap_s=RATE_WINDOW_S / settings.runs_per_minute,
        )

    def now(self) -> float:
        """The queue's clock, which the run registry shares so its stale check measures the same time."""
        return self._clock()

    def user_cap(self, lane: Lane) -> int | None:
        """The entries one user may hold when they submit in `lane`; None sets no cap."""
        return self.admin_per_user if lane == "admin" else self.per_user

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

    def user_entries(self, user: str) -> int:
        """The user's entries in the queue, waiting and running, in every session."""
        return sum(1 for entry in (*self._waiting, *self._running) if entry.user == user)

    def submit(self, user: str, session_id: str, lane: Lane = "normal") -> Ticket:
        """Queue a run, or start it at once.

        Raises `QueueUserLimit` when the user already holds their lane's cap of entries (checked first), and
        `QueueFull` when the run would wait past the maximum.
        """
        now = self._clock()
        self._pump(now)  # an entry that expired just now no longer counts against its user
        cap = self.user_cap(lane)
        if cap is not None and self.user_entries(user) >= cap:
            raise QueueUserLimit(f"the user already holds {cap} entries")
        ticket = Ticket(user=user, session_id=session_id, lane=lane, seq=next(self._seq), enqueued_at=now)
        position = 1 + sum(1 for other in self._waiting if other.order < ticket.order)
        if position > self.capacity and not (position == 1 and self._can_start(now)):
            raise QueueFull(f"position {position} is past the queue's capacity of {self.capacity}")
        self._waiting.append(ticket)
        self._waiting.sort(key=lambda entry: entry.order)
        self._wake(self._waiting)
        self._pump(now)
        if ticket.waiting:
            ticket.submitted_position = position
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
        """The next time a waiting entry's fate can change without any call: an expiry, the window opening or the
        start gap passing."""
        if not self._waiting:
            return math.inf
        times = [entry.enqueued_at + self.max_wait_s for entry in self._waiting]
        self._trim(now)
        if len(self._running) < self.concurrency:
            if len(self._starts) >= self.per_minute:
                times.append(self._starts[0] + self.window_s)
            if now - self._last_start < self.start_gap_s:
                times.append(self._last_start + self.start_gap_s)
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
        return (
            len(self._running) < self.concurrency
            and len(self._starts) < self.per_minute
            and now - self._last_start >= self.start_gap_s
        )

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
            self._last_start = now
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
