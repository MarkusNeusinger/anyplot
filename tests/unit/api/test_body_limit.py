"""The bound on request bodies: refused before they are read, or cut off while they stream.

Two halves. The first holds `BodyLimitMiddleware` against small apps that record what reaches
them, because "refused" is only worth something if the application never took the bytes. The
second sends through the real `api.main` app, where the position in the middleware stack and the
framework's own handling of a body that ends early decide what a client sees.

What these tests can see is what the application is handed. Whether the server in front goes on
taking bytes off the connection after the refusal is its own matter and not measured here.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi.routing import APIRoute
from pydantic import TypeAdapter
from starlette.applications import Starlette
from starlette.requests import ClientDisconnect, Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from api.body_limit import (
    BUSY,
    DEFAULT_MAX_BODY_BYTES,
    LENGTH_REQUIRED,
    SLOW,
    TOO_LARGE,
    BodyCutMidAnswer,
    BodyLimitMiddleware,
    Bound,
    ClientGoneFilter,
    LargeBodies,
)
from api.main import app, fastapi_app
from api.origin_gate import ORIGIN_SECRET_HEADER
from api.routers import agent, agent_public
from api.routers.agent import (
    BODY_PREFIXES,
    LARGE_BODY_STALL_S,
    LARGE_BODY_TOTAL_S,
    MAX_CONVERT_BASE64_CHARS,
    MAX_CONVERT_BYTES,
    MAX_DATASET_BYTES,
    MAX_DATASET_TABLES,
    MAX_LARGE_BODIES,
    MAX_MESSAGE_CHARS,
    MAX_PASTE_BODY_BYTES,
    MAX_REQUEST_BODY_BYTES,
    MAX_SHEET_NAME_CHARS,
    MAX_SOURCE_CHARS,
    Binding,
    ConvertBody,
    DatasetBody,
    MessageBody,
)
from core.config import settings


CAP = 100
CHUNK = 16
AGENT_PREFIXES = ("/agent", "/debug/agent")
PASTE_PATHS = ("/agent/session/dataset", "/debug/agent/sessions/s1/dataset")
FILE_PATHS = ("/agent/session/dataset/convert", "/debug/agent/sessions/s1/dataset/convert")
JSON_BODY = {"Content-Type": "application/json"}
# The character a browser writes longest: six bytes as sent (`\u0001`) for one code point.
LONGEST = "\u0001"


class Recorder:
    """An app that reads the whole body and says how much it got."""

    def __init__(self) -> None:
        self.calls = 0
        self.read = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.calls += 1
        body = await Request(scope, receive).body()
        self.read = len(body)
        await JSONResponse({"read": len(body)})(scope, receive, send)


class Pulls:
    """A body that counts the chunks pulled from it, sent without a declared length."""

    def __init__(self, chunks: int, size: int = CHUNK) -> None:
        self.chunks = chunks
        self.size = size
        self.pulled = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for _ in range(self.chunks):
            self.pulled += 1
            yield b"a" * self.size


class Wire:
    """The two ends of one request, driven by hand: the messages a server would hand over, and
    everything the application side sent back."""

    def __init__(self, *bodies: bytes) -> None:
        self.incoming = [
            {"type": "http.request", "body": body, "more_body": index < len(bodies) - 1}
            for index, body in enumerate(bodies)
        ]
        self.taken = 0
        self.sent: list[dict] = []

    async def receive(self) -> dict:
        self.taken += 1
        return self.incoming.pop(0)

    async def send(self, message: dict) -> None:
        self.sent.append(message)

    @property
    def starts(self) -> list[int]:
        return [message["status"] for message in self.sent if message["type"] == "http.response.start"]


def scope_of(path: str = "/x", headers: list[tuple[bytes, bytes]] | None = None) -> dict:
    return {"type": "http", "method": "POST", "path": path, "headers": headers or []}


def api_routes(routes) -> list[APIRoute]:
    """Every route of the app, the ones of its included routers too.

    The framework keeps an included router as one entry that holds the router; its routes carry
    the router's own prefix in their path.
    """
    found: list[APIRoute] = []
    for route in routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            found += api_routes(included.routes)
        elif isinstance(route, APIRoute):
            found.append(route)
    return found


def from_the_bound(answer: httpx.Response) -> bool:
    """Whether a data route's answer is one of the bound's three, and not the lane's own: the
    admin gate answers 503 too where no admin is configured, in another shape."""
    codes = {413: "too_long", 411: "length_required", 503: "capacity"}
    return answer.status_code in codes and answer.json() == {"detail": codes[answer.status_code]}


def client_for(target) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=target), base_url="https://api.anyplot.ai")


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
def bounded(recorder: Recorder) -> BodyLimitMiddleware:
    return BodyLimitMiddleware(
        recorder,
        default=CAP,
        prefixes={"/wide": Bound(10 * CAP), "/wide/narrow": Bound(CAP // 2), "/coded": Bound(CAP, detail="own_code")},
    )


class TestTheMiddleware:
    async def test_a_body_within_the_cap_reaches_the_app_whole(self, bounded, recorder) -> None:
        async with client_for(bounded) as client:
            answer = await client.post("/x", content=b"a" * CAP)
        assert answer.status_code == 200
        assert answer.json() == {"read": CAP}

    async def test_a_declared_length_above_the_cap_is_refused_unread(self, bounded, recorder) -> None:
        body = Pulls(chunks=50)
        async with client_for(bounded) as client:
            answer = await client.post("/x", content=body, headers={"Content-Length": str(50 * CHUNK)})
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/x"}
        assert answer.headers["cache-control"] == "private, no-store"
        # Neither the app nor the body was touched.
        assert recorder.calls == 0
        assert body.pulled == 0

    async def test_a_body_without_a_length_is_cut_off_at_the_cap(self, bounded, recorder) -> None:
        body = Pulls(chunks=500)
        async with client_for(bounded) as client:
            answer = await client.post("/x", content=body)
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/x"}
        assert answer.headers["cache-control"] == "private, no-store"
        # The application was handed what arrived up to the cap, not the body's end.
        assert body.pulled <= CAP // CHUNK + 2
        assert recorder.read == 0

    async def test_the_refusal_is_the_one_answer_whatever_the_application_says_next(self) -> None:
        """An application that answers for itself when its body ends early (a framework's parse
        error, a mounted app's own error page) must not be heard: the refusal is already out."""

        async def answers_anyway(scope: Scope, receive: Receive, send: Send) -> None:
            while (await receive())["type"] == "http.request":
                pass
            await PlainTextResponse("my own error", status_code=400)(scope, receive, send)

        wire = Wire(b"a" * CAP, b"a" * CAP, b"a" * CAP)
        await BodyLimitMiddleware(answers_anyway, default=CAP)(scope_of(), wire.receive, wire.send)
        assert wire.starts == [413]
        # The second chunk passed the cap; the third was never taken.
        assert wire.taken == 2

    async def test_an_application_that_keeps_asking_gets_no_more_of_the_body(self) -> None:
        """After the cut every further read is answered here: nothing more is taken for an
        application that ignores the end it was told of."""
        seen: list[str] = []

        async def keeps_asking(scope: Scope, receive: Receive, send: Send) -> None:
            for _ in range(6):
                seen.append((await receive())["type"])

        wire = Wire(*[b"a" * CAP] * 6)
        await BodyLimitMiddleware(keeps_asking, default=CAP)(scope_of(), wire.receive, wire.send)
        assert seen == ["http.request"] + ["http.disconnect"] * 5
        assert wire.taken == 2
        assert wire.starts == [413]

    async def test_an_app_with_error_handling_of_its_own_gets_the_same_refusal(self) -> None:
        """A whole app behind the bound, as the MCP server is mounted: its own handlers answer an
        early end of the body in their own shape, and the client still gets this one."""

        async def reads(request: Request) -> JSONResponse:
            return JSONResponse({"read": len(await request.body())})

        inner = Starlette(routes=[Route("/x", reads, methods=["POST"])])
        async with client_for(BodyLimitMiddleware(inner, default=CAP)) as client:
            answer = await client.post("/x", content=Pulls(chunks=500))
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/x"}
        assert answer.headers["cache-control"] == "private, no-store"

    async def test_a_cut_after_the_answer_began_is_raised_and_the_rest_is_not_sent(self) -> None:
        """An answer on its way cannot be replaced by a refusal. The rest of it is dropped, and
        the failure leaves here as an error instead of passing in silence. What a client then
        sees is up to the layers outside, which may end the short answer properly."""

        async def answers_then_reads(scope: Scope, receive: Receive, send: Send) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"first half", "more_body": True})
            while (await receive())["type"] == "http.request":
                pass
            await send({"type": "http.response.body", "body": b"second half", "more_body": False})

        wire = Wire(b"a" * CAP, b"a" * CAP, b"a" * CAP)
        with pytest.raises(BodyCutMidAnswer):
            await BodyLimitMiddleware(answers_then_reads, default=CAP)(scope_of(), wire.receive, wire.send)
        assert wire.starts == [200]
        assert wire.taken == 2
        # The half that went out stays the last word: the rest is not sent, and nothing ends it.
        assert [message.get("body") for message in wire.sent[1:]] == [b"first half"]
        assert wire.sent[-1]["more_body"] is True

    async def test_an_error_before_the_cut_is_still_an_error(self) -> None:
        async def broken(scope: Scope, receive: Receive, send: Send) -> None:
            raise RuntimeError("a real fault")

        wire = Wire(b"a")
        with pytest.raises(RuntimeError, match="a real fault"):
            await BodyLimitMiddleware(broken, default=CAP)(scope_of(), wire.receive, wire.send)

    @pytest.mark.parametrize(
        "lengths",
        [
            [b"lots"],
            [b"-1"],
            [b"1_0"],
            [b""],
            # Two that differ: a refusal that read only the first would let the second decide.
            [b"0", b"100000"],
            [b"100000", b"0"],
        ],
    )
    async def test_a_length_nobody_can_go_by_is_a_bad_request(self, bounded, recorder, lengths) -> None:
        wire = Wire(b"a")
        await bounded(scope_of(headers=[(b"content-length", value) for value in lengths]), wire.receive, wire.send)
        assert wire.starts == [400]
        assert wire.taken == 0
        assert recorder.calls == 0

    @pytest.mark.parametrize("length", [b"18446744073709551616", b"9" * 5000])
    async def test_a_length_of_any_number_of_digits_is_still_a_length(self, bounded, recorder, length) -> None:
        """A number too long to read is not a malformed one: it is above every cap, so it gets
        the refusal for a body that is too large (Python itself stops at a few thousand digits)."""
        wire = Wire(b"a")
        await bounded(scope_of(headers=[(b"content-length", length)]), wire.receive, wire.send)
        assert wire.starts == [413]
        assert wire.taken == 0
        assert recorder.calls == 0

    async def test_leading_zeros_do_not_make_a_length_longer(self, bounded, recorder) -> None:
        wire = Wire(b"abc")
        await bounded(scope_of(headers=[(b"content-length", b"0" * 40 + b"3")]), wire.receive, wire.send)
        assert wire.starts == [200]
        assert recorder.read == 3

    async def test_a_body_no_application_reads_is_never_taken(self) -> None:
        """What is bounded is what the application takes. A route that answers without reading
        gets nothing counted and nothing refused, because nothing is pulled from the connection."""

        async def answers_unread(scope: Scope, receive: Receive, send: Send) -> None:
            await JSONResponse({"ok": True})(scope, receive, send)

        wire = Wire(*[b"a" * CAP] * 6)
        await BodyLimitMiddleware(answers_unread, default=CAP)(scope_of(), wire.receive, wire.send)
        assert wire.starts == [200]
        assert wire.taken == 0

    async def test_the_same_length_stated_twice_is_one_length(self, bounded, recorder) -> None:
        wire = Wire(b"abc")
        headers = [(b"content-length", b"3"), (b"content-length", b"3")]
        await bounded(scope_of(headers=headers), wire.receive, wire.send)
        assert wire.starts == [200]
        assert recorder.read == 3

    @pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
    async def test_a_method_no_route_reads_a_body_on_passes_untouched(self, bounded, recorder, method) -> None:
        async with client_for(bounded) as client:
            answer = await client.request(method, "/x", headers={"Content-Length": "0"})
        assert answer.status_code == 200
        assert recorder.calls == 1

    def test_the_cap_of_a_path_is_that_of_its_longest_prefix(self, bounded) -> None:
        assert bounded.bound_for("/x").max_bytes == CAP
        assert bounded.bound_for("/wide").max_bytes == 10 * CAP
        assert bounded.bound_for("/wide/open").max_bytes == 10 * CAP
        assert bounded.bound_for("/wide/narrow/deep").max_bytes == CAP // 2
        # A prefix ends at a path segment: a longer first segment is another path.
        assert bounded.bound_for("/wider").max_bytes == CAP
        assert bounded.bound_for("/x/wide").max_bytes == CAP

    def test_a_prefix_written_with_a_trailing_slash_means_the_same(self, recorder) -> None:
        slashed = BodyLimitMiddleware(recorder, default=CAP, prefixes={"/wide/": Bound(10 * CAP)})
        assert slashed.bound_for("/wide").max_bytes == 10 * CAP
        assert slashed.bound_for("/wide/open").max_bytes == 10 * CAP

    async def test_a_prefix_takes_what_the_default_refuses(self, bounded, recorder) -> None:
        async with client_for(bounded) as client:
            narrow = await client.post("/x", content=b"a" * (CAP + 1))
            wide = await client.post("/wide/open", content=b"a" * (CAP + 1))
        assert narrow.status_code == 413
        assert wide.status_code == 200

    async def test_a_prefix_with_a_code_of_its_own_answers_in_that_shape(self, bounded, recorder) -> None:
        """Declared or cut off while it streams, a body above the cap gets the one answer its
        routes give themselves, so a client that reads their codes needs no second case."""
        async with client_for(bounded) as client:
            declared = await client.post(
                "/coded/x", content=Pulls(chunks=50), headers={"Content-Length": str(50 * CHUNK)}
            )
            streamed = await client.post("/coded/x", content=Pulls(chunks=500))
        for answer in (declared, streamed):
            assert answer.status_code == 413
            assert answer.json() == {"detail": "own_code"}
            assert answer.headers["cache-control"] == "private, no-store"

    async def test_the_refusal_names_the_path_as_the_client_knows_it(self, bounded) -> None:
        """A crawler's request arrives under an internal prefix that no answer gives back."""
        async with client_for(bounded) as client:
            answer = await client.post(
                "/seo-proxy/scatter-basic", content=Pulls(chunks=50), headers={"Content-Length": str(50 * CHUNK)}
            )
        assert answer.json()["path"] == "/scatter-basic"


