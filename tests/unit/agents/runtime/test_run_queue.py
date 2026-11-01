"""Tests for agents/anyplot/run_queue.py: order, the limits, the rate window, waiting and leaving.

Time is a fake clock that the tests advance; a `pump()` (or any queue call) evaluates
the new time, so no test sleeps for the rate window or the maximum wait.
"""

import asyncio

import pytest

from agents.anyplot.run_queue import (
    HEARTBEAT_S,
    QueueFull,
    QueuePosition,
    QueueTimeout,
    QueueUserLimit,
    QueueWithdrawn,
    RunQueue,
    Ticket,
)
from agents.anyplot.settings import AgentSettings


class Clock:
    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> Clock:
    return Clock()


def make(clock: Clock, *, concurrency: int = 1, per_minute: int = 1_000, max_wait_s: float = 600) -> RunQueue:
    return RunQueue(concurrency=concurrency, per_minute=per_minute, max_wait_s=max_wait_s, clock=clock)


async def settle() -> None:
    """Let every ready task run until it waits again; no time passes."""
    for _ in range(10):
        await asyncio.sleep(0)


async def collect(queue: RunQueue, ticket: Ticket, into: list[QueuePosition]) -> None:
    async for position in queue.wait(ticket):
        into.append(position)


class TestOrder:
    def test_first_come_first_served_one_at_a_time(self, clock: Clock) -> None:
        queue = make(clock)
        a, b, c = (queue.submit(user, f"s-{user}") for user in ("a", "b", "c"))

        assert (a.running, b.waiting, c.waiting) == (True, True, True)
        queue.release(a)
        assert (b.running, c.waiting) == (True, True)
        queue.release(b)
        assert c.running and queue.in_flight == 1 and queue.waiting_count == 0

    def test_concurrency_one_holds_the_second_run(self, clock: Clock) -> None:
        queue = make(clock)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")

        assert (queue.in_flight, queue.waiting_count) == (1, 1)
        assert queue.position(b) == QueuePosition(position=1, waiting=1)

    def test_concurrency_two_runs_two(self, clock: Clock) -> None:
        queue = make(clock, concurrency=2)
        tickets = [queue.submit(user, f"s-{user}") for user in ("a", "b", "c")]

        assert [ticket.state for ticket in tickets] == ["running", "running", "waiting"]

    def test_premium_goes_before_every_normal_entry(self, clock: Clock) -> None:
        queue = make(clock)
        first = queue.submit("a", "s-a")
        normal_1 = queue.submit("n1", "s-n1")
        normal_2 = queue.submit("n2", "s-n2")
        premium_1 = queue.submit("p1", "s-p1", lane="premium")
        premium_2 = queue.submit("p2", "s-p2", lane="premium")

        positions = [queue.position(ticket) for ticket in (premium_1, premium_2, normal_1, normal_2)]
        assert [position.position for position in positions if position] == [1, 2, 3, 4]
        queue.release(first)
        assert premium_1.running and normal_1.waiting


class TestRate:
    def test_a_run_starts_only_when_the_window_allows(self, clock: Clock) -> None:
        queue = make(clock, concurrency=2, per_minute=1)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")

        assert b.waiting  # a slot is free, but one run already started in the last 60 s
        clock.advance(59.9)
        queue.pump()
        assert b.waiting
        clock.advance(0.1)
        queue.pump()
        assert b.running

    def test_the_window_counts_starts_not_runs(self, clock: Clock) -> None:
        queue = make(clock, per_minute=1)
        a = queue.submit("a", "s-a")
        queue.release(a)

        b = queue.submit("b", "s-b")

        assert b.waiting and queue.in_flight == 0
        assert queue.next_change_at(clock()) == clock() + 60

    def test_next_change_at_without_a_time_bound(self, clock: Clock) -> None:
        queue = make(clock, max_wait_s=600)
        assert queue.next_change_at(clock()) == float("inf")
        queue.submit("a", "s-a")
        queue.submit("b", "s-b")  # waits for the slot, not for time: only its expiry is time-bound

        assert queue.next_change_at(clock()) == clock() + 600


