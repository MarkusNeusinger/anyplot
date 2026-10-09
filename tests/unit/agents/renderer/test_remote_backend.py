"""Tests for agents/anyplot/render/backends/remote.py against the renderer app, in process.

The backend talks to `agents.renderer.main.app` through httpx's ASGI transport, so
the caller check, the contract and the slot are the real ones; only the executor is
a fake, except in the end-to-end test, which runs the real executor with the fake
launcher and the real harness.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import google.auth.exceptions
import google.oauth2.credentials
import httpx
import pytest

from agents.anyplot.render.backends import remote as remote_module
from agents.anyplot.render.backends.remote import IdTokenSource, RemoteBackend, token_expiry
from agents.anyplot.render.contract import RendererUnavailable, RenderJob
from agents.anyplot.render.gates import evaluate
from agents.anyplot.render.serial import SerialRenderer
from agents.renderer.executor import ExecutorConfig, SandboxExecutor
from agents.renderer.main import Renderer, app, get_renderer
from agents.renderer.settings import RendererSettings, get_settings

from .helpers import AGENTS_SA, CANVAS_PLOT, URL, FakeExecutor, id_token


GOOD = id_token(aud=URL, email=AGENTS_SA)


class StaticTokens:
    def __init__(self, token: str = GOOD) -> None:
        self.value = token
        self.calls = 0

    async def token(self) -> str:
        self.calls += 1
        return self.value


class Flaky(httpx.AsyncBaseTransport):
    """Fails the first `failures` requests with `error`, then hands over to `inner`."""

    def __init__(self, inner: httpx.AsyncBaseTransport, failures: int, error: type[httpx.TransportError]) -> None:
        self.inner = inner
        self.failures = failures
        self.error = error
        self.requests = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        if self.requests <= self.failures:
            raise self.error("connection refused", request=request)
        return await self.inner.handle_async_request(request)


def render_job(**overrides: Any) -> RenderJob:
    values: dict[str, Any] = {
        "job_id": "job123",
        "language": "python",
        "library": "matplotlib",
        "source": CANVAS_PLOT,
        "data_csv": "x,y\n1,2\n",
        "themes": ("light",),
        "timeout_s": 30.0,
    }
    return RenderJob(**{**values, **overrides})


@pytest.fixture
def settings() -> RendererSettings:
    return RendererSettings(
        environment="production", audiences=[URL], allowed_callers=[AGENTS_SA], min_mem_available_mb=0
    )


@pytest.fixture
def fake() -> FakeExecutor:
    return FakeExecutor()


@pytest.fixture
def renderer(settings: RendererSettings, fake: FakeExecutor) -> Renderer:
    return Renderer(settings, fake)


@pytest.fixture
def overrides(settings: RendererSettings, renderer: Renderer) -> Iterator[None]:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_renderer] = lambda: renderer
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def backend(overrides: None) -> AsyncIterator[RemoteBackend]:
    backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=httpx.ASGITransport(app=app), retry_delay_s=0)
    yield backend
    await backend.aclose()


class TestRoundTrip:
    async def test_a_render_comes_back_as_a_render_result_the_gates_accept(
        self, backend: RemoteBackend, fake: FakeExecutor
    ) -> None:
        result = await backend.render(render_job(themes=("light", "dark")))

        assert result.job_id == "job123" and set(result.outputs) == {"light", "dark"}
        light = result.outputs["light"]
        assert light.exit_code == 0 and light.png is not None and light.png.startswith(b"\x89PNG")
        assert light.probe == {"texts": [], "tick_overlaps": 0, "points": 0} and light.wall_s == 0.5
        report = evaluate(result, themes=("light", "dark"), library="matplotlib", rows=1)
        assert report.passed_host_gates and report.canvas_ok, report.blocking
        assert fake.calls == [("job123", "light"), ("job123", "dark")]

    async def test_behind_the_serial_renderer_each_theme_is_its_own_request(
        self, backend: RemoteBackend, fake: FakeExecutor
    ) -> None:
        serial = SerialRenderer(backend, concurrency=1)

        result = await serial.render(render_job(themes=("light", "dark")))

        assert set(result.outputs) == {"light", "dark"}
        assert isinstance(backend.tokens, StaticTokens) and backend.tokens.calls == 2

    async def test_end_to_end_with_the_real_executor_and_harness(
        self, overrides: None, settings: RendererSettings, config: ExecutorConfig
    ) -> None:
        app.dependency_overrides[get_renderer] = lambda: Renderer(settings, SandboxExecutor(config))
        backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=httpx.ASGITransport(app=app))
        try:
            result = await backend.render(render_job(themes=("dark",)))
        finally:
            await backend.aclose()

        report = evaluate(result, themes=("dark",), library="matplotlib", rows=1)
        assert report.passed_host_gates and report.canvas_ok, (report.blocking, result.outputs["dark"].stderr_tail)
        assert result.outputs["dark"].probe is not None and result.outputs["dark"].probe["canvas"] == [3200, 1800]


class TestFailures:
    async def test_a_refused_caller_is_unavailable(self, overrides: None) -> None:
        backend = RemoteBackend(
            url=URL,
            tokens=StaticTokens(id_token(aud=URL, email="someone@example.com")),
            transport=httpx.ASGITransport(app=app),
        )
        with pytest.raises(RendererUnavailable, match="refused this caller"):
            await backend.render(render_job())
        await backend.aclose()

    async def test_one_connection_error_is_retried(self, overrides: None) -> None:
        transport = Flaky(httpx.ASGITransport(app=app), failures=1, error=httpx.ConnectError)
        backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=transport, retry_delay_s=0)

        result = await backend.render(render_job())

        assert result.outputs["light"].exit_code == 0 and transport.requests == 2
        await backend.aclose()

    async def test_a_second_connection_error_is_unavailable(self, overrides: None) -> None:
        transport = Flaky(httpx.ASGITransport(app=app), failures=2, error=httpx.ConnectError)
        backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=transport, retry_delay_s=0)

        with pytest.raises(RendererUnavailable, match=r"could not be reached \(ConnectError\)"):
            await backend.render(render_job())
        assert transport.requests == 2
        await backend.aclose()

    async def test_a_front_end_error_is_retried_but_the_renderers_own_is_not(self) -> None:
        answers = [
            httpx.Response(429, text="<html>no available instance</html>", headers={"content-type": "text/html"}),
            httpx.Response(503, json={"detail": "busy"}),
        ]
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers["authorization"])
            return answers[len(seen) - 1]

        backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=httpx.MockTransport(handler), retry_delay_s=0)

        with pytest.raises(RendererUnavailable, match="HTTP 503, busy"):
            await backend.render(render_job())
        assert seen == [f"Bearer {GOOD}"] * 2
        await backend.aclose()

    @pytest.mark.parametrize(
        ("answer", "message"),
        [
            (httpx.Response(200, text="not json"), "does not match the contract"),
            (httpx.Response(500, text="<html>Server Error</html>"), "HTTP 500"),
        ],
    )
    async def test_malformed_or_failed_answers_are_unavailable(self, answer: httpx.Response, message: str) -> None:
        backend = RemoteBackend(
            url=URL, tokens=StaticTokens(), transport=httpx.MockTransport(lambda request: answer), retry_delay_s=0
        )

        with pytest.raises(RendererUnavailable, match=message):
            await backend.render(render_job())
        await backend.aclose()

    async def test_an_answer_for_another_job_is_refused(self) -> None:
        def other(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"job_id": "other", "outputs": {}, "timings": {"slot_wait_s": 0, "total_s": 0}, "version": "x"},
            )

        stray = RemoteBackend(url=URL, tokens=StaticTokens(), transport=httpx.MockTransport(other))
        with pytest.raises(RendererUnavailable, match="another job"):
            await stray.render(render_job())
        await stray.aclose()

    async def test_a_theme_without_an_answer_is_left_for_r1(self) -> None:
        def light_only(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "job_id": "job123",
                    "outputs": {"light": {"theme": "light", "exit_code": 1, "png_base64": "%%%"}},
                    "timings": {"slot_wait_s": 0, "total_s": 0},
                    "version": "x",
                },
            )

        backend = RemoteBackend(url=URL, tokens=StaticTokens(), transport=httpx.MockTransport(light_only))
        result = await backend.render(render_job(themes=("light", "dark")))
        await backend.aclose()

        assert set(result.outputs) == {"light"} and result.outputs["light"].png is None  # undecodable base64
        report = evaluate(result, themes=("light", "dark"), library="matplotlib", rows=1)
        assert not report.passed_host_gates
        assert any("dark" in line and "no output" in line for line in report.blocking)

    async def test_a_job_outside_the_contract_never_leaves(self) -> None:
        calls: list[httpx.Request] = []
        backend = RemoteBackend(
            url=URL,
            tokens=StaticTokens(),
            transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(500)),
        )

        with pytest.raises(RendererUnavailable, match="language"):
            await backend.render(render_job(language="r"))
        assert calls == []
        await backend.aclose()


class FakeIdCredentials:
    """What `fetch_id_token_credentials` returns: refresh() sets `token`."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.token: str | None = None
        self.refreshes = 0

    def refresh(self, request: object) -> None:
        self.token = self.tokens[self.refreshes]
        self.refreshes += 1


