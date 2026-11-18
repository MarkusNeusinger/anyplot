"""A bound on every request body, applied before anything reads it.

FastAPI reads and parses the whole body of a route that declares a body model before a
dependency or the route's own checks run, so a size check inside a route or a dependency comes
after the bytes are already in memory. This middleware sits in front of the router instead:

- A request that declares a `Content-Length` above the cap of its path is refused unread.
- A request that declares none (a chunked body, some HTTP/2 and proxied ones) is counted as it
  streams. When it passes the cap, the refusal is sent from here and the application is told
  the client has gone, so it takes no more of the body.

The refusal never depends on what the application behind does with an error: a route, the
framework and an app mounted beside it (the MCP server) all meet the same end of the body, and
whatever they answer after the refusal went out is dropped.

Every path has the same small cap unless a longer one is named for its prefix (`api/main.py`).
A route keeps any narrower check of its own, such as the field lengths of the feedback form:
this is the outer bound, not a replacement.

`GET`, `HEAD` and `OPTIONS` pass untouched. No route reads a body on them, and a body nobody
reads is never handed to the application.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.exceptions import public_path


# The cap of a path no prefix names. Every body outside the agent chat is a small JSON object
# (a feedback entry, an admin edit, a JSON-RPC call to the MCP server), far below this.
DEFAULT_MAX_BODY_BYTES = 64 * 1024

TOO_LARGE = "request body too large"

_BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_NO_STORE = {"Cache-Control": "private, no-store"}
_GONE: Message = {"type": "http.disconnect"}


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
        return JSONResponse(
            {"status": 413, "message": TOO_LARGE, "path": public_path(path)}, status_code=413, headers=_NO_STORE
        )


def _declared_length(scope: Scope) -> int | None:
    """The `Content-Length` a request declares, or `None` without one.

    `-1` for a length nobody can go by: one that is not a plain number, and more than one header
    whose values differ. The server in front refuses those itself; this is the second line for a
    server that does not.
    """
    declared = {value.strip() for name, value in scope["headers"] if name == b"content-length"}
    if not declared:
        return None
    if len(declared) > 1:
        return -1
    value = declared.pop()
    return int(value) if value.isdigit() else -1


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
        # A prefix is kept without a trailing slash: `bound_for` adds the one that ends a segment.
        self.prefixes = sorted(
            ((prefix.rstrip("/"), bound) for prefix, bound in (prefixes or {}).items()),
            key=lambda item: len(item[0]),
            reverse=True,
        )

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
                {"status": 400, "message": "bad Content-Length", "path": public_path(path)},
                status_code=400,
                headers=_NO_STORE,
            )
            await bad_length(scope, receive, send)
            return
        if declared is not None and declared > bound.max_bytes:
            await bound.refusal(path)(scope, receive, send)
            return

        received = 0
        cut = False
        answering = False

        async def counted_receive() -> Message:
            nonlocal received, cut
            if cut:
                return _GONE
            message = await receive()
            if message["type"] != "http.request":
                return message
            received += len(message.get("body", b""))
            if received <= bound.max_bytes:
                return message
            cut = True
            # An answer already on its way cannot be replaced; the body still ends here.
            if not answering:
                await bound.refusal(path)(scope, receive, send)
            return _GONE

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
            # After the cut the request is over. An application that fails on the body it lost
            # has nothing more to report; anything raised before the cut is a real error.
            if not cut:
                raise