class TestCapacity:
    def test_the_defaults_hold_sixty_waiting_entries(self) -> None:
        """Owner decision of 2026-11-01: five in flight, one start every 10 s, so 6 a minute times 600 s / 60."""
        queue = RunQueue.from_settings(AgentSettings())

        assert (queue.concurrency, queue.per_minute, queue.max_wait_s, queue.capacity) == (5, 6, 600, 60)
        assert queue.start_gap_s == 10

    def test_a_full_queue_refuses_a_new_entry(self, clock: Clock) -> None:
        queue = make(clock, per_minute=1, max_wait_s=120)  # two entries wait at most two minutes
        queue.submit("a", "s-a")
        queue.submit("b", "s-b")
        queue.submit("c", "s-c")

        with pytest.raises(QueueFull):
            queue.submit("d", "s-d")
        assert queue.waiting_count == 2

    def test_an_entry_that_starts_at_once_is_never_refused(self, clock: Clock) -> None:
        queue = make(clock, per_minute=1, max_wait_s=30)  # capacity 0: nobody may wait

        first = queue.submit("a", "s-a")

        assert queue.capacity == 0 and first.running
        with pytest.raises(QueueFull):
            queue.submit("b", "s-b")

    def test_a_premium_entry_counts_only_the_entries_ahead_of_it(self, clock: Clock) -> None:
        queue = make(clock, per_minute=1, max_wait_s=120)
        queue.submit("a", "s-a")
        queue.submit("b", "s-b")
        queue.submit("c", "s-c")

        premium = queue.submit("p", "s-p", lane="premium")

        assert queue.position(premium) == QueuePosition(position=1, waiting=3)


class TestPerUser:
    """`AGENT_USER_MAX_RUNS`: a user's entries, waiting and running, across their sessions (2026-10-21)."""

    def test_the_default_caps_are_two_and_five_for_an_admin(self) -> None:
        queue = RunQueue.from_settings(AgentSettings())

        assert (queue.user_cap("normal"), queue.user_cap("premium"), queue.user_cap("admin")) == (2, 2, 5)

    def test_the_fourth_entry_of_a_user_is_refused_and_another_user_still_queues(self, clock: Clock) -> None:
        queue = RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600, clock=clock, per_user=3)
        mine = [queue.submit("u", f"s-{window}") for window in range(3)]  # one running, two waiting

        with pytest.raises(QueueUserLimit):
            queue.submit("u", "s-4")
        other = queue.submit("v", "s-v")

        assert [ticket.state for ticket in mine] == ["running", "waiting", "waiting"]
        assert other.waiting and queue.position(other) == QueuePosition(position=3, waiting=3)
        assert queue.user_entries("u") == 3 and queue.user_entries("v") == 1

    def test_the_cap_is_checked_before_the_queue_length(self, clock: Clock) -> None:
        """A user at their cap learns that from their own runs, even when the queue is full too."""
        queue = RunQueue(concurrency=1, per_minute=1, max_wait_s=60, clock=clock, per_user=2)  # capacity 1
        queue.submit("u", "s-1")
        queue.submit("u", "s-2")

        with pytest.raises(QueueUserLimit):
            queue.submit("u", "s-3")
        with pytest.raises(QueueFull):
            queue.submit("v", "s-v")

    def test_a_released_withdrawn_or_expired_entry_frees_its_place(self, clock: Clock) -> None:
        queue = RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600, clock=clock, per_user=3)
        first, second, third = (queue.submit("u", f"s-{window}") for window in range(3))

        queue.release(first)  # the second starts in its place
        assert queue.submit("u", "s-3").waiting  # the run that ended no longer counts
        queue.withdraw(third)
        assert queue.submit("u", "s-4").waiting  # nor does a cancelled wait
        clock.advance(600)
        queue.pump()  # every waiting entry expired; the running one still holds its place
        assert queue.user_entries("u") == 1 and second.running
        assert queue.submit("u", "s-5").waiting and queue.user_entries("u") == 2

    def test_without_a_cap_a_user_may_hold_any_number(self, clock: Clock) -> None:
        queue = make(clock)
        for window in range(5):
            queue.submit("u", f"s-{window}")

        assert queue.per_user is None and queue.user_entries("u") == 5