class FakeUserCredentials(google.oauth2.credentials.Credentials):
    """A user's Application Default Credentials: refresh() brings an ID token for the ADC client."""

    def __init__(self, token: str | None) -> None:
        super().__init__(token=None)
        self.next_id_token = token

    def refresh(self, request: object) -> None:
        self._id_token = self.next_id_token


class TestIdTokens:
    async def test_a_static_token_is_sent_until_it_expires(self) -> None:
        source = IdTokenSource(URL, development=True, static_token=GOOD)
        assert await source.token() == GOOD

        expired = IdTokenSource(URL, development=True, static_token=id_token(exp=1))
        with pytest.raises(RendererUnavailable, match="AGENT_RENDER_TOKEN has expired"):
            await expired.token()

    async def test_deployed_tokens_come_from_the_metadata_server_and_are_cached(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        now = 1_800_000_000.0
        first, second = id_token(aud=URL, exp=int(now) + 3600), id_token(aud=URL, exp=int(now) + 7200)
        credentials = FakeIdCredentials([first, second])
        audiences: list[str] = []

        def fetch(audience: str, request: object = None) -> FakeIdCredentials:
            audiences.append(audience)
            return credentials

        monkeypatch.setattr(remote_module.google_id_token, "fetch_id_token_credentials", fetch)
        clock = [now]
        source = IdTokenSource(URL, development=False, clock=lambda: clock[0])

        assert await source.token() == first
        assert await source.token() == first  # cached
        clock[0] = now + 3600 - 120  # inside the refresh margin
        assert await source.token() == second
        assert audiences == [URL, URL] and credentials.refreshes == 2

    async def test_development_uses_the_users_adc_id_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        user_token = id_token(aud="764086051850-adc.apps.googleusercontent.com", email="owner@example.com")
        monkeypatch.setattr("google.auth.default", lambda: (FakeUserCredentials(user_token), "anyplot"))

        def no_fetch(*args: object, **kwargs: object) -> None:
            raise AssertionError("a user's ADC never go through the metadata path")

        monkeypatch.setattr(remote_module.google_id_token, "fetch_id_token_credentials", no_fetch)

        assert await IdTokenSource(URL, development=True).token() == user_token

    async def test_adc_without_an_id_token_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        monkeypatch.setattr("google.auth.default", lambda: (FakeUserCredentials(None), "anyplot"))

        with pytest.raises(RendererUnavailable, match="carry no ID token"):
            await IdTokenSource(URL, development=True).token()

    async def test_missing_credentials_are_unavailable_with_a_hint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def broken(*args: object, **kwargs: object) -> None:
            raise google.auth.exceptions.DefaultCredentialsError("no credentials")

        monkeypatch.setattr(remote_module.google_id_token, "fetch_id_token_credentials", broken)

        with pytest.raises(RendererUnavailable, match="DefaultCredentialsError"):
            await IdTokenSource(URL, development=False).token()

    def test_token_expiry(self) -> None:
        assert token_expiry(id_token(exp=1234)) == 1234.0
        assert token_expiry("not-a-token") is None
        assert token_expiry("a.%%%.c") is None


def test_tokens_are_minted_off_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """google-auth blocks; minting must run in a worker thread."""
    threads: list[bool] = []

    def fetch(audience: str, request: object = None) -> FakeIdCredentials:
        try:
            asyncio.get_running_loop()
            threads.append(False)
        except RuntimeError:
            threads.append(True)
        return FakeIdCredentials([GOOD])

    monkeypatch.setattr(remote_module.google_id_token, "fetch_id_token_credentials", fetch)

    assert asyncio.run(IdTokenSource(URL, development=False).token()) == GOOD
    assert threads == [True]
