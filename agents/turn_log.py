"""The latest chat turn of each session, kept so a page whose stream was cut can read the rest of it.

A turn's stream (`POST /v1/sessions/{sid}/messages`) gives every event the SSE id `<run_id>.<n>`: the
turn's `run_id` (the `ready` event's, 16 hex digits) and the event's number in the turn, from 1 for
`ready`. The session keeps the numbered events of its latest turn (`Runtime.turns`), and
`GET /v1/sessions/{sid}/turn` with `Last-Event-ID: <run_id>.<n>` streams the events after `n`, then
follows the turn live until it ends. A connection the browser loses between itself and the edge
proxy (an HTTP/3 error, say) is invisible to the origin, which runs the turn to its end and stores
its plot; the page reads the rest of the turn from here instead of showing an error while a plot
exists, and never asks for the same plot a second time.

The log only records: the turn still ends when its own stream ends, so a client that goes cancels
the run as before, and a reader of the log never holds or stops it. A log whose stream ended
without `done` (the client went) simply ends; the BFF closes such a read with `error` and `done`.

Bounded by the turn: one turn's events (its steps, at most `MAX_ATTEMPTS` rounds, the queue's
positions while it waits, one plot, one reply, one `done` within `MAX_DONE_EVENT_CHARS`), one turn
per session, replaced by the session's next turn and dropped with the session.
"""

import asyncio
import contextlib
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field


PING = ": ping\n\n"
"""An SSE comment: bytes on the wire while nothing happens, which every reader ignores."""
RUN_ID_PATTERN = r"[0-9a-f]{16}"
"""A turn's `run_id` (`secrets.token_hex(8)` in the messages route)."""
EVENT_ID_PATTERN = rf"^{RUN_ID_PATTERN}\.[0-9]{{1,6}}$"
"""The `Last-Event-ID` a resume names: the run and the number of the last event the page read."""
EVENT_ID = re.compile(rf"^({RUN_ID_PATTERN})\.([0-9]{{1,6}})$")


@dataclass(eq=False)
class TurnLog:
    """One turn's numbered events, in order, and whether its stream has ended."""

    run_id: str
    events: list[str] = field(default_factory=list)
    ended: bool = False
    _changed: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def add(self, chunk: str) -> str:
        """`chunk`, one SSE event, with its id, kept for a later reader; a comment passes unnumbered and unkept."""
        if chunk.startswith(":"):
            return chunk
        stamped = f"id: {self.run_id}.{len(self.events) + 1}\n{chunk}"
        self.events.append(stamped)
        self._notify()
        return stamped

    def end(self) -> None:
        self.ended = True
        self._notify()

    def _notify(self) -> None:
        # A fresh event per change: a reader waits on the one it saw, so it never misses a change between two waits.
        self._changed.set()
        self._changed = asyncio.Event()

    async def follow(self, after: int, *, heartbeat_s: float) -> AsyncGenerator[str, None]:
        """The events after number `after`, then each new one as it comes, until the turn's stream has ended.

        A `PING` after every `heartbeat_s` without an event, so a quiet step keeps every hop of the read busy.
        """
        index = after
        while True:
            while index < len(self.events):
                yield self.events[index]
                index += 1
            if self.ended:
                return
            # No await between the checks above and this read: a change after them sets the event taken here.
            changed = self._changed
            try:
                # The timeout wraps the wait only, never a yield (PEP 789).
                async with asyncio.timeout(heartbeat_s):
                    await changed.wait()
            except TimeoutError:
                yield PING


async def logged(chunks: AsyncGenerator[str, None], log: TurnLog) -> AsyncGenerator[str, None]:
    """`chunks`, a turn's stream, with every event numbered and kept in `log`.

    Closing or cancelling this stream closes or cancels `chunks` the same way, so the turn ends as it would
    without the log; the log ends with the stream, however the stream ends.
    """
    try:
        async with contextlib.aclosing(chunks) as source:
            async for chunk in source:
                yield log.add(chunk)
    finally:
        log.end()


def parse_event_id(value: str) -> tuple[str, int] | None:
    """`(run_id, n)` of a `Last-Event-ID`, or None when it is not one this service wrote."""
    match = EVENT_ID.fullmatch(value)
    return (match[1], int(match[2])) if match else None