def production(clock: Clock) -> RunQueue:
    """The queue at the production defaults (owner decision of 2026-11-01): 5 in flight, one start every 10 s,
    60 waiting entries, 2 runs per public user and 5 per admin."""
    return RunQueue.from_settings(AgentSettings(), clock=clock)


class TestStartGap:
    """`AGENT_RUNS_PER_MINUTE` 6 spaces the starts 10 s apart: a fan-out's runs never start, or render, together."""

    def test_starts_are_spaced_by_the_gap_even_with_free_slots(self, clock: Clock) -> None:
        queue = production(clock)
        first, second, third = (queue.submit(user, f"s-{user}") for user in ("a", "b", "c"))

        assert (first.running, second.waiting, third.waiting) == (True, True, True)
        assert queue.next_change_at(clock()) == clock() + 10
        clock.advance(10)
        queue.pump()
        assert second.running and third.waiting
        clock.advance(9.9)
        queue.pump()
        assert third.waiting
        clock.advance(0.1)
        queue.pump()
        assert third.running and queue.in_flight == 3

    def test_without_a_gap_the_window_alone_decides(self, clock: Clock) -> None:
        queue = make(clock, concurrency=3)

        tickets = [queue.submit(user, f"s-{user}") for user in ("a", "b", "c")]

        assert queue.start_gap_s == 0 and all(ticket.running for ticket in tickets)

    def test_the_gap_is_refused_below_zero(self, clock: Clock) -> None:
        with pytest.raises(ValueError):
            RunQueue(concurrency=1, per_minute=1, max_wait_s=600, clock=clock, start_gap_s=-1)


class TestLanes:
    """The admin lane (owner decision of 2026-11-01): the same concurrency, rate and order as everyone, a cap of 5."""

    def test_the_admin_lane_shares_the_concurrency_and_the_rate(self, clock: Clock) -> None:
        queue = production(clock)
        public = queue.submit("u", "s-u")
        admin = [queue.submit("admin", f"s-{index}", lane="admin") for index in range(5)]

        for _ in range(4):
            clock.advance(10)
            queue.pump()

        assert public.running and [ticket.state for ticket in admin] == ["running"] * 4 + ["waiting"]
        clock.advance(10)
        queue.pump()
        assert admin[-1].waiting  # five in flight: the gap passed, but no slot is free
        queue.release(public)
        assert admin[-1].running and queue.in_flight == 5

    def test_each_lane_has_its_own_per_user_cap(self, clock: Clock) -> None:
        queue = production(clock)
        public = [queue.submit("u", f"s-u{index}") for index in range(2)]
        admin = [queue.submit("admin", f"s-a{index}", lane="admin") for index in range(5)]

        with pytest.raises(QueueUserLimit):
            queue.submit("u", "s-u2")
        with pytest.raises(QueueUserLimit):
            queue.submit("admin", "s-a5", lane="admin")
        assert len(public) == 2 and len(admin) == 5 and queue.user_entries("admin") == 5

    def test_premium_goes_first_and_admin_keeps_its_arrival_order(self, clock: Clock) -> None:
        queue = make(clock)
        queue.submit("x", "s-x")
        normal = queue.submit("n", "s-n")
        admin = queue.submit("admin", "s-a", lane="admin")
        premium = queue.submit("p", "s-p", lane="premium")

        positions = [queue.position(ticket) for ticket in (premium, normal, admin)]
        assert [position.position for position in positions if position] == [1, 2, 3]

    def test_the_admin_entry_records_where_it_stood_and_how_long_it_waited(self, clock: Clock) -> None:
        """The usage telemetry's `queue_position` and `queue_wait_ms` (`pipeline_run`): numbers, never a user."""
        queue = production(clock)
        first = queue.submit("u", "s-u")
        second = queue.submit("admin", "s-a", lane="admin")

        assert (first.submitted_position, first.waited_s) == (0, 0.0)
        assert (second.submitted_position, second.waited_s) == (1, None)
        clock.advance(10)
        queue.pump()
        assert second.waited_s == 10


