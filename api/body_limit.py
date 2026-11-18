"""A bound on every request body, applied before anything reads it.

FastAPI reads and parses the whole body of a route that declares a body model before a
dependency or the route's own checks run, so a size check inside a route or a dependency comes
after the bytes are already in memory. This middleware sits in front of the router instead:

- A request that declares a `Content-Length` above the cap of its path is refused unread.
- A request that declares none (a chunked body, some HTTP/2 and proxied ones) is counted as the
  application reads it. When it passes the cap, the refusal is sent from here and the
  application is told the client has gone, so it takes no more of the body.

What is bounded is what the application takes. A route that never reads its body is never
handed it, whatever its size: nothing here reads a body ahead of the application, and the
server in front keeps only its own small read buffer until the application asks.

The refusal never depends on what the application behind does with an error: a route, the
framework and an app mounted beside it (the MCP server) all meet the same end of the body, and
whatever they answer after the refusal went out is dropped.

Every path has the same small cap unless another one is named for it (`api/main.py`): by a rule
for single routes, looked at first, or by a prefix for everything under it. A route keeps any
narrower check of its own, such as the field lengths of the feedback form: this is the outer
bound, not a replacement.

A bound can also be marked `large`, for the few routes whose bodies are megabytes. Such bodies
are taken a few at a time (`LargeBodies`), so that the memory they hold together stays small
beside what the instance has. A request there has to declare its length, which settles its
place before any of it is read.

`GET`, `HEAD` and `OPTIONS` pass untouched. No route reads a body on them, and a body nobody
reads is never handed to the application.
"""

import logging
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.exceptions import public_path


# The cap of a path no prefix names. Every body outside the agent chat is a small JSON object
# (a feedback entry, an admin edit, a JSON-RPC call to the MCP server), far below this.
DEFAULT_MAX_BODY_BYTES = 64 * 1024

TOO_LARGE = "request body too large"
LENGTH_REQUIRED = "request body needs a Content-Length"
BUSY = "too many large request bodies at once; try again"

logger = logging.getLogger(__name__)

_BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_NO_STORE = {"Cache-Control": "private, no-store"}
# Python refuses to read a number of several thousand digits. A length of more digits than this
# (leading zeros aside) is above every cap anyway and needs no reading.
_MAX_INT_DIGITS = 18


class ClientGoneFilter(logging.Filter):
    """Keep a client that went away mid-body out of a logger's error records.

    The bound ends a body it cuts off the way a client that hangs up does. A library that logs
    that as its own error (the MCP server does, with a traceback) would count every refusal as
    a fault of the service. A client going away is neither.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.exc_info and isinstance(record.exc_info[1], ClientDisconnect))


class BodyCutMidAnswer(RuntimeError):
    """A body passed its bound after the application had begun to answer.

    No refusal can replace an answer that is on its way. The rest of that answer is dropped, and
    this is raised once the application returns, so the short answer is at least recorded as a
    failure and the server hangs up after it. It is not a promise that the client can tell: a
    layer outside may already have ended the answer properly on the wire. No route of this API
    answers before it has read its body, so this is the second line for one that would.
    """


def _refusal(status: int, message: str, detail: str | None, path: str) -> JSONResponse:
    """A refusal of the bound, never cached: a route's own code where it has one, else the standard shape."""
    if detail is not None:
        return JSONResponse({"detail": detail}, status_code=status, headers=_NO_STORE)
    return JSONResponse(
        {"status": status, "message": message, "path": public_path(path)}, status_code=status, headers=_NO_STORE
    )


@dataclass(frozen=True)
class Bound:
    """The cap of the paths under a prefix or a rule, and how a body above it is answered there.

    `detail` is for routes whose clients read errors by a code of their own: the refusal is then
    `{"detail": <detail>}`, the shape those routes answer with themselves. Without it the refusal
    has the API's standard error shape (`api/exceptions.py`).

    `large` marks routes whose bodies are taken a few at a time (`LargeBodies`). A request there
    has to declare its length; `length_detail` and `busy_detail` are the codes of the two answers
    that follow from it, for the same clients as `detail`.
    """

    max_bytes: int
    detail: str | None = None
    large: bool = False
    length_detail: str | None = None
    busy_detail: str | None = None

    def refusal(self, path: str) -> JSONResponse:
        """The 413 of a body above this bound."""
        return _refusal(413, TOO_LARGE, self.detail, path)

    def length_required(self, path: str) -> JSONResponse:
        """The 411 of a body that declares no length where one is needed."""
        return _refusal(411, LENGTH_REQUIRED, self.length_detail, path)

    def busy(self, path: str) -> JSONResponse:
        """The 503 of a large body that found no place free."""
        return _refusal(503, BUSY, self.busy_detail, path)


class LargeBodies:
    """The places for large bodies in flight: at most `places` bodies above `above` bytes at once.

    A body is in memory from the moment it is read until its route has answered, and a route
    holds more than one form of it on the way: the bytes, the parsed text, what it sends on.
    Bodies of a few kilobytes do not add up to anything; bodies of megabytes do, so those are
    counted here. A body at or below `above` never needs a place.

    One process serves all requests on one event loop, so taking a place is a plain count with
    nothing awaited between the look and the step.
    """

    def __init__(self, places: int, above: int = DEFAULT_MAX_BODY_BYTES) -> None:
        if places < 1:
            raise ValueError("at least one place")
        self.places = places
        self.above = above
        self.taken = 0

    def take(self) -> bool:
        """Take a place if one is free."""
        if self.taken >= self.places:
            return False
        self.taken += 1
        return True

    def release(self) -> None:
        self.taken -= 1