class TestTheRules:
    """A rule names single routes under a prefix that has another cap."""

    @staticmethod
    def ruled(target) -> BodyLimitMiddleware:
        return BodyLimitMiddleware(
            target,
            default=CAP,
            prefixes={"/lane": Bound(2 * CAP, detail="own_code")},
            rules=[
                (re.compile(r"/lane/[^/]+/data"), Bound(10 * CAP)),
                (re.compile(r"/lane/[^/]+/data/file"), Bound(20 * CAP)),
            ],
        )

    def test_a_rule_is_looked_at_before_a_prefix(self, recorder) -> None:
        ruled = self.ruled(recorder)
        assert ruled.bound_for("/lane/s1/data").max_bytes == 10 * CAP
        assert ruled.bound_for("/lane/s1/data/file").max_bytes == 20 * CAP
        assert ruled.bound_for("/lane/s1/other") == Bound(2 * CAP, detail="own_code")
        assert ruled.bound_for("/elsewhere").max_bytes == CAP

    def test_a_rule_has_to_match_the_whole_path(self, recorder) -> None:
        """A longer or a shorter path is another route, which takes its prefix's cap."""
        ruled = self.ruled(recorder)
        for path in ("/lane/s1/data/more", "/lane/s1/s2/data", "/lane/s1/data/"):
            assert ruled.bound_for(path).max_bytes == 2 * CAP, path
        assert ruled.bound_for("/x/lane/s1/data").max_bytes == CAP

    async def test_a_rule_takes_what_its_prefix_refuses(self, recorder) -> None:
        async with client_for(self.ruled(recorder)) as client:
            beside = await client.post("/lane/s1/other", content=b"a" * (5 * CAP))
            ruled = await client.post("/lane/s1/data", content=b"a" * (5 * CAP))
        assert (beside.status_code, beside.json()) == (413, {"detail": "own_code"})
        assert (ruled.status_code, ruled.json()) == (200, {"read": 5 * CAP})