class TestFanOut:
    """The owner's check of 2026-11-01: a 15-library fan-out never loses a library to `capacity` or `run_limit`."""

    @staticmethod
    def fan_out(queue: RunQueue, clock: Clock, *, libraries: int = 15, others: int = 0) -> tuple[int, int, float]:
        """The page's pool (`FanOut.tsx`): one admin keeps `user_max_runs` libraries submitted, a new one each time a
        run ends; each run takes 60 to 240 s once it starts. `others` public users submit two runs each at the
        start. Returns the libraries started, the refusals, and the minutes until the last run ended."""
        durations = [60 + (index * 37) % 181 for index in range(libraries)]  # 60 to 240 s, spread
        cap = queue.user_cap("admin") or libraries
        for user in range(others):
            for run in range(2):
                queue.submit(f"public-{user}", f"s-p{user}-{run}")
        pending, live, started, refused, start = list(range(libraries)), {}, 0, 0, clock()
        while pending or live:
            while pending and len(live) < cap:
                library = pending.pop(0)
                try:
                    live[library] = queue.submit("admin", f"s-{library}", lane="admin")
                except QueueFull, QueueUserLimit:
                    refused += 1
            clock.advance(1)
            queue.pump()
            for library, ticket in list(live.items()):
                if ticket.state == "expired":
                    refused += 1
                    del live[library]
                elif ticket.running and clock() - (ticket.started_at or 0) >= durations[library]:
                    started += 1
                    queue.release(ticket)
                    del live[library]
            for entry in list(queue._running):  # the public runs end after 120 s
                if entry.user.startswith("public") and clock() - (entry.started_at or 0) >= 120:
                    queue.release(entry)
        return started, refused, (clock() - start) / 60

    def test_fifteen_libraries_of_one_admin_all_start_and_none_is_refused(self, clock: Clock) -> None:
        started, refused, minutes = self.fan_out(production(clock), clock)

        assert (started, refused) == (15, 0)
        assert minutes < 10  # five at a time, one start every 10 s: about three rounds of runs

    def test_the_fanout_still_loses_nothing_beside_public_users(self, clock: Clock) -> None:
        """Three public users hold six runs when the fan-out starts: the admin's entries wait, none is refused."""
        started, refused, _ = self.fan_out(production(clock), clock, others=3)

        assert (started, refused) == (15, 0)


class TestMaxWait:
    def test_an_entry_expires_at_the_maximum_wait(self, clock: Clock) -> None:
        queue = make(clock, max_wait_s=600)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")

        clock.advance(599.9)
        queue.pump()
        assert b.waiting
        clock.advance(0.1)
        queue.pump()
        assert b.state == "expired" and queue.waiting_count == 0

    def test_an_entry_whose_turn_comes_as_its_wait_runs_out_starts(self, clock: Clock) -> None:
        """The last of a full queue at instant runs: its start and its expiry fall on the same pump."""
        queue = make(clock, per_minute=1, max_wait_s=600)
        running = queue.submit("r", "s-r")
        entries = [queue.submit(f"u{index}", f"s-u{index}") for index in range(1, 11)]

        queue.release(running)
        for entry in entries[:-1]:
            clock.advance(60)
            queue.pump()
            assert entry.running
            queue.release(entry)
        clock.advance(60)  # t = 600: the window opens just as the last entry waited the maximum
        queue.pump()

        assert entries[-1].running and queue.waiting_count == 0

    def test_runs_longer_than_the_window_push_accepted_entries_past_the_maximum(self, clock: Clock) -> None:
        """The owner's capacity formula assumes runs within 60 s: admission promises a place, not a start."""
        queue = make(clock, per_minute=1, max_wait_s=600)
        running = queue.submit("r", "s-r")
        entries = [queue.submit(f"u{index}", f"s-u{index}") for index in range(1, 11)]

        current = running
        while True:
            clock.advance(90)  # every run takes 90 s
            queue.release(current)
            started = [entry for entry in entries if entry.running]
            if not started:
                break
            current = started[0]

        assert [entry.state for entry in entries].count("done") == 6
        assert [entry.state for entry in entries].count("expired") == 4

    async def test_the_waiter_ends_with_queue_timeout(self, clock: Clock) -> None:
        queue = make(clock, max_wait_s=600)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        seen: list[QueuePosition] = []
        waiter = asyncio.create_task(collect(queue, b, seen))
        await settle()

        clock.advance(600)
        queue.pump()

        with pytest.raises(QueueTimeout):
            await asyncio.wait_for(waiter, 1)
        assert seen == [QueuePosition(1, 1)]


