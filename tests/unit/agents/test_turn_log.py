"""The turn log: numbered events, a reader that replays and follows, and a stream that ends the log however it ends."""

import asyncio
from collections.abc import AsyncGenerator

import pytest

from agents.turn_log import PING, TurnLog, logged, parse_event_id


RUN = "0123456789abcdef"


def event(name: str) -> str:
    return f"event: {name}\ndata: {{}}\n\n"


async def collect(reader: AsyncGenerator[str, None]) -> list[str]:
    return [chunk async for chunk in reader]


def test_events_are_numbered_from_one_and_comments_pass_unkept() -> None:
    log = TurnLog(RUN)

    assert log.add(event("ready")) == f"id: {RUN}.1\nevent: ready\ndata: {{}}\n\n"
    assert log.add(PING) == PING
    assert log.add(event("done")).startswith(f"id: {RUN}.2\n")
    assert len(log.events) == 2


async def test_a_reader_gets_the_events_after_the_one_it_names() -> None:
    log = TurnLog(RUN)
    for name in ("ready", "status", "plot", "done"):
        log.add(event(name))
    log.end()

    assert await collect(log.follow(2, heartbeat_s=1)) == log.events[2:]
    assert await collect(log.follow(4, heartbeat_s=1)) == []
    assert await collect(log.follow(0, heartbeat_s=1)) == log.events


async def test_a_reader_follows_the_turn_live_until_its_stream_ends() -> None:
    log = TurnLog(RUN)
    log.add(event("ready"))
    reader = asyncio.create_task(collect(log.follow(1, heartbeat_s=5)))
    await asyncio.sleep(0)
    log.add(event("status"))
    await asyncio.sleep(0)
    log.add(event("plot"))
    log.add(event("done"))
    log.end()

    assert await asyncio.wait_for(reader, 2) == log.events[1:]


async def test_a_quiet_turn_pings_its_reader() -> None:
    log = TurnLog(RUN)
    log.add(event("ready"))
    chunks: list[str] = []

    async def read() -> None:
        async for chunk in log.follow(1, heartbeat_s=0.01):
            chunks.append(chunk)

    reader = asyncio.create_task(read())
    while PING not in chunks:
        await asyncio.sleep(0.01)
    log.add(event("done"))
    log.end()
    await asyncio.wait_for(reader, 2)

    assert chunks[-1] == log.events[-1] and set(chunks[:-1]) == {PING}


async def test_closing_the_stream_closes_the_turn_and_ends_the_log() -> None:
    """The client went: the turn's own generator is closed as without the log (its cleanup runs), and the log ends."""
    log = TurnLog(RUN)
    cleaned = asyncio.Event()

    async def turn() -> AsyncGenerator[str, None]:
        try:
            yield event("ready")
            yield event("status")
            await asyncio.Event().wait()  # a step that never ends on its own
            yield event("done")
        finally:
            cleaned.set()

    stream = logged(turn(), log)
    assert await anext(stream) == log.events[0]
    await stream.aclose()

    assert cleaned.is_set() and log.ended and len(log.events) == 1
    assert await collect(log.follow(1, heartbeat_s=1)) == []  # a reader of a cut turn simply ends


async def test_a_cancelled_stream_cancels_the_turn_and_ends_the_log() -> None:
    log = TurnLog(RUN)
    cancelled = asyncio.Event()

    async def turn() -> AsyncGenerator[str, None]:
        yield event("ready")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise
        yield event("done")

    async def consume() -> None:
        async for _ in logged(turn(), log):
            pass

    task = asyncio.create_task(consume())
    while not log.events:
        await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert cancelled.is_set() and log.ended


@pytest.mark.parametrize(
    ("value", "parsed"),
    [
        (f"{RUN}.0", (RUN, 0)),
        (f"{RUN}.12", (RUN, 12)),
        ("0123456789ABCDEF.1", None),  # the service writes lower-case hex only
        (f"{RUN}.", None),
        (f"{RUN}.1234567", None),
        (f"{RUN}.1\n", None),
        ("r1.1", None),
    ],
)
def test_an_event_id_is_one_this_service_wrote(value: str, parsed: tuple[str, int] | None) -> None:
    assert parse_event_id(value) == parsed