def _declared_length(scope: Scope) -> int | None:
    """The `Content-Length` a request declares, or `None` without one.

    `-1` for a length nobody can go by: one that is not a plain number, and more than one header
    whose values differ. The server in front refuses those itself; this is the second line for a
    server that does not. A number of more digits than Python reads is still a length, far above
    any cap, and is answered as one.
    """
    declared = {value.strip() for name, value in scope["headers"] if name == b"content-length"}
    if not declared:
        return None
    if len(declared) > 1:
        return -1
    value = declared.pop()
    if not value.isdigit():
        return -1
    digits = value.lstrip(b"0")
    return int(digits or b"0") if len(digits) <= _MAX_INT_DIGITS else sys.maxsize


class BodyLimitMiddleware:
    """Refuse a request body above the bound of its path, before or while it is read.

    A raw ASGI middleware, like the origin gate: a refused request must cost as little as
    possible, and only at this level can the body be bounded before the framework buffers it.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        default: int = DEFAULT_MAX_BODY_BYTES,
        prefixes: Mapping[str, Bound] | None = None,
        rules: Sequence[tuple[re.Pattern[str], Bound]] = (),
        large: LargeBodies | None = None,
    ) -> None:
        self.app = app
        self.default = Bound(default)
        # Longest prefix first, so `/debug/agent` is found before a bound that `/debug` might get.
        # A prefix is kept without a trailing slash: `bound_for` adds the one that ends a segment.
        self.prefixes = sorted(
            ((prefix.rstrip("/"), bound) for prefix, bound in (prefixes or {}).items()),
            key=lambda item: len(item[0]),
            reverse=True,
        )
        self.rules = tuple(rules)
        self.large = large
        if large is None and any(bound.large for bound in self._bounds()):
            raise ValueError("a bound marked large needs the places its bodies are counted against")

    def _bounds(self) -> list[Bound]:
        return [bound for _, bound in self.rules] + [bound for _, bound in self.prefixes]

    def bound_for(self, path: str) -> Bound:
        """The bound of a path: that of the first rule the whole path matches, else that of the
        longest named prefix it lies under, else the default."""
        for pattern, bound in self.rules:
            if pattern.fullmatch(path):
                return bound
        for prefix, bound in self.prefixes:
            if path == prefix or path.startswith(prefix + "/"):
                return bound
        return self.default

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in _BODYLESS_METHODS:
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        bound = self.bound_for(path)
        declared = _declared_length(scope)
        if declared is not None and declared < 0:
            bad_length = JSONResponse(
                {"status": 400, "message": "bad Content-Length", "path": public_path(path)},
                status_code=400,
                headers=_NO_STORE,
            )
            await bad_length(scope, receive, send)
            return
        if declared is not None and declared > bound.max_bytes:
            await bound.refusal(path)(scope, receive, send)
            return

        places = self.large if bound.large else None
        limit = bound.max_bytes
        holds_place = False
        if places is not None:
            if declared is None:
                await bound.length_required(path)(scope, receive, send)
                return
            if declared > places.above:
                if not places.take():
                    logger.warning("a large request body was refused: all %d places are taken", places.places)
                    await bound.busy(path)(scope, receive, send)
                    return
                holds_place = True
            else:
                # A body that needs no place is held to the size that needs none, whatever it sends.
                limit = places.above
        try:
            await self._bounded(scope, receive, send, bound, limit)
        finally:
            if holds_place and places is not None:
                places.release()

    async def _bounded(self, scope: Scope, receive: Receive, send: Send, bound: Bound, limit: int) -> None:
        """Hand the request to the application and count its body against `limit` as it is read."""
        path = scope["path"]
        received = 0
        cut = False
        answering = False
        mid_answer = False

        async def counted_receive() -> Message:
            nonlocal received, cut, mid_answer
            if cut:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] != "http.request":
                return message
            received += len(message.get("body", b""))
            if received <= limit:
                return message
            cut = True
            if answering:
                # An answer already on its way cannot be replaced; the body still ends here.
                mid_answer = True
            else:
                await bound.refusal(path)(scope, receive, send)
            return {"type": "http.disconnect"}

        async def guarded_send(message: Message) -> None:
            nonlocal answering
            if cut:
                # The refusal is out (or the body ended mid-answer): what the application says
                # about the body it lost goes nowhere.
                return
            if message["type"] == "http.response.start":
                answering = True
            await send(message)

        try:
            await self.app(scope, counted_receive, guarded_send)
        except Exception:
            # After the refusal the request is over. An application that fails on the body it
            # lost has nothing more to report; anything raised before the cut is a real error.
            if not cut:
                raise
        if mid_answer:
            raise BodyCutMidAnswer(f"the body of {scope['method']} {path} passed its bound after the answer began")
