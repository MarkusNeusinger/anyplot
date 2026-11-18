"""A bound on every request body, applied before anything reads it.

FastAPI reads and parses the whole body of a route that declares a body model before a
dependency or the route's own checks run, so a size check inside a route or a dependency comes
after the bytes are already in memory. This middleware sits in front of the router instead:

- A request that declares a `Content-Length` above the cap of its path is refused unread.
- A request that declares none (a chunked body, some HTTP/2 and proxied ones) is counted as it
  streams and cut off when it passes the cap.

Every path has the same small cap unless a longer one is named for its prefix (`api/main.py`).
A route keeps any narrower check of its own, such as the field lengths of the feedback form:
this is the outer bound, not a replacement.

`GET`, `HEAD` and `OPTIONS` pass untouched. No route reads a body on them, and a body nobody
reads is never taken off the connection.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# The cap of a path no prefix names. Every body outside the agent chat is a small JSON object
# (a feedback entry, an admin edit, a JSON-RPC call to the MCP server), far below this.
DEFAULT_MAX_BODY_BYTES = 64 * 1024

TOO_LARGE = "request body too large"

_BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_NO_STORE = {"Cache-Control": "private, no-store"}


@dataclass(frozen=True)
class Bound:
    """The cap of the paths under a prefix, and how a body above it is answered there.

    `detail` is for routes whose clients read errors by a code of their own: the refusal is then
    `{"detail": <detail>}`, the shape those routes answer with themselves. Without it the refusal
    has the API's standard error shape (`api/exceptions.py`).
    """

    max_bytes: int
    detail: str | None = None

    def refusal(self, path: str) -> JSONResponse:
        """The 413 of a body above this bound, never cached."""
        if self.detail is not None:
            return JSONResponse({"detail": self.detail}, status_code=413, headers=_NO_STORE)
        return JSONResponse({"status": 413, "message": TOO_LARGE, "path": path}, status_code=413, headers=_NO_STORE)


class BodyTooLarge(HTTPException):
    """A streamed body passed its bound.

    FastAPI's own `HTTPException`, not Starlette's base class: FastAPI turns every other error
    of a body read into `400 There was an error parsing the body`, and passes only its own
    kind on as what it is. `body_too_large_handler` then answers it.
    """

    def __init__(self, bound: Bound) -> None:
        super().__init__(status_code=413, detail=bound.detail or TOO_LARGE)
        self.bound = bound


async def body_too_large_handler(request: Request, exc: BodyTooLarge) -> JSONResponse:
    """Answer a body cut off while a route read it, in the same shape as one refused unread."""
    return exc.bound.refusal(request.url.path)


def _declared_length(scope: Scope) -> int | None:
    """The `Content-Length` a request declares, `None` without one, `-1` for one that is no number."""
    for name, value in scope["headers"]:
        if name == b"content-length":
            try:
                return int(value)
            except ValueError:
                return -1
    return None


class BodyLimitMiddleware:
    """Refuse a request body above the bound of its path, before or while it is read.

    A raw ASGI middleware, like the origin gate: a refused request must cost as little as
    possible, and only at this level can the body be bounded before the framework buffers it.
    """

    def __init__(
        self, app: ASGIApp, *, default: int = DEFAULT_MAX_BODY_BYTES, prefixes: Mapping[str, Bound] | None = None
    ) -> None:
        self.app = app
        self.default = Bound(default)
        # Longest prefix first, so `/debug/agent` is found before a bound that `/debug` might get.
        self.prefixes = sorted((prefixes or {}).items(), key=lambda item: len(item[0]), reverse=True)

    def bound_for(self, path: str) -> Bound:
        """The bound of a path: that of the longest named prefix it lies under, else the default."""
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
                {"status": 400, "message": "bad Content-Length", "path": path}, status_code=400, headers=_NO_STORE
            )
            await bad_length(scope, receive, send)
            return
        if declared is not None and declared > bound.max_bytes:
            await bound.refusal(path)(scope, receive, send)
            return

        received = 0
        answered = False

        async def counted_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > bound.max_bytes:
                    raise BodyTooLarge(bound)
            return message

        async def watched_send(message: Message) -> None:
            nonlocal answered
            if message["type"] == "http.response.start":
                answered = True
            await send(message)

        try:
            await self.app(scope, counted_receive, watched_send)
        except BodyTooLarge:
            # FastAPI answers it itself (`body_too_large_handler`). An app mounted beside it (the
            # MCP server) may let it through; then the answer is given here, unless one is
            # already on its way.
            if answered:
                raise
            await bound.refusal(path)(scope, receive, send)