class TestWaiting:
    async def test_positions_on_every_change_then_the_turn(self, clock: Clock) -> None:
        queue = make(clock)
        a = queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        c = queue.submit("c", "s-c")
        seen: list[QueuePosition] = []
        waiter = asyncio.create_task(collect(queue, c, seen))
        await settle()
        assert seen == [QueuePosition(2, 2)]

        queue.submit("d", "s-d")  # one more behind: the queue length changed
        await settle()
        queue.release(a)  # b runs, c moves up
        await settle()
        queue.release(b)  # c runs: the generator returns

        await asyncio.wait_for(waiter, 1)
        assert seen == [QueuePosition(2, 2), QueuePosition(2, 3), QueuePosition(1, 2)]
        assert c.running

    async def test_an_unchanged_position_is_repeated_every_heartbeat(self, clock: Clock) -> None:
        queue = make(clock)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        seen: list[QueuePosition] = []
        waiter = asyncio.create_task(collect(queue, b, seen))
        await settle()

        clock.advance(HEARTBEAT_S - 1)
        b.changed.set()  # stands in for the waiter's own timeout
        await settle()
        assert seen == [QueuePosition(1, 1)]
        clock.advance(1)
        b.changed.set()
        await settle()

        assert seen == [QueuePosition(1, 1), QueuePosition(1, 1)]
        waiter.cancel()
        await settle()
        assert b.state == "withdrawn"

    async def test_a_gone_waiter_takes_its_entry_out_of_the_queue(self, clock: Clock) -> None:
        """A client that disconnects while it waits cancels the waiter, which withdraws the entry."""
        queue = make(clock)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        c = queue.submit("c", "s-c")
        waiter = asyncio.create_task(collect(queue, b, []))
        await settle()

        waiter.cancel()
        await settle()

        assert b.state == "withdrawn"
        assert queue.position(c) == QueuePosition(1, 1)

    async def test_a_withdrawn_entry_ends_its_waiter(self, clock: Clock) -> None:
        queue = make(clock)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        waiter = asyncio.create_task(collect(queue, b, []))
        await settle()

        assert queue.withdraw(b) is True

        with pytest.raises(QueueWithdrawn):
            await asyncio.wait_for(waiter, 1)

    async def test_a_run_that_can_start_never_yields(self, clock: Clock) -> None:
        queue = make(clock)
        ticket = queue.submit("a", "s-a")
        seen: list[QueuePosition] = []

        await asyncio.wait_for(collect(queue, ticket, seen), 1)

        assert seen == [] and ticket.running


class TestRelease:
    def test_release_frees_the_slot_once(self, clock: Clock) -> None:
        queue = make(clock)
        a = queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")
        c = queue.submit("c", "s-c")

        queue.release(a)
        queue.release(a)  # a second release must not free b's slot

        assert (a.state, b.state, c.state) == ("done", "running", "waiting")

    def test_release_of_a_waiting_entry_withdraws_it(self, clock: Clock) -> None:
        queue = make(clock)
        queue.submit("a", "s-a")
        b = queue.submit("b", "s-b")

        queue.release(b)

        assert b.state == "withdrawn" and queue.waiting_count == 0 and queue.in_flight == 1

    def test_withdraw_leaves_a_running_entry_alone(self, clock: Clock) -> None:
        queue = make(clock)
        a = queue.submit("a", "s-a")

        assert queue.withdraw(a) is False and a.running

    def test_invalid_limits_are_refused(self, clock: Clock) -> None:
        with pytest.raises(ValueError):
            RunQueue(concurrency=0, per_minute=1, max_wait_s=600, clock=clock)
        with pytest.raises(ValueError):
            RunQueue(concurrency=1, per_minute=1, max_wait_s=600, clock=clock, per_user=0)
