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
    def test_the_defaults_hold_ten_waiting_entries(self) -> None:
        queue = RunQueue.from_settings(AgentSettings())

        assert (queue.concurrency, queue.per_minute, queue.max_wait_s, queue.capacity) == (1, 1, 600, 10)

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