class Held:
    """An app that reads its body and then waits to be let go."""

    def __init__(self) -> None:
        self.go = asyncio.Event()
        self.calls = 0
        self.waiting = 0
        self.fail = False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        self.calls += 1
        body = await Request(scope, receive).body()
        self.waiting += 1
        try:
            await self.go.wait()
        finally:
            self.waiting -= 1
        if self.fail:
            raise RuntimeError("the route failed")
        await JSONResponse({"read": len(body)})(scope, receive, send)

    async def holds(self, count: int) -> None:
        """Wait until `count` requests have been read and are held."""
        for _ in range(1000):
            if self.waiting >= count:
                return
            await asyncio.sleep(0)
        raise AssertionError(f"{self.waiting} requests are held, not {count}")


class TestLargeBodies:
    """Bodies above the threshold of a route marked large are taken a few at a time."""

    PLACES = 2
    BIG = 5 * CAP
    # The time limits of a test: long enough that nothing ordinary meets them, short enough to wait them out.
    STALL_S = 0.2
    BODY_S = 0.6

    def counted(
        self, target, stall_s: float = STALL_S, body_s: float = BODY_S
    ) -> tuple[BodyLimitMiddleware, LargeBodies]:
        places = LargeBodies(places=self.PLACES, above=CAP, stall_s=stall_s, body_s=body_s)
        coded = Bound(
            10 * CAP,
            detail="own_code",
            large=True,
            length_detail="own_length",
            busy_detail="own_busy",
            slow_detail="own_slow",
        )
        middleware = BodyLimitMiddleware(
            target,
            default=CAP,
            prefixes={"/coded": coded},
            rules=[(re.compile(r"/data/[^/]+"), Bound(10 * CAP, large=True))],
            large=places,
        )
        return middleware, places

    def test_a_bound_marked_large_needs_the_places(self, recorder) -> None:
        with pytest.raises(ValueError, match="places"):
            BodyLimitMiddleware(recorder, prefixes={"/data": Bound(10 * CAP, large=True)})
        with pytest.raises(ValueError, match="places"):
            BodyLimitMiddleware(recorder, rules=[(re.compile("/data"), Bound(10 * CAP, large=True))])
        with pytest.raises(ValueError, match="at least one"):
            LargeBodies(places=0, stall_s=1, body_s=1)
        for stall_s, body_s in ((0, 1), (1, 0), (-1, 1)):
            with pytest.raises(ValueError, match="time limits"):
                LargeBodies(places=1, stall_s=stall_s, body_s=body_s)

    async def test_a_body_without_a_length_is_refused_unread(self, recorder) -> None:
        """Its place has to be settled before any of it is read, and without a length there is
        nothing to settle it by."""
        middleware, places = self.counted(recorder)
        plain, coded = Pulls(chunks=2), Pulls(chunks=2)
        async with client_for(middleware) as client:
            standard = await client.post("/data/s1", content=plain)
            own = await client.post("/coded/x", content=coded)
        assert standard.status_code == 411
        assert standard.json() == {"status": 411, "message": LENGTH_REQUIRED, "path": "/data/s1"}
        assert (own.status_code, own.json()) == (411, {"detail": "own_length"})
        assert standard.headers["cache-control"] == "private, no-store"
        assert (recorder.calls, plain.pulled, coded.pulled, places.taken) == (0, 0, 0, 0)

    async def test_a_body_at_the_threshold_needs_no_place(self) -> None:
        held = Held()
        middleware, places = self.counted(held)
        async with client_for(middleware) as client:
            small = [asyncio.create_task(client.post("/data/s1", content=b"a" * CAP)) for _ in range(self.PLACES + 3)]
            await held.holds(self.PLACES + 3)
            assert places.taken == 0
            held.go.set()
            answers = await asyncio.gather(*small)
        assert [answer.status_code for answer in answers] == [200] * (self.PLACES + 3)

    async def test_one_body_more_than_the_places_is_refused_unread(self) -> None:
        held = Held()
        middleware, places = self.counted(held)
        one_more, coded = Pulls(chunks=1), Pulls(chunks=1)
        declared = {"Content-Length": str(self.BIG)}
        async with client_for(middleware) as client:
            first = [asyncio.create_task(client.post("/data/s1", content=b"a" * self.BIG)) for _ in range(self.PLACES)]
            await held.holds(self.PLACES)
            assert places.taken == self.PLACES
            refused = await client.post("/data/s2", content=one_more, headers=declared)
            own = await client.post("/coded/x", content=coded, headers=declared)
            # A small body on the same route still passes while every place is taken.
            small = asyncio.create_task(client.post("/data/s3", content=b"a" * CAP))
            await held.holds(self.PLACES + 1)
            held.go.set()
            answers = await asyncio.gather(*first, small)
            # The places are free again, and the next large body is taken.
            after = await client.post("/data/s2", content=b"a" * self.BIG)
        assert refused.status_code == 503
        assert refused.json() == {"status": 503, "message": BUSY, "path": "/data/s2"}
        assert refused.headers["cache-control"] == "private, no-store"
        assert (own.status_code, own.json()) == (503, {"detail": "own_busy"})
        assert (one_more.pulled, coded.pulled) == (0, 0)
        assert [answer.status_code for answer in answers] == [200] * (self.PLACES + 1)
        assert (after.status_code, after.json()) == (200, {"read": self.BIG})
        assert places.taken == 0
        assert held.calls == self.PLACES + 2

    async def test_a_place_is_given_back_when_the_route_fails(self) -> None:
        held = Held()
        held.fail = True
        held.go.set()
        middleware, places = self.counted(held)
        async with client_for(middleware) as client:
            for _ in range(self.PLACES + 1):
                with pytest.raises(RuntimeError, match="the route failed"):
                    await client.post("/data/s1", content=b"a" * self.BIG)
        assert places.taken == 0

    async def test_a_place_is_given_back_when_the_request_is_cancelled(self) -> None:
        """A client that goes away, or a server that shuts down, ends a request by cancelling it:
        that is no `Exception`, and the place has to come back all the same."""
        held = Held()
        middleware, places = self.counted(held)
        async with client_for(middleware) as client:
            requests = [
                asyncio.create_task(client.post("/data/s1", content=b"a" * self.BIG)) for _ in range(self.PLACES)
            ]
            await held.holds(self.PLACES)
            assert places.taken == self.PLACES
            for request in requests:
                request.cancel()
            assert all(
                isinstance(end, asyncio.CancelledError)
                for end in await asyncio.gather(*requests, return_exceptions=True)
            )
            assert places.taken == 0
            held.go.set()
            after = await client.post("/data/s1", content=b"a" * self.BIG)
        assert (after.status_code, after.json()) == (200, {"read": self.BIG})
        assert places.taken == 0

    async def test_a_body_above_its_cap_takes_no_place(self, recorder) -> None:
        middleware, places = self.counted(recorder)
        body = Pulls(chunks=1)
        async with client_for(middleware) as client:
            answer = await client.post("/data/s1", content=body, headers={"Content-Length": str(50 * CAP)})
        assert answer.status_code == 413
        assert (recorder.calls, body.pulled, places.taken) == (0, 0, 0)

    async def test_a_body_that_declared_a_small_length_is_held_to_it(self, recorder) -> None:
        """A request that needs no place is cut off at the size that needs none: what it declared
        is what it may send, also where a server in front does not hold it to that."""
        middleware, places = self.counted(recorder)
        wire = Wire(b"a" * CAP, b"a" * CAP, b"a" * CAP)
        scope = scope_of("/data/s1", headers=[(b"content-length", str(CAP).encode())])
        await middleware(scope, wire.receive, wire.send)
        assert wire.starts == [413]
        assert wire.taken == 2
        assert places.taken == 0


