"""The bound on request bodies: refused before they are read, or cut off while they stream.

Two halves. The first holds `BodyLimitMiddleware` against a small app that records what reaches it,
because "refused" is only worth something if the bytes were never taken. The second sends through
the real `api.main` app, where the position in the middleware stack and the framework's own
handling of a failed body read decide what a client sees.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from api.body_limit import DEFAULT_MAX_BODY_BYTES, TOO_LARGE, BodyLimitMiddleware, BodyTooLarge, Bound
from api.main import app
from api.origin_gate import ORIGIN_SECRET_HEADER
from api.routers.agent import MAX_REQUEST_BODY_BYTES
from core.config import settings


CAP = 100
CHUNK = 16


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
        assert answer.json()["message"] == TOO_LARGE
        # The reading stopped where the cap was passed, not at the body's end.
        assert body.pulled <= CAP // CHUNK + 2
        assert recorder.read == 0

    @pytest.mark.parametrize(
        "lengths",
        [
            [b"lots"],
            [b"-1"],
            # Two that differ: a refusal that read only the first would let the second decide.
            [b"0", b"100000"],
            [b"100000", b"0"],
        ],
    )
    async def test_a_length_nobody_can_go_by_is_a_bad_request(self, bounded, recorder, lengths) -> None:
        headers = [(b"content-length", value) for value in lengths]
        scope = {"type": "http", "method": "POST", "path": "/x", "headers": headers}
        sent: list[dict] = []

        async def receive() -> dict:
            raise AssertionError("the body must not be read")

        async def send(message: dict) -> None:
            sent.append(message)

        await bounded(scope, receive, send)
        assert sent[0]["status"] == 400
        assert recorder.calls == 0

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

    async def test_the_same_length_stated_twice_is_one_length(self, bounded, recorder) -> None:
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/x",
            "headers": [(b"content-length", b"3"), (b"content-length", b"3")],
        }
        messages = [{"type": "http.request", "body": b"abc", "more_body": False}]
        sent: list[dict] = []

        async def receive() -> dict:
            return messages.pop(0)

        async def send(message: dict) -> None:
            sent.append(message)

        await bounded(scope, receive, send)
        assert sent[0]["status"] == 200
        assert recorder.read == 3

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

    async def test_a_prefix_takes_what_the_default_refuses(self, bounded, recorder) -> None:
        async with client_for(bounded) as client:
            narrow = await client.post("/x", content=b"a" * (CAP + 1))
            wide = await client.post("/wide/open", content=b"a" * (CAP + 1))
        assert narrow.status_code == 413
        assert wide.status_code == 200

    async def test_an_app_that_lets_the_cut_through_still_gets_the_413(self) -> None:
        async def careless(scope: Scope, receive: Receive, send: Send) -> None:
            await Request(scope, receive).body()

        async with client_for(BodyLimitMiddleware(careless, default=CAP)) as client:
            answer = await client.post("/x", content=Pulls(chunks=500))
        assert answer.status_code == 413

    async def test_a_cut_after_the_answer_began_is_not_answered_twice(self) -> None:
        async def answers_first(scope: Scope, receive: Receive, send: Send) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await Request(scope, receive).body()

        transport = httpx.ASGITransport(app=BodyLimitMiddleware(answers_first, default=CAP))
        async with httpx.AsyncClient(transport=transport, base_url="https://api.anyplot.ai") as client:
            with pytest.raises(BodyTooLarge):
                await client.post("/x", content=Pulls(chunks=500))


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

    async def test_a_body_without_a_length_gets_the_413_and_is_not_read_to_its_end(self) -> None:
        """A route with a body model has its body read by the framework, which turns most errors of
        that read into its own 400. The cut has to arrive as the 413 it is, and the read has to stop."""
        chunks = 64
        body = Pulls(chunks=chunks, size=DEFAULT_MAX_BODY_BYTES // 4)
        async with client_for(app) as client:
            answer = await client.post("/feedback", content=body, headers={"Content-Type": "application/json"})
        assert answer.status_code == 413
        assert answer.json() == {"status": 413, "message": TOO_LARGE, "path": "/feedback"}
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
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(2 * DEFAULT_MAX_BODY_BYTES),
            "Origin": "https://anyplot.ai",
        }
        async with client_for(app) as client:
            answer = await client.post("/feedback", content=Pulls(chunks=1), headers=headers)
        assert answer.status_code == 413
        assert answer.headers["access-control-allow-origin"] == "https://anyplot.ai"

    @pytest.mark.parametrize("path", ["/agent/session/dataset", "/debug/agent/sessions"])
    async def test_the_agent_lanes_keep_their_cap_and_their_own_answer(self, path: str) -> None:
        """Nothing a lane accepts today is refused, and a body above its cap is answered with the
        code the chat page reads from those routes, whether it declares its length or not."""
        json_body = {"Content-Type": "application/json"}
        chunk = 256 * 1024
        streamed_body = Pulls(chunks=4 * (MAX_REQUEST_BODY_BYTES // chunk), size=chunk)
        async with client_for(app) as client:
            # What the default would refuse still reaches the lane, which answers for itself.
            within = await client.post(path, content=b"a" * (2 * DEFAULT_MAX_BODY_BYTES), headers=json_body)
            declared = await client.post(
                path, content=Pulls(chunks=1), headers={**json_body, "Content-Length": str(MAX_REQUEST_BODY_BYTES + 1)}
            )
            streamed = await client.post(path, content=streamed_body, headers=json_body)
        assert within.status_code != 413
        for above in (declared, streamed):
            assert above.status_code == 413
            assert above.json() == {"detail": "too_long"}
        assert streamed_body.pulled <= MAX_REQUEST_BODY_BYTES // chunk + 2

    async def test_the_mcp_server_is_bounded_like_any_other_path(self) -> None:
        headers = {"Content-Type": "application/json", "Content-Length": str(2 * DEFAULT_MAX_BODY_BYTES)}
        body = Pulls(chunks=1)
        async with client_for(app) as client:
            answer = await client.post("/mcp/", content=body, headers=headers)
        assert answer.status_code == 413
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


def test_every_other_body_is_far_below_the_default() -> None:
    """The default has to hold the largest body a route outside the agent lanes accepts: the
    feedback form's fields at four bytes a character, with room for the JSON around them."""
    from api.routers import feedback

    largest = 4 * (feedback.MAX_MESSAGE_LENGTH + feedback.MAX_CONTACT_LENGTH) + 4096
    assert largest < DEFAULT_MAX_BODY_BYTES