class Trickle:
    """A request body that arrives in parts with a pause before each, or never: a declared length and no bytes.
    With `stops_after`, that many parts arrive and then nothing more does."""

    def __init__(self, parts: int, size: int, pause_s: float, stops_after: int | None = None) -> None:
        self.parts = parts
        self.size = size
        self.pause_s = pause_s
        self.stops_after = stops_after
        self.sent = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        if not self.parts:
            await asyncio.Event().wait()
        for _ in range(self.parts):
            if self.sent == self.stops_after:
                await asyncio.Event().wait()
            await asyncio.sleep(self.pause_s)
            self.sent += 1
            yield b"a" * self.size


class TestTheTimeOfALargeBody:
    """A place is taken on a declared length, so the body has to come: it may not stall, and it may not take
    for ever. Without that, a request that declares a length and sends nothing would keep its place."""

    PLACES = TestLargeBodies.PLACES
    BIG = TestLargeBodies.BIG
    counted = TestLargeBodies.counted

    async def test_a_body_that_never_comes_gives_its_place_back(self, recorder) -> None:
        # The whole-body limit lies far beyond the test's own waits: only the wait for a part can end these.
        middleware, places = self.counted(recorder, stall_s=0.05, body_s=60)
        declared = {"Content-Length": str(self.BIG)}
        async with client_for(middleware) as client:
            silent = [
                asyncio.create_task(client.post("/data/s1", content=Trickle(0, 0, 0), headers=declared))
                for _ in range(self.PLACES)
            ]
            first, second = await asyncio.wait_for(asyncio.gather(*silent), 5)
            assert places.taken == 0
            own = await asyncio.wait_for(client.post("/coded/x", content=Trickle(0, 0, 0), headers=declared), 5)
            # The places are free again for a body that does come.
            after = await asyncio.wait_for(client.post("/data/s1", content=b"a" * self.BIG), 5)
        assert first.status_code == second.status_code == 408
        assert first.json() == {"status": 408, "message": SLOW, "path": "/data/s1"}
        assert first.headers["cache-control"] == "private, no-store"
        # The rest of the body may still come: the connection is closed with the answer, never read on.
        assert first.headers["connection"] == "close"
        assert (own.status_code, own.json()) == (408, {"detail": "own_slow"})
        assert (after.status_code, after.json()) == (200, {"read": self.BIG})
        # Each request reached the application once, and only the last one's body did.
        assert (recorder.calls, recorder.read) == (self.PLACES + 2, self.BIG)

    async def test_a_body_that_keeps_coming_but_takes_too_long_gives_its_place_back(self, recorder) -> None:
        """Each part arrives well within the wait for the next one; the whole does not arrive in its time."""
        middleware, places = self.counted(recorder, stall_s=0.5, body_s=0.2)
        body = Trickle(parts=50, size=self.BIG // 50, pause_s=0.02)
        async with client_for(middleware) as client:
            answer = await asyncio.wait_for(
                client.post("/data/s1", content=body, headers={"Content-Length": str(self.BIG)}), 5
            )
        assert answer.status_code == 408
        assert 0 < body.sent < 50
        assert places.taken == 0

    async def test_a_body_that_sends_one_part_and_stops_gives_its_place_back(self, recorder) -> None:
        """The wait for a part goes on after the first one: a body that starts and then stops is ended by it, long
        before the limit on the whole body would."""
        middleware, places = self.counted(recorder, stall_s=0.05, body_s=60)
        body = Trickle(parts=10, size=self.BIG // 10, pause_s=0, stops_after=1)
        async with client_for(middleware) as client:
            answer = await asyncio.wait_for(
                client.post("/data/s1", content=body, headers={"Content-Length": str(self.BIG)}), 5
            )
        assert answer.status_code == 408
        assert body.sent == 1
        assert places.taken == 0

    async def test_a_slow_body_within_both_limits_is_taken_whole(self, recorder) -> None:
        """The wait for a part starts anew with every part: this body takes longer in all than that wait allows
        for one part, and every pause in it is shorter."""
        middleware, places = self.counted(recorder, stall_s=0.3, body_s=30)
        body = Trickle(parts=10, size=self.BIG // 10, pause_s=0.05)
        started = asyncio.get_running_loop().time()
        async with client_for(middleware) as client:
            answer = await asyncio.wait_for(
                client.post("/data/s1", content=body, headers={"Content-Length": str(self.BIG)}), 10
            )
        assert asyncio.get_running_loop().time() - started > 0.3
        assert (answer.status_code, answer.json()) == (200, {"read": self.BIG})
        assert places.taken == 0

    async def test_a_part_after_the_end_does_not_start_the_clock_again(self) -> None:
        """A whole body stays whole: a server that hands over one more part after the last one must not put a
        route that is already working back under the body's limits."""
        parts = [
            {"type": "http.request", "body": b"a" * self.BIG, "more_body": False},
            {"type": "http.request", "body": b"", "more_body": True},
        ]
        never = asyncio.Event()

        async def receive() -> dict:
            if parts:
                return parts.pop(0)
            await never.wait()
            raise AssertionError("unreachable")

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        async def working_route(scope: Scope, receive: Receive, send: Send) -> None:
            await receive()
            await receive()
            try:
                async with asyncio.timeout(0.2):  # longer than both limits below
                    await receive()
            except TimeoutError:
                pass
            await JSONResponse({"worked": True})(scope, receive, send)

        middleware, places = self.counted(working_route, stall_s=0.05, body_s=0.1)
        scope = scope_of("/data/s1", headers=[(b"content-length", str(self.BIG).encode())])
        await asyncio.wait_for(middleware(scope, receive, send), 5)
        assert [message["status"] for message in sent if message["type"] == "http.response.start"] == [200]
        assert places.taken == 0

    async def test_a_timeout_of_the_servers_own_is_not_answered_as_a_slow_body(self, recorder) -> None:
        """Only the limit's own wait running out is a slow body. Any other timeout is the server's fault, and it
        must show as one."""

        async def receive() -> dict:
            raise TimeoutError("the server's own")

        sent: list[dict] = []

        async def send(message: dict) -> None:
            sent.append(message)

        middleware, places = self.counted(recorder)
        scope = scope_of("/data/s1", headers=[(b"content-length", str(self.BIG).encode())])
        with pytest.raises(TimeoutError, match="the server's own"):
            await middleware(scope, receive, send)
        assert sent == []
        assert places.taken == 0

    async def test_a_route_that_works_long_on_a_whole_body_is_not_hurried(self) -> None:
        """The limits are on the body's arrival. A route that then takes longer than both, and listens for the
        client meanwhile as a streamed answer does, keeps its request and its place until it answers."""
        listened: list[str] = []

        async def slow_route(scope: Scope, receive: Receive, send: Send) -> None:
            body = await Request(scope, receive).body()
            try:
                async with asyncio.timeout(0.3):
                    listened.append((await receive())["type"])
            except TimeoutError:
                listened.append("nothing")
            await JSONResponse({"read": len(body)})(scope, receive, send)

        middleware, places = self.counted(slow_route, stall_s=0.05, body_s=0.1)
        async with client_for(middleware) as client:
            answer = await asyncio.wait_for(client.post("/data/s1", content=b"a" * self.BIG), 5)
        assert (answer.status_code, answer.json()) == (200, {"read": self.BIG})
        assert listened == ["nothing"]
        assert places.taken == 0

    async def test_a_small_body_is_not_timed(self, recorder) -> None:
        """A body that needs no place holds nothing another request waits for."""
        middleware, places = self.counted(recorder, stall_s=0.05, body_s=0.1)
        body = Trickle(parts=4, size=CAP // 4, pause_s=0.08)
        async with client_for(middleware) as client:
            answer = await asyncio.wait_for(
                client.post("/data/s1", content=body, headers={"Content-Length": str(CAP)}), 5
            )
        assert (answer.status_code, answer.json()) == (200, {"read": CAP})


class TestTheApp:
    """Through `api.main`: every body-taking path is bounded where the bytes arrive."""

    async def test_a_public_form_is_refused_unread_above_the_default(self) -> None:
        body = Pulls(chunks=8, size=DEFAULT_MAX_BODY_BYTES)
        headers = {"Content-Type": "application/json", "Content-Length": str(8 * DEFAULT_MAX_BODY_BYTES)}
        async with client_for(app) as client:
            answer = await client.post("/feedback", content=body, headers=headers)
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/feedback"}
        assert body.pulled == 0

    async def test_a_body_without_a_length_gets_the_413_and_is_not_taken_to_its_end(self) -> None:
        """A route with a body model has its body read by the framework, which answers a body
        that ends early with its own 400. The client has to get the 413, and the read has to stop."""
        chunks = 64
        body = Pulls(chunks=chunks, size=DEFAULT_MAX_BODY_BYTES // 4)
        async with client_for(app) as client:
            answer = await client.post("/feedback", content=body, headers={"Content-Type": "application/json"})
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/feedback"}
        assert answer.headers["cache-control"] == "private, no-store"
        assert body.pulled <= 6
        assert body.pulled < chunks

    async def test_a_read_passes_whatever_length_it_declares(self) -> None:
        """No route reads a body on a `GET`, so the bound has nothing to refuse there."""
        async with client_for(app) as client:
            answer = await client.request(
                "GET", "/health", headers={"Content-Length": str(8 * DEFAULT_MAX_BODY_BYTES)}, content=Pulls(chunks=1)
            )
        assert answer.status_code == 200

    async def test_a_browser_can_read_the_refusal(self) -> None:
        headers = {"Content-Type": "application/json", "Origin": "https://anyplot.ai"}
        declared = {**headers, "Content-Length": str(2 * DEFAULT_MAX_BODY_BYTES)}
        async with client_for(app) as client:
            unread = await client.post("/feedback", content=Pulls(chunks=1), headers=declared)
            cut = await client.post("/feedback", content=Pulls(chunks=64, size=4096), headers=headers)
        for answer in (unread, cut):
            assert answer.status_code == 413
            assert answer.headers["access-control-allow-origin"] == "https://anyplot.ai"

    @pytest.mark.parametrize(
        "path",
        ["/agent/sessions", "/agent/session/messages", "/debug/agent/sessions", "/debug/agent/sessions/s1/library"],
    )
    async def test_an_agent_route_without_data_takes_the_default_and_answers_with_its_own_code(self, path: str) -> None:
        """The chat page reads errors by their code, so a body above the cap is answered in the
        shape those routes use themselves, whether it declares its length or not."""
        streamed_body = Pulls(chunks=64, size=DEFAULT_MAX_BODY_BYTES // 4)
        async with client_for(app) as client:
            within = await client.post(path, content=b"a" * DEFAULT_MAX_BODY_BYTES, headers=JSON_BODY)
            declared = await client.post(
                path, content=Pulls(chunks=1), headers={**JSON_BODY, "Content-Length": str(DEFAULT_MAX_BODY_BYTES + 1)}
            )
            streamed = await client.post(path, content=streamed_body, headers=JSON_BODY)
        assert within.status_code != 413
        for above in (declared, streamed):
            assert above.status_code == 413
            assert above.json() == {"detail": "too_long"}
        assert streamed_body.pulled <= 6

    @pytest.mark.parametrize(
        ("path", "cap"),
        [(path, MAX_PASTE_BODY_BYTES) for path in PASTE_PATHS]
        + [(path, MAX_REQUEST_BODY_BYTES) for path in FILE_PATHS],
    )
    async def test_a_data_route_takes_the_body_it_needs_and_no_more(self, path: str, cap: int) -> None:
        """A body at the route's cap reaches the lane, which answers for itself; one byte more is
        refused unread with the code the page reads, and so is a body that declares no length."""
        above, unsized = Pulls(chunks=1), Pulls(chunks=4)
        async with client_for(app) as client:
            within = await client.post(path, content=b"a" * cap, headers=JSON_BODY)
            too_long = await client.post(path, content=above, headers={**JSON_BODY, "Content-Length": str(cap + 1)})
            no_length = await client.post(path, content=unsized, headers=JSON_BODY)
        assert not from_the_bound(within)
        assert (too_long.status_code, too_long.json()) == (413, {"detail": "too_long"})
        assert (no_length.status_code, no_length.json()) == (411, {"detail": "length_required"})
        assert (above.pulled, unsized.pulled) == (0, 0)

    async def test_one_large_body_more_than_the_places_is_answered_busy(self) -> None:
        """Both lanes and both data routes share the places: with every place taken by pastes, a
        file is answered at once, unread, in the page's own shape, and a small paste still passes."""
        size = 4 * DEFAULT_MAX_BODY_BYTES
        go = asyncio.Event()
        started = 0

        async def waiting() -> AsyncIterator[bytes]:
            nonlocal started
            started += 1
            await go.wait()
            yield b"a" * size

        declared = {**JSON_BODY, "Content-Length": str(size)}
        paths = [PASTE_PATHS[index % 2] for index in range(MAX_LARGE_BODIES)]
        one_more = Pulls(chunks=1)
        async with client_for(app) as client:
            held = [asyncio.create_task(client.post(path, content=waiting(), headers=declared)) for path in paths]
            try:
                for _ in range(1000):
                    if started == MAX_LARGE_BODIES:
                        break
                    await asyncio.sleep(0)
                assert started == MAX_LARGE_BODIES
                busy = await asyncio.wait_for(client.post(FILE_PATHS[0], content=one_more, headers=declared), 5)
                small = await asyncio.wait_for(
                    client.post(PASTE_PATHS[0], content=b"a" * DEFAULT_MAX_BODY_BYTES, headers=JSON_BODY), 5
                )
                go.set()
                answers = await asyncio.wait_for(asyncio.gather(*held), 5)
            finally:
                # A failed assertion must not leave the app's places taken for the tests after this one.
                for request in held:
                    request.cancel()
                await asyncio.gather(*held, return_exceptions=True)
            after = await asyncio.wait_for(client.post(PASTE_PATHS[0], content=b"a" * size, headers=JSON_BODY), 5)
        assert (busy.status_code, busy.json()) == (503, {"detail": "capacity"})
        assert one_more.pulled == 0
        for answer in (small, after, *answers):
            assert not from_the_bound(answer)

    @pytest.mark.parametrize("path", [PASTE_PATHS[0], FILE_PATHS[1]])
    async def test_a_large_body_that_never_comes_is_ended_with_the_pages_own_shape(
        self, path: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        places = TestTheTable.middleware().large
        assert places is not None
        monkeypatch.setattr(places, "stall_s", 0.05)

        async def never() -> AsyncIterator[bytes]:
            await asyncio.Event().wait()
            yield b""

        declared = {**JSON_BODY, "Content-Length": str(4 * DEFAULT_MAX_BODY_BYTES)}
        async with client_for(app) as client:
            answer = await asyncio.wait_for(client.post(path, content=never(), headers=declared), 5)
        assert places.taken == 0
        if path in PASTE_PATHS:
            # The paste's body is read before its lane answers, so the wait for it ends here.
            assert (answer.status_code, answer.json()) == (408, {"detail": "upload_timeout"})
        else:
            # The file route takes its body by hand, after its gates: a closed lane never waits for it.
            assert not from_the_bound(answer) and answer.status_code != 408

    async def test_the_mcp_server_is_bounded_like_any_other_path(self) -> None:
        headers = {"Content-Type": "application/json", "Content-Length": str(2 * DEFAULT_MAX_BODY_BYTES)}
        body = Pulls(chunks=1)
        async with client_for(app) as client:
            answer = await client.post("/mcp/", content=body, headers=headers)
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/mcp/"}
        assert body.pulled == 0

    async def test_a_caller_past_the_edge_is_refused_before_a_length_is_looked_at(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "origin_secret", "the-edge-secret")
        headers = {"Content-Type": "application/json", "Content-Length": str(2 * DEFAULT_MAX_BODY_BYTES)}
        async with client_for(app) as client:
            direct = await client.post("/feedback", content=Pulls(chunks=1), headers=headers)
            through_the_edge = await client.post(
                "/feedback", content=Pulls(chunks=1), headers={**headers, ORIGIN_SECRET_HEADER: "the-edge-secret"}
            )
        assert direct.status_code == 403
        assert through_the_edge.status_code == 413


class TestTheLog:
    """A body the bound ended is not a fault of the service."""

    def test_a_client_that_went_away_is_no_error_record(self) -> None:
        logger = logging.getLogger("test.body_limit.filter")
        logger.addFilter(ClientGoneFilter())
        kept: list[logging.LogRecord] = []

        class Keep(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                kept.append(record)

        handler = Keep()
        logger.addHandler(handler)
        try:
            for fault in (ClientDisconnect(), ValueError("a real fault")):
                try:
                    raise fault
                except Exception:
                    logger.exception("Error handling POST request")
            logger.error("an error without an exception")
        finally:
            logger.removeHandler(handler)
        assert [record.getMessage() for record in kept] == [
            "Error handling POST request",
            "an error without an exception",
        ]
        assert isinstance(kept[0].exc_info[1], ValueError)

    def test_the_mcp_transport_has_the_filter(self) -> None:
        filters = logging.getLogger("mcp.server.streamable_http").filters
        assert any(isinstance(entry, ClientGoneFilter) for entry in filters)


class TestTheTable:
    """Which paths get which cap, held against the app's own routes."""

    DATA_ROUTES = {"upload_dataset": MAX_PASTE_BODY_BYTES, "convert_dataset_file": MAX_REQUEST_BODY_BYTES}
    """The endpoints that carry data, by name (the file conversion declares no body model), and the body each needs."""

    @staticmethod
    def middleware() -> BodyLimitMiddleware:
        (entry,) = [m for m in fastapi_app.user_middleware if m.cls is BodyLimitMiddleware]
        return BodyLimitMiddleware(lambda scope, receive, send: None, *entry.args, **entry.kwargs)

    @staticmethod
    def concrete(path: str) -> str:
        """A route's path as a request writes it, every parameter filled in."""
        return re.sub(r"\{[^}]+\}", "x1", path)

    @staticmethod
    def as_sent(payload: object) -> bytes:
        """A body as a browser writes it: no spaces, and only the escapes JSON needs."""
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def test_the_two_lanes_take_the_default_and_answer_with_their_own_code(self) -> None:
        middleware = self.middleware()
        assert dict(middleware.prefixes) == BODY_PREFIXES
        assert set(BODY_PREFIXES) == set(AGENT_PREFIXES) == {agent.router.prefix, agent_public.router.prefix}
        for bound in BODY_PREFIXES.values():
            assert bound == Bound(DEFAULT_MAX_BODY_BYTES, detail="too_long")
        assert middleware.default == Bound(DEFAULT_MAX_BODY_BYTES)

    def test_large_bodies_have_the_places_the_chat_names(self) -> None:
        places = self.middleware().large
        assert places is not None
        assert (places.places, places.above) == (MAX_LARGE_BODIES, DEFAULT_MAX_BODY_BYTES)
        assert (places.stall_s, places.body_s) == (LARGE_BODY_STALL_S, LARGE_BODY_TOTAL_S)
        # The largest body, the file as it is sent, arrives in its time on a line of half a megabit a second.
        assert MAX_REQUEST_BODY_BYTES * 8 / LARGE_BODY_TOTAL_S < 500_000

    def test_only_the_data_routes_of_the_two_lanes_take_more_than_the_default(self) -> None:
        """A new route that carries data, a rule that reaches a route it was not written for, or
        a wide prefix added for one route would change a line here."""
        middleware = self.middleware()
        routes = [route for route in api_routes(fastapi_app.routes) if route.methods - {"GET", "HEAD", "OPTIONS"}]
        assert any(route.path.startswith("/feedback") for route in routes), "routes outside the lanes are looked at"
        bounds = {
            (route.path, route.endpoint.__name__): middleware.bound_for(self.concrete(route.path)) for route in routes
        }
        wide = {key: bound for key, bound in bounds.items() if bound.max_bytes > DEFAULT_MAX_BODY_BYTES or bound.large}
        in_a_lane = tuple(prefix + "/" for prefix in AGENT_PREFIXES)
        assert set(wide) == {
            (path, name) for path, name in bounds if name in self.DATA_ROUTES and path.startswith(in_a_lane)
        }
        assert len(wide) == 2 * len(self.DATA_ROUTES), "the paste and the file conversion, on each lane"
        for (_, name), bound in wide.items():
            assert bound == Bound(
                self.DATA_ROUTES[name],
                detail="too_long",
                large=True,
                length_detail="length_required",
                busy_detail="capacity",
                slow_detail="upload_timeout",
            )

    @pytest.mark.parametrize("doubled", ["\n", "\t", "\r", '"', "\\"])
    def test_the_largest_paste_the_route_accepts_passes_its_bound(self, doubled: str) -> None:
        """The text at its cap in characters that are each sent as two bytes, the file name at its
        cap in characters that are each sent as six, and the fields beside them at their longest."""
        body = self.as_sent(
            {
                "text": doubled * MAX_DATASET_BYTES,
                "confirmed": False,
                "source": LONGEST * MAX_SOURCE_CHARS,
                "table": MAX_DATASET_TABLES,
            }
        )
        parsed = DatasetBody.model_validate_json(body)
        assert len(parsed.text.encode("utf-8")) == MAX_DATASET_BYTES
        assert len(body) <= MAX_PASTE_BODY_BYTES
        # The bound is the body the route needs, with little to spare.
        assert MAX_PASTE_BODY_BYTES - len(body) < 1024

    def test_the_largest_file_the_route_accepts_passes_its_bound(self) -> None:
        body = self.as_sent(
            {"data_base64": "A" * (MAX_CONVERT_BASE64_CHARS - 1) + "=", "sheet": LONGEST * MAX_SHEET_NAME_CHARS}
        )
        parsed = ConvertBody.model_validate_json(body)
        assert len(base64.b64decode(parsed.data_base64, validate=True)) == MAX_CONVERT_BYTES
        assert len(body) <= MAX_REQUEST_BODY_BYTES

    def test_every_other_body_of_the_lanes_is_far_below_the_default(self) -> None:
        """The largest bodies beside the data: every column binding with its name at its longest,
        and a chat message of the longest characters."""
        bindings = self.as_sent([{"role": "r" * 32, "column": LONGEST * 64} for _ in range(50)])
        message = self.as_sent({"text": LONGEST * MAX_MESSAGE_CHARS, "action": None})
        assert len(TypeAdapter(list[Binding]).validate_json(bindings)) == 50
        assert MessageBody.model_validate_json(message).text is not None
        for body in (bindings, message):
            assert 2 * len(body) < DEFAULT_MAX_BODY_BYTES

    def test_every_other_body_is_far_below_the_default(self) -> None:
        """The default has to hold the largest body a route outside the agent lanes accepts: the
        feedback form's fields at four bytes a character, with room for the JSON around them."""
        from api.routers import feedback

        largest = 4 * (feedback.MAX_MESSAGE_LENGTH + feedback.MAX_CONTACT_LENGTH) + 4096
        assert largest < DEFAULT_MAX_BODY_BYTES
